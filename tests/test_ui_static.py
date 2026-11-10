"""F-00: statyczne sprawdzenie UI (wygląd akceptuje użytkownik na screenshocie)."""
import re
from pathlib import Path

UI = Path(__file__).resolve().parents[1] / "ui"
SCREENS = ["Stół", "Liczenie", "Statystyki", "Symulacja", "Ściąga", "Ustawienia"]
COLORS = ["#0B0E1F", "#090B18", "#2A3060", "#7C5CFF", "#8F74FF", "#4ADE80", "#FF6B81",
          "#FBBF24", "#E7E9FF", "#8D92B8"]


def test_sidebar_has_six_screens_in_order():
    html = (UI / "index.html").read_text(encoding="utf-8")
    labels = re.findall(r'data-screen="[^"]+"[^>]*>.*?<span[^>]*>([^<]+)</span>', html, re.S)
    assert labels == SCREENS


def test_palette_tokens_present():
    css = (UI / "styles.css").read_text(encoding="utf-8").upper()
    for c in COLORS:
        assert c in css, c
    assert "RGBA(26,31,61,0.6)" in css.replace(" ", "")
    assert "BLUR(16PX)" in css
    assert "TABULAR-NUMS" in css


def test_inter_font_is_local():
    css = (UI / "styles.css").read_text(encoding="utf-8")
    assert "@font-face" in css and "Inter" in css
    assert "fonts.googleapis" not in css
    assert list((UI / "vendor").glob("inter*.woff2"))


def test_no_external_resources():
    html = (UI / "index.html").read_text(encoding="utf-8")
    assert not re.search(r'(src|href)="https?://', html)
