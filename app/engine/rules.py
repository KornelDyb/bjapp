from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Rules:
    decks: int = 6
    penetration: float = 0.75
    h17: bool = False              # krupier dobiera na miękkich 17
    das: bool = True               # podwojenie po splicie
    surrender: bool = False        # poddanie (pierwszy ruch)
    hole_card: str = "enhc"        # "enhc" (bez zakrytej karty) | "peek"
    enhc_obo: bool = True          # ENHC: przy BJ krupiera tracisz tylko stawkę początkową
    blackjack_payout: float = 1.5
    max_hands: int = 4
    resplit_aces: bool = False
    hit_split_aces: bool = False

    def __post_init__(self):
        if self.hole_card not in ("enhc", "peek"):
            raise ValueError("hole_card musi być 'enhc' albo 'peek'")
        if not 1 <= self.decks <= 8:
            raise ValueError("Liczba talii: 1–8")
        if not 0.3 <= self.penetration <= 0.95:
            raise ValueError("Penetracja: 30–95%")

    def to_dict(self) -> dict:
        return asdict(self)
