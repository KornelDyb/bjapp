# Feature'y — Trener Blackjacka

Statusy: ⬜ todo | 🟨 w toku | ❓ czeka na decyzję | 👀 czeka na akceptację | ✅ gotowe | 🔴 zablokowane | ♻️ do poprawy

## F-00 Szkielet aplikacji
Status: ✅ gotowe (wygląd zaakceptowany 10.11; okno WebView2 do potwierdzenia na PC)
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
Status: ✅ gotowe
Typ: logika
Zależy od: F-00
Kryteria akceptacji:
- [x] But: N talii (domyślnie 6) = N×52 karty, tasowanie po przekroczeniu penetracji (domyślnie 75%) — dopiero przed następnym rozdaniem, nigdy w trakcie; deterministyczny przy podanym seedzie
- [x] Wartość ręki: as = 1 lub 11, figury = 10; rozpoznaje rękę miękką/twardą, blackjacka (2 karty = 21, nie po splicie)
- [x] Rozdanie: ENHC (domyślnie) → gracz, krupier, gracz; krupier dobiera drugą kartę dopiero po graczu. Peek (opcja) → krupier ma zakrytą kartę i sprawdza BJ przy A/10
- [x] Legalne ruchy: H/S zawsze; D tylko na 2 kartach (po splicie tylko przy DAS); P na parze o tej samej wartości, maks. 4 ręce, asy bez ponownego splitu i bez dobierania (1 karta); R tylko jako pierwszy ruch, bez splitu i tylko gdy zasady pozwalają
- [x] Nielegalny ruch → czytelny błąd („Nie możesz teraz podwoić.”), stan bez zmian
- [x] Krupier: dobiera do 17; S17 stoi na miękkich 17, H17 dobiera; nie dobiera, gdy wszystkie ręce gracza przegrały (bust/poddanie)
- [x] Wypłaty (netto): wygrana +1×, blackjack +1,5× (konfig.), push 0, przegrana −1×, double ±2×, poddanie −0,5×; BJ gracza vs BJ krupiera = push
- [x] ENHC + BJ krupiera: domyślnie tracisz tylko stawkę początkową (zwrot dopłat do double/split, „OBO”); opcja „tracisz wszystko”
- [x] Stan rundy jako słownik dla UI (ręce, sumy, miękka, stawki, aktywna ręka, legalne ruchy, karty krupiera z ukrytą kartą, wyniki)
- [x] Sanity check: odsetek bustów krupiera z silnika (S17 i H17, 6 talii, każda karta) w granicach 4,5 błędu standardowego (≈0,5–0,95 pp) od dokładnego wyliczenia rekurencyjnego
Otwarte pytania: brak (zasady konkretnego kasyna → BJ-02; reguła OBO do potwierdzenia razem z nimi)
Testy: tests/engine/ · Wizualizacja: docs/bj01-krupier.png

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
