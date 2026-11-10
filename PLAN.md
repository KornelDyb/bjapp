# PRD: Trener Blackjacka

> Źródło: dokument „PRD: Trener Blackjacka” (Claude Docs, https://claude.ai/artifact/FJXfhFVznZtL6cKqiM3MSF), 10.11.2026.
> Ten plik jest źródłem prawdy dla kodu; zmiany planu wpisujemy tu i w dokumencie.

Lokalna aplikacja desktopowa na Windows, która uczy grać według strategii podstawowej i liczyć karty Hi-Lo: korekta każdej decyzji, podpowiedź stawki, statystyki postępów i symulacja budżetu. Python + pywebview, styl Midnight glass, offline, 0 zł.

## Cel i kryteria sukcesu
Cel: grać według strategii podstawowej bez wahania i umieć liczyć karty Hi-Lo przed grą w kasynie stacjonarnym.

**Problem:** gra na wyczucie zamiast optymalnych decyzji, brak narzędzia do ćwiczenia i mierzenia postępów.

**Kryteria sukcesu (3 miesiące):**
- ≥ 95% trafnych decyzji strategii w 3 kolejnych sesjach po min. 100 rozdań
- ≥ 90% trafnych odpowiedzi o running count i true count
- z symulacji wiem, ile realnie kosztuje mnie gra przy mojej trafności

**Persona:** Kornel, gracz rekreacyjny. Gra w kasynie stacjonarnym, uczy się na własnych błędach, lubi widzieć postęp w liczbach.

**Główne zadania:**
1. Rozegrać sesję i od razu wiedzieć, która decyzja była zła i dlaczego.
2. Sprawdzić strategię dla zasad stołu, przy którym będę grał.
3. Ćwiczyć liczenie kart i dobór stawki.
4. Zobaczyć, gdzie najczęściej się mylę i czy się poprawiam.
5. Zobaczyć, ile wygrywam lub tracę przy danym stylu gry.

## Zakres
MVP = 10 funkcji budowanych po kolei (szczegóły i kryteria akceptacji: `FEATURES.md`).

| # | Funkcja | Gotowe, gdy… |
|---|---|---|
| F-00 | Szkielet aplikacji | Okno w stylu Midnight glass z paskiem bocznym, most Python↔JS, baza SQLite, testy działają |
| BJ-01 | Silnik gry | But, rozdania, ruchy i wypłaty (blackjack 3:2) zgodne z zasadami, pokryte testami |
| BJ-02 | Zasady stołu + strategia | Strategia przelicza się po zmianie zasad i zgadza z opublikowanymi tabelami komórka po komórce |
| BJ-03 | Stół z korektą na żywo | Animowane karty, po każdej decyzji ✅/❌ i krótkie „dlaczego”, skróty klawiszowe |
| BJ-04 | Ściąga strategii | Tabela z podświetloną bieżącą sytuacją |
| BJ-05 | Liczenie Hi-Lo | Apka pyta o running/true count i ocenia odpowiedzi |
| BJ-06 | Podpowiedź stawki | Stawka zależna od true count, ocena postawionej kwoty |
| BJ-07 | Statystyki | % trafności, mapa błędów na tabeli strategii, historia sesji |
| BJ-08 | Symulacja budżetu | Wykres 10 000 rozdań: Twój styl vs gra idealna vs z liczeniem |
| BJ-09 | Paczka .exe | Apka odpala się dwuklikiem bez Pythona |

**v2:** ćwiczenie szybkości liczenia, odchylenia zależne od liczenia (Illustrious 18), tryb egzaminu, dźwięki, ubezpieczenie przy TC ≥ +3.
**Poza zakresem:** gra na prawdziwe pieniądze, tryb online, konta użytkowników.

## Flow, ekrany i styl
Apka startuje od razu na stole; pasek boczny prowadzi do 6 ekranów: Stół, Liczenie, Statystyki, Symulacja, Ściąga, Ustawienia.

**Główna pętla na stole:** 1) Postaw stawkę. 2) Rozdanie z animacją. 3) Decyzja → ✅/❌ + „dlaczego” (decyzja i tak jest wykonana). 4) Krupier dobiera, wynik, zapis do bazy. 5) Następne rozdanie (Spacja).

Skróty: H dobierz, S stój, D podwój, P rozdziel, R poddaj, C ściąga.

**Stany:** pusty („Zagraj pierwsze 20 rozdań, żeby zobaczyć statystyki”), ładowanie symulacji z paskiem postępu i „Przerwij”, błąd po ludzku + log w `%APPDATA%`, historia stronicowana po 20.

**Styl Midnight glass** (tylko ciemny, animacje bez dźwięków):

