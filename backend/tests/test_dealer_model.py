# backend/tests/test_dealer_model.py

from __future__ import annotations

import math

from app.cards import ACE_VALUE
from app.dealer_model import (
    get_dealer_distribution,
    get_dealer_distribution_no_blackjack,
    dealer_blackjack_probability,
)
from app.rules import DEFAULT_RULES


def _sum_probs(dist):
    return sum(dist.values())


def test_dealer_distribution_sums_to_one():
    """
    Les distributions du croupier doivent sommer à ~1 pour quelques upcards.
    """
    rules = DEFAULT_RULES

    for upcard in [2, 6, 10, ACE_VALUE]:
        dist = get_dealer_distribution(upcard, rules)
        total = _sum_probs(dist)
        assert math.isclose(total, 1.0, rel_tol=1e-9, abs_tol=1e-9)

        for p in dist.values():
            assert 0.0 <= p <= 1.0


def test_dealer_blackjack_probability_and_no_bj_distribution():
    """
    Vérifie que :
    - la probabilité de blackjack naturel est positive sur 10/A,
    - la distribution conditionnelle "pas de blackjack" est bien normalisée
      et que la probabilité de 21 y est réduite.
    """
    rules = DEFAULT_RULES

    for upcard in [10, ACE_VALUE]:
        pbj = dealer_blackjack_probability(upcard)
        assert pbj > 0.0
        assert pbj < 1.0

        dist_full = get_dealer_distribution(upcard, rules)
        dist_no_bj = get_dealer_distribution_no_blackjack(upcard, rules)

        total_full = _sum_probs(dist_full)
        total_no_bj = _sum_probs(dist_no_bj)

        assert math.isclose(total_full, 1.0, rel_tol=1e-9, abs_tol=1e-9)
        assert math.isclose(total_no_bj, 1.0, rel_tol=1e-9, abs_tol=1e-9)

        # La part de 21 doit être plus petite dans la distribution sans BJ
        p21_full = dist_full.get(21, 0.0)
        p21_no_bj = dist_no_bj.get(21, 0.0)
        assert p21_no_bj <= p21_full
