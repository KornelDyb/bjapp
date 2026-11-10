"""Sesja przy stole: runda, ocena każdej decyzji, zapis do bazy."""
import os
import random

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
        self.stats = {"hands": 0, "decisions": 0, "correct": 0, "accuracy": None, "net": 0.0}

    def _stats(self):
        s = dict(self.stats)
        s["accuracy"] = round(s["correct"] / s["decisions"], 4) if s["decisions"] else None
        return s

    def new_round(self, bet: float) -> dict:
        if self.game and self.game.phase == "player":
            raise IllegalMove("Najpierw dokończ bieżące rozdanie.")
        rules = self.rules_provider()
        if rules != self.rules or self.game is None:
            self.rules = rules
            self.game = Game(rules, shoe=self.shoe_factory(rules))
        state = self.game.start_round(bet)
        if self.session_id is None:
            self.session_id = self.db.start_session(rules.to_dict(), "table")
        self.hand_id = self.db.add_hand(self.session_id, bet)
        if state["phase"] == "done":
            self._finish(state)
        return {"state": state, "stats": self._stats()}

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
        return {"state": state, "feedback": fb, "stats": self._stats()}

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
        self.stats["net"] = round(self.stats["net"] + state["net"], 2)
