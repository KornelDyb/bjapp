# Changelog

## 2026-11-10
- Start projektu z PRD (Claude Docs). Utworzono PLAN.md, FEATURES.md, PROGRESS.md.
- Zmiana planu: budowa w chmurze (Linux) zamiast na PC — zdecydował Kornel. Wpływ: okno pywebview i BJ-09 (.exe) weryfikowane na PC.
- F-00 Szkielet aplikacji → 👀: SQLite (sessions, hands, decisions, count_checks, settings), Api (ping, get/set_setting, błędy po ludzku + app.log), UI Midnight glass z 6 ekranami, Inter lokalnie (OFL), serwer podglądu i testy e2e. Testy: 16 passed.
- Repo projektu: KornelDyb/bjapp (zamiast trener-blackjack) — zdecydował Kornel.
- BJ-01 Silnik gry ✅: but (N talii, penetracja, seed), wartości rąk, rozdanie ENHC/peek, ruchy H/S/D/P/R z walidacją, gra krupiera S17/H17, wypłaty (3:2 konfig., OBO w ENHC), stan rundy dla UI. Dodano `engine/exact.py` (dokładne P(bust) krupiera). Testy: 74 passed.
- Poprawka testu (BJ-01): referencyjne wartości bustu krupiera wpisane z pamięci były błędne dla kart 4–6 (o 0,7–1 pp). Zastąpione dokładnym wyliczeniem rekurencyjnym; tolerancja 4,5 SE (ostrzejsza niż pierwotne 1,5 pp). Silnik nie wymagał zmian.
- Zmiana (Kornel): przy BJ krupiera w ENHC tracisz wszystko — domyślnie enhc_obo=False. BJ-01 ♻️→✅ (zmiana domyślnej, testy zaktualizowane pod nowe wymaganie).
- BJ-02 Zasady stołu + strategia → 👀: dokładny solver 6 talii (`strategy/finite.py`), 6 tabel EV (peek/ENHC/ENHC+OBO × S17/H17; DAS i poddanie bez osobnych tabel), `best_action()`, API get/set_rules + get_strategy, ekran Ustawienia (autozapis). Tabela US zgodna komórka po komórce; EU różni się w 4 komórkach (11 vs 10, 8,8 vs 10/A, A,A vs A → dobierz). Testy: 99 passed.
- Odkrycie przy BJ-02: model nieskończonej talii dawał „dobierz” dla A,2 vs 5 (6 talii: „podwój”, różnica 0,003 stawki) → przejście na dokładny solver z tabelami liczonymi raz (6,5 min).
- Decyzje 10.11: BJ-02 ✅; „dlaczego” = zdanie + rozwijane EV; poddanie bez zmian (Tak/Nie).
- BJ-03 Stół z korektą na żywo → 👀: żetony stawki, animowane rozdanie/flip, ✅/❌ + błysk + zdanie „dlaczego” + rozwijane EV (3 miejsca przy bliskich wartościach) i koszt błędu, skróty H/S/D/P/R/Spacja, baner wyniku, statystyki sesji, zapis sesji/rozdań/decyzji do SQLite. Frontend podzielony na api.js / table.js / app.js. Testy: 121 passed.
- Zmiana (Kornel 10.11): BJ-03 ✅ (mechanika ENHC potwierdzona). Liczenie Hi-Lo ma być przy stole: BJ-05 rozszerzony i przesunięty przed BJ-04; licznik ukryty + pytania przed stawką co N rozdań.
- BJ-05 Liczenie Hi-Lo → 👀: running/true count z buta, pytanie przed stawką co N rozdań (domyślnie 3), ocena (RC dokładnie, TC ±0,5), zapis count_checks i TC na starcie rozdania, przełącznik licznika, info o tasowaniu, ekran Liczenie, ustawienia liczenia. Pasek akcji zawsze widoczny (prośba Kornela). Poprawka: stan rozdania odtwarzany po przeładowaniu strony. Testy: 144 passed.
