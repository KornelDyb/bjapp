"""Jedyne wejście z UI (window.pywebview.api). Każda metoda zwraca {ok: bool, ...}."""
import functools
import json
import logging

from . import __version__
from .paths import log_path
from .engine.rules import Rules
from .storage.db import Database
from .strategy.solver import chart

log = logging.getLogger("trener_bj")


class UserError(Exception):
    """Błąd z komunikatem gotowym do pokazania użytkownikowi."""


def setup_logging() -> None:
    if any(isinstance(h, logging.FileHandler) and h.baseFilename == str(log_path()) for h in log.handlers):
        return
    for h in list(log.handlers):
        log.removeHandler(h)
    handler = logging.FileHandler(log_path(), encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(handler)
    log.setLevel(logging.INFO)


def endpoint(fn):
    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        try:
            result = fn(self, *args, **kwargs)
            return {"ok": True, **(result or {})}
        except UserError as e:
            log.warning("%s: %s", fn.__name__, e)
            return {"ok": False, "error": str(e)}
        except Exception:
            log.exception("%s: nieoczekiwany błąd", fn.__name__)
            return {"ok": False, "error": "Coś poszło nie tak. Szczegóły zapisano w app.log."}
    return wrapper


class Api:
    def __init__(self, db: Database):
        self._db = db
        setup_logging()

    @endpoint
    def ping(self):
        return {"version": __version__, "db_path": str(self._db.path)}

    @endpoint
    def get_setting(self, key):
        raw = self._db.get_setting(self._check_key(key))
        return {"value": None if raw is None else json.loads(raw)}

    @endpoint
    def set_setting(self, key, value):
        self._db.set_setting(self._check_key(key), json.dumps(value))

    # ----- zasady stołu i strategia -----
    EDITABLE = {
        "decks": int, "h17": bool, "das": bool, "surrender": bool, "hole_card": str,
        "enhc_obo": bool, "blackjack_payout": float, "penetration": float,
    }
    FIELD_NAMES = {"decks": "liczba talii", "penetration": "penetracja", "blackjack_payout": "wypłata za blackjacka",
                   "hole_card": "zakryta karta krupiera"}

    def _rules(self) -> Rules:
        raw = self._db.get_setting("rules")
        return Rules(**json.loads(raw)) if raw else Rules()

    @staticmethod
    def _warnings(rules: Rules) -> list[str]:
        w = []
        if rules.decks <= 2:
            w.append("Strategia jest liczona dla 4–8 talii; przy 1–2 taliach kilka decyzji może się różnić.")
        return w

    @endpoint
    def get_rules(self):
        rules = self._rules()
        return {"rules": rules.to_dict(), "warnings": self._warnings(rules)}

    @endpoint
    def set_rules(self, changes):
        if not isinstance(changes, dict):
            raise UserError("Zasady muszą być słownikiem.")
        unknown = set(changes) - set(self.EDITABLE)
        if unknown:
            raise UserError(f"Nieznane zasady: {', '.join(sorted(unknown))}.")
        clean = {}
        for k, v in changes.items():
            t = self.EDITABLE[k]
            ok = isinstance(v, bool) if t is bool else (isinstance(v, (int, float)) and not isinstance(v, bool)
                                                       if t in (int, float) else isinstance(v, t))
            if not ok:
                raise UserError(f"Zła wartość dla „{k}” ({self.FIELD_NAMES.get(k, k)}).")
            clean[k] = t(v)
        if "blackjack_payout" in clean and clean["blackjack_payout"] not in (1.5, 1.2, 1.0):
            raise UserError("Wypłata za blackjacka: 3:2, 6:5 albo 1:1.")
        try:
            rules = Rules(**{**self._rules().to_dict(), **clean})
        except ValueError as e:
            msg = str(e).replace("hole_card musi być", "Zakryta karta krupiera: wybierz")
            raise UserError(msg + ".") from None
        self._db.set_setting("rules", json.dumps(rules.to_dict()))
        return {"rules": rules.to_dict(), "warnings": self._warnings(rules)}

    @endpoint
    def get_strategy(self):
        return {"chart": chart(self._rules())}

    @staticmethod
    def _check_key(key):
        if not isinstance(key, str) or not key.strip():
            raise UserError("Klucz ustawienia nie może być pusty.")
        return key.strip()
