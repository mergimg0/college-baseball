"""PEAR Ratings importer — loads existing scraped data and fetches live updates.

PEAR API endpoints (discovered):
    /api/cbase/teams    — list all team names
    /api/cbase/ratings  — all team ratings
    /api/cbase/team/{n} — individual team detail (stats + schedule + games)
"""

from __future__ import annotations

import json
import sqlite3
import ssl
import time
import urllib.parse
import urllib.request
from pathlib import Path

try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CTX = ssl.create_default_context()

BASE_URL = "https://pearatings.com/api/cbase"
HEADERS = {"User-Agent": "ForgeStream/1.0 (college baseball research)"}
RATE_LIMIT = 0.5


def _fetch_json(endpoint: str) -> dict | list | None:
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        resp = urllib.request.urlopen(req, context=SSL_CTX, timeout=30)
        return json.loads(resp.read().decode())
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}")
        return None


def fetch_ratings() -> list[dict]:
    """Fetch current ratings for all teams."""
    data = _fetch_json("/ratings")
    if isinstance(data, dict) and "teams" in data:
        teams = data["teams"]
        return teams if isinstance(teams, list) else []
    return []


def fetch_team_detail(team_name: str) -> dict | None:
    """Fetch detailed stats + schedule for one team."""
    encoded = urllib.parse.quote(team_name)
    result = _fetch_json(f"/team/{encoded}")
    return result if isinstance(result, dict) else None


def import_from_file(conn: sqlite3.Connection, ratings_path: Path) -> int:
    """Import PEAR ratings from existing JSON file into database.

    Returns number of teams imported.
    """
    with open(ratings_path) as f:
        data = json.load(f)

    teams = data.get("teams", data) if isinstance(data, dict) else data
    count = 0

    for t in teams:
        conn.execute("""
            INSERT INTO teams (name, conference, pear_power_rating, pear_net,
                               pear_net_score, pear_elo, pear_sos, pear_sor,
                               pear_rpi, pear_prr, pear_rqi)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                pear_power_rating=excluded.pear_power_rating,
                pear_net=excluded.pear_net,
                pear_net_score=excluded.pear_net_score,
                pear_elo=excluded.pear_elo,
                pear_sos=excluded.pear_sos,
                pear_sor=excluded.pear_sor,
                pear_rpi=excluded.pear_rpi,
                pear_prr=excluded.pear_prr,
                pear_rqi=excluded.pear_rqi
        """, (
            t["Team"],
            t.get("Conference", "Unknown"),
            t.get("power_rating"),
            t.get("NET"),
            t.get("net_score"),
            t.get("ELO"),
            t.get("SOS"),
            t.get("SOR"),
            t.get("RPI"),
            t.get("PRR"),
            t.get("RQI"),
        ))
        count += 1

    conn.commit()
    return count


def import_team_detail(conn: sqlite3.Connection, team_name: str, detail: dict) -> None:
    """Import a team's detailed stats (RS, RA, games, record) from PEAR team detail."""
    t = detail.get("team", {})
    if not t:
        return

    rs = int(t.get("RS") or 0)
    ra = int(t.get("RA") or 0)
    games = int(t.get("G") or 0)
    record = t.get("Record") or "0-0"

    parts = str(record).split("-")
    wins = int(parts[0]) if len(parts) >= 2 else 0
    losses = int(parts[1]) if len(parts) >= 2 else 0

    conn.execute("""
        UPDATE teams SET total_rs=?, total_ra=?, games_played=?, wins=?, losses=?
        WHERE name=?
    """, (rs, ra, games, wins, losses, team_name))
    conn.commit()


