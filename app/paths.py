"""Ścieżki danych: %APPDATA%\\TrenerBlackjack na Windows, ~/.local/share/TrenerBlackjack gdzie indziej."""
import os
import sys
from pathlib import Path

APP_DIR_NAME = "TrenerBlackjack"
ROOT = Path(__file__).resolve().parents[1]
UI_DIR = ROOT / "ui"


def data_dir() -> Path:
    override = os.environ.get("TRENER_BJ_DATA_DIR")
    if override:
        base = Path(override)
    elif sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / APP_DIR_NAME
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / APP_DIR_NAME
    base.mkdir(parents=True, exist_ok=True)
    return base


def db_path() -> Path:
    return data_dir() / "data.db"


def log_path() -> Path:
    return data_dir() / "app.log"
