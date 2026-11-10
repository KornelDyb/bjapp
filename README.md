# Trener Blackjacka

Lokalna aplikacja desktopowa (Windows) do nauki strategii podstawowej i liczenia kart Hi-Lo. Python + pywebview, offline.
Plan: [PLAN.md](PLAN.md) · Feature'y: [FEATURES.md](FEATURES.md) · Stan: [PROGRESS.md](PROGRESS.md)

## Start (Windows)
```
py -3.12 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m app
```
Dane: `%APPDATA%\TrenerBlackjack\data.db`, log: `app.log` w tym samym folderze.

## Testy
```
python -m pytest
```
Testy e2e UI wymagają `playwright` (`python -m playwright install chromium`); bez niego są pomijane.

## Podgląd UI w przeglądarce (bez okna)
```
python tools/dev_server.py
```
→ http://localhost:8765 — to samo UI, z prawdziwym Pythonowym API.
