# PROGRESS

- **Bieżący:** BJ-02 Zasady stołu + strategia — ❓ czeka na decyzję (zasady Twojego kasyna).
- **Ostatnia sesja (10.11.2026, chmura):** F-00 ✅ (wygląd zaakceptowany), BJ-01 ✅ silnik gry — 74 testy zielone; wizualizacja docs/bj01-krupier.png.
- **Do sprawdzenia na PC:** czy `python -m app` otwiera okno WebView2 i w stopce jest „Połączono · v0.1.0”.
- **Dalej:** BJ-02 — ustawienia zasad + tabele strategii podstawowej jako JSON, `best_action()`, testy komórka po komórce.
- **Otwarte pytania:** BJ-02 kasyno/zasady (+ czy przy BJ krupiera tracisz tylko stawkę początkową) · BJ-03 „dlaczego” 1 zdanie czy rozwijane · BJ-07 próg mapy błędów (50?).
- **Repo:** https://github.com/KornelDyb/bjapp (publiczne), gałąź `main`.
- **Uruchomienie:** `python -m app` · testy: `python -m pytest` (w chmurze: `PW_CHROMIUM_PATH=/opt/pw-browsers/chromium`).
