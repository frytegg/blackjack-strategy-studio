# backend/app/strategy_engine.py

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Dict, List

from .cards import (
    ACE_VALUE,
    CARD_VALUES,
    CARD_PROBABILITIES,
    DEALER_UPCARDS,
    add_card_to_total,
    is_bust,
)
from .dealer_model import (
    get_dealer_distribution,
    get_dealer_distribution_no_blackjack,
)
from .player_state import HandType, PlayerState
from .rules import Rules


class Action(str, Enum):
    HIT = "H"
    STAND = "S"
    DOUBLE = "D"
    SPLIT = "P"
    SURRENDER = "R"


def _card_value_to_label(value: int) -> str:
    """
    Convertit une valeur de carte interne (2–10, 11=As) en étiquette "2".."10","A".
    """
    if value == ACE_VALUE:
        return "A"
    return str(value)


def _dealer_distribution_for_eval(dealer_upcard: int, rules: Rules) -> Dict:
    """
    Choisit la bonne distribution du croupier en fonction des règles :

    - european_no_hole_card = False  -> jeu US avec hole card + peek :
      on utilise la distribution conditionnelle "pas de blackjack naturel".
    - european_no_hole_card = True   -> ENHC :
      on utilise la distribution inconditionnelle (incluant les blackjacks naturels).
    """
    if rules.european_no_hole_card:
        return get_dealer_distribution(dealer_upcard, rules)
    else:
        return get_dealer_distribution_no_blackjack(dealer_upcard, rules)


def _ev_stand(state: PlayerState, dealer_upcard: int, rules: Rules) -> float:
    """
    EV du Stand pour l'état donné.
    Hypothèse : la mise de base vaut 1 unité.
    - Gain : +1
    - Perte : -1
    - Push : 0

    Différence ENHC / jeu US :
    - ENHC : on utilise la distribution inconditionnelle, l'EV inclut
      l'impact des blackjacks du croupier.
    - US (hole card + peek) : on conditionne sur "pas de blackjack", ce qui
      correspond à la situation réelle au moment où le joueur décide.
    """
    if state.total > 21:
        return -1.0  # bust déjà atteint

    player_total = state.total
    dist = _dealer_distribution_for_eval(dealer_upcard, rules)

    p_win = dist["bust"] + sum(
        prob for total, prob in dist.items()
        if isinstance(total, int) and 17 <= total <= 21 and total < player_total
    )
    p_push = sum(
        prob for total, prob in dist.items()
        if isinstance(total, int) and total == player_total
    )
    p_lose = 1.0 - p_win - p_push

    return p_win - p_lose


def _apply_hit(state: PlayerState, card_value: int) -> PlayerState | None:
    """
    Applique un Hit à un état joueur et retourne le nouvel état,
    ou None en cas de bust.

    Règles simplifiées :
    - Après un Hit, la main n'est plus considérée comme une paire.
    - Le double n'est plus autorisé (can_double=False).
    - On ne permet pas de split après un Hit (can_split=False).
    """
    # Interpréter la main actuelle comme hard/soft avant la carte
    if state.hand_type == HandType.PAIR:
        if state.pair_value == ACE_VALUE:
            base_total = 12
            is_soft = True
        else:
            base_total = 2 * (state.pair_value or 0)
            is_soft = False
    else:
        base_total = state.total
        is_soft = state.hand_type == HandType.SOFT

    new_total, new_is_soft = add_card_to_total(base_total, is_soft, card_value)
    if is_bust(new_total):
        return None

    new_hand_type = HandType.SOFT if new_is_soft else HandType.HARD

    return PlayerState(
        hand_type=new_hand_type,
        total=new_total,
        pair_value=None,
        from_split=state.from_split,
        from_split_aces=state.from_split_aces,
        can_double=False,  # après hit, plus de double
        can_split=False,   # plus de split
    )


def _ev_hit(state: PlayerState, dealer_upcard: int, rules: Rules) -> float:
    """
    EV d'un Hit à partir de l'état donné.
    """
    ev = 0.0
    for card_value, p_card in CARD_PROBABILITIES.items():
        new_state = _apply_hit(state, card_value)
        if new_state is None:
            ev += p_card * (-1.0)
        else:
            ev += p_card * V(new_state, dealer_upcard, rules)
    return ev


