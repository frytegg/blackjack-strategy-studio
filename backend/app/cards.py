# backend/app/cards.py

from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

# Représentation des cartes :
# - 2–10 pour les cartes numériques
# - 10 représente aussi J/Q/K (même valeur)
# - 11 représente l'As (A)
ACE_VALUE: int = 11

# Valeurs possibles des cartes pour joueur et croupier
CARD_VALUES: List[int] = [2, 3, 4, 5, 6, 7, 8, 9, 10, ACE_VALUE]

# Upcards du croupier (2–10, A)
DEALER_UPCARDS: List[int] = CARD_VALUES[:]  # 2-10, 11(A)

# Probabilités par valeur, modèle "paquet infini" / sabot complet sans suivi :
# - 2–9 : 4 cartes sur 52 => 4/52 => 1/13
# - 10/J/Q/K : 16 cartes sur 52 => 16/52 => 4/13
# - A : 4 cartes sur 52 => 4/52 => 1/13
_CARD_COPIES: Dict[int, int] = {
    2: 4,
    3: 4,
    4: 4,
    5: 4,
    6: 4,
    7: 4,
    8: 4,
    9: 4,
    10: 16,  # 10, J, Q, K
    ACE_VALUE: 4,
}
_TOTAL_COPIES: int = sum(_CARD_COPIES.values())

CARD_PROBABILITIES: Dict[int, float] = {
    value: copies / _TOTAL_COPIES for value, copies in _CARD_COPIES.items()
}


def card_probability(card_value: int) -> float:
    """
    Retourne la probabilité de tirer une carte de valeur donnée.
    card_value doit être dans CARD_VALUES.
    """
    try:
        return CARD_PROBABILITIES[card_value]
    except KeyError:
        raise ValueError(f"Valeur de carte invalide: {card_value!r}")


def all_card_probabilities() -> Dict[int, float]:
    """
    Copie du dict des probabilités par valeur de carte.
    """
    return dict(CARD_PROBABILITIES)


def is_bust(total: int) -> bool:
    """
    Indique si un total est un bust (> 21).
    """
    return total > 21


def add_card_to_total(total: int, is_soft: bool, card_value: int) -> Tuple[int, bool]:
    """
    Calcule le nouveau total et le statut soft/hard après avoir tiré une carte.

    Paramètres
    ----------
    total : int
        Total actuel "effectif" (en tenant compte des As déjà optimisés).
    is_soft : bool
        True si le total actuel est "soft" (au moins un As compté 11).
    card_value : int
        Valeur de la carte tirée (2–10, ACE_VALUE=11).

    Retourne
    --------
    new_total : int
    new_is_soft : bool

    Logique
    -------
    - Si la carte n'est pas un As :
      * on additionne;
      * si on dépasse 21 et que la main était soft, on convertit un As de 11 en 1
        (on soustrait 10 et la main devient hard).
    - Si la carte est un As :
      * si total + 11 <= 21: l'As est compté 11 (main soft).
      * sinon, l'As est compté 1 (total + 1), et on vérifie quand même si
        on doit convertir un As 11 existant en 1 (cas extrêmes).
    """
    if card_value not in CARD_VALUES:
        raise ValueError(f"Valeur de carte invalide: {card_value!r}")

    # Carte non As
    if card_value != ACE_VALUE:
        new_total = total + card_value
        new_is_soft = is_soft
        if new_is_soft and new_total > 21:
            # On convertit un As de 11 en 1
            new_total -= 10
            new_is_soft = False
        return new_total, new_is_soft

    # Carte = As
    # Essayer de la compter comme 11 si possible
    if total + 11 <= 21:
        return total + 11, True

    # Sinon, on la compte comme 1
    new_total = total + 1
    new_is_soft = is_soft
    if new_is_soft and new_total > 21:
        # On convertit un As de 11 en 1 si nécessaire
        new_total -= 10
        new_is_soft = False
    return new_total, new_is_soft


def initial_hand_total(cards: Iterable[int]) -> Tuple[int, bool]:
    """
    Calcule le total et le statut soft/hard d'une main de départ à partir
    d'une séquence de valeurs de cartes.

    Utile surtout pour les tests ou pour construire des PlayerState à partir
    de cartes explicites.
    """
    total = 0
    is_soft = False
    for c in cards:
        total, is_soft = add_card_to_total(total, is_soft, c)
    return total, is_soft
