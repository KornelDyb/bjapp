"""Sanity check (tolerancja 4,5 SE — rozdania z jednego buta są skorelowane):
 bust krupiera z silnika (Monte Carlo) vs dokładna rekurencja, S17 i H17, 6 talii."""
import random

import pytest

from app.engine.cards import Card, hand_value
from app.engine.exact import dealer_bust_probability
from app.engine.game import dealer_play
from app.engine.rules import Rules
from app.engine.shoe import Shoe

UPS = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "T": 10, "A": 1}


def test_exact_matches_published_points():
    # punkty kontrolne (6 talii, S17): bust przy 2 ≈ 35,4%, przy asie ≈ 11,5–11,7%
    assert abs(100 * dealer_bust_probability(2) - 35.35) < 0.05
    assert 11.4 < 100 * dealer_bust_probability(1) < 11.8


@pytest.mark.parametrize("h17", [False, True])
@pytest.mark.parametrize("up", list(UPS))
def test_engine_dealer_bust_matches_exact(up, h17):
    rng = random.Random(1000 + UPS[up] + 50 * h17)
    rules = Rules(h17=h17)
    shoe = Shoe(decks=6, rng=rng)
    n, busts = 50_000, 0
    for _ in range(n):
        if shoe.needs_shuffle():
            shoe.shuffle()
        busts += hand_value(dealer_play([Card(up)], shoe, rules))[0] > 21
    p = dealer_bust_probability(UPS[up], h17=h17)
    tolerance = 4.5 * (p * (1 - p) / n) ** 0.5  # 4,5 błędu standardowego (~0,5–0,95 pp)
    assert abs(busts / n - p) < tolerance
