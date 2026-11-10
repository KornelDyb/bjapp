"""Jedyne wejście z UI (window.pywebview.api). Każda metoda zwraca {ok: bool, ...}."""
import functools
import json
import logging

from . import __version__
from .paths import log_path
from .storage.db import Database

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

    @staticmethod
    def _check_key(key):
        if not isinstance(key, str) or not key.strip():
            raise UserError("Klucz ustawienia nie może być pusty.")
        return key.strip()
