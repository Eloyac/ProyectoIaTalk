import sqlite3
import pytest
import gc
import src.storage.db as db_module
from src.storage.models import CallRecord


@pytest.fixture(autouse=True)
def clean_db(tmp_path, monkeypatch):
    db_path = tmp_path / "calls.db"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    db_module.init_db()
    yield
    # Ensure all connections are closed before cleanup
    gc.collect()
    db_path.unlink(missing_ok=True)


def test_init_creates_call_records_table():
    with sqlite3.connect(db_module.DB_PATH) as conn:
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
    assert "call_records" in tables


def test_save_call_persists_all_fields():
    record = CallRecord(
        call_sid="CA123abc",
        caller_name="Ana López",
        community="Comunidad Las Rosas 4",
        phone="612345678",
        block="A",
        resolution="email_sent",
        anger_level="low",
    )
    db_module.save_call(record)

    with sqlite3.connect(db_module.DB_PATH) as conn:
        row = conn.execute(
            "SELECT caller_name, community, block FROM call_records WHERE call_sid=?",
            ("CA123abc",),
        ).fetchone()
    assert row == ("Ana López", "Comunidad Las Rosas 4", "A")


def test_save_call_with_defaults():
    db_module.save_call(CallRecord(call_sid="CA_minimal"))
    with sqlite3.connect(db_module.DB_PATH) as conn:
        count = conn.execute("SELECT COUNT(*) FROM call_records").fetchone()[0]
    assert count == 1
