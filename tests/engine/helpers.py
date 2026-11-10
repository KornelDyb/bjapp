from app.engine.cards import parse
from app.engine.game import Game
from app.engine.rules import Rules
from app.engine.shoe import Shoe


def game(order: str, **rules) -> Game:
    """Gra z butem o ustalonej kolejności kart, np. 'T 6 7 | 5' (| ignorowane, dla czytelności)."""
    return Game(Rules(**rules), shoe=Shoe.stacked(parse(order.replace("|", " "))))


def cards_of(state, i=0):
    return [c["rank"] for c in state["hands"][i]["cards"]]
