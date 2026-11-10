"""Sesja przy stole: runda, ocena każdej decyzji, zapis do bazy."""
import json
import os
import random

from app.counting.hilo import check_answer, count_state
from app.engine.cards import hand_value
from app.engine.errors import IllegalMove
from app.engine.game import Game
from app.engine.rules import Rules
from app.engine.shoe import Shoe
from app.strategy.explain import feedback


def default_shoe(rules: Rules) -> Shoe:
    seed = os.environ.get("TRENER_BJ_SEED")
    return Shoe(rules.decks, rules.penetration, random.Random(int(seed) if seed else None))


class TableSession:
    def __init__(self, db, rules_provider, shoe_factory=default_shoe):
        self.db = db
        self.rules_provider = rules_provider
        self.shoe_factory = shoe_factory
        self.rules: Rules | None = None
        self.game: Game | None = None
        self.session_id: int | None = None
        self.hand_id: int | None = None
        self.stats = {"hands": 0, "decisions": 0, "correct": 0, "accuracy": None, "net": 0.0,
                      "count_checks": 0, "count_correct": 0, "count_accuracy": None}
        self.rounds_since_quiz = 0

    def _stats(self):
        s = dict(self.stats)
        s["accuracy"] = round(s["correct"] / s["decisions"], 4) if s["decisions"] else None
        s["count_accuracy"] = round(s["count_correct"] / s["count_checks"], 4) if s["count_checks"] else None
        return s

    # ----- liczenie -----
    def quiz_every(self) -> int:
        raw = self.db.get_setting("count.every")
        return int(json.loads(raw)) if raw is not None else 3

    def count(self) -> dict:
        if self.game is None:
            return {"running": 0, "true": 0.0, "decks_remaining": None, "cards_seen": 0}
        return count_state(self.game.shoe)

    def quiz_due(self) -> bool:
        every = self.quiz_every()
        return (every > 0 and self.game is not None and self.game.phase != "player"
                and self.rounds_since_quiz >= every and self.count()["cards_seen"] >= 5)

    def answer_count(self, rc, tc) -> dict:
        if not self.quiz_due():
            raise IllegalMove("Teraz nie ma pytania o count.")
        truth = self.count()
        try:
            res = check_answer(truth, rc, tc)
        except ValueError as e:
            raise IllegalMove(str(e)) from None
        self.db.add_count_check(self.session_id, truth["running"], res["answer_rc"], truth["true"],
                                res["answer_tc"], res["correct"])
        self.rounds_since_quiz = 0
        self.stats["count_checks"] += 1
        self.stats["count_correct"] += res["correct"]
        return {**res, "running": truth["running"], "true": truth["true"],
                "decks_remaining": truth["decks_remaining"], "stats": self._stats()}

    def status(self) -> dict:
        return {"count": self.count(), "quiz_due": self.quiz_due(), "stats": self._stats(),
                "state": self.game.state() if self.game and self.game.hands else None}

    def new_round(self, bet: float) -> dict:
        if self.game and self.game.phase == "player":
            raise IllegalMove("Najpierw dokończ bieżące rozdanie.")
        if self.quiz_due():
            raise IllegalMove("Najpierw odpowiedz na pytanie o count.")
        rules = self.rules_provider()
        if rules != self.rules or self.game is None:
            self.rules = rules
            self.game = Game(rules, shoe=self.shoe_factory(rules))
        tc_start = 0.0 if self.game.shoe.needs_shuffle() else self.count()["true"]
        state = self.game.start_round(bet)
        if state["shuffled"]:
            self.rounds_since_quiz = 0
        if self.session_id is None:
            self.session_id = self.db.start_session(rules.to_dict(), "table")
        self.hand_id = self.db.add_hand(self.session_id, bet, tc_start)
        if state["phase"] == "done":
            self._finish(state)
        return {"state": state, "stats": self._stats(), "count": self.count(), "quiz_due": self.quiz_due()}

    def act(self, action: str) -> dict:
        g = self.game
        if g is None or g.phase != "player":
            raise IllegalMove("Najpierw rozdaj karty.")
        action = (action or "").upper()
        legal = g.legal_actions()
        if action not in legal:
            return g.act(action)  # rzuci IllegalMove z komunikatem
        hand = g.hands[g.active]
        cards, up = list(hand.cards), g.dealer[0]
        fb = feedback(cards, up, self.rules, action, legal)
        total, soft = hand_value(cards)
        pair = len(cards) == 2 and cards[0].value == cards[1].value
        state = g.act(action)
        self.db.add_decision(self.session_id, self.hand_id, total, soft, pair, up.value, action, fb["best"], fb["correct"])
        self.stats["decisions"] += 1
        self.stats["correct"] += fb["correct"]
        if state["phase"] == "done":
            self._finish(state)
        return {"state": state, "feedback": fb, "stats": self._stats(), "count": self.count(),
                "quiz_due": self.quiz_due()}

    def _finish(self, state: dict) -> None:
        g = self.game
        self.db.finish_hand(
            self.hand_id, self.session_id,
            [[c.rank for c in h.cards] for h in g.hands],
            [c.rank for c in g.dealer],
            ",".join(h["result"] for h in state["hands"]),
            state["net"],
        )
        self.stats["hands"] += 1
        self.rounds_since_quiz += 1
        self.stats["net"] = round(self.stats["net"] + state["net"], 2)
