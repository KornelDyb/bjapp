"""Ocena decyzji i krótkie „dlaczego” po polsku."""
from functools import lru_cache

from app.engine.cards import Card, hand_value
from app.engine.exact import dealer_bust_probability
from app.engine.rules import Rules

from .advisor import NAMES, best_action, situation, up_key


def fmt_ev(v: float, digits: int = 2) -> str:
    return f"{v:+.{digits}f}".replace(".", ",").replace("-", "−")


@lru_cache(maxsize=64)
def _bust(up: str, decks: int, h17: bool) -> int:
    return round(100 * dealer_bust_probability(1 if up == "A" else int(up), decks=decks, h17=h17))


def _sentence(cards: list[Card], up: str, rules: Rules, best: str, evs: dict) -> str:
    total, soft = hand_value(cards)
    section, row = situation(cards)
    up_lbl = "As" if up == "A" else up
    weak = up in ("2", "3", "4", "5", "6")
    bust = _bust(up, min(rules.decks, 8), rules.h17)
    enhc_lose_all = rules.hole_card == "enhc" and not rules.enhc_obo and up in ("10", "A")
    name = NAMES[best]

    if section == "pairs":
        c = row
        lbl = f"{c},{c}"
        if best == "P":
            if c == "8":
                return f"{lbl} vs {up_lbl}: Rozdziel — 16 to najgorsza ręka, a dwie ręce od 8 grają dużo lepiej."
            if c == "A":
                return f"{lbl} vs {up_lbl}: Rozdziel — każdy as to duża szansa na 20 lub 21."
            if weak:
                return f"{lbl} vs {up_lbl}: Rozdziel — krupier z {up_lbl} przebija w {bust}% rozdań, więc dwie ręce zarabiają więcej niż jedna."
            return f"{lbl} vs {up_lbl}: Rozdziel — dwie ręce od {c} dają więcej niż {total} na jednej ręce."
        if c == "10":
            return f"{lbl} vs {up_lbl}: Stój — 20 to prawie pewna wygrana, nie rozbijaj jej."
        if c in ("8", "A") and enhc_lose_all:
            return f"{lbl} vs {up_lbl}: Dobierz — krupier może jeszcze dobrać blackjacka i zabrać obie stawki."
        if c == "A":  # A,A bez splitu = miękkie 12
            return f"{lbl} vs {up_lbl}: {name} — miękkie 12 nie może przebić."

    lbl = f"Miękkie {total}" if soft else str(total)
    if best == "R":
        lose = -evs.get("H", evs.get("S", -0.5))
        return f"{lbl} vs {up_lbl}: Poddaj — tracisz pół stawki zamiast średnio {round(lose * 100)}% przy grze."
    if best == "D":
        return f"{lbl} vs {up_lbl}: Podwój — masz przewagę nad krupierem, więc warto podwoić stawkę."
    if best == "H" and "D" in evs and enhc_lose_all and total in (10, 11):
        return f"{lbl} vs {up_lbl}: Dobierz — krupier może jeszcze dobrać blackjacka i zabrać podwójną stawkę."
    if soft:
        if best == "H":
            return f"{lbl} vs {up_lbl}: Dobierz — nie możesz przebić, a {total} jest za słabe na krupiera z {up_lbl}."
        return f"{lbl} vs {up_lbl}: Stój — {total} to dobra ręka na krupiera z {up_lbl}."
    if best == "H" and total <= 11:
        return f"{lbl} vs {up_lbl}: Dobierz — nie możesz przebić, a każda karta poprawia rękę."
    if best == "S" and total >= 17:
        return f"{lbl} vs {up_lbl}: Stój — ryzyko przebicia jest za duże."
    if 12 <= total <= 16:
        if best == "S":
            return f"{lbl} vs {up_lbl}: Stój — krupier z {up_lbl} przebija w {bust}% rozdań; nie ryzykuj własnego przebicia."
        if weak:
            return f"{lbl} vs {up_lbl}: Dobierz — przebić Cię może tylko dziesiątka, a krupier z {up_lbl} przebija tylko w {bust}% rozdań."
        return f"{lbl} vs {up_lbl}: Dobierz — krupier z {up_lbl} rzadko przebija ({bust}%), a {total} bez dobierania zwykle przegrywa."
    return f"{lbl} vs {up_lbl}: {name} — średnio {fmt_ev(evs[best])} stawki na rozdanie."


def feedback(cards: list[Card], dealer_up: Card, rules: Rules, taken: str, legal: list[str]) -> dict:
    taken = taken.upper()
    adv = best_action(cards, dealer_up, rules, legal)
    best, evs = adv["action"], adv["evs"]
    if not evs:  # 21 z 3+ kart
        return {"correct": taken == "S", "taken": taken, "best": "S", "cost": 0.0, "evs": [],
                "sentence": f"21 vs {'As' if up_key(dealer_up) == 'A' else up_key(dealer_up)}: Stój — masz 21."}
    cost = max(0.0, evs[best] - evs.get(taken, evs[best]))
    correct = taken == best or cost < 1e-9
    ranked = sorted(evs.items(), key=lambda kv: -kv[1])
    # gdy różne EV wyglądają tak samo po zaokrągleniu, pokaż 3 miejsca
    labels2 = [fmt_ev(v) for _, v in ranked]
    digits = 3 if len(set(labels2)) < len(labels2) else 2
    return {
        "correct": correct,
        "taken": taken,
        "best": best,
        "cost": round(cost, 4),
        "evs": [{"action": a, "name": NAMES[a], "ev": round(v, 4), "label": fmt_ev(v, digits)} for a, v in ranked],
        "sentence": _sentence(cards, up_key(dealer_up), rules, best, evs),
    }
