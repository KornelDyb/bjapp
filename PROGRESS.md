# PROGRESS

- **Bieżący:** BJ-02 Zasady stołu + strategia — 👀 czeka na akceptację ekranu Ustawienia (logika gotowa, 99 testów zielonych).
- **Ostatnia sesja (10.11.2026, chmura):** F-00 ✅, BJ-01 ✅ (domyślnie: przy BJ krupiera tracisz wszystko), BJ-02 solver + tabele + Ustawienia. Wizualizacje w docs/.
- **Do sprawdzenia na PC:** czy `python -m app` otwiera okno WebView2 i w stopce jest „Połączono · v0.1.0”.
- **Dalej:** BJ-03 Stół z korektą na żywo — najpierw pytanie: „dlaczego” jednym zdaniem czy rozwijane.
- **Otwarte pytania:** BJ-03 „dlaczego” · BJ-07 próg mapy błędów (50?) · decyzja Claude'a do potwierdzenia: tabele strategii liczone solverem.
- **Tabele strategii:** po zmianie solvera przelicz `python tools/build_strategy.py` (~7 min na 4 rdzeniach).
- **Repo:** https://github.com/KornelDyb/bjapp (publiczne), gałąź `main`.
- **Uruchomienie:** `python -m app` · testy: `python -m pytest` (w chmurze: `PW_CHROMIUM_PATH=/opt/pw-browsers/chromium`) · podgląd: `python tools/dev_server.py`.
