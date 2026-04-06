"""Tests for fsbb.db."""

import sqlite3
from pathlib import Path
from fsbb.db import init_db, schema_version, apply_migrations


def test_init_creates_tables():
    """init_db should create all required tables."""
    test_path = Path("/tmp/test_fsbb.db")
    if test_path.exists():
        test_path.unlink()
    conn = init_db(test_path)
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()]
    conn.close()
    test_path.unlink()

    assert "teams" in tables
    assert "games" in tables
    assert "predictions" in tables
    assert "team_aliases" in tables
    assert "schema_version" in tables


def test_foreign_keys_enforced():
    """Foreign keys should be enabled."""
    test_path = Path("/tmp/test_fsbb_fk.db")
    if test_path.exists():
        test_path.unlink()
    conn = init_db(test_path)
    fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    conn.close()
    test_path.unlink()
    assert fk == 1


def test_schema_version_tracks():
    """schema_version should return the latest migration number."""
    test_path = Path("/tmp/test_fsbb_sv.db")
    if test_path.exists():
        test_path.unlink()
    conn = init_db(test_path)
    v = schema_version(conn)
    conn.close()
    test_path.unlink()
    assert v >= 1


def test_apply_migrations_idempotent():
    """Running apply_migrations twice should not error."""
    test_path = Path("/tmp/test_fsbb_mig.db")
    if test_path.exists():
        test_path.unlink()
    conn = init_db(test_path)
    count1 = apply_migrations(conn)
    count2 = apply_migrations(conn)
    conn.close()
    test_path.unlink()
    assert count2 == 0  # No new migrations to apply on second run
