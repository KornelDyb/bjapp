import random
from collections import Counter

import pytest

from app.engine.cards import hand_value, is_blackjack, parse
from app.engine.shoe import Shoe


@pytest.mark.parametrize("hand,total,soft", [
    ("A 6", 17, True), ("A 6 T", 17, False), ("A A", 12, True), ("A A 9", 21, True),
    ("K Q", 20, False), ("A K", 21, True), ("5 6 A", 12, False), ("A A A A", 14, True),
    ("T 6 9", 25, False),
])
def test_hand_value(hand, total, soft):
    assert hand_value(parse(hand)) == (total, soft)


def test_blackjack_only_two_cards():
    assert is_blackjack(parse("A J"))
    assert not is_blackjack(parse("A 5 5"))


def test_shoe_has_n_decks():
    shoe = Shoe(decks=6, rng=random.Random(1))
    assert shoe.total == 312 and shoe.remaining == 312
    c = Counter(card.rank for card in shoe._cards)
    assert c["A"] == 24 and c["T"] == 24 and c["K"] == 24 and len(c) == 13


def test_shoe_seeded_is_deterministic():
    a = [Shoe(decks=2, rng=random.Random(7)).draw() for _ in range(1)]
    b = [Shoe(decks=2, rng=random.Random(7)).draw() for _ in range(1)]
    assert a == b


def test_needs_shuffle_after_penetration():
    shoe = Shoe(decks=1, penetration=0.5, rng=random.Random(1))
    for _ in range(25):
        shoe.draw()
    assert not shoe.needs_shuffle()
    shoe.draw()
    assert shoe.needs_shuffle()
    shoe.shuffle()
    assert shoe.remaining == 52 and not shoe.needs_shuffle()
