"""Solver (nieskończona talia) vs symulacja na silniku (6 talii) — EV kontrolnych ruchów."""
import random

import pytest

from app.engine.cards import RANKS, SUITS, Card, parse
from app.engine.game import Game
from app.engine.rules import Rules
from app.engine.shoe import Shoe
from app.strategy.solver import action_evs


def shoe_with_prefix(prefix, rng):
    rest = [Card(r, s) for _ in range(6) for s in SUITS for r in RANKS]
    for c in prefix:
        rest.remove(next(x for x in rest if x.rank == c.rank))
    rng.shuffle(rest)
    return Shoe.stacked(prefix + rest)


def simulate(rules, p1, up, p2, first_action, n, seed):
    """EV pierwszego ruchu; potem: dobieraj do twardych 17 (dla H)."""
    rng = random.Random(seed)
    nets = []
    prefix = parse(f"{p1} {up} {p2}")
    for _ in range(n):
        g = Game(rules, shoe=shoe_with_prefix(prefix, rng))
        s = g.start_round(1)
        if s["phase"] == "player":
            s = g.act(first_action)
            while s["phase"] == "player":
                h = s["hands"][s["active"]]
                s = g.act("H" if h["total"] < 17 else "S")
        nets.append(s["net"])
    m = sum(nets) / n
    sd = (sum((x - m) ** 2 for x in nets) / (n - 1)) ** 0.5
    return m, sd / n ** 0.5


@pytest.mark.parametrize("rules,p1,up,p2,action,row", [
    (Rules(), "T", "T", "6", "S", ("hard", 16)),
    (Rules(), "5", "6", "6", "D", ("hard", 11)),
    (Rules(), "5", "T", "6", "D", ("hard", 11)),   # ENHC bez OBO: BJ krupiera zabiera podwójną stawkę
    (Rules(hole_card="peek"), "T", "7", "9", "S", ("hard", 19)),
])
def test_solver_ev_matches_engine(rules, p1, up, p2, action, row):
    m, se = simulate(rules, p1, up, p2, action, 30_000, seed=hash((p1, up, p2, action)) % 10_000)
    up_key = "10" if up in "TJQK" else up
    ev = action_evs(rules, row[0], row[1], up_key)[action]
    # nieskończona talia vs 6 talii: dopuszczamy dodatkowe 0,01 na efekt usunięcia kart
    assert abs(m - ev) < 4.5 * se + 0.01, (m, ev, se)
