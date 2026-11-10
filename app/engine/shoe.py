import random

from .cards import RANKS, SUITS, Card


class Shoe:
    def __init__(self, decks: int = 6, penetration: float = 0.75, rng: random.Random | None = None):
        self.decks = decks
        self.penetration = penetration
        self.rng = rng or random.Random()
        self._stacked = False
        self.shuffle()

    @classmethod
    def stacked(cls, cards: list[Card]) -> "Shoe":
        """But z ustaloną kolejnością (testy). Karty wychodzą od pierwszej."""
        shoe = cls.__new__(cls)
        shoe.decks, shoe.penetration, shoe.rng = 1, 1.0, random.Random(0)
        shoe._cards = list(reversed(cards))
        shoe.total = len(cards)
        shoe._stacked = True
        shoe.seen = []
        return shoe

    def shuffle(self) -> None:
        self._cards = [Card(r, s) for _ in range(self.decks) for s in SUITS for r in RANKS]
        self.rng.shuffle(self._cards)
        self.total = len(self._cards)
        self.seen: list[Card] = []  # karty, które wyszły od tasowania (do liczenia)

    def draw(self) -> Card:
        if not self._cards:
            raise RuntimeError("But jest pusty")
        card = self._cards.pop()
        self.seen.append(card)
        return card

    @property
    def remaining(self) -> int:
        return len(self._cards)

    @property
    def dealt(self) -> int:
        return self.total - self.remaining

    @property
    def decks_remaining(self) -> float:
        return self.remaining / 52

    def needs_shuffle(self) -> bool:
        return not self._stacked and self.dealt >= self.penetration * self.total
