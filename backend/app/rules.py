# backend/app/rules.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rules:
    """
    Représente un ensemble de règles de blackjack.

    Modèle de pioche :
    ------------------
    Pour le moteur de stratégie, nous utilisons un modèle de pioche à
    probabilités fixes par valeur de carte (comme un paquet infini).
    Dans ce modèle, `num_decks` n'affecte pas directement les probabilités
    de tirage (2–9 : 1/13, 10/J/Q/K : 4/13, A : 1/13), mais il est conservé
    pour éventuellement affiner le modèle plus tard ou l'afficher dans l'UI.

    Variante européenne (no hole card) :
    ------------------------------------
    - european_no_hole_card = False : jeu "US" avec hole card + peek.
      Le croupier regarde sa carte fermée sur 10/A; si blackjack, la main
      se termine avant toute décision du joueur. Les décisions du joueur
      (Hit/Stand/Double/Split/Surrender) se font donc conditionnellement
      au fait que le croupier n'a PAS blackjack.
    - european_no_hole_card = True : variante européenne (ENHC).
      Il n'y a pas de carte fermée au début. Le croupier tire sa seconde
      carte après les décisions du joueur. Si cela donne un blackjack,
      toutes les mises engagées (doubles, splits) sont perdues. Les décisions
      du joueur se font donc sans savoir si le croupier fera blackjack.
    """

    num_decks: int = 6
    csm: bool = False  # Continuous Shuffling Machine

    dealer_hits_soft_17: bool = False  # False = S17, True = H17

    # Variante européenne ENHC (no hole card)
    european_no_hole_card: bool = False

    # Split / double / surrender
    allow_split_aces: bool = True
    allow_resplit_aces: bool = False
    allow_double_after_split: bool = True

    allow_surrender: bool = False
    surrender_allowed_vs_ace: bool = False

    # Règle sur les As splittés : une seule carte par As, puis stand forcé.
    one_card_only_after_split_aces: bool = True

    def signature(self) -> tuple:
        """
        Signature hashable des règles, utile pour la mémoïsation.
        """
        return (
            self.num_decks,
            self.csm,
            self.dealer_hits_soft_17,
            self.european_no_hole_card,
            self.allow_split_aces,
            self.allow_resplit_aces,
            self.allow_double_after_split,
            self.allow_surrender,
            self.surrender_allowed_vs_ace,
            self.one_card_only_after_split_aces,
        )


# Règles par défaut proches d'un jeu de casino standard 6-decks, S17, DAS,
# no surrender, variante US (avec hole card).
DEFAULT_RULES = Rules(
    num_decks=6,
    csm=False,
    dealer_hits_soft_17=False,
    european_no_hole_card=False,
    allow_split_aces=True,
    allow_resplit_aces=False,
    allow_double_after_split=True,
    allow_surrender=False,
    surrender_allowed_vs_ace=False,
    one_card_only_after_split_aces=True,
)