def _ev_double(state: PlayerState, dealer_upcard: int, rules: Rules) -> float:
    """
    EV d'un Double :
    - Le joueur reçoit exactement une carte supplémentaire, puis se tient (Stand).
    - La mise est doublée, donc l'EV finale est multipliée par 2.

    ENHC vs US :
    - ENHC : l'EV intègre les blackjacks du croupier dans la distribution.
    - US  : l'EV est conditionnée au fait que le croupier n'a pas blackjack
            (peek déjà fait). La différence entre les deux variantes est donc
            entièrement portée par _ev_stand() via la distribution utilisée.
    """
    ev_one_unit = 0.0
    for card_value, p_card in CARD_PROBABILITIES.items():
        new_state = _apply_hit(state, card_value)
        if new_state is None:
            ev_one_unit += p_card * (-1.0)
        else:
            # On se tient obligatoirement après la carte
            ev_one_unit += p_card * _ev_stand(new_state, dealer_upcard, rules)

    return 2.0 * ev_one_unit


def _ev_surrender() -> float:
    """
    EV d'un abandon : perte de la moitié de la mise.
    (On ne distingue pas ici finement ENHC/US pour le surrender.)
    """
    return -0.5


def _ev_split_non_aces(
    pair_value: int,
    dealer_upcard: int,
    rules: Rules,
) -> float:
    """
    EV du Split pour une paire non-As.

    Modélisation :
    --------------
    - On part d'une paire (v, v).
    - Après split, on obtient deux mains symétriques :
        - main 1 : v + c1
        - main 2 : v + c2
    - Chaque main est jouée de façon optimale selon V().
    - On ignore les re-splits (on met can_split=False sur les mains issues d'un split).
    - Si rules.allow_double_after_split est False, les mains issues du split
      n'ont pas le droit de doubler (can_double=False).

    EV(Split) = EV(main 1) + EV(main 2)
              = 2 * E[ EV(V(main_issue_du_split)) ]
    """
    total_ev_one_hand = 0.0

    for card_value, p_card in CARD_PROBABILITIES.items():
        # Construire la main v + card_value
        base_total, is_soft = add_card_to_total(0, False, pair_value)
        total, is_soft = add_card_to_total(base_total, is_soft, card_value)
        if is_bust(total):
            # Cette main est bust immédiatement (cas très rare avec v>=2 et une seule carte)
            ev_hand = -1.0
        else:
            hand_type = HandType.SOFT if is_soft else HandType.HARD
            split_hand_state = PlayerState(
                hand_type=hand_type,
                total=total,
                pair_value=None,
                from_split=True,
                from_split_aces=False,
                can_double=rules.allow_double_after_split,
                can_split=False,  # Pas de re-split dans cette version
            )
            ev_hand = V(split_hand_state, dealer_upcard, rules)

        total_ev_one_hand += p_card * ev_hand

    return 2.0 * total_ev_one_hand


def _ev_split_aces(
    dealer_upcard: int,
    rules: Rules,
) -> float:
    """
    EV du Split pour une paire d'As.

    Cas 1 : one_card_only_after_split_aces == True (le plus courant)
    ---------------------------------------------------------------
    - Chaque As reçoit exactement une carte.
    - Aucun Hit/Double/Split supplémentaire n'est autorisé.
    - On se tient (Stand) automatiquement après cette carte.
    - EV(Split AA) = 2 * E[ EV(Stand | A + c) ]

    Cas 2 : one_card_only_after_split_aces == False
    -----------------------------------------------
    - On traite les As comme une paire normale, avec possibilités de Hit/Double
      après split (selon allow_double_after_split). On réutilise alors la
      logique de _ev_split_non_aces(ACE_VALUE, ...).
    """
    if not rules.one_card_only_after_split_aces:
        # Traiter comme une paire générique
        return _ev_split_non_aces(ACE_VALUE, dealer_upcard, rules)

    # Cas "une seule carte par As, puis Stand"
    total_ev_one_hand = 0.0

    # Main de départ après split : un As (ACE_VALUE)
    base_total, is_soft = add_card_to_total(0, False, ACE_VALUE)

    for card_value, p_card in CARD_PROBABILITIES.items():
        total, is_soft2 = add_card_to_total(base_total, is_soft, card_value)
        if is_bust(total):
            ev_hand = -1.0
        else:
            # A + c, Stand forcé
            hand_state = PlayerState(
                hand_type=HandType.SOFT if is_soft2 else HandType.HARD,
                total=total,
                pair_value=None,
                from_split=True,
                from_split_aces=True,
                can_double=False,
                can_split=False,
            )
            ev_hand = _ev_stand(hand_state, dealer_upcard, rules)

        total_ev_one_hand += p_card * ev_hand

    return 2.0 * total_ev_one_hand


