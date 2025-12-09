# backend/tests/test_strategy_engine.py

from __future__ import annotations

from app.rules import DEFAULT_RULES
from app.strategy_engine import generate_strategy


def test_basic_decision_16_vs_10_is_hit():
    """
    Sous règles standard (6 decks, S17, DAS, pas de surrender),
    16 vs 10 doit être Hit dans la basic strategy.
    """
    rules = DEFAULT_RULES
    strategy = generate_strategy(rules)

    hard_table = strategy["hard"]
    action = hard_table["16"]["10"]
    assert action == "H"


def test_basic_decision_9_9_vs_7_is_stand():
    """
    Sous règles standard multi-sabot S17, la stratégie classique recommande
    de Stand sur 9-9 vs 7 (et ne pas Split) pour la plupart des jeux.
    """
    rules = DEFAULT_RULES
    strategy = generate_strategy(rules)

    pairs_table = strategy["pairs"]
    action = pairs_table["9"]["7"]
    assert action == "S"


def test_basic_decision_8_8_vs_10_is_split():
    """
    Rappel connu : 8-8 se split quasi systématiquement, y compris vs 10.
    Le moteur doit recommander Split (P) dans ce cas.
    """
    rules = DEFAULT_RULES
    strategy = generate_strategy(rules)

    pairs_table = strategy["pairs"]
    action = pairs_table["8"]["10"]
    assert action == "P"
