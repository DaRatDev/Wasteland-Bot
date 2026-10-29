"""Saves the meter and an activity log in a SQLite file in the data folder."""

import sqlite3
import time
from pathlib import Path

from .meter import MeterState

SCHEMA = """
CREATE TABLE IF NOT EXISTS meter (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    percent REAL NOT NULL,
    updated_at REAL NOT NULL,
    last_milestone INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS activity (
    ts REAL NOT NULL,
    kind TEXT NOT NULL,
    points REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS activity_ts ON activity (ts);
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


class Store:
    def __init__(self, data_dir: Path):
        self.db = sqlite3.connect(data_dir / "wasteland.db")
        self.db.executescript(SCHEMA)

    def load(self) -> tuple[MeterState, int] | None:
        row = self.db.execute("SELECT percent, updated_at, last_milestone FROM meter WHERE id = 1").fetchone()
        if row is None:
            return None
        return MeterState(row[0], row[1]), row[2]

    def save(self, state: MeterState, last_milestone: int) -> None:
        self.db.execute(
            "INSERT INTO meter (id, percent, updated_at, last_milestone) VALUES (1, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET percent = excluded.percent, "
            "updated_at = excluded.updated_at, last_milestone = excluded.last_milestone",
            (state.percent, state.updated_at, last_milestone),
        )
        self.db.commit()

    def log_activity(self, kind: str, points: float, ts: float | None = None) -> None:
        self.db.execute(
            "INSERT INTO activity (ts, kind, points) VALUES (?, ?, ?)",
            (ts if ts is not None else time.time(), kind, points),
        )
        self.db.commit()

    def activity_since(self, ts: float) -> dict[str, float]:
        rows = self.db.execute(
            "SELECT kind, SUM(points) FROM activity WHERE ts >= ? GROUP BY kind", (ts,)
        ).fetchall()
        return dict(rows)

    def get_meta(self, key: str) -> str | None:
        row = self.db.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row[0] if row else None

    def set_meta(self, key: str, value: str) -> None:
        self.db.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        self.db.commit()
