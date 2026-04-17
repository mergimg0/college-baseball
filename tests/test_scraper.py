"""Tests for fsbb.scraper.ncaa scheduled game import."""

import sqlite3
from pathlib import Path
from fsbb.db import init_db


def _setup_test_db():
    """Create a test DB with two teams."""
    test_path = Path("/tmp/test_fsbb_scraper.db")
    if test_path.exists():
        test_path.unlink()
    conn = init_db(test_path)
    conn.execute("INSERT INTO teams (name, conference) VALUES ('Texas', 'Big 12')")
    conn.execute("INSERT INTO teams (name, conference) VALUES ('UCLA', 'Big Ten')")
    conn.commit()
    return conn, test_path


def test_scrape_date_skips_scheduled_by_default():
    """scrape_date with include_scheduled=False should skip non-final games."""
    conn, path = _setup_test_db()
    from unittest.mock import patch
    fake_games = [{"game": {
        "gameState": "pre",
        "home": {"names": {"short": "Texas"}, "score": ""},
        "away": {"names": {"short": "UCLA"}, "score": ""},
    }}]
    with patch("fsbb.scraper.ncaa._fetch_scoreboard", return_value=fake_games):
        from fsbb.scraper.ncaa import scrape_date
        from datetime import date
        result = scrape_date(conn, date(2026, 4, 20), include_scheduled=False)
    assert result["imported"] == 0
    assert result["skipped"] == 1
    count = conn.execute("SELECT COUNT(*) FROM games").fetchone()[0]
    assert count == 0
    conn.close()
    path.unlink()


def test_scrape_date_imports_scheduled_when_enabled():
    """scrape_date with include_scheduled=True should import pre-game entries."""
    conn, path = _setup_test_db()
    from unittest.mock import patch
    fake_games = [{"game": {
        "gameState": "pre",
        "home": {"names": {"short": "Texas"}, "score": ""},
        "away": {"names": {"short": "UCLA"}, "score": ""},
    }}]
    with patch("fsbb.scraper.ncaa._fetch_scoreboard", return_value=fake_games):
        from fsbb.scraper.ncaa import scrape_date
        from datetime import date
        result = scrape_date(conn, date(2026, 4, 20), include_scheduled=True)
    assert result["imported"] == 1
    game = conn.execute("SELECT status, home_runs, away_runs, actual_winner_id FROM games").fetchone()
    assert game[0] == "scheduled"
    assert game[1] is None
    assert game[2] is None
    assert game[3] is None
    conn.close()
    path.unlink()


def test_scrape_date_scheduled_to_final_upsert():
    """A scheduled game should update to final when scores arrive."""
    conn, path = _setup_test_db()
    from unittest.mock import patch
    from fsbb.scraper.ncaa import scrape_date
    from datetime import date

    # First: import as scheduled
    pre_games = [{"game": {
        "gameState": "pre",
        "home": {"names": {"short": "Texas"}, "score": ""},
        "away": {"names": {"short": "UCLA"}, "score": ""},
    }}]
    with patch("fsbb.scraper.ncaa._fetch_scoreboard", return_value=pre_games):
        scrape_date(conn, date(2026, 4, 20), include_scheduled=True)

    # Second: import as final with scores
    final_games = [{"game": {
        "gameState": "final",
        "home": {"names": {"short": "Texas"}, "score": "5"},
        "away": {"names": {"short": "UCLA"}, "score": "3"},
    }}]
    with patch("fsbb.scraper.ncaa._fetch_scoreboard", return_value=final_games):
        scrape_date(conn, date(2026, 4, 20), include_scheduled=False)

    # Should be exactly 1 game (upserted, not duplicated)
    count = conn.execute("SELECT COUNT(*) FROM games").fetchone()[0]
    assert count == 1
    game = conn.execute("SELECT status, home_runs, away_runs FROM games").fetchone()
    assert game[0] == "final"
    assert game[1] == 5
    assert game[2] == 3
    conn.close()
    path.unlink()


def test_scrape_date_re_import_scheduled_stays_scheduled():
    """Re-importing a scheduled game that's still scheduled should NOT flip to final."""
    conn, path = _setup_test_db()
    from unittest.mock import patch
    from fsbb.scraper.ncaa import scrape_date
    from datetime import date

    pre_games = [{"game": {
        "gameState": "pre",
        "home": {"names": {"short": "Texas"}, "score": ""},
        "away": {"names": {"short": "UCLA"}, "score": ""},
    }}]
    with patch("fsbb.scraper.ncaa._fetch_scoreboard", return_value=pre_games):
        scrape_date(conn, date(2026, 4, 20), include_scheduled=True)
        scrape_date(conn, date(2026, 4, 20), include_scheduled=True)

    game = conn.execute("SELECT status FROM games").fetchone()
    assert game[0] == "scheduled"
    conn.close()
    path.unlink()
