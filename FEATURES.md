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
Status: ✅ gotowe (Kornel przeszedł do BJ-03 10.11)
Typ: logika + UI (ekran Ustawienia)
Zależy od: BJ-01
Kryteria akceptacji:
- [x] Solver EV (dokładny, 6 talii, bez zwracania kart; tabele JSON z tools/build_strategy.py) liczy dla każdej sytuacji (twarde 4–21, miękkie 13–21, pary 2–A) × karta krupiera (2–A) EV ruchów S/H/D/P/R przy danych zasadach
- [x] Dla zasad US (6 talii, S17, DAS, peek, bez poddania) tabela zgadza się z kanoniczną strategią podstawową w każdej komórce
- [x] Znane różnice reguł: H17 → 11 vs A podwój, A7 vs 2 podwój, A8 vs 6 podwój; poddanie → 16 vs 9/10/A i 15 vs 10 poddaj; ENHC bez OBO → 11 vs 10 i 11 vs A dobierz
- [x] EV z solvera zgadza się z symulacją na silniku (6 talii) w granicach 4,5 SE dla kontrolnych sytuacji
- [x] `best_action(karty, karta krupiera, zasady, legalne ruchy)` wybiera najlepszy LEGALNY ruch (np. 3 karty = 11 → dobierz, nie podwój) i zwraca EV wszystkich ruchów
- [x] Ściąga jako kody: H, S, D/Dh/Ds (podwój, inaczej dobierz/stój), P, R/Rh/Rs/Rp
- [x] Zasady zapisywane w ustawieniach; domyślne europejskie (6 talii, S17, DAS, bez poddania, ENHC, 3:2, bez OBO); zmiana zasad → strategia przełącza się na właściwą tabelę (< 100 ms, cache)
- [x] Błędne zasady → komunikat po ludzku, nic nie zapisane
- [x] Ekran Ustawienia: formularz zasad, zapis, informacja „strategia przeliczona”; ostrzeżenie dla 1–2 talii (strategia liczona dla 4+ talii)
Otwarte pytania: brak (zasady potwierdzone 10.11)
Testy: tests/strategy/, tests/test_api.py, tests/test_ui_e2e.py · Wizualizacje: docs/bj02-strategia.png, docs/bj02-ustawienia.png

## BJ-03 Stół z korektą na żywo
Status: ✅ gotowe (mechanika ENHC potwierdzona przez Kornela 10.11)
Typ: UI + logika
Zależy od: BJ-02
Kryteria akceptacji:
- [x] Stawka: wybór żetonem (1, 5, 10, 25, 50, 100 jednostek), domyślnie 10; „Rozdaj” (Spacja) startuje rozdanie
- [x] Karty animowane: rozdanie ~250 ms na kartę, flip zakrytej karty krupiera (tryb peek), ręce po splicie obok siebie, aktywna podświetlona
- [x] Po każdej decyzji: ✅/❌ + błysk zielony/czerwony + jedno zdanie „dlaczego” (konkretnie dla sytuacji: suma, karta krupiera, powód); decyzja jest wykonywana zawsze
- [x] Rozwinięcie „Szczegóły”: EV każdego legalnego ruchu (np. „Dobierz −0,54”) i koszt błędu w % stawki
- [x] Skróty: H S D P R (tylko legalne), Spacja = następne rozdanie; przyciski nielegalnych ruchów wyłączone
- [x] Wynik rozdania: baner (wygrana/przegrana/push/blackjack/poddanie) z kwotą; nagłówek: trafność sesji, liczba rozdań, wynik sesji
- [x] Zapis do bazy: sesja (przy pierwszym rozdaniu), rozdanie (karty, stawka, wynik, wypłata), każda decyzja (suma, miękka, para, karta krupiera, ruch, ruch poprawny, czy trafny)
- [x] Zmiana zasad w Ustawieniach działa od następnego rozdania (nowy but)
- [x] Feedback po decyzji < 100 ms (po stronie Pythona)
Otwarte pytania: brak („dlaczego” = zdanie + rozwijane EV, decyzja 10.11)
Testy: tests/test_table.py, tests/strategy/test_explain.py, tests/test_ui_e2e.py · Screenshoty: docs/bj03-*.png

## BJ-04 Ściąga strategii
Status: ⬜ todo · Typ: UI · Zależy od: BJ-02

## BJ-05 Liczenie Hi-Lo (przy stole)
Status: 👀 czeka na akceptację (przesunięte przed BJ-04 — decyzja 10.11)
Typ: logika + UI
Zależy od: BJ-03
Kryteria akceptacji:
- [x] Hi-Lo: 2–6 = +1, 7–9 = 0, 10/figury/as = −1; running count liczony ze wszystkich kart, które wyszły z buta od tasowania; tasowanie zeruje
- [x] True count = running / talie pozostałe w bucie (karty pozostałe / 52); odpowiedź TC uznana, gdy różni się od dokładnej o ≤ 0,5; RC musi być dokładny
- [x] Pytanie kontrolne przed stawką co N rozdań (Ustawienia: co rozdanie / co 3 (domyślnie) / co 5 / wyłączone); nie pyta, gdy od tasowania wyszło < 5 kart
- [x] Okno pytania: pola running i true count (przecinek lub kropka), Enter zatwierdza; wynik ✅/❌ z poprawnymi wartościami i jednym zdaniem, potem rozdanie rusza
- [x] Zapis: count_checks (prawdziwe i podane RC/TC, trafność); hands.true_count_at_start
- [x] Licznik domyślnie ukryty; przełącznik „Pokaż licznik” w Ustawieniach pokazuje running/true count na stole na żywo
- [x] Po tasowaniu informacja „Przetasowano — liczysz od zera”
- [x] Nagłówek stołu: trafność liczenia w sesji
- [x] Ekran Liczenie: zasady Hi-Lo, kiedy liczenie ma sens (tasownica ciągła = bez sensu), trafność liczenia
- [x] (dodane 10.11) Wszystkie akcje zawsze na ekranie: H/S/D/P/R, Rozdaj, Ściąga, przełącznik licznika — niedostępne wyłączone
- [x] (poprawka) Po przeładowaniu strony w trakcie rozdania stół odtwarza bieżący stan z Pythona
Otwarte pytania: brak
Testy: tests/counting/, tests/test_table.py, tests/test_ui_e2e.py · Screenshoty: docs/bj05-*.png

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
