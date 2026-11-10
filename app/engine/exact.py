"""Dokładne prawdopodobieństwo bustu krupiera (rekurencja bez zwracania kart).
Niezależny od silnika punkt odniesienia dla testów i ściągi."""
from functools import lru_cache

VALS = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)


def dealer_bust_probability(up: int, decks: int = 6, h17: bool = False) -> float:
    """up: 1 = as, 10 = dziesiątka/figura. Zwraca P(bust) w ENHC (bez warunku 'brak BJ')."""
    comp = [4 * decks] * 9 + [16 * decks]
    comp[up - 1] -= 1

    @lru_cache(None)
    def rec(c, total, aces):
        soft = aces and total + 10 <= 21
        t = total + 10 if soft else total
        if t > 21:
            return 1.0
        if t > 17 or (t == 17 and not (soft and h17)):
            return 0.0
        n = sum(c)
        p = 0.0
        for i, k in enumerate(c):
            if k:
                cc = list(c)
                cc[i] -= 1
                p += k / n * rec(tuple(cc), total + VALS[i], aces or i == 0)
        return p

    return rec(tuple(comp), up, up == 1)
