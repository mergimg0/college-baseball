"""NCAA box score scraper — extracts pitcher data from completed games.

Endpoint: https://ncaa-api.henrygd.me/game/{gameID}/boxscore
Rate limit: 5 req/s. Use 0.3s delay between requests.
Each game gives: starting pitcher identity, IP, ERA, K, BB for all pitchers.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import ssl
import time
import urllib.request
from datetime import date, timedelta

logger = logging.getLogger(__name__)

try:
    import certifi
    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CTX = ssl.create_default_context()

BASE_URL = "https://ncaa-api.henrygd.me"
HEADERS = {"User-Agent": "ForgeStream/1.0 (college baseball research)"}


def fetch_boxscore(game_id: str | int) -> dict | None:
    """Fetch box score for a single NCAA game."""
    url = f"{BASE_URL}/game/{game_id}/boxscore"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        resp = urllib.request.urlopen(req, timeout=20, context=_SSL_CTX)
        return json.loads(resp.read().decode())
    except Exception:
        return None


def extract_pitchers(boxscore: dict, conn: sqlite3.Connection, game_db_id: int) -> int:
    """Extract pitcher data from a box score and store in database.

    Returns number of pitchers imported.
    """
    count = 0
    teams_data = boxscore.get("teams", [])

    for team_bs in boxscore.get("teamBoxscore", []):
        ncaa_team_id = team_bs.get("teamId")

        # Find team name from the teams array
        team_name = None
        for t in teams_data:
            if str(t.get("teamId")) == str(ncaa_team_id):
                team_name = t.get("nameShort", "")
                break

        if not team_name:
            continue

        # Resolve to our team ID
        our_team_id = _resolve_team_id(conn, team_name)
        if not our_team_id:
            continue

        for player in team_bs.get("playerStats", []):
            ps = player.get("pitcherStats")
            if not ps:
                continue

            name = f"{player.get('firstName', '')} {player.get('lastName', '')}".strip()
            if not name:
                continue

            number = player.get("number")
            is_starter = 1 if player.get("starter", False) else 0

            # Upsert pitcher
            conn.execute("""
                INSERT INTO pitchers (name, team_id, number)
                VALUES (?, ?, ?)
                ON CONFLICT(name, team_id) DO UPDATE SET
                    number=COALESCE(excluded.number, pitchers.number),
                    updated_at=datetime('now')
            """, (name, our_team_id, number))

            pitcher_row = conn.execute(
                "SELECT id FROM pitchers WHERE name=? AND team_id=?",
                (name, our_team_id)
            ).fetchone()
            if not pitcher_row:
                continue
            pitcher_id = pitcher_row[0]

            # Parse IP
            ip_str = ps.get("inningsPitched", "0")
            try:
                ip = float(ip_str)
            except (ValueError, TypeError):
                ip = 0.0

            try:
                conn.execute("""
                    INSERT INTO game_pitchers
                        (game_id, pitcher_id, team_id, is_starter,
                         ip, hits_allowed, runs_allowed, earned_runs,
                         walks, strikeouts, pitches, got_win, got_loss, got_save)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(game_id, pitcher_id) DO UPDATE SET
                        is_starter=excluded.is_starter,
                        ip=excluded.ip,
                        hits_allowed=excluded.hits_allowed,
                        runs_allowed=excluded.runs_allowed,
                        earned_runs=excluded.earned_runs,
                        walks=excluded.walks,
                        strikeouts=excluded.strikeouts
                """, (
                    game_db_id, pitcher_id, our_team_id, is_starter,
                    ip,
                    int(ps.get("hitsAllowed", 0)),
                    int(ps.get("runsAllowed", 0)),
                    int(ps.get("earnedRunsAllowed", 0)),
                    int(ps.get("walksAllowed", 0)),
                    int(ps.get("strikeouts", 0)),
                    int(ps.get("strikes", 0) or 0),
                    int(ps.get("win", 0)),
                    int(ps.get("loss", 0)),
                    int(ps.get("save", 0)),
                ))
                count += 1
            except sqlite3.IntegrityError:
                pass

    conn.commit()
    return count


def scrape_date_boxscores(
    conn: sqlite3.Connection,
    target_date: date,
    rate_limit: float = 0.3,
) -> dict:
    """Scrape box scores for all completed games on a single date.

    Returns {"games": int, "pitchers": int}
    """
    from fsbb.scraper.ncaa import _fetch_scoreboard

    raw_games = _fetch_scoreboard(target_date)
    total_pitchers = 0
    total_games = 0

    for entry in raw_games:
        g = entry.get("game", {})
        if g.get("gameState") not in ("final", "FIN"):
            continue

        game_id = g.get("gameID")
        if not game_id:
            continue

        home_name = g.get("home", {}).get("names", {}).get("short", "")
        away_name = g.get("away", {}).get("names", {}).get("short", "")

        # Find matching game in our DB
        db_game = _find_game_in_db(conn, target_date.isoformat(), home_name, away_name)
        if not db_game:
            continue

        # Check if we already have pitcher data for this game
        existing = conn.execute(
            "SELECT COUNT(*) FROM game_pitchers WHERE game_id=?", (db_game,)
        ).fetchone()[0]
        if existing > 0:
            continue

        # Fetch and extract
        boxscore = fetch_boxscore(game_id)
        if boxscore:
            n = extract_pitchers(boxscore, conn, db_game)
            total_pitchers += n
            if n > 0:
                total_games += 1

        time.sleep(rate_limit)

    return {"games": total_games, "pitchers": total_pitchers}


def scrape_season_boxscores(
    conn: sqlite3.Connection,
    start: date | None = None,
    end: date | None = None,
    rate_limit: float = 0.3,
    progress: bool = True,
    max_days: int = 0,
) -> dict:
    """Scrape box scores for a range of dates.

    Args:
        max_days: If > 0, stop after this many days (for incremental scraping)
    """
    if start is None:
        start = date(date.today().year, 2, 14)
    if end is None:
        end = date.today() - timedelta(days=1)

    total_pitchers = 0
    total_games = 0
    current = start
    days_scraped = 0

    while current <= end:
        result = scrape_date_boxscores(conn, current, rate_limit)
        total_pitchers += result["pitchers"]
        total_games += result["games"]
        days_scraped += 1

        if progress:
            day_g = result["games"]
            if day_g == 0:
                print(f"  {current}: ⚠ 0 games matched (0 pitchers)")
            elif days_scraped % 7 == 0:
                print(f"  {current}: {total_games} games, {total_pitchers} pitcher entries")

        if max_days > 0 and days_scraped >= max_days:
            break

        current += timedelta(days=1)

    # Recompute pitcher season stats
    recompute_pitcher_stats(conn)

    return {
        "days": days_scraped,
        "games": total_games,
        "pitchers": total_pitchers,
    }


def recompute_pitcher_stats(conn: sqlite3.Connection) -> None:
    """Recompute pitcher season totals from game_pitchers data."""
    conn.execute("""
        UPDATE pitchers SET
            season_ip = COALESCE((SELECT SUM(ip) FROM game_pitchers WHERE pitcher_id = pitchers.id), 0),
            season_k = COALESCE((SELECT SUM(strikeouts) FROM game_pitchers WHERE pitcher_id = pitchers.id), 0),
            season_bb = COALESCE((SELECT SUM(walks) FROM game_pitchers WHERE pitcher_id = pitchers.id), 0),
            season_hits_allowed = COALESCE((SELECT SUM(hits_allowed) FROM game_pitchers WHERE pitcher_id = pitchers.id), 0),
            season_er = COALESCE((SELECT SUM(earned_runs) FROM game_pitchers WHERE pitcher_id = pitchers.id), 0),
            season_era = CASE
                WHEN COALESCE((SELECT SUM(ip) FROM game_pitchers WHERE pitcher_id = pitchers.id), 0) > 0
                THEN COALESCE((SELECT SUM(earned_runs) FROM game_pitchers WHERE pitcher_id = pitchers.id), 0) * 9.0
                     / (SELECT SUM(ip) FROM game_pitchers WHERE pitcher_id = pitchers.id)
                ELSE NULL
            END,
            games_started = COALESCE((SELECT SUM(is_starter) FROM game_pitchers WHERE pitcher_id = pitchers.id), 0),
            games_relieved = COALESCE((SELECT COUNT(*) - SUM(is_starter) FROM game_pitchers WHERE pitcher_id = pitchers.id), 0),
            updated_at = datetime('now')
    """)
    conn.commit()


def get_starter_quality(conn: sqlite3.Connection, game_id: int, team_id: int) -> float | None:
    """Get the starting pitcher's quality rating for a game.

    Returns quality_rating (0-100 scale, 50=average) if available,
    falls back to inverted ERA (lower ERA → higher rating).
    Returns None if no starter data or insufficient IP.
    """
    row = conn.execute("""
        SELECT p.quality_rating, p.season_era, p.season_ip
        FROM game_pitchers gp
        JOIN pitchers p ON gp.pitcher_id = p.id
        WHERE gp.game_id = ? AND gp.team_id = ? AND gp.is_starter = 1
    """, (game_id, team_id)).fetchone()
    if not row or not row[2] or row[2] < 10:
        return None
    # Prefer quality_rating if computed, else derive from ERA
    if row[0] is not None:
        return row[0]
    # Fallback: invert ERA to 0-100 scale (ERA 0 → 100, ERA 9+ → 0)
    era = row[1] if row[1] else 4.5
    return max(0, min(100, 100 - era * 11))


def fetch_play_by_play(game_id: str | int) -> dict | None:
    """Fetch play-by-play for a single NCAA game."""
    url = f"{BASE_URL}/game/{game_id}/play-by-play"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        resp = urllib.request.urlopen(req, timeout=20, context=_SSL_CTX)
        return json.loads(resp.read().decode())
    except Exception:
        return None


def import_play_by_play(
    pbp_data: dict,
    conn: sqlite3.Connection,
    game_db_id: int,
    home_team_id: int,
    away_team_id: int,
) -> int:
    """Import play-by-play events for a single game.

    Returns number of events imported.
    """
    from fsbb.parser import parse_play_text

    count = 0
    home_score = 0
    away_score = 0

    # Map NCAA team IDs to our team IDs
    ncaa_to_db: dict[int, int] = {}
    for t in pbp_data.get("teams", []):
        ncaa_id = int(t.get("teamId", 0))
        if t.get("isHome"):
            ncaa_to_db[ncaa_id] = home_team_id
        else:
            ncaa_to_db[ncaa_id] = away_team_id

    for period in pbp_data.get("periods", []):
        inning = period.get("periodNumber", 0)
        seq = 0

        for stat in period.get("playbyplayStats", []):
            ncaa_team_id = stat.get("teamId", 0)
            batting_team_id = ncaa_to_db.get(ncaa_team_id)
            if not batting_team_id:
                continue

            is_top = 1 if batting_team_id == away_team_id else 0

            for play in stat.get("plays", []):
                text = play.get("playText", "")
                if not text:
                    continue

                seq += 1
                parsed = parse_play_text(text)

                # Track score
                if play.get("homeScore") is not None:
                    try:
                        home_score = int(play["homeScore"])
                    except (ValueError, TypeError):
                        pass
                if play.get("visitorScore") is not None:
                    try:
                        away_score = int(play["visitorScore"])
                    except (ValueError, TypeError):
                        pass

                try:
                    conn.execute("""
                        INSERT INTO play_events (
                            game_id, inning, is_top, batting_team_id, sequence_in_inning,
                            raw_text, event_type, batter_name, pitcher_sub_in, pitcher_sub_out,
                            hit_direction, pitch_count, pitch_sequence,
                            runs_scored, rbi, is_error, is_sacrifice,
                            stolen_base, caught_stealing, wild_pitch,
                            home_score_after, away_score_after
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(game_id, inning, is_top, sequence_in_inning) DO NOTHING
                    """, (
                        game_db_id, inning, is_top, batting_team_id, seq,
                        text, parsed["event_type"], parsed["batter_name"],
                        parsed["pitcher_sub_in"], parsed["pitcher_sub_out"],
                        parsed["hit_direction"], parsed["pitch_count"], parsed["pitch_sequence"],
                        parsed["runs_scored"], parsed["rbi"], parsed["is_error"],
                        parsed["is_sacrifice"], parsed["stolen_base"],
                        parsed["caught_stealing"], parsed["wild_pitch"],
                        home_score, away_score,
                    ))
                    count += 1
                except sqlite3.IntegrityError:
                    pass

    conn.commit()
    return count


def scrape_date_pbp(
    conn: sqlite3.Connection,
    target_date: date,
    rate_limit: float = 0.3,
) -> dict:
    """Scrape play-by-play for all completed games on a date.

    Returns {"games": int, "events": int}
    """
    from fsbb.scraper.ncaa import _fetch_scoreboard

    raw_games = _fetch_scoreboard(target_date)
    total_events = 0
    total_games = 0

    for entry in raw_games:
        g = entry.get("game", {})
        if g.get("gameState") not in ("final", "FIN"):
            continue

        game_id = g.get("gameID")
        if not game_id:
            continue

        home_name = g.get("home", {}).get("names", {}).get("short", "")
        away_name = g.get("away", {}).get("names", {}).get("short", "")

        db_game_id = _find_game_in_db(conn, target_date.isoformat(), home_name, away_name)
        if not db_game_id:
            continue

        # Check if PBP already imported
        existing = conn.execute(
            "SELECT COUNT(*) FROM play_events WHERE game_id=?", (db_game_id,)
        ).fetchone()[0]
        if existing > 0:
            continue

        # Get team IDs
        game_row = conn.execute(
            "SELECT home_team_id, away_team_id FROM games WHERE id=?", (db_game_id,)
        ).fetchone()
        if not game_row:
            continue

        pbp = fetch_play_by_play(game_id)
        if pbp:
            n = import_play_by_play(pbp, conn, db_game_id, game_row[0], game_row[1])
            total_events += n
            if n > 0:
                total_games += 1

        time.sleep(rate_limit)

    return {"games": total_games, "events": total_events}


def _resolve_team_id(conn: sqlite3.Connection, name: str) -> int | None:
    """Resolve team name to database ID."""
    row = conn.execute("SELECT id FROM teams WHERE name=?", (name,)).fetchone()
    if row:
        return row[0]
    alias = conn.execute(
        "SELECT team_id FROM team_aliases WHERE alias=?", (name,)
    ).fetchone()
    if alias:
        return alias[0]
    logger.warning("Team resolution failed: %r (no exact match or alias)", name)
    return None


def _find_game_in_db(conn: sqlite3.Connection, date_str: str, home: str, away: str) -> int | None:
    """Find a game in our DB by date and team names."""
    home_id = _resolve_team_id(conn, home)
    away_id = _resolve_team_id(conn, away)
    if not home_id or not away_id:
        missing = []
        if not home_id:
            missing.append(f"home={home!r}")
        if not away_id:
            missing.append(f"away={away!r}")
        logger.warning(
            "Game match failed (team not found): date=%s %s",
            date_str, ", ".join(missing),
        )
        return None

    row = conn.execute(
        "SELECT id FROM games WHERE date=? AND home_team_id=? AND away_team_id=?",
        (date_str, home_id, away_id)
    ).fetchone()
    if row:
        return row[0]

    # Try swapped home/away — PEAR and NCAA sometimes disagree on who's home
    row = conn.execute(
        "SELECT id FROM games WHERE date=? AND home_team_id=? AND away_team_id=?",
        (date_str, away_id, home_id)
    ).fetchone()
    if row:
        logger.info(
            "Game matched via home/away swap: date=%s %r vs %r", date_str, home, away,
        )
        return row[0]

    logger.warning(
        "Game match failed (no game record): date=%s home=%r(id=%d) away=%r(id=%d)",
        date_str, home, home_id, away, away_id,
    )
    return None