| Element | Wartość |
|---|---|
| Tło / pasek boczny | `#0B0E1F` / `#090B18` |
| Szkło | `rgba(26,31,61,0.6)` + blur 16px, obramowanie `#2A3060` |
| Akcent | fiolet `#7C5CFF` (hover `#8F74FF`) |
| Sukces / błąd / ostrzeżenie | `#4ADE80` / `#FF6B81` / `#FBBF24` |
| Tekst / drugorzędny | `#E7E9FF` / `#8D92B8` |
| Typografia | Inter (lokalnie), liczby tabular-nums |
| Animacje | rozdanie ~250 ms, flip karty krupiera, błysk zielony/czerwony po decyzji |

## Technologia i architektura
Cała logika w Pythonie i testowana; frontend tylko wyświetla i wysyła akcje przez `window.pywebview.api`. Koszt 0 zł/mies., brak integracji zewnętrznych.

| Warstwa | Wybór |
|---|---|
| Język | Python 3.12+ |
| Okno | pywebview (WebView2 / Edge, wbudowany w Windows 10/11) |
| Frontend | czysty HTML + CSS + JS (moduły ES), bez kroku budowania |
| Wykresy | Chart.js (lokalnie) |
| Dane | SQLite w `%APPDATA%\TrenerBlackjack\data.db` |
| Testy | pytest |
| Paczka | PyInstaller |

**Moduły Pythona:** `engine/` (gra), `strategy/` (zasady + tabele JSON + `best_action()`), `counting/` (Hi-Lo, bet ramp), `simulation/` (Monte Carlo w wątku tła), `storage/` (SQLite), `api.py` (jedyne wejście z UI).

**Model danych:**

| Tabela | Kluczowe pola |
|---|---|
| sessions | started_at, ended_at, rules_json, mode, hands_count, correct_count |
| hands | session_id, player_cards, dealer_cards, bet, result, payout, true_count_at_start |
| decisions | hand_id, player_total, soft, pair, dealer_upcard, action_taken, action_correct, is_correct |
| count_checks | session_id, true_rc, answer_rc, true_tc, answer_tc, is_correct |
| settings | key, value |

**Wymagania:** start < 3 s, feedback po decyzji < 100 ms, symulacja 100 × 10 000 rozdań < 60 s bez zamrażania okna, brak danych osobowych.

## Ryzyka, założenia i decyzje
| Ryzyko | Jak ograniczamy |
|---|---|
| Błędne tabele strategii = nauka błędów | Tabele ze zweryfikowanego źródła (Wizard of Odds), testy komórka po komórce |
| Inne zasady w kasynie niż domyślne | Zasady w ustawieniach, weryfikacja przy BJ-02 |
| Liczenie bez sensu przy tasownicy ciągłej; kasyno może wyprosić | Ekran informacyjny: kiedy liczenie ma sens |
| Wolna symulacja w Pythonie | Wątek tła, pasek postępu, można zmniejszyć liczbę przebiegów |
| Ostrzeżenie SmartScreen przy .exe | Opis w README; w trakcie budowy uruchamianie z kodu |

**Założenia do sprawdzenia:**
- Domyślne zasady: 6 talii, S17, DAS, bez poddania, ENHC, 3:2, penetracja 75% → BJ-02.
- Bet ramp: TC ≤ +1 → 1 j., +2 → 2, +3 → 4, ≥ +4 → 8 → BJ-06.
- Pytanie kontrolne o count co 5–15 kart i przed każdą stawką → BJ-05.
- „Twój styl” w symulacji = trafność z ostatnich 500 decyzji i mapa błędów → BJ-08.

**Otwarte pytania:**
- [ ] BJ-02: w jakim kasynie grasz i jakie są tam zasady?
- [ ] BJ-03: wyjaśnienie „dlaczego” jednym zdaniem czy rozwijane?
- [ ] BJ-07: od ilu rozdań pokazywać mapę błędów (propozycja: 50)?

## Decision log
| Data | Decyzja | Dlaczego |
|---|---|---|
| 10.11.2026 | Python + pywebview + czysty HTML/CSS/JS | Czytelna logika w Pythonie, nowoczesny wygląd z HTML, bez kroku budowania |
| 10.11.2026 | Styl Midnight glass, animacje bez dźwięków | Wybór użytkownika |
| 10.11.2026 | Zasady konfigurowalne, domyślnie europejskie | Zasady różnią się między kasynami |
| 10.11.2026 | Tabele strategii jako dane ze źródła | Pewność poprawności, prostszy kod |
| 10.11.2026 | Osobny projekt i repo `trener-blackjack` | Jeden PRD na aplikację |
| 10.11.2026 | Nawigacja: pasek boczny z ikonami | Wybór użytkownika |
| 10.11.2026 | **Zmiana:** budowa w Claude Code w chmurze (Linux), nie na PC; okno pywebview i .exe weryfikowane na PC po `git pull` | Wybór użytkownika; logika i testy niezależne od systemu, UI podglądane w przeglądarce |
| 10.11.2026 | Ścieżka danych: `%APPDATA%\TrenerBlackjack` na Windows, `~/.local/share/TrenerBlackjack` gdzie indziej, nadpisywalna `TRENER_BJ_DATA_DIR` | Testy i budowa w chmurze; decyzja Claude'a (techniczna) |
