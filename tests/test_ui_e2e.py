"""F-00 e2e: UI w Chromium z prawdziwym Api przez tools/dev_server.py."""
import os
import threading

import pytest

pw = pytest.importorskip("playwright.sync_api")

from tools.dev_server import serve  # noqa: E402


def open_page(data_dir, monkeypatch, quiz_every):
    monkeypatch.setenv("TRENER_BJ_SEED", "7")
    from app.paths import db_path
    from app.storage.db import Database
    Database(db_path()).set_setting("count.every", str(quiz_every))
    server = serve(0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    with pw.sync_playwright() as p:
        browser = p.chromium.launch(executable_path=os.environ.get("PW_CHROMIUM_PATH") or None)
        pg = browser.new_page(viewport={"width": 1280, "height": 800})
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(f"http://127.0.0.1:{server.server_address[1]}/")
        yield pg
        assert errors == []
        browser.close()
    server.shutdown()


@pytest.fixture
def page(data_dir, monkeypatch):
    yield from open_page(data_dir, monkeypatch, 0)


@pytest.fixture
def quiz_page(data_dir, monkeypatch):
    yield from open_page(data_dir, monkeypatch, 1)


def test_starts_on_table_and_bridge_connects(page):
    page.wait_for_selector("text=Połączono · v0.1.0")
    assert page.locator('.nav-item[aria-current="page"]').get_attribute("data-screen") == "table"
    assert page.locator("h1").inner_text() == "Stół"


def test_navigation_and_placeholders(page):
    page.click('[data-screen="stats"]')
    assert page.locator("h1").inner_text() == "Statystyki"
    assert "Zagraj pierwsze 20 rozdań" in page.inner_text(".content")
    assert page.locator('.nav-item[aria-current="page"]').count() == 1
    page.keyboard.press("c")
    assert page.locator("h1").inner_text() == "Ściąga"


def test_inter_font_loaded(page):
    page.wait_for_function("document.fonts.status === 'loaded'")
    assert page.evaluate("document.fonts.check('600 16px Inter')")
    assert page.evaluate("[...document.fonts].some(f => f.family.includes('Inter') && f.status === 'loaded')")


def test_settings_change_rule_saves_and_updates_table(page):
    page.wait_for_selector("text=Połączono · v0.1.0")
    page.click('[data-screen="settings"]')
    page.click('button[data-key="h17"][data-val="true"]')
    page.wait_for_selector("#saved:not([hidden])")
    assert page.get_attribute('button[data-key="h17"][data-val="true"]', "aria-checked") == "true"
    page.click('[data-screen="table"]')
    assert "dobiera na miękkich 17" in page.inner_text("#table-rules")


def test_obo_option_only_without_hole_card(page):
    page.wait_for_selector("text=Połączono · v0.1.0")
    page.click('[data-screen="settings"]')
    page.wait_for_selector('[data-key="enhc_obo"]')
    page.click('button[data-key="hole_card"][data-val="\\"peek\\""]')
    page.wait_for_selector('[data-key="enhc_obo"]', state="detached")


def play_until_feedback(page, key="s", max_rounds=8):
    for _ in range(max_rounds):
        page.keyboard.press(" ")
        page.wait_for_selector("#controls [data-act]:not([disabled]), .banner")
        if page.locator("#controls [data-act]:not([disabled])").count():
            page.keyboard.press(key)
            page.wait_for_selector("#feedback:not([hidden])")
            return True
        page.wait_for_selector("#deal")
    return False


def test_table_round_with_live_feedback(page):
    page.wait_for_selector("text=Połączono · v0.1.0")
    page.click('[data-bet="25"]')
    assert play_until_feedback(page)
    fb = page.inner_text("#feedback")
    assert ("Dobrze" in fb) or ("Błąd" in fb and "kosztuje" in fb)
    assert " vs " in fb
    page.click("#fb-toggle")
    evs = page.inner_text(".evs")
    assert "(Twój ruch)" in evs and "Stój" in evs
    # dokończ rozdanie stojąc
    while page.locator("#controls [data-act]:not([disabled])").count():
        page.keyboard.press("s")
        page.wait_for_timeout(50)
    page.wait_for_selector(".banner")
    assert int(page.inner_text("#st-hands")) >= 1
    assert page.inner_text("#st-acc").endswith("%")


def test_illegal_key_does_nothing(page):
    page.wait_for_selector("text=Połączono · v0.1.0")
    page.keyboard.press(" ")
    page.wait_for_selector("#controls [data-act]:not([disabled]), .banner")
    if page.locator('#controls [data-act="R"][disabled]').count():
        page.keyboard.press("r")  # poddanie wyłączone w zasadach
        page.wait_for_timeout(150)
        assert page.locator("#feedback").is_hidden()


def finish_round(page):
    page.wait_for_selector("#controls [data-act]:not([disabled]), .banner")
    while page.locator("#controls [data-act]:not([disabled])").count():
        page.keyboard.press("s")
        page.wait_for_timeout(60)
    page.wait_for_selector(".banner")


def test_all_actions_always_on_screen(page):
    page.wait_for_selector("text=Połączono · v0.1.0")
    for k in "HSDPR":
        assert page.locator(f'#controls [data-act="{k}"]').count() == 1
    assert page.locator("#deal").is_enabled() and page.locator("#go-cheat").count() == 1
    page.click("#deal")
    page.wait_for_selector("#controls [data-act]:not([disabled]), .banner")
    if page.locator("#controls [data-act]:not([disabled])").count():
        assert page.locator("#deal").is_disabled()
    page.click("#go-cheat")
    assert page.locator("h1").inner_text() == "Ściąga"


def test_count_quiz_before_bet(quiz_page):
    page = quiz_page
    page.wait_for_selector("text=Połączono · v0.1.0")
    for _ in range(4):  # rozegraj, aż padnie pytanie (po >= 5 kartach)
        page.keyboard.press(" ")
        if page.locator("#quiz:not([hidden])").count():
            break
        finish_round(page)
    page.keyboard.press(" ")
    page.wait_for_selector("#quiz:not([hidden])")
    page.fill("#q-rc", "0")
    page.fill("#q-tc", "0")
    page.keyboard.press("Enter")
    page.wait_for_selector(".quiz-msg.ok, .quiz-msg.bad")
    assert "count" in page.inner_text("#q-msg").lower()
    page.keyboard.press("Enter")  # zamyka i rozdaje
    page.wait_for_selector("#quiz", state="hidden")
    assert page.inner_text("#st-cacc").endswith("%")


def test_toggle_live_count(page):
    page.wait_for_selector("text=Połączono · v0.1.0")
    assert page.locator("#count-live").is_hidden()
    page.click("#toggle-count")
    page.wait_for_selector("#count-live:not([hidden])")
    page.keyboard.press(" ")
    finish_round(page)
    assert "·" in page.inner_text("#st-count")


def test_reload_mid_round_restores_table(page):
    page.wait_for_selector("text=Połączono · v0.1.0")
    for _ in range(6):
        page.keyboard.press(" ")
        page.wait_for_selector("#controls [data-act]:not([disabled]), .banner")
        if page.locator("#controls [data-act]:not([disabled])").count():
            break
    page.reload()
    page.wait_for_selector("#controls [data-act]:not([disabled])")
    finish_round(page)
