# backend/app/dealer_model.py

from __future__ import annotations

from functools import lru_cache
from typing import Dict, Tuple, Union

from .cards import (
    ACE_VALUE,
    CARD_VALUES,
    CARD_PROBABILITIES,
    add_card_to_total,
)
from .rules import Rules

# Clé de sortie : 17, 18, 19, 20, 21, ou "bust"
OutcomeKey = Union[int, str]

_STAND_TOTALS = (17, 18, 19, 20, 21)
_OUTCOME_KEYS: Tuple[OutcomeKey, ...] = (17, 18, 19, 20, 21, "bust")


def _tuple_to_distribution(dist_tuple: Tuple[float, float, float, float, float, float]) -> Dict[OutcomeKey, float]:
    """
    Convertit la forme tuple interne (p17, p18, p19, p20, p21, pbust)
    en dict {17: p17, 18: p18, ... , "bust": pbust}.
    """
    return {key: value for key, value in zip(_OUTCOME_KEYS, dist_tuple)}


@lru_cache(maxsize=None)
def _dealer_state_distribution(
    total: int,
    is_soft: bool,
    hits_soft_17: bool,
) -> Tuple[float, float, float, float, float, float]:
    """
    Distribution finale du croupier (p17, p18, p19, p20, p21, pbust)
    à partir d'un état (total, is_soft), en appliquant la règle H17/S17.

    Modèle de tirage : paquet infini (probabilités CARD_PROBABILITIES).
    La distinction "natural blackjack" (2 cartes) vs 21 obtenu en tirant
    des cartes supplémentaires n'est pas modélisée ici : 21 est 21.
    """

    # Bust direct
    if total > 21:
        return (0.0, 0.0, 0.0, 0.0, 0.0, 1.0)

    # Décision de s'arrêter ou de continuer à tirer
    if total >= 17:
        if total == 17 and is_soft and hits_soft_17:
            # Soft 17 et règle H17 : le croupier doit tirer
            pass
        else:
            # Le croupier s'arrête sur ce total
            p17 = 1.0 if total == 17 else 0.0
            p18 = 1.0 if total == 18 else 0.0
            p19 = 1.0 if total == 19 else 0.0
            p20 = 1.0 if total == 20 else 0.0
            p21 = 1.0 if total == 21 else 0.0
            pbust = 0.0
            return (p17, p18, p19, p20, p21, pbust)

    # Le croupier doit tirer une carte
    acc = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]  # p17, p18, p19, p20, p21, pbust
    for card_value, p_card in CARD_PROBABILITIES.items():
        new_total, new_is_soft = add_card_to_total(total, is_soft, card_value)
        sub = _dealer_state_distribution(new_total, new_is_soft, hits_soft_17)
        for i in range(6):
            acc[i] += p_card * sub[i]

    # Normalisation défensive (somme proche de 1)
    s = sum(acc)
    if s > 0:
        acc = [x / s for x in acc]

    return tuple(acc)  # type: ignore[return-value]


@lru_cache(maxsize=None)
def _dealer_distribution_cached(
    upcard: int,
    rules_signature: Tuple,
    hits_soft_17: bool,
) -> Tuple[float, float, float, float, float, float]:
    """
    Distribution finale du croupier (p17, p18, p19, p20, p21, pbust)
    conditionnée sur l'upcard donnée et les règles (via signature).

    Hypothèses :
    ------------
    - Modèle paquet infini : la carte fermée (hole card) est tirée avec les
      probabilités CARD_PROBABILITIES, indépendamment de l'upcard.
    - On ne suit pas la composition exacte du sabot.
    - CSM ou non ne change donc pas cette distribution dans notre modèle.
    """

    if upcard not in CARD_VALUES:
        raise ValueError(f"Upcard invalide: {upcard!r}")

    # On construit d'abord l'état à partir de l'upcard seule,
    # puis on ajoute la hole card.
    total0, is_soft0 = add_card_to_total(0, False, upcard)

    acc = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    for hole_value, p_hole in CARD_PROBABILITIES.items():
        total, is_soft = add_card_to_total(total0, is_soft0, hole_value)
        sub = _dealer_state_distribution(total, is_soft, hits_soft_17)
        for i in range(6):
            acc[i] += p_hole * sub[i]

    # Normalisation défensive
    s = sum(acc)
    if s > 0:
        acc = [x / s for x in acc]

    return tuple(acc)  # type: ignore[return-value]


def get_dealer_distribution(upcard: int, rules: Rules) -> Dict[OutcomeKey, float]:
    """
    Retourne la distribution finale du croupier pour une upcard donnée,
    sous la forme d'un dict :

        {
            17: p17,
            18: p18,
            19: p19,
            20: p20,
            21: p21,
            "bust": pbust,
        }

    C'est la distribution "inconditionnelle" : elle inclut le cas où le
    croupier a un blackjack naturel (21 en 2 cartes) pour upcard 10/A.
    """
    dist_tuple = _dealer_distribution_cached(
        upcard,
        rules.signature(),
        rules.dealer_hits_soft_17,
    )
    return _tuple_to_distribution(dist_tuple)


def dealer_blackjack_probability(upcard: int) -> float:
    """
    Probabilité que le croupier ait un blackjack naturel (21 en 2 cartes)
    compte tenu de l'upcard, dans le modèle paquet infini.

    - upcard = 10  -> hole card = As
    - upcard = As  -> hole card = 10 (10/J/Q/K)
    - sinon -> 0
    """
    if upcard == 10:
        return CARD_PROBABILITIES[ACE_VALUE]
    if upcard == ACE_VALUE:
        return CARD_PROBABILITIES[10]
    return 0.0


@lru_cache(maxsize=None)
def _dealer_distribution_no_blackjack_cached(
    upcard: int,
    rules_signature: Tuple,
    hits_soft_17: bool,
) -> Tuple[float, float, float, float, float, float]:
    """
    Distribution finale du croupier conditionnée au fait qu'il n'a PAS
    de blackjack naturel, pour un upcard et des règles donnés.

    Utilisée pour modéliser le jeu US avec hole card + peek :
    le joueur prend ses décisions après que le croupier a vérifié qu'il
    n'avait pas blackjack sur 10/A.
    """
    base = _dealer_distribution_cached(upcard, rules_signature, hits_soft_17)
    pbj = dealer_blackjack_probability(upcard)

    # Si aucun risque de blackjack naturel, la distribution est identique.
    if pbj <= 0.0:
        return base

    p17, p18, p19, p20, p21, pbust = base
    # Partie de 21 liée au blackjack naturel
    p21_non_bj = max(0.0, p21 - pbj)
    denom = 1.0 - pbj
    if denom <= 0.0:
        # Cas pathologique (ne devrait pas arriver), on renvoie base.
        return base

    return (
        p17 / denom,
        p18 / denom,
        p19 / denom,
        p20 / denom,
        p21_non_bj / denom,
        pbust / denom,
    )


def get_dealer_distribution_no_blackjack(upcard: int, rules: Rules) -> Dict[OutcomeKey, float]:
    """
    Distribution finale du croupier conditionnée à "pas de blackjack naturel".

    - Pour upcard 10/A, on retire le poids du blackjack naturel de la case 21,
      puis on renormalise.
    - Pour les autres upcards, c'est identique à get_dealer_distribution().
    """
    dist_tuple = _dealer_distribution_no_blackjack_cached(
        upcard,
        rules.signature(),
        rules.dealer_hits_soft_17,
    )
    return _tuple_to_distribution(dist_tuple)
