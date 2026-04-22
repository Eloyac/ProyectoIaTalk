import sqlite3
from pathlib import Path
from .models import CallRecord

DB_PATH = Path("data/calls.db")


def init_db() -> None:
    DB_PATH.parent.mkdir(exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS call_records (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                call_sid     TEXT    NOT NULL,
                caller_name  TEXT    DEFAULT '',
                community    TEXT    DEFAULT '',
                phone        TEXT    DEFAULT '',
                block        TEXT    DEFAULT '',
                resolution   TEXT    DEFAULT '',
                anger_level  TEXT    DEFAULT 'low',
                created_at   TEXT    NOT NULL
            )
        """)


def save_call(record: CallRecord) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """INSERT INTO call_records
               (call_sid, caller_name, community, phone, block, resolution, anger_level, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record.call_sid, record.caller_name, record.community,
                record.phone, record.block, record.resolution,
                record.anger_level, record.created_at.isoformat(),
            ),
        )
