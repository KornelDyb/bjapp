"""F-00 e2e: UI w Chromium z prawdziwym Api przez tools/dev_server.py."""
import os
import threading

import pytest

pw = pytest.importorskip("playwright.sync_api")

from tools.dev_server import serve  # noqa: E402


@pytest.fixture
def page(data_dir):
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
