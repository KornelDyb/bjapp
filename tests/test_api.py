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


def test_rules_default_european(data_dir):
    r = make_api().get_rules()
    assert r["ok"] and r["rules"]["decks"] == 6 and r["rules"]["hole_card"] == "enhc"
    assert r["rules"]["enhc_obo"] is False and r["rules"]["h17"] is False and r["rules"]["das"] is True
    assert r["warnings"] == []


def test_set_rules_persists_and_recomputes_strategy(data_dir):
    api = make_api()
    before = api.get_strategy()["chart"]
    r = api.set_rules({"h17": True, "hole_card": "peek"})
    assert r["ok"] and r["rules"]["h17"] is True
    assert make_api().get_rules()["rules"]["hole_card"] == "peek"  # zapisane w bazie
    after = api.get_strategy()["chart"]
    assert after["key"] == "peek-h17" and after != before


def test_set_rules_rejects_bad_input_and_keeps_old(data_dir):
    api = make_api()
    for bad, word in [({"decks": 0}, "talii"), ({"hole_card": "x"}, "zakryt"), ({"foo": 1}, "nieznane"),
                      ({"h17": "tak"}, "h17"), ({"blackjack_payout": 3}, "wypłat")]:
        r = api.set_rules(bad)
        assert r["ok"] is False and word in r["error"].lower(), (bad, r)
    assert api.get_rules()["rules"]["decks"] == 6


def test_few_decks_warning(data_dir):
    api = make_api()
    r = api.set_rules({"decks": 1})
    assert r["ok"] and any("talii" in w for w in r["warnings"])


def test_strategy_fast_after_cache(data_dir):
    import time
    api = make_api()
    api.get_strategy()
    t = time.perf_counter()
    api.set_rules({"h17": True})
    api.get_strategy()
    assert time.perf_counter() - t < 0.5
