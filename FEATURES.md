# Feature'y — Trener Blackjacka

Statusy: ⬜ todo | 🟨 w toku | ❓ czeka na decyzję | 👀 czeka na akceptację | ✅ gotowe | 🔴 zablokowane | ♻️ do poprawy

## F-00 Szkielet aplikacji
Status: 👀 czeka na akceptację
Typ: UI
Zależy od: —
Kryteria akceptacji:
- [ ] (do sprawdzenia na PC) `python -m app` otwiera okno pywebview „Trener Blackjacka” (min. 1100×720) ładujące `ui/index.html`
- [x] Pasek boczny z ikonami i 6 pozycjami: Stół, Liczenie, Statystyki, Symulacja, Ściąga, Ustawienia; start na „Stół”, aktywna pozycja podświetlona akcentem
- [x] Kolory z tabeli Midnight glass w zmiennych CSS; szkło z blur 16px; liczby tabular-nums; Inter ładowany lokalnie
- [x] Most Python↔JS: `Api.ping()` zwraca `{ok, version, db_path}`; UI pokazuje wersję i status połączenia w stopce paska
- [x] Przy starcie tworzy się baza SQLite z tabelami sessions, hands, decisions, count_checks, settings (idempotentnie)
- [x] Ustawienia zapisywane i czytane przez `Api.get_setting / set_setting`
- [x] Błąd w API zwraca `{ok: false, error: "<po ludzku>"}` i trafia do logu `app.log` w katalogu danych
- [x] Puste ekrany (poza Stołem) pokazują stan „wkrótce” z nazwą feature'a
- [x] `pytest` przechodzi
Otwarte pytania: brak
Testy: tests/test_storage.py, tests/test_api.py, tests/test_ui_static.py, tests/test_ui_e2e.py · Screenshoty: docs/f00-*.png

## BJ-01 Silnik gry
Status: ⬜ todo · Typ: logika · Zależy od: F-00
Kryteria akceptacji: but N talii + tasowanie wg penetracji; rozdanie 2+1 (ENHC); wartości rąk (miękkie/twarde, as); ruchy H/S/D/P/R wg zasad; krupier S17/H17; wypłaty: wygrana 1:1, blackjack 3:2, push, double, split (DAS, split asów jedna karta), surrender ½; ENHC: przy BJ krupiera tracisz tylko stawkę początkową. Do doprecyzowania przy starcie.
Testy: tests/engine/

## BJ-02 Zasady stołu + strategia
Status: ⬜ todo · Typ: logika · Zależy od: BJ-01
Otwarte pytania: w jakim kasynie grasz i jakie są tam zasady? (+ weryfikacja założenia o domyślnych zasadach)

## BJ-03 Stół z korektą na żywo
Status: ⬜ todo · Typ: UI · Zależy od: BJ-02
Otwarte pytania: „dlaczego” jednym zdaniem czy rozwijane?

## BJ-04 Ściąga strategii
Status: ⬜ todo · Typ: UI · Zależy od: BJ-02

## BJ-05 Liczenie Hi-Lo
Status: ⬜ todo · Typ: logika + UI · Zależy od: BJ-01
Założenie do weryfikacji: pytanie kontrolne co 5–15 kart i przed każdą stawką.

## BJ-06 Podpowiedź stawki
Status: ⬜ todo · Typ: logika + UI · Zależy od: BJ-05
Założenie do weryfikacji: bet ramp 1/2/4/8.

## BJ-07 Statystyki
Status: ⬜ todo · Typ: UI · Zależy od: BJ-03
Otwarte pytania: od ilu rozdań mapa błędów (propozycja 50)?

## BJ-08 Symulacja budżetu
Status: ⬜ todo · Typ: logika + UI · Zależy od: BJ-02, BJ-06, BJ-07
Założenie do weryfikacji: „Twój styl” = ostatnie 500 decyzji + mapa błędów.

## BJ-09 Paczka .exe
Status: ⬜ todo · Typ: integracja · Zależy od: wszystkie
Uwaga: budowa .exe wymaga Windowsa (PyInstaller nie robi cross-compile) — krok wykonywany na PC.
