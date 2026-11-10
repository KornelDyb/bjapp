import pytest

from app.engine.errors import IllegalMove
from app.engine.game import Game
from app.engine.rules import Rules
from .helpers import cards_of, game

# Kolejność ENHC: gracz, krupier, gracz, potem ruchy gracza, potem krupier.


def test_enhc_deal_order_and_dealer_has_one_card():
    s = game("T 6 7").start_round(10)
    assert cards_of(s) == ["T", "7"]
    assert [c["rank"] for c in s["dealer"]["cards"]] == ["6"]
    assert s["phase"] == "player"
    assert set(s["legal"]) == {"H", "S", "D"}


def test_stand_dealer_draws_to_17_and_player_wins():
    g = game("T 6 9 T 5")  # krupier 6,T,5 = 21
    g.start_round(10)
    s = g.act("S")
    assert s["phase"] == "done"
    assert s["dealer"]["total"] == 21
    assert s["hands"][0]["result"] == "lose" and s["net"] == -10


def test_player_wins_when_dealer_busts():
    g = game("T 6 9 T 8")  # krupier 6+T+8 = 24
    g.start_round(10)
    s = g.act("S")
    assert s["dealer"]["bust"] and s["hands"][0]["result"] == "win" and s["net"] == 10


def test_push():
    g = game("T 7 8 T")  # gracz 18 vs krupier 7+T = 17
    g.start_round(10)
    s = g.act("S")
    assert s["dealer"]["total"] == 17
    assert s["hands"][0]["result"] == "win"
    g = game("T 7 7 T")  # 17 vs 17
    g.start_round(10)
    assert g.act("S")["hands"][0]["result"] == "push"


def test_hit_and_bust_dealer_does_not_draw():
    g = game("T 6 6 9")
    g.start_round(10)
    s = g.act("H")
    assert s["hands"][0]["result"] == "bust" and s["net"] == -10
    assert len(s["dealer"]["cards"]) == 1  # ENHC: krupier nie dobiera


def test_hit_to_21_auto_stands():
    g = game("5 6 6 T T 9")  # gracz 5,6 + T = 21 -> krupier 6,T,9 = 25
    g.start_round(10)
    s = g.act("H")
    assert s["phase"] == "done" and s["hands"][0]["total"] == 21 and s["net"] == 10


def test_double_one_card_double_stake():
    g = game("5 6 6 T T 9")
    g.start_round(10)
    s = g.act("D")
    assert cards_of(s) == ["5", "6", "T"]
    assert s["hands"][0]["bet"] == 20 and s["net"] == 20


def test_double_only_on_two_cards():
    g = game("2 6 3 2 T")
    g.start_round(10)
    g.act("H")
    with pytest.raises(IllegalMove, match="podwoić"):
        g.act("D")


def test_illegal_move_leaves_state_unchanged():
    g = game("T 6 7")
    before = g.start_round(10)
    with pytest.raises(IllegalMove):
        g.act("P")
    assert g.state() == before


def test_player_blackjack_pays_3_to_2():
    g = game("A 6 K")
    s = g.start_round(10)
    assert s["phase"] == "done" and s["hands"][0]["result"] == "blackjack" and s["net"] == 15
    assert len(s["dealer"]["cards"]) == 1  # 6 nie da BJ -> krupier nie dobiera


def test_blackjack_payout_configurable():
    g = Game(Rules(blackjack_payout=1.2), shoe=game("A 6 K").shoe)
    assert g.start_round(10)["net"] == 12


def test_blackjack_vs_dealer_blackjack_push():
    g = game("A A K T")
    s = g.start_round(10)
    assert s["dealer"]["blackjack"] and s["hands"][0]["result"] == "push" and s["net"] == 0


def test_enhc_dealer_blackjack_obo_loses_only_original_bet():
    g = game("5 T 6 9 A", enhc_obo=True)  # double: gracz dostaje 9 (=20), krupier T+A = BJ
    g.start_round(10)
    s = g.act("D")
    assert s["dealer"]["blackjack"]
    assert s["net"] == -10