def _ev_split(state: PlayerState, dealer_upcard: int, rules: Rules) -> float:
    """
    EV du Split pour une paire.
    """
    if state.hand_type != HandType.PAIR or state.pair_value is None:
        raise ValueError("EV Split appelé sur une main non paire")

    if state.pair_value == ACE_VALUE:
        return _ev_split_aces(dealer_upcard, rules)
    else:
        return _ev_split_non_aces(state.pair_value, dealer_upcard, rules)


def _available_actions(
    state: PlayerState,
    dealer_upcard: int,
    rules: Rules,
) -> List[Action]:
    """
    Liste des actions disponibles pour un état donné, en fonction des règles.
    """
    actions: List[Action] = []

    # Bust : aucun choix, EV déjà -1
    if state.total > 21:
        return actions

    # Cas particulier : As splittés avec règle "une seule carte" :
    if state.from_split_aces and rules.one_card_only_after_split_aces:
        # Dans ce modèle, ces mains ne peuvent que Stand.
        actions.append(Action.STAND)
        return actions

    # Stand et Hit sont toujours disponibles tant qu'on n'est pas bust
    actions.append(Action.STAND)
    actions.append(Action.HIT)

    # Double :
    # - seulement si can_double == True
    # - après split, seulement si allow_double_after_split == True
    if state.can_double:
        if not state.from_split or (state.from_split and rules.allow_double_after_split):
            actions.append(Action.DOUBLE)

    # Split :
    # - seulement pour les paires
    # - can_split doit être True
    # - pour les As, il faut allow_split_aces
    if state.hand_type == HandType.PAIR and state.can_split and state.pair_value is not None:
        if state.pair_value == ACE_VALUE:
            if rules.allow_split_aces:
                actions.append(Action.SPLIT)
        else:
            actions.append(Action.SPLIT)

    # Surrender :
    # - seulement si allow_surrender == True
    # - uniquement au "premier coup" : on réutilise can_double pour approximer
    #   (on suppose que surrender n'est possible que sur la main initiale non splittée).
    # - pas de surrender après split.
    if (
        rules.allow_surrender
        and state.can_double
        and not state.from_split
    ):
        if dealer_upcard != ACE_VALUE or rules.surrender_allowed_vs_ace:
            actions.append(Action.SURRENDER)

    return actions


@lru_cache(maxsize=None)
def _V_memo(state: PlayerState, dealer_upcard: int, rules: Rules) -> float:
    """
    Fonction de valeur mémoïsée.

    Retourne l'EV maximale du joueur à partir d'un état donné, en supposant
    qu'il choisit l'action optimale (parmi les actions disponibles).
    """
    # Bust
    if state.total > 21:
        return -1.0

    # Total 21 : Stand est toujours optimal vs Hit/Double
    if state.total == 21 and state.hand_type != HandType.PAIR:
        return _ev_stand(state, dealer_upcard, rules)

    actions = _available_actions(state, dealer_upcard, rules)
    if not actions:
        # Par sécurité : si aucune action listée, considérer Stand
        return _ev_stand(state, dealer_upcard, rules)

    best_ev = float("-inf")

    for action in actions:
        if action == Action.STAND:
            ev = _ev_stand(state, dealer_upcard, rules)
        elif action == Action.HIT:
            ev = _ev_hit(state, dealer_upcard, rules)
        elif action == Action.DOUBLE:
            ev = _ev_double(state, dealer_upcard, rules)
        elif action == Action.SPLIT:
            ev = _ev_split(state, dealer_upcard, rules)
        elif action == Action.SURRENDER:
            ev = _ev_surrender()
        else:
            continue

        if ev > best_ev:
            best_ev = ev

    return best_ev


def V(state: PlayerState, dealer_upcard: int, rules: Rules) -> float:
    """
    Wrapper public pour la fonction de valeur mémoïsée.
    """
    return _V_memo(state, dealer_upcard, rules)


def evaluate_actions(
    state: PlayerState,
    dealer_upcard: int,
    rules: Rules,
) -> Dict[Action, float]:
    """
    Calcule l'EV de toutes les actions disponibles pour un état donné.

    Utilisé à la fois par V() (interne) et pour générer les tableaux de
    stratégie (afin de récupérer l'action optimale).
    """
    actions = _available_actions(state, dealer_upcard, rules)
    evs: Dict[Action, float] = {}

    if not actions:
        evs[Action.STAND] = _ev_stand(state, dealer_upcard, rules)
        return evs

    for action in actions:
        if action == Action.STAND:
            ev = _ev_stand(state, dealer_upcard, rules)
        elif action == Action.HIT:
            ev = _ev_hit(state, dealer_upcard, rules)
        elif action == Action.DOUBLE:
            ev = _ev_double(state, dealer_upcard, rules)
        elif action == Action.SPLIT:
            ev = _ev_split(state, dealer_upcard, rules)
        elif action == Action.SURRENDER:
            ev = _ev_surrender()
        else:
            continue
        evs[action] = ev

    return evs


