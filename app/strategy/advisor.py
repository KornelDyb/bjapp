"""Najlepszy legalny ruch dla konkretnej ręki."""
from app.engine.cards import Card, hand_value
from app.engine.rules import Rules

from .solver import action_evs

NAMES = {"H": "Dobierz", "S": "Stój", "D": "Podwój", "P": "Rozdziel", "R": "Poddaj"}


def up_key(card: Card) -> str:
    return "A" if card.rank == "A" else str(card.value)


def situation(cards: list[Card]) -> tuple[str, str]:
    """('hard'|'soft'|'pairs', wiersz tabeli) — para tylko dla 2 kart o tej samej wartości."""
    total, soft = hand_value(cards)
    if len(cards) == 2 and cards[0].value == cards[1].value:
        return "pairs", ("A" if cards[0].rank == "A" else str(cards[0].value))
    if soft:
        return "soft", str(total)
    return "hard", str(total)


def best_action(cards: list[Card], dealer_up: Card, rules: Rules, legal: list[str]) -> dict:
    total, soft = hand_value(cards)
    up = up_key(dealer_up)
    section, row = situation(cards)
    if total >= 21:  # 21 z 3+ kart: zawsze stój
        return {"action": "S", "name": NAMES["S"], "evs": {}, "section": section, "row": row, "up": up}
    if section == "pairs" and "P" in legal:
        evs = action_evs(rules, "pairs", row, up)
    else:
        if section == "pairs":
            section, row = ("soft", "12") if soft else ("hard", str(total))
        if soft:
            evs = action_evs(rules, "soft", total, up) if total >= 13 else action_evs(rules, "pairs", "A", up)
        else:
            evs = action_evs(rules, "hard", total, up)
    evs = {k: v for k, v in evs.items() if k in legal}
    action = max(evs, key=evs.get)
    return {"action": action, "name": NAMES[action], "evs": evs, "section": section, "row": row, "up": up}
