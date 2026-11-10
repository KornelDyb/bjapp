"""Karty i wartości rąk. Rangi: A 2–9 T J Q K (T = dziesiątka)."""
from dataclasses import dataclass

RANKS = "A23456789TJQK"
SUITS = "♠♥♦♣"


@dataclass(frozen=True)
class Card:
    rank: str
    suit: str = "♠"

    @property
    def value(self) -> int:
        """As = 1 (miękkość liczona w hand_value), T/J/Q/K = 10."""
        if self.rank == "A":
            return 1
        if self.rank in "TJQK":
            return 10
        return int(self.rank)

    def to_dict(self) -> dict:
        return {"rank": self.rank, "suit": self.suit}


def parse(text: str) -> list[Card]:
    """'A T 5' -> [Card('A'), Card('T'), Card('5')] (kolor ♠) — do testów."""
    out = []
    for tok in text.split():
        tok = tok.upper().replace("10", "T")
        if tok not in RANKS:
            raise ValueError(f"Nieznana karta: {tok}")
        out.append(Card(tok))
    return out


def hand_value(cards) -> tuple[int, bool]:
    """(suma, czy miękka) — jeden as liczony jako 11, jeśli nie przekracza 21."""
    total = sum(c.value for c in cards)
    if any(c.rank == "A" for c in cards) and total + 10 <= 21:
        return total + 10, True
    return total, False


def is_blackjack(cards) -> bool:
    return len(cards) == 2 and hand_value(cards)[0] == 21
