"""Strategia podstawowa z tabel EV (app/strategy/tables/*.json), zbudowanych przez tools/build_strategy.py
dokładnym solverem dla 6 talii (app/strategy/finite.py). EV w jednostkach stawki początkowej."""
import json
from functools import lru_cache
from pathlib import Path

from app.engine.rules import Rules

TABLES = Path(__file__).with_name("tables")
UPCARDS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "A"]
PAIR_ROWS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "A"]


def table_key(rules: Rules) -> str:
    mode = "peek" if rules.hole_card == "peek" else ("enhc_obo" if rules.enhc_obo else "enhc")
    return f"{mode}-{'h17' if rules.h17 else 's17'}"


@lru_cache(maxsize=None)
def _load(key: str) -> dict:
    path = TABLES / f"{key}.json"
    if not path.exists():
        raise FileNotFoundError(f"Brak tabeli strategii {key}. Uruchom: python tools/build_strategy.py")
    doc = json.loads(path.read_text(encoding="utf-8"))
    ups = doc["upcards"]
    for up in ups.values():  # twarde 4 i 20 występują tylko jako pary (2,2 i 10,10)
        for row, pair in (("4", "2"), ("20", "10")):
            up["hard"].setdefault(row, {k: up["pairs"][pair][k] for k in ("S", "H", "D")})
    return ups


def action_evs(rules: Rules, section: str, row, up: str) -> dict:
    """section: 'hard' (suma 4–20), 'soft' (suma 13–21), 'pairs' ('2'..'10','A')."""
    e = _load(table_key(rules))[up][section][str(row)]
    out = {k: e[k] for k in ("S", "H", "D")}
    if section == "pairs":
        out["P"] = e["P_das"] if rules.das else e["P_ndas"]
    if rules.surrender:
        out["R"] = -0.5
    return out


def _code(evs: dict) -> str:
    best = max(evs, key=evs.get)
    fallback = "H" if evs["H"] >= evs["S"] else "S"
    if best == "D":
        return "D" + fallback.lower()
    if best == "R":
        rest = {k: v for k, v in evs.items() if k not in ("R", "D")}
        return "R" + max(rest, key=rest.get).lower()
    return best


@lru_cache(maxsize=64)
def chart(rules: Rules) -> dict:
    def section(name, rows):
        out = []
        for r in rows:
            cells = []
            for up in UPCARDS:
                e = action_evs(rules, name, r, up)
                cells.append({"code": _code(e), "evs": {k: round(v, 4) for k, v in e.items()}})
            out.append({"label": str(r), "cells": cells})
        return out

    return {
        "upcards": UPCARDS,
        "key": table_key(rules),
        "hard": section("hard", range(5, 21)),
        "soft": section("soft", range(13, 21)),
        "pairs": section("pairs", PAIR_ROWS),
    }
