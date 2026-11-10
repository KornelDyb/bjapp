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
    assert r["stats"].items() >= {"hands": 1, "decisions": 1, "correct": 1, "accuracy": 1.0, "net": 5.0}.items()


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


def make_count(order: str, every=3):
    db = Database(db_path())
    db.set_setting("count.every", json.dumps(every))
    t = TableSession(db, rules_provider=lambda: Rules(), shoe_factory=lambda r: Shoe.stacked(parse(order)))
    return t, db


ROUND = "T 6 9 T 5 "   # gracz 19 stoi; krupier 6+T+5 = 21  (RC rundy: -1+1+0-1+1 = 0)


def test_count_quiz_due_every_n_rounds(data_dir):
    t, db = make_count(ROUND * 6, every=2)
    assert t.quiz_due() is False  # 0 kart od tasowania
    t.new_round(1); t.act("S")
    assert t.quiz_due() is False  # 1 rozdanie
    t.new_round(1); t.act("S")
    assert t.quiz_due() is True   # 2 rozdania, 10 kart
    r = t.answer_count(0, 0)
    assert r["correct"] is True and r["running"] == 0
    assert t.quiz_due() is False
    with pytest.raises(IllegalMove):
        t.answer_count(0, 0)  # nie było pytania


def test_new_round_blocked_while_quiz_due(data_dir):
    t, _ = make_count(ROUND * 4, every=1)
    t.new_round(1); t.act("S")
    with pytest.raises(IllegalMove, match="count"):
        t.new_round(1)
    t.answer_count(0, 0)
    t.new_round(1)


def test_quiz_disabled(data_dir):
    t, _ = make_count(ROUND * 4, every=0)
    t.new_round(1); t.act("S")
    t.new_round(1); t.act("S")
    assert t.quiz_due() is False


def test_count_answer_recorded(data_dir):
    t, db = make_count("2 3 4 T 8 " + ROUND * 3, every=1)   # gracz 2,4 vs 3, dobiera T = 16, stoi; krupier 3+8+...
    t.new_round(1)
    while t.game.phase == "player":
        t.act("S")
    rc = t.count()["running"]
    r = t.answer_count(rc + 1, 0)
    assert r["correct"] is False and r["rc_ok"] is False
    row = rows(db, "SELECT true_rc, answer_rc, is_correct FROM count_checks")[0]
    assert row == (rc, rc + 1, 0)
    assert t._stats()["count_checks"] == 1 and t._stats()["count_correct"] == 0


def test_true_count_at_start_recorded(data_dir):
    t, db = make_count(ROUND * 3, every=0)
    t.new_round(1); t.act("S")
    t.new_round(1)
    tcs = [r[0] for r in rows(db, "SELECT true_count_at_start FROM hands ORDER BY id")]
    assert tcs[0] == 0 and tcs[1] is not None


def test_state_includes_count_and_shuffle_flag(data_dir):
    t, _ = make_count(ROUND * 2, every=0)
    r = t.new_round(1)
    assert set(r["count"]) >= {"running", "true", "decks_remaining", "cards_seen"}


def test_status_restores_round_in_progress(data_dir):
    t, _ = make("T 6 7 5 T 8")
    assert t.status()["state"] is None
    t.new_round(10)
    st = t.status()["state"]
    assert st["phase"] == "player" and st["hands"][0]["total"] == 17
