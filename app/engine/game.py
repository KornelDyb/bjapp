"""Runda blackjacka: rozdanie, ruchy gracza, gra krupiera, rozliczenie."""
from dataclasses import dataclass, field

from .cards import Card, hand_value, is_blackjack
from .errors import IllegalMove
from .rules import Rules
from .shoe import Shoe

ACTIONS = ("H", "S", "D", "P", "R")
MSG = {
    "H": "Nie możesz teraz dobrać.",
    "S": "Nie możesz teraz stanąć.",
    "D": "Nie możesz teraz podwoić.",
    "P": "Nie możesz teraz rozdzielić.",
    "R": "Nie możesz teraz się poddać.",
}


@dataclass
class Hand:
    bet: float
    cards: list[Card] = field(default_factory=list)
    from_split: bool = False
    split_aces: bool = False
    doubled: bool = False
    status: str = "playing"   # playing | stood | bust | surrendered | blackjack
    result: str | None = None  # win | lose | push | blackjack | bust | surrender
    net: float = 0.0

    @property
    def total(self):
        return hand_value(self.cards)[0]

    def to_dict(self):
        total, soft = hand_value(self.cards)
        return {"cards": [c.to_dict() for c in self.cards], "total": total, "soft": soft,
                "bet": self.bet, "doubled": self.doubled, "status": self.status,
                "result": self.result, "net": self.net}


def dealer_should_hit(cards, rules: Rules) -> bool:
    total, soft = hand_value(cards)
    return total < 17 or (total == 17 and soft and rules.h17)


def dealer_play(cards: list[Card], shoe: Shoe, rules: Rules) -> list[Card]:
    cards = list(cards)
    while dealer_should_hit(cards, rules):
        cards.append(shoe.draw())
    return cards


