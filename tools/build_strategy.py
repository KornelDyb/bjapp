"""Buduje tabele strategii (EV zależne od sumy) dla 6 talii: python tools/build_strategy.py
Wynik: app/strategy/tables/<tryb>-<s17|h17>.json  (tryb: peek | enhc | enhc_obo)."""
import json
import sys
import time
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.strategy.finite import HOLE_MODES, FiniteSolver  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "app" / "strategy" / "tables"
UPS = [2, 3, 4, 5, 6, 7, 8, 9, 10, 1]
UP_KEYS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "A"]
DECKS = 6


def avg(cells):
    tot = sum(w for w, _ in cells)
    keys = cells[0][1].keys()
    return {k: sum(w * e[k] for w, e in cells) / tot for k in keys}


def build_up(args):
    mode, h17, up = args
    s = FiniteSolver(DECKS, h17, mode)
    hard, soft, pairs = {}, {}, {}
    for c1 in range(1, 11):
        for c2 in range(c1, 11):
            e = s.cell(c1, c2, up)
            w = s.combo_weight(c1, c2, up)
            if c1 == c2:
                pairs["A" if c1 == 1 else str(c1)] = e
                if c1 == 1:
                    continue  # A,A = miękkie 12 tylko jako para
            base = {k: e[k] for k in ("S", "H", "D")}
            if c1 == 1:
                soft.setdefault(c2 + 11, []).append((w, base))
            else:
                hard.setdefault(c1 + c2, []).append((w, base))
    return (mode, h17, up, {
        "hard": {str(t): avg(c) for t, c in hard.items()},
        "soft": {str(t): avg(c) for t, c in soft.items()},
        "pairs": pairs,
    })


def main():
    OUT.mkdir(exist_ok=True)
    jobs = [(m, h, u) for m in HOLE_MODES for h in (False, True) for u in UPS]
    t0 = time.time()
    with Pool() as pool:
        results = pool.map(build_up, jobs, chunksize=1)
    by_set = {}
    for mode, h17, up, data in results:
        by_set.setdefault((mode, h17), {})[UP_KEYS[UPS.index(up)]] = data
    for (mode, h17), ups in by_set.items():
        name = f"{mode}-{'h17' if h17 else 's17'}.json"
        doc = {"decks": DECKS, "mode": mode, "h17": h17, "source": "app/strategy/finite.py (dokładnie, bez zwracania kart)",
               "upcards": {k: {sec: {row: {a: round(v, 5) for a, v in e.items()} for row, e in rows.items()}
                               for sec, rows in d.items()} for k, d in ups.items()}}
        (OUT / name).write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        print("zapisano", name)
    print(f"czas: {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
