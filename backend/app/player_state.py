# backend/app/player_state.py

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class HandType(str, Enum):
    HARD = "HARD"
    SOFT = "SOFT"
    PAIR = "PAIR"


@dataclass(frozen=True)
class PlayerState:
    """
    Représente l'état de la main du joueur au moment de prendre une décision.

    Attributs principaux
    --------------------
    hand_type : HandType
        - HARD : main sans As compté 11
        - SOFT : main avec au moins un As compté 11
        - PAIR : main de deux cartes de même valeur (2–2, 3–3, ..., A–A)

    total : int
        Total effectif de la main pour HARD/SOFT.
        Pour PAIR, on peut choisir de stocker 2 * pair_value ou simplement
        la somme des deux cartes; on garde total cohérent pour faciliter
        certains calculs, mais pair_value est la référence pour les tableaux.

    pair_value : Optional[int]
        Valeur de la paire lorsque hand_type == PAIR (2–10, 11 pour A).
        None sinon.

    from_split : bool
        True si cette main provient d'un split.

    from_split_aces : bool
        True si cette main provient d'un split d'As.
        Selon les règles, on pourra restreindre les actions (ex: pas de re-split).

    can_double : bool
        True si le double est encore autorisé pour cette main (utile si on
        veut modéliser des restrictions fines comme "double only on 9–11" plus tard).

    can_split : bool
        True si un split est autorisé (une paire, pas de restriction de re-split déjà atteinte, etc.).
    """

    hand_type: HandType
    total: int
    pair_value: Optional[int] = None

    from_split: bool = False
    from_split_aces: bool = False

    can_double: bool = True
    can_split: bool = True

    def is_soft(self) -> bool:
        """
        Indique si la main est soft (pour les totaux non-pair).
        """
        return self.hand_type == HandType.SOFT

    def is_pair(self) -> bool:
        """
        Indique si la main est une paire.
        """
        return self.hand_type == HandType.PAIR