class Game:
    def __init__(self, rules: Rules | None = None, shoe: Shoe | None = None, seed: int | None = None):
        import random
        self.rules = rules or Rules()
        self.shoe = shoe or Shoe(self.rules.decks, self.rules.penetration, random.Random(seed))
        self.phase = "betting"
        self.hands: list[Hand] = []
        self.dealer: list[Card] = []
        self.active = 0
        self.base_bet = 0.0
        self.shuffled = False

    # ---------- publiczne ----------
    def start_round(self, bet: float) -> dict:
        if self.phase == "player":
            raise IllegalMove("Najpierw dokończ bieżące rozdanie.")
        if not isinstance(bet, (int, float)) or bet <= 0:
            raise IllegalMove("Stawka musi być większa od zera.")
        self.shuffled = self.shoe.needs_shuffle()
        if self.shuffled:
            self.shoe.shuffle()
        self.base_bet = bet
        hand = Hand(bet=bet)
        self.hands, self.active, self.dealer = [hand], 0, []
        hand.cards.append(self.shoe.draw())
        self.dealer.append(self.shoe.draw())
        hand.cards.append(self.shoe.draw())
        if self.rules.hole_card == "peek":
            self.dealer.append(self.shoe.draw())
        self.phase = "player"

        up_can_bj = self.dealer[0].value in (1, 10)
        if self.rules.hole_card == "peek" and up_can_bj and is_blackjack(self.dealer):
            return self._settle()
        if is_blackjack(hand.cards):
            hand.status = "blackjack"
            if self.rules.hole_card == "enhc" and up_can_bj:
                self.dealer.append(self.shoe.draw())
            return self._settle()
        return self.state()

    def legal_actions(self) -> list[str]:
        if self.phase != "player":
            return []
        h = self.hands[self.active]
        two = len(h.cards) == 2
        legal = ["H", "S"]
        if two and (not h.from_split or self.rules.das):
            legal.append("D")
        if (two and h.cards[0].value == h.cards[1].value and len(self.hands) < self.rules.max_hands
                and (not h.split_aces or self.rules.resplit_aces)):
            legal.append("P")
        if two and self.rules.surrender and len(self.hands) == 1 and not h.from_split:
            legal.append("R")
        return legal

    def act(self, action: str) -> dict:
        action = (action or "").upper()
        if action not in ACTIONS:
            raise IllegalMove(f"Nieznany ruch: {action}")
        if action not in self.legal_actions():
            raise IllegalMove(MSG[action])
        h = self.hands[self.active]
        if action == "H":
            h.cards.append(self.shoe.draw())
            if h.total > 21:
                h.status = "bust"
            elif h.total == 21:
                h.status = "stood"
        elif action == "S":
            h.status = "stood"
        elif action == "D":
            h.bet *= 2
            h.doubled = True
            h.cards.append(self.shoe.draw())
            h.status = "bust" if h.total > 21 else "stood"
        elif action == "R":
            h.status = "surrendered"
        elif action == "P":
            self._split(h)
        return self._advance()

    def state(self) -> dict:
        hide_hole = self.rules.hole_card == "peek" and self.phase == "player"
        shown = self.dealer[:1] if hide_hole else self.dealer
        total, soft = hand_value(shown) if shown else (0, False)
        dealer = {
            "cards": [c.to_dict() for c in shown] + ([{"hidden": True}] if hide_hole else []),
            "total": total, "soft": soft,
            "bust": total > 21,
            "blackjack": not hide_hole and is_blackjack(self.dealer),
        }
        return {
            "phase": self.phase,
            "hands": [h.to_dict() for h in self.hands],
            "active": self.active if self.phase == "player" else None,
            "dealer": dealer,
            "legal": self.legal_actions(),
            "net": sum(h.net for h in self.hands) if self.phase == "done" else None,
            "shuffled": self.shuffled,
            "cards_remaining": self.shoe.remaining,
        }

    # ---------- wewnętrzne ----------
    def _split(self, h: Hand) -> None:
        aces = h.cards[0].rank == "A"
        new = Hand(bet=self.base_bet, cards=[h.cards.pop()], from_split=True, split_aces=aces)
        h.from_split, h.split_aces = True, aces
        self.hands.insert(self.active + 1, new)
        h.cards.append(self.shoe.draw())
        if aces and not self.rules.hit_split_aces:
            h.status = "stood"
            new.cards.append(self.shoe.draw())
            new.status = "stood"

    def _advance(self) -> dict:
        while self.active < len(self.hands):
            h = self.hands[self.active]
            if len(h.cards) == 1:  # ręka po splicie czeka na drugą kartę
                h.cards.append(self.shoe.draw())
                if h.total == 21:
                    h.status = "stood"
            if h.status == "playing":
                return self.state()
            self.active += 1
        return self._settle()

    def _settle(self) -> dict:
        live = [h for h in self.hands if h.status in ("stood", "playing")]
        if live:
            for h in live:
                h.status = "stood"
            self.dealer = dealer_play(self.dealer, self.shoe, self.rules)
        d_total = hand_value(self.dealer)[0]
        d_bj = is_blackjack(self.dealer)

        for h in self.hands:
            if h.status == "surrendered":
                h.result, h.net = "surrender", -h.bet / 2
            elif h.status == "bust":
                h.result, h.net = "bust", -h.bet
            elif h.status == "blackjack":
                if d_bj:
                    h.result, h.net = "push", 0.0
                else:
                    h.result, h.net = "blackjack", h.bet * self.rules.blackjack_payout
            elif d_bj:
                h.result, h.net = "lose", -h.bet
            elif d_total > 21 or h.total > d_total:
                h.result, h.net = "win", h.bet
            elif h.total == d_total:
                h.result, h.net = "push", 0.0
            else:
                h.result, h.net = "lose", -h.bet

        if d_bj and self.rules.hole_card == "enhc" and self.rules.enhc_obo:
            # tracisz tylko stawkę początkową: dopłaty do double/split wracają
            losers = [h for h in self.hands if h.result in ("lose", "bust")]
            for i, h in enumerate(losers):
                h.net = -self.base_bet if i == 0 else 0.0

        self.phase = "done"
        self.active = len(self.hands)
        return self.state()
