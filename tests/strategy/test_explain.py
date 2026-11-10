from app.engine.cards import parse
from app.engine.rules import Rules
from app.strategy.explain import feedback, fmt_ev

EU = Rules()


def fb(hand, up, taken, legal=("H", "S", "D"), rules=EU):
    return feedback(parse(hand), parse(up)[0], rules, taken, list(legal))


def test_correct_decision():
    f = fb("T 6", "6", "S")
    assert f["correct"] is True and f["best"] == "S" and f["cost"] == 0
    assert f["sentence"].startswith("16 vs 6")
    assert "przebija" in f["sentence"]


def test_wrong_decision_has_cost_and_reason():
    f = fb("T 6", "6", "H")
    assert f["correct"] is False and f["best"] == "S" and f["cost"] > 0
    assert "Stój" in f["sentence"]


def test_stiff_vs_strong_card_says_hit():
    f = fb("T 5", "T", "S")
    assert f["best"] == "H" and "rzadko" in f["sentence"]


def test_enhc_11_vs_10_mentions_dealer_blackjack():
    f = fb("5 6", "T", "D")
    assert f["best"] == "H" and "blackjack" in f["sentence"]


def test_double_reason():
    f = fb("5 6", "6", "D")
    assert f["correct"] and "Podwój" in f["sentence"]


def test_split_eights():
    f = fb("8 8", "6", "S", legal=("H", "S", "D", "P"))
    assert f["best"] == "P" and "16" in f["sentence"]


def test_never_split_tens():
    f = fb("T K", "6", "P", legal=("H", "S", "D", "P"))
    assert f["best"] == "S" and "20" in f["sentence"]


def test_soft_hand_sentence():
    f = fb("A 7", "T", "S")
    assert f["best"] == "H" and f["sentence"].startswith("Miękkie 18 vs 10")


def test_evs_sorted_best_first_with_names():
    f = fb("5 6", "6", "H")
    assert [e["action"] for e in f["evs"]][0] == "D"
    assert f["evs"][0]["name"] == "Podwój"
    assert f["evs"][0]["ev"] >= f["evs"][-1]["ev"]


def test_three_card_21_always_correct_stand():
    f = fb("7 7 7", "T", "S", legal=("H", "S"))
    assert f["correct"] and f["evs"] == []


def test_fmt_ev_polish():
    assert fmt_ev(0.0812) == "+0,08" and fmt_ev(-0.5404) == "−0,54"


def test_close_evs_shown_with_three_decimals():
    f = fb("A 7", "2", "D")  # S i D różnią się o ~0,003
    labels = [e["label"] for e in f["evs"]]
    assert len(set(labels)) == len(labels) and len(labels[0].split(",")[1]) == 3
