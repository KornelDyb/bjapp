import pytest

from app.counting.hilo import check_answer, count_state, hilo
from app.engine.cards import parse
from app.engine.shoe import Shoe


@pytest.mark.parametrize("rank,v", [("2", 1), ("6", 1), ("7", 0), ("9", 0), ("T", -1), ("K", -1), ("A", -1)])
def test_hilo_values(rank, v):
    assert hilo(parse(rank)[0]) == v


def test_count_follows_shoe_and_resets_on_shuffle():
    import random
    shoe = Shoe(decks=6, rng=random.Random(5))
    drawn = [shoe.draw() for _ in range(52)]
    st = count_state(shoe)
    assert st["running"] == sum(hilo(c) for c in drawn)
    assert st["cards_seen"] == 52
    assert st["decks_remaining"] == pytest.approx(5.0)
    assert st["true"] == pytest.approx(st["running"] / 5.0)
    shoe.shuffle()
    assert count_state(shoe)["running"] == 0 and count_state(shoe)["cards_seen"] == 0


def test_full_shoe_counts_to_zero():
    import random
    shoe = Shoe(decks=2, penetration=0.95, rng=random.Random(1))
    for _ in range(104):
        shoe.draw()
    assert count_state(shoe)["running"] == 0  # Hi-Lo jest zbalansowany


def test_stacked_shoe_counts_drawn_cards():
    shoe = Shoe.stacked(parse("2 3 K 7 A 5"))
    for _ in range(5):
        shoe.draw()
    assert count_state(shoe)["running"] == 1 + 1 - 1 + 0 - 1


def test_check_answer_rules():
    truth = {"running": 6, "true": 2.4}
    r = check_answer(truth, "6", "2,5")
    assert r["rc_ok"] and r["tc_ok"] and r["correct"]
    r = check_answer(truth, 6, 3.0)
    assert r["rc_ok"] and not r["tc_ok"] and not r["correct"]
    r = check_answer(truth, 5, 2.4)
    assert not r["rc_ok"] and not r["correct"]
    assert "6" in r["sentence"] and "2,4" in r["sentence"]


def test_check_answer_rejects_garbage():
    with pytest.raises(ValueError, match="liczb"):
        check_answer({"running": 0, "true": 0}, "abc", "1")
