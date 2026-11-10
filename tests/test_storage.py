from app.paths import data_dir, db_path, log_path
from app.storage.db import Database

TABLES = {"sessions", "hands", "decisions", "count_checks", "settings"}


def test_data_dir_respects_env_override(data_dir):
    assert str(db_path()).startswith(str(data_dir))
    assert db_path().name == "data.db"
    assert log_path().name == "app.log"


def test_data_dir_on_windows_uses_appdata(monkeypatch, tmp_path):
    monkeypatch.delenv("TRENER_BJ_DATA_DIR", raising=False)
    monkeypatch.setattr("app.paths.sys.platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert data_dir() == tmp_path / "TrenerBlackjack"


def test_schema_created_with_all_tables(data_dir):
    db = Database(db_path())
    assert TABLES <= db.table_names()


def test_schema_init_is_idempotent(data_dir):
    Database(db_path()).set_setting("x", "1")
    db = Database(db_path())  # second start must not wipe data
    assert TABLES <= db.table_names()
    assert db.get_setting("x") == "1"


def test_table_columns_match_plan(data_dir):
    db = Database(db_path())
    assert {"started_at", "ended_at", "rules_json", "mode", "hands_count", "correct_count"} <= db.columns("sessions")
    assert {"session_id", "player_cards", "dealer_cards", "bet", "result", "payout", "true_count_at_start"} <= db.columns("hands")
    assert {"hand_id", "player_total", "soft", "pair", "dealer_upcard", "action_taken", "action_correct", "is_correct"} <= db.columns("decisions")
    assert {"session_id", "true_rc", "answer_rc", "true_tc", "answer_tc", "is_correct"} <= db.columns("count_checks")
    assert {"key", "value"} <= db.columns("settings")


def test_settings_roundtrip_and_default(data_dir):
    db = Database(db_path())
    assert db.get_setting("missing", "dflt") == "dflt"
    db.set_setting("decks", "6")
    db.set_setting("decks", "8")
    assert db.get_setting("decks") == "8"
