"""Liczenie kart Hi-Lo: 2–6 = +1, 7–9 = 0, 10/figury/as = −1."""
from app.engine.cards import Card

TC_TOLERANCE = 0.5


def hilo(card: Card) -> int:
    v = card.value
    if 2 <= v <= 6:
        return 1
    if 7 <= v <= 9:
        return 0
    return -1


def count_state(shoe) -> dict:
    running = sum(hilo(c) for c in shoe.seen)
    decks = max(shoe.remaining / 52, 0.25)
    return {
        "running": running,
        "true": round(running / decks, 2),
        "decks_remaining": round(decks, 2),
        "cards_seen": len(shoe.seen),
    }


def _num(x, name: str) -> float:
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return float(x)
    try:
        return float(str(x).strip().replace(",", ".").replace("−", "-"))
    except ValueError:
        raise ValueError(f"Podaj liczby: {name} (np. 4 albo −2).") from None


def _fmt(x: float) -> str:
    return f"{x:.1f}".replace(".", ",").replace("-", "−")


def check_answer(truth: dict, answer_rc, answer_tc) -> dict:
    rc = _num(answer_rc, "running count")
    tc = _num(answer_tc, "true count")
    rc_ok = rc == truth["running"]
    tc_ok = abs(tc - truth["true"]) <= TC_TOLERANCE
    correct = rc_ok and tc_ok
    decks = truth.get("decks_remaining")
    if correct:
        sentence = f"Dobrze: running count {truth['running']}, true count {_fmt(truth['true'])}."
    else:
        parts = [f"Running count to {truth['running']}"]
        parts.append(f"true count {_fmt(truth['true'])}" + (f" ({truth['running']} ÷ {_fmt(decks)} talii w bucie)" if decks else ""))
        sentence = ", ".join(parts) + "."
        if rc_ok and not tc_ok:
            sentence += " Running dobrze — popraw dzielenie przez liczbę talii."
    return {"correct": correct, "rc_ok": rc_ok, "tc_ok": tc_ok, "answer_rc": rc, "answer_tc": tc, "sentence": sentence}
