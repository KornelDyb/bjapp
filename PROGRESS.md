# PROGRESS

- **Bieżący:** F-00 Szkielet aplikacji — 👀 czeka na akceptację (testy 16/16 zielone).
- **Ostatnia sesja (10.11.2026, chmura):** PLAN/FEATURES z PRD; baza SQLite (5 tabel), Api z obsługą błędów i logiem, UI Midnight glass z paskiem bocznym (6 ekranów), Inter lokalnie, serwer podglądu `tools/dev_server.py`, testy jednostkowe + e2e (Playwright).
- **Do sprawdzenia na PC:** czy `python -m app` otwiera okno WebView2 i w stopce jest „Połączono · v0.1.0” (w chmurze nie ma okna — sprawdzone w Chromium).
- **Dalej:** BJ-01 Silnik gry (logika, bez pytań). Przed BJ-02: zasady w Twoim kasynie.
- **Otwarte pytania:** BJ-02 kasyno/zasady · BJ-03 „dlaczego” 1 zdanie czy rozwijane · BJ-07 próg mapy błędów (50?).
- **Repo:** lokalny git, jeszcze bez remote — trzeba założyć `trener-blackjack` na GitHubie i podpiąć.
- **Uruchomienie:** `python -m app` · testy: `python -m pytest` (w chmurze: `PW_CHROMIUM_PATH=/opt/pw-browsers/chromium`).