def import_team_games(conn: sqlite3.Connection, team_name: str, detail: dict) -> int:
    """Import a team's game results from PEAR team detail into games table.

    Returns number of games imported.
    """
    recent = detail.get("recent_games", [])
    if not recent:
        return 0

    team_row = conn.execute("SELECT id FROM teams WHERE name=?", (team_name,)).fetchone()
    if not team_row:
        return 0
    team_id = team_row["id"]

    count = 0
    seen_games: set[tuple[str, str, str]] = set()  # (date, home, away) dedup

    for g in recent:
        # Only process games from THIS team's perspective (skip opponent dupes)
        game_team = g.get("Team", "").strip()
        if game_team != team_name:
            continue

        opponent = g.get("Opponent", "").strip()
        if not opponent:
            continue

        # Use explicit Location and home_team fields from PEAR
        location = g.get("Location", "").strip()
        pear_home = g.get("home_team", "").strip()

        # Determine home/away
        if location == "Home" or pear_home == team_name:
            is_home = True
        elif location == "Away":
            is_home = False
        elif opponent.startswith("@"):
            opponent = opponent[1:].strip()
            is_home = False
        else:
            is_home = True

        # Look up opponent ID
        opp_row = conn.execute("SELECT id FROM teams WHERE name=?", (opponent,)).fetchone()
        if not opp_row:
            alias_row = conn.execute(
                "SELECT team_id FROM team_aliases WHERE alias=?", (opponent,)
            ).fetchone()
            if alias_row:
                opp_id = alias_row["team_id"]
            else:
                continue
        else:
            opp_id = opp_row["id"]

        home_id = team_id if is_home else opp_id
        away_id = opp_id if is_home else team_id

        game_date = g.get("Date", "")

        # Dedup: skip if we've already imported this game
        dedup_key = (game_date, str(home_id), str(away_id))
        if dedup_key in seen_games:
            continue
        seen_games.add(dedup_key)

        result = g.get("Result", "")

        # Skip scheduled games
        if result in ("SCH", "", None):
            continue

        # Parse result like "W9 - 8" or "L2 - 7" (PEAR format: no space after W/L)
        home_runs = None
        away_runs = None
        actual_winner = None
        status = "final"

        if result and len(result) >= 2:
            outcome = result[0]  # W or L
            try:
                score_str = result[1:].strip()
                scores = score_str.split("-")
                team_score = int(scores[0].strip())
                opp_score = int(scores[1].strip()) if len(scores) > 1 else 0

                if is_home:
                    home_runs = team_score
                    away_runs = opp_score
                else:
                    home_runs = opp_score
                    away_runs = team_score

                if outcome == "W":
                    actual_winner = team_id
                elif outcome == "L":
                    actual_winner = opp_id
            except (ValueError, IndexError):
                status = "unknown"

        try:
            conn.execute("""
                INSERT INTO games (date, home_team_id, away_team_id, home_runs, away_runs,
                                   status, actual_winner_id, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'pear')
                ON CONFLICT(date, home_team_id, away_team_id) DO UPDATE SET
                    home_runs=COALESCE(excluded.home_runs, games.home_runs),
                    away_runs=COALESCE(excluded.away_runs, games.away_runs),
                    status=excluded.status,
                    actual_winner_id=COALESCE(excluded.actual_winner_id, games.actual_winner_id)
            """, (game_date, home_id, away_id, home_runs, away_runs, status, actual_winner))
            count += 1
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    return count


def scrape_all_team_details(conn: sqlite3.Connection, progress: bool = True) -> dict:
    """Scrape detailed stats for all teams from PEAR API.

    Returns summary stats.
    """
    teams = conn.execute("SELECT name FROM teams ORDER BY pear_net").fetchall()
    total = len(teams)
    games_imported = 0

    for i, row in enumerate(teams):
        name = row["name"]
        detail = fetch_team_detail(name)
        if detail:
            import_team_detail(conn, name, detail)
            n = import_team_games(conn, name, detail)
            games_imported += n

        if progress and (i + 1) % 25 == 0:
            print(f"  {i+1}/{total} teams scraped ({games_imported} games)")

        time.sleep(RATE_LIMIT)

    return {"teams": total, "games": games_imported}
