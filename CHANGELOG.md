# Changelog

## 2026-11-10
- Start projektu z PRD (Claude Docs). Utworzono PLAN.md, FEATURES.md, PROGRESS.md.
- Zmiana planu: budowa w chmurze (Linux) zamiast na PC — zdecydował Kornel. Wpływ: okno pywebview i BJ-09 (.exe) weryfikowane na PC.
- F-00 Szkielet aplikacji → 👀: SQLite (sessions, hands, decisions, count_checks, settings), Api (ping, get/set_setting, błędy po ludzku + app.log), UI Midnight glass z 6 ekranami, Inter lokalnie (OFL), serwer podglądu i testy e2e. Testy: 16 passed.
- Repo projektu: KornelDyb/bjapp (zamiast trener-blackjack) — zdecydował Kornel.
- BJ-01 Silnik gry ✅: but (N talii, penetracja, seed), wartości rąk, rozdanie ENHC/peek, ruchy H/S/D/P/R z walidacją, gra krupiera S17/H17, wypłaty (3:2 konfig., OBO w ENHC), stan rundy dla UI. Dodano `engine/exact.py` (dokładne P(bust) krupiera). Testy: 74 passed.
- Poprawka testu (BJ-01): referencyjne wartości bustu krupiera wpisane z pamięci były błędne dla kart 4–6 (o 0,7–1 pp). Zastąpione dokładnym wyliczeniem rekurencyjnym; tolerancja 4,5 SE (ostrzejsza niż pierwotne 1,5 pp). Silnik nie wymagał zmian.
