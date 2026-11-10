import json

import pytest

from app.engine.cards import parse
from app.engine.errors import IllegalMove
from app.engine.rules import Rules
from app.engine.shoe import Shoe
from app.paths import db_path
from app.storage.db import Database
from app.table import TableSession


def make(order: str, rules=None):
    db = Database(db_path())
    rules = rules or Rules()
    t = TableSession(db, rules_provider=lambda: rules,
                     shoe_factory=lambda r: Shoe.stacked(parse(order)))
    return t, db


def rows(db, sql):
    return db._conn.execute(sql).fetchall()


def test_round_wrong_decision_is_executed_and_recorded(data_dir):
    t, db = make("T 6 6 5 T 8")   # gracz 16 vs 6; zły ruch H -> 21; krupier 6+T+8 = 24
    s = t.new_round(10)
    assert s["state"]["phase"] == "player" and "feedback" not in s
    r = t.act("H")
    f = r["feedback"]
    assert f["correct"] is False and f["best"] == "S" and f["taken"] == "H"
    assert r["state"]["hands"][0]["total"] == 21  # decyzja wykonana mimo błędu
    assert r["state"]["phase"] == "done"
    dec = rows(db, "SELECT player_total, soft, pair, dealer_upcard, action_taken, action_correct, is_correct FROM decisions")
    assert dec == [(16, 0, 0, 6, "H", "S", 0)]
    hand = rows(db, "SELECT bet, result, payout, player_cards, dealer_cards FROM hands")[0]
    assert hand[0] == 10 and hand[1] == "win" and hand[2] == 10
    assert json.loads(hand[3]) == [["T", "6", "5"]]
    ses = rows(db, "SELECT hands_count, correct_count, mode, rules_json FROM sessions")[0]
    assert ses[:3] == (1, 0, "table") and json.loads(ses[3])["decks"] == 6


def test_correct_decision_counts_in_session(data_dir):
    t, db = make("T 6 6 T 8")
    t.new_round(5)
    r = t.act("S")
    assert r["feedback"]["correct"] is True
    assert r["stats"] == {"hands": 1, "decisions": 1, "correct": 1, "accuracy": 1.0, "net": 5.0}


def test_natural_blackjack_no_decisions(data_dir):
    t, db = make("A 6 K")
    s = t.new_round(10)
    assert s["state"]["phase"] == "done" and s["stats"]["net"] == 15
    assert rows(db, "SELECT COUNT(*) FROM decisions")[0][0] == 0
    assert rows(db, "SELECT result FROM hands")[0][0] == "blackjack"


def test_split_records_decision_per_hand(data_dir):
    t, db = make("8 6 8 3 T T T 7")
    t.new_round(10)
    r = t.act("P")
    assert r["feedback"]["correct"] is True and r["feedback"]["best"] == "P"
    t.act("D")
    r = t.act("S")
    assert r["state"]["phase"] == "done"
    dec = rows(db, "SELECT player_total, pair, action_taken FROM decisions ORDER BY id")
    assert dec == [(16, 1, "P"), (11, 0, "D"), (18, 0, "S")]
    assert json.loads(rows(db, "SELECT player_cards FROM hands")[0][0]) == [["8", "3", "T"], ["8", "T"]]


def test_illegal_and_out_of_order(data_dir):
    t, _ = make("T 6 7")
    with pytest.raises(IllegalMove):
        t.act("H")
    t.new_round(10)
    with pytest.raises(IllegalMove):
        t.new_round(10)
    with pytest.raises(IllegalMove):
        t.act("P")


def test_rules_change_takes_effect_next_round(data_dir):
    db = Database(db_path())
    current = {"r": Rules()}
    made = []
    def factory(r):
        made.append(r)
        return Shoe.stacked(parse("T 6 9 T 5 T 6 9 T 5"))
    t = TableSession(db, rules_provider=lambda: current["r"], shoe_factory=factory)
    t.new_round(1); t.act("S")
    current["r"] = Rules(h17=True)
    t.new_round(1)
    assert len(made) == 2 and made[1].h17 is True


def test_feedback_is_fast(data_dir):
    import time
    t, _ = make("T 6 6 T 8")
    t.new_round(1)
    t0 = time.perf_counter()
    t.act("S")
    assert time.perf_counter() - t0 < 0.1
