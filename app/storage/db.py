"""SQLite: schemat z PLAN.md i proste ustawienia klucz–wartość."""
import json
import sqlite3
from datetime import datetime
import threading
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    rules_json TEXT NOT NULL,
    mode TEXT NOT NULL,
    hands_count INTEGER NOT NULL DEFAULT 0,
    correct_count INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS hands (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    player_cards TEXT NOT NULL,
    dealer_cards TEXT NOT NULL,
    bet REAL NOT NULL,
    result TEXT,
    payout REAL,
    true_count_at_start REAL
);
CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY,
    hand_id INTEGER NOT NULL REFERENCES hands(id),
    player_total INTEGER NOT NULL,
    soft INTEGER NOT NULL,
    pair INTEGER NOT NULL,
    dealer_upcard INTEGER NOT NULL,
    action_taken TEXT NOT NULL,
    action_correct TEXT NOT NULL,
    is_correct INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS count_checks (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    true_rc INTEGER NOT NULL,
    answer_rc INTEGER,
    true_tc REAL NOT NULL,
    answer_tc REAL,
    is_correct INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
CREATE INDEX IF NOT EXISTS idx_hands_session ON hands(session_id);
CREATE INDEX IF NOT EXISTS idx_decisions_hand ON decisions(hand_id);
"""


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)
        # pywebview woła API z innych wątków -> jedno połączenie + blokada
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._lock = threading.Lock()
        with self._lock, self._conn:
            self._conn.executescript(SCHEMA)

    def table_names(self) -> set[str]:
        rows = self._conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        return {r[0] for r in rows}

    def columns(self, table: str) -> set[str]:
        if table not in self.table_names():
            raise ValueError(f"Nieznana tabela: {table}")
        return {r[1] for r in self._conn.execute(f"PRAGMA table_info({table})")}

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        row = self._conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row[0] if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO settings(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )

    # ----- sesje, rozdania, decyzje -----
    def _exec(self, sql, params=()) -> int:
        with self._lock, self._conn:
            return self._conn.execute(sql, params).lastrowid

    def start_session(self, rules: dict, mode: str) -> int:
        return self._exec("INSERT INTO sessions(started_at, rules_json, mode) VALUES(?, ?, ?)",
                          (datetime.now().isoformat(timespec="seconds"), json.dumps(rules), mode))

    def end_session(self, session_id: int) -> None:
        self._exec("UPDATE sessions SET ended_at = ? WHERE id = ?",
                   (datetime.now().isoformat(timespec="seconds"), session_id))

    def add_hand(self, session_id: int, bet: float, true_count: float | None = None) -> int:
        return self._exec("INSERT INTO hands(session_id, player_cards, dealer_cards, bet, true_count_at_start) "
                          "VALUES(?, '[]', '[]', ?, ?)", (session_id, bet, true_count))

    def finish_hand(self, hand_id: int, session_id: int, player_cards, dealer_cards, result: str, payout: float) -> None:
        self._exec("UPDATE hands SET player_cards = ?, dealer_cards = ?, result = ?, payout = ? WHERE id = ?",
                   (json.dumps(player_cards), json.dumps(dealer_cards), result, payout, hand_id))
        self._exec("UPDATE sessions SET hands_count = hands_count + 1, ended_at = ? WHERE id = ?",
                   (datetime.now().isoformat(timespec="seconds"), session_id))

    def add_decision(self, session_id: int, hand_id: int, total: int, soft: bool, pair: bool, upcard: int,
                     taken: str, correct_action: str, is_correct: bool) -> None:
        self._exec("INSERT INTO decisions(hand_id, player_total, soft, pair, dealer_upcard, action_taken, "
                   "action_correct, is_correct) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                   (hand_id, total, int(soft), int(pair), upcard, taken, correct_action, int(is_correct)))
        if is_correct:
            self._exec("UPDATE sessions SET correct_count = correct_count + 1 WHERE id = ?", (session_id,))

    def add_count_check(self, session_id: int, true_rc: int, answer_rc: int, true_tc: float,
                        answer_tc: float, is_correct: bool) -> None:
        self._exec("INSERT INTO count_checks(session_id, true_rc, answer_rc, true_tc, answer_tc, is_correct) "
                   "VALUES(?, ?, ?, ?, ?, ?)", (session_id, true_rc, answer_rc, true_tc, answer_tc, int(is_correct)))

    def close(self) -> None:
        self._conn.close()