def _best_action(state: PlayerState, dealer_upcard: int, rules: Rules) -> Action:
    """
    Retourne l'action optimale (celle qui maximise l'EV) pour un état donné.
    """
    evs = evaluate_actions(state, dealer_upcard, rules)
    # Choix simple : première action avec EV maximum.
    best_action = max(evs.items(), key=lambda kv: kv[1])[0]
    return best_action


def _initial_hard_state(total: int) -> PlayerState:
    """
    Construit un PlayerState pour un total hard de départ (main à 2 cartes non paire).
    """
    return PlayerState(
        hand_type=HandType.HARD,
        total=total,
        pair_value=None,
        from_split=False,
        from_split_aces=False,
        can_double=True,
        can_split=False,
    )


def _initial_soft_state(total: int) -> PlayerState:
    """
    Construit un PlayerState pour un total soft de départ (A+X, X != A).
    """
    return PlayerState(
        hand_type=HandType.SOFT,
        total=total,
        pair_value=None,
        from_split=False,
        from_split_aces=False,
        can_double=True,
        can_split=False,
    )


def _initial_pair_state(pair_value: int) -> PlayerState:
    """
    Construit un PlayerState pour une paire de départ (v, v), v=2..10,11(A).
    """
    if pair_value == ACE_VALUE:
        total = 12  # A+A => soft 12 au départ
    else:
        total = 2 * pair_value

    return PlayerState(
        hand_type=HandType.PAIR,
        total=total,
        pair_value=pair_value,
        from_split=False,
        from_split_aces=False,
        can_double=True,
        can_split=True,
    )


def generate_strategy(rules: Rules) -> Dict:
    """
    Génère la stratégie de base (basic strategy) pour un ensemble de règles donné.

    Retourne un dict de la forme :
    {
      "rules": { ... },
      "hard": {
        "5": { "2": "H", "3": "H", ... },
        ...
      },
      "soft": {
        "13": { "2": "H", ... },  # A+2
        ...
      },
      "pairs": {
        "2": { "2": "P", ... },
        "A": { "2": "P", ... },
        ...
      }
    }
    """
    # Réinitialiser le cache de V pour ne pas mélanger plusieurs règlements
    _V_memo.cache_clear()

    # Tables
    hard_table: Dict[str, Dict[str, str]] = {}
    soft_table: Dict[str, Dict[str, str]] = {}
    pairs_table: Dict[str, Dict[str, str]] = {}

    # 1) Hard totals : 5–20
    for total in range(5, 21):
        row: Dict[str, str] = {}
        state = _initial_hard_state(total)

        for upcard in DEALER_UPCARDS:
            label_up = _card_value_to_label(upcard)
            best = _best_action(state, upcard, rules)
            row[label_up] = best.value

        hard_table[str(total)] = row

    # 2) Soft totals : A+2 (13) à A+9 (20)
    for total in range(13, 21):
        row = {}
        state = _initial_soft_state(total)

        for upcard in DEALER_UPCARDS:
            label_up = _card_value_to_label(upcard)
            best = _best_action(state, upcard, rules)
            row[label_up] = best.value

        soft_table[str(total)] = row

    # 3) Paires : 2–2 à A–A
    for pair_value in CARD_VALUES:
        row = {}
        state = _initial_pair_state(pair_value)
        label_pair = _card_value_to_label(pair_value)

        for upcard in DEALER_UPCARDS:
            label_up = _card_value_to_label(upcard)
            best = _best_action(state, upcard, rules)
            row[label_up] = best.value

        pairs_table[label_pair] = row

    # Représentation des règles dans la réponse (dict simple)
    rules_dict = {
        "num_decks": rules.num_decks,
        "csm": rules.csm,
        "dealer_hits_soft_17": rules.dealer_hits_soft_17,
        "european_no_hole_card": rules.european_no_hole_card,
        "allow_split_aces": rules.allow_split_aces,
        "allow_resplit_aces": rules.allow_resplit_aces,
        "allow_double_after_split": rules.allow_double_after_split,
        "allow_surrender": rules.allow_surrender,
        "surrender_allowed_vs_ace": rules.surrender_allowed_vs_ace,
        "one_card_only_after_split_aces": rules.one_card_only_after_split_aces,
    }

    return {
        "rules": rules_dict,
        "hard": hard_table,
        "soft": soft_table,
        "pairs": pairs_table,
    }
