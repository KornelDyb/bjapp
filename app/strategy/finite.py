"""Dokładny solver dla skończonej liczby talii (bez zwracania kart).

EV ruchów S/H/D dla konkretnych 2 kart gracza vs karta krupiera, z usunięciem tych kart z buta.
Split: każda ręka liczona osobno z buta bez obu kart pary (bez ponownego splitu) — standardowe przybliżenie.
Używany przez tools/build_strategy.py do zbudowania tabel JSON (zależnych od sumy).
"""
from functools import lru_cache

HOLE_MODES = ("peek", "enhc", "enhc_obo")


def val(t: int, a: bool) -> int:
    return t + 10 if a and t + 10 <= 21 else t


class FiniteSolver:
    def __init__(self, decks: int, h17: bool, mode: str):
        assert mode in HOLE_MODES
        self.decks, self.h17, self.mode = decks, h17, mode
        self.full = tuple([4 * decks] * 9 + [16 * decks])  # indeks 0 = as, 9 = dziesiątki
        self.dealer = lru_cache(maxsize=None)(self._dealer)
        self.hit = lru_cache(maxsize=None)(self._hit)
        self.stand_cache = {}

    # ----- krupier -----
    def _dealer(self, comp, total, ace, n):
        """(p17, p18, p19, p20, p21, bust, bj)"""
        v = val(total, ace)
        soft = ace and total + 10 <= 21
        if n == 2 and v == 21:
            return (0, 0, 0, 0, 0, 0, 1.0)
        if v > 21:
            return (0, 0, 0, 0, 0, 1.0, 0)
        if v > 17 or (v == 17 and not (soft and self.h17)):
            r = [0.0] * 7
            r[v - 17] = 1.0
            return tuple(r)
        N = sum(comp)
        out = [0.0] * 7
        for i, k in enumerate(comp):
            if k:
                c = list(comp)
                c[i] -= 1
                sub = self.dealer(tuple(c), total + i + 1, ace or i == 0, n + 1)
                for j in range(7):
                    out[j] += k / N * sub[j]
        return tuple(out)

    def p_bj(self, comp, up):
        return self.dealer(comp, up, up == 1, 1)[6]

    def stand(self, comp, v, up):
        if v > 21:
            return -1.0
        key = (comp, v, up)
        if key in self.stand_cache:
            return self.stand_cache[key]
        d = self.dealer(comp, up, up == 1, 1)
        bj = d[6]
        if self.mode == "enhc":           # BJ krupiera bije wszystko
            ev = d[5] - bj + sum(d[j] * ((v > 17 + j) - (v < 17 + j)) for j in range(5))
        else:                             # peek / OBO: warunkowo „bez BJ krupiera”
            ev = (d[5] + sum(d[j] * ((v > 17 + j) - (v < 17 + j)) for j in range(5))) / (1 - bj)
        self.stand_cache[key] = ev
        return ev

    # ----- gracz -----
    def best_after(self, comp, t, a, up):
        v = val(t, a)
        if v > 21:
            return -1.0
        return max(self.stand(comp, v, up), self.hit(comp, t, a, up))

    def _hit(self, comp, t, a, up):
        N = sum(comp)
        ev = 0.0
        for i, k in enumerate(comp):
            if k:
                c = list(comp)
                c[i] -= 1
                ev += k / N * self.best_after(tuple(c), t + i + 1, a or i == 0, up)
        return ev

    def double(self, comp, t, a, up):
        N = sum(comp)
        ev = 0.0
        for i, k in enumerate(comp):
            if k:
                c = list(comp)
                c[i] -= 1
                ev += k / N * 2 * self.stand(tuple(c), val(t + i + 1, a or i == 0), up)
        return ev

    def split(self, comp, card, up, das):
        """comp: but bez obu kart pary i karty krupiera."""
        N = sum(comp)
        ev = 0.0
        for i, k in enumerate(comp):
            if not k:
                continue
            c = list(comp)
            c[i] -= 1
            c = tuple(c)
            x = i + 1
            t, a = card + x, card == 1 or x == 1
            if card == 1:
                best = self.stand(c, val(t, a), up)
            else:
                opts = [self.stand(c, val(t, a), up), self.hit(c, t, a, up)]
                if das:
                    opts.append(self.double(c, t, a, up))
                best = max(opts)
            ev += k / N * best
        return 2 * ev

    def _wrap(self, comp0, up, ev):
        if self.mode == "enhc_obo":
            p = self.p_bj(comp0, up)
            return -p + (1 - p) * ev
        return ev

    def cell(self, c1: int, c2: int, up: int) -> dict:
        """EV dla konkretnych kart (1 = as, 10 = dziesiątka)."""
        comp = list(self.full)
        for x in (c1, c2, up):
            comp[x - 1] -= 1
        comp = tuple(comp)
        t, a = c1 + c2, 1 in (c1, c2)
        v = val(t, a)
        out = {
            "S": self.stand(comp, v, up),
            "H": self.hit(comp, t, a, up),
            "D": self.double(comp, t, a, up),
        }
        if c1 == c2:
            out["P_das"] = self.split(comp, c1, up, True)
            out["P_ndas"] = self.split(comp, c1, up, False)
        return {k: self._wrap(comp, up, e) for k, e in out.items()}

    def combo_weight(self, c1, c2, up):
        comp = list(self.full)
        comp[up - 1] -= 1
        N = sum(comp)
        p = comp[c1 - 1] / N * (comp[c2 - 1] - (c1 == c2)) / (N - 1)
        return p if c1 == c2 else 2 * p