def test_enhc_dealer_blackjack_default_loses_all():
    g = game("5 T 6 9 A")  # domyślnie (decyzja 10.11): tracisz wszystko
    g.start_round(10)
    assert g.act("D")["net"] == -20


def test_dealer_s17_stands_soft17_h17_hits():
    g = game("T A 8 6")  # krupier A+6 = miękkie 17
    g.start_round(10)
    s = g.act("S")
    assert s["dealer"]["total"] == 17 and len(s["dealer"]["cards"]) == 2
    g = game("T A 8 6 2", h17=True)
    g.start_round(10)
    s = g.act("S")
    assert s["dealer"]["total"] == 19


def test_split_two_hands_played_in_order():
    # gracz 8,8 vs 6: split -> ręka1: 8+3 (11) double -> +T = 21; ręka2: 8+T = 18 stój; krupier 6+T+7 = 23
    g = game("8 6 8 3 T T T 7")
    g.start_round(10)
    s = g.act("P")
    assert len(s["hands"]) == 2 and s["active"] == 0 and cards_of(s, 0) == ["8", "3"]
    s = g.act("D")  # DAS domyślnie dozwolone
    assert s["active"] == 1 and cards_of(s, 1) == ["8", "T"]
    s = g.act("S")
    assert s["phase"] == "done" and s["dealer"]["bust"]
    assert s["net"] == 20 + 10


def test_no_double_after_split_without_das():
    g = game("8 6 8 3 T", das=False)
    g.start_round(10)
    s = g.act("P")
    assert "D" not in s["legal"]


def test_split_aces_one_card_each_no_blackjack():
    g = game("A 6 A K 9 T 5")  # ręka1 A+K = 21 (nie BJ), ręka2 A+9 = 20; krupier 6+T+5 = 21
    g.start_round(10)
    s = g.act("P")
    assert s["phase"] == "done"
    assert [h["result"] for h in s["hands"]] == ["push", "lose"]
    assert s["net"] == -10


def test_split_same_value_tens_and_max_hands():
    g = game("K 6 Q T T T 2 2 2 2 T")
    g.start_round(10)
    assert "P" in g.state()["legal"]  # K + Q: ta sama wartość
    s = g.act("P")  # ręka1 K,T
    s = g.act("P")  # ręka1 K,T -> 3 ręce
    s = g.act("P")  # 4 ręce
    assert len(s["hands"]) == 4 and "P" not in s["legal"]


def test_surrender_only_when_allowed_and_first_move():
    g = game("T 6 6")
    g.start_round(10)
    assert "R" not in g.state()["legal"]
    g = game("T 6 6", surrender=True)
    g.start_round(10)
    s = g.act("R")
    assert s["hands"][0]["result"] == "surrender" and s["net"] == -5


def test_peek_dealer_blackjack_ends_round_immediately():
    g = game("T A 9 K", hole_card="peek")  # gracz T,9; krupier A + K (zakryta)
    s = g.start_round(10)
    assert s["phase"] == "done" and s["dealer"]["blackjack"] and s["net"] == -10


def test_peek_hole_card_hidden_during_play():
    g = game("T 9 7 8 5", hole_card="peek")
    s = g.start_round(10)
    assert s["phase"] == "player"
    assert s["dealer"]["cards"][1] == {"hidden": True}
    assert s["dealer"]["total"] == 9  # tylko widoczna karta


def test_cannot_start_round_during_play_or_with_bad_bet():
    g = game("T 6 7")
    with pytest.raises(IllegalMove):
        g.start_round(0)
    g.start_round(10)
    with pytest.raises(IllegalMove):
        g.start_round(10)


def test_reshuffle_only_between_rounds():
    import random
    from app.engine.shoe import Shoe
    shoe = Shoe(decks=1, penetration=0.1, rng=random.Random(3))
    g = Game(Rules(decks=1), shoe=shoe)  # penetracja 10% ustawiona w bucie
    for _ in range(30):
        s = g.start_round(1)
        while s["phase"] == "player":
            s = g.act("S")
        assert shoe.remaining >= 52 - 6 * 4  # nigdy nie wyczerpuje buta w rundzie
