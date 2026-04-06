"""NCAA Scoreboard scraper via henrygd/ncaa-api.

Pulls game scores for every D1 baseball game in the 2026 season.
API: https://ncaa-api.henrygd.me/scoreboard/baseball/d1/{yyyy}/{mm}/{dd}

Rate limit: 5 req/s. Full season (~50 days): ~10 seconds at 1 req/s.
"""

from __future__ import annotations

import json
import sqlite3
import ssl
import time
import urllib.request
from datetime import date, timedelta

BASE_URL = "https://ncaa-api.henrygd.me"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}

# SSL context — use certifi for proper verification
try:
    import certifi
    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CTX = ssl.create_default_context()


def _fetch_scoreboard(d: date) -> list[dict]:
    """Fetch all D1 baseball scores for a given date."""
    url = f"{BASE_URL}/scoreboard/baseball/d1/{d.year}/{d.month:02d}/{d.day:02d}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        resp = urllib.request.urlopen(req, timeout=20, context=_SSL_CTX)
        data = json.loads(resp.read().decode())
        return data.get("games", [])
    except Exception as e:
        print(f"  ERROR {d}: {e}")
        return []


def _resolve_team(conn: sqlite3.Connection, name: str) -> int | None:
    """Resolve a team name to its database ID, trying exact match then alias."""
    row = conn.execute("SELECT id FROM teams WHERE name=?", (name,)).fetchone()
    if row:
        return row[0]

    # Try alias
    alias = conn.execute(
        "SELECT team_id FROM team_aliases WHERE alias=?", (name,)
    ).fetchone()
    if alias:
        return alias[0]

    # Try fuzzy: strip common suffixes/prefixes
    # NCAA API uses names like "North Carolina" while PEAR uses "North Carolina"
    # But sometimes NCAA says "UNC" or "N. Carolina"
    for variant in [
        name.replace("State", "St."),
        name.replace("St.", "State"),
        name.replace("Southern", "So."),
        name.replace("Northern", "No."),
        name.replace("University", ""),
        name.strip(),
    ]:
        row = conn.execute("SELECT id FROM teams WHERE name=?", (variant.strip(),)).fetchone()
        if row:
            # Cache the alias for future lookups
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO team_aliases (alias, team_id) VALUES (?, ?)",
                    (name, row[0])
                )
                conn.commit()
            except sqlite3.OperationalError:
                pass  # Table locked or similar — non-critical, alias is a cache
            return row[0]

    return None


def scrape_date(conn: sqlite3.Connection, d: date) -> dict:
    """Scrape and import all D1 games for a single date.

    Returns: {"date": str, "found": int, "imported": int, "skipped": int}
    """
    raw_games = _fetch_scoreboard(d)
    date_str = d.isoformat()
    imported = 0
    skipped = 0

    for entry in raw_games:
        g = entry.get("game", {})
        state = g.get("gameState", "")

        # Only import completed games
        if state not in ("final", "FIN"):
            skipped += 1
            continue

        home_info = g.get("home", {})
        away_info = g.get("away", {})

        home_name = home_info.get("names", {}).get("short") or home_info.get("names", {}).get("full", "")
        away_name = away_info.get("names", {}).get("short") or away_info.get("names", {}).get("full", "")

        if not home_name or not away_name:
            skipped += 1
            continue

        home_score = home_info.get("score")
        away_score = away_info.get("score")

        if home_score is None or away_score is None:
            skipped += 1
            continue

        try:
            home_runs = int(home_score)
            away_runs = int(away_score)
        except (ValueError, TypeError):
            skipped += 1
            continue

        # Resolve team IDs
        home_id = _resolve_team(conn, home_name)
        away_id = _resolve_team(conn, away_name)

        if not home_id or not away_id:
            skipped += 1
            continue

        # Determine winner
        if home_runs > away_runs:
            winner_id = home_id
        elif away_runs > home_runs:
            winner_id = away_id
        else:
            winner_id = None  # tie (rare in baseball but possible in suspended)

        date_str = d.isoformat()

        try:
            conn.execute("""
                INSERT INTO games (date, home_team_id, away_team_id, home_runs, away_runs,
                                   status, actual_winner_id, source)
                VALUES (?, ?, ?, ?, ?, 'final', ?, 'ncaa')
                ON CONFLICT(date, home_team_id, away_team_id) DO UPDATE SET
                    home_runs=excluded.home_runs,
                    away_runs=excluded.away_runs,
                    status='final',
                    actual_winner_id=excluded.actual_winner_id,
                    source='ncaa'
            """, (date_str, home_id, away_id, home_runs, away_runs, winner_id))
            imported += 1
        except sqlite3.IntegrityError:
            skipped += 1

    conn.commit()
    return {"date": date_str, "found": len(raw_games), "imported": imported, "skipped": skipped}


def scrape_season(
    conn: sqlite3.Connection,
    start: date | None = None,
    end: date | None = None,
    rate_limit: float = 0.5,
    progress: bool = True,
) -> dict:
    """Scrape full D1 baseball season scores.

    Args:
        conn: Database connection
        start: Season start date (default: Feb 14 of current year)
        end: Last date to scrape (default: yesterday)
        rate_limit: Seconds between API calls
        progress: Print progress

    Returns:
        Summary with total games found/imported
    """
    if start is None:
        start = date(date.today().year, 2, 14)  # D1 season typically starts mid-Feb
    if end is None:
        end = date.today() - timedelta(days=1)

    total_found = 0
    total_imported = 0
    total_skipped = 0

    current = start
    day_count = 0

    while current <= end:
        result = scrape_date(conn, current)
        total_found += result["found"]
        total_imported += result["imported"]
        total_skipped += result["skipped"]
        day_count += 1

        if progress and day_count % 7 == 0:
            print(f"  {current}: {total_imported} games imported ({total_skipped} skipped)")

        current += timedelta(days=1)
        time.sleep(rate_limit)

    return {
        "days_scraped": day_count,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "games_found": total_found,
        "games_imported": total_imported,
        "games_skipped": total_skipped,
    }


def get_todays_schedule(conn: sqlite3.Connection) -> list[dict]:
    """Get today's scheduled games from NCAA API (for predictions).

    Returns list of dicts with home_team, away_team, game_time.
    """
    today = date.today()
    raw = _fetch_scoreboard(today)
    schedule = []

    for entry in raw:
        g = entry.get("game", {})
        home_info = g.get("home", {})
        away_info = g.get("away", {})

        home_name = home_info.get("names", {}).get("full", "")
        away_name = away_info.get("names", {}).get("full", "")

        if not home_name or not away_name:
            continue

        home_id = _resolve_team(conn, home_name)
        away_id = _resolve_team(conn, away_name)

        state = g.get("gameState", "pre")
        start_time = g.get("startTime", "")

        entry_dict = {
            "home_team": home_name,
            "away_team": away_name,
            "home_id": home_id,
            "away_id": away_id,
            "state": state,
            "start_time": start_time,
            "home_score": home_info.get("score"),
            "away_score": away_info.get("score"),
        }
        schedule.append(entry_dict)

    return schedule
