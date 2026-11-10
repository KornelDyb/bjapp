from app import __version__
from app.api import Api
from app.paths import db_path, log_path
from app.storage.db import Database


def make_api():
    return Api(Database(db_path()))


def test_ping_reports_version_and_db(data_dir):
    r = make_api().ping()
    assert r["ok"] is True
    assert r["version"] == __version__
    assert r["db_path"] == str(db_path())


def test_settings_via_api(data_dir):
    api = make_api()
    assert api.set_setting("rules.decks", 6) == {"ok": True}
    r = api.get_setting("rules.decks")
    assert r == {"ok": True, "value": 6}  # JSON-typed roundtrip
    assert api.get_setting("nope")["value"] is None


def test_api_error_is_human_readable_and_logged(data_dir):
    api = make_api()
    r = api.set_setting("", 1)
    assert r["ok"] is False
    assert "klucz" in r["error"].lower()
    assert "Traceback" not in r["error"]
    assert "set_setting" in log_path().read_text(encoding="utf-8")
