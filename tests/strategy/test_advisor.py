from app.engine.cards import parse
from app.engine.rules import Rules
from app.strategy.advisor import best_action

EU = Rules()


def test_two_card_double():
    a = best_action(parse("5 6"), parse("6")[0], EU, ["H", "S", "D"])
    assert a["action"] == "D" and set(a["evs"]) == {"H", "S", "D"}


def test_three_card_11_hits_when_double_illegal():
    assert best_action(parse("2 4 5"), parse("6")[0], EU, ["H", "S"])["action"] == "H"


def test_pair_uses_pair_row_when_split_legal():
    assert best_action(parse("8 8"), parse("6")[0], EU, ["H", "S", "D", "P"])["action"] == "P"
    # bez możliwości splitu: 16 vs 6 -> stój
    assert best_action(parse("8 8"), parse("6")[0], EU, ["H", "S", "D"])["action"] == "S"


def test_soft_hand_multi_card():
    # A,2,5 = miękkie 18 vs 9 -> dobierz
    assert best_action(parse("A 2 5"), parse("9")[0], EU, ["H", "S"])["action"] == "H"


def test_face_cards_are_tens():
    assert best_action(parse("K Q"), parse("J")[0], EU, ["H", "S", "D", "P"])["action"] == "S"


def test_soft_21_three_cards_stands():
    assert best_action(parse("A 5 5"), parse("T")[0], EU, ["H", "S"])["action"] == "S"
