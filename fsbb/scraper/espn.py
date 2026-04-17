"""ESPN Hidden API scraper for college baseball.

Undocumented ESPN API — no authentication required, JSON responses.

Endpoints:
    /scoreboard — all D1 games for a date (~60-90 games/day)
    /summary    — full box score, play-by-play, team/player stats

Data available per game:
    Team batting:   HBP, K, RBI, SH, H, SB, BB, R, GIDP, SF, AB, HR, LOB, 3B, 2B, AVG, SLG, OBP
    Team pitching:  SV, K, H, ER, BB, R, HR, IP, ERA, WHIP, OBA, PC, S
    Team fielding:  DP, E, PB, A, PO, TP (we have ZERO fielding data from other sources)
    Player batting: H-AB, AB, R, H, RBI, HR, BB, K, AVG, OBP, SLG (season cumulative!)
    Player pitching: IP, H, R, ER, BB, K, HR, PC-ST, ERA, PC
    Play-by-play:   272+ events per game with pitch sequences in text
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

BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/baseball/college-baseball"
HEADERS = {"User-Agent": "ForgeStream/1.0 (college baseball research)"}

try:
    import certifi
    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CTX = ssl.create_default_context()


def _fetch_json(url: str) -> dict | None:
    """Fetch JSON from ESPN API."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        resp = urllib.request.urlopen(req, timeout=30, context=_SSL_CTX)
        return json.loads(resp.read().decode())
    except Exception as e:
        logger.warning("ESPN fetch failed: %s — %s", url[:80], e)
        return None


# ---------------------------------------------------------------------------
# Scoreboard — list all games for a date
# ---------------------------------------------------------------------------

def fetch_scoreboard(d: date, limit: int = 200) -> list[dict]:
    """Fetch all D1 baseball games for a given date.

    Returns list of event dicts with game_id, teams, scores, status.
    """
    url = f"{BASE_URL}/scoreboard?dates={d.strftime('%Y%m%d')}&limit={limit}"
    data = _fetch_json(url)
    if not data:
        return []
    return data.get("events", [])


def fetch_game_summary(espn_game_id: str) -> dict | None:
    """Fetch full game detail: box score, PBP, team stats, rosters."""
    url = f"{BASE_URL}/summary?event={espn_game_id}"
    return _fetch_json(url)


# ---------------------------------------------------------------------------
# Team name resolution — ESPN uses full names with mascots
# ---------------------------------------------------------------------------

# ESPN displayName → our DB name mapping (common mismatches)
_ESPN_NAME_MAP: dict[str, str] = {
    "UConn Huskies": "Connecticut",
    "UMass Minutemen": "UMass",
    "UNLV Rebels": "UNLV",
    "USC Trojans": "Southern California",
    "UCF Knights": "UCF",
    "LSU Tigers": "LSU",
    "Ole Miss Rebels": "Ole Miss",
    "Miami Hurricanes": "Miami",
    "Pitt Panthers": "Pittsburgh",
    "SMU Mustangs": "SMU",
    # Multi-word mascots that fail simple strip
    "Arkansas-Pine Bluff Golden Lions": "Arkansas-Pine Bluff",
    "Southern Miss Golden Eagles": "Southern Miss.",
    "St. John's Red Storm": "St. John's (NY)",
    "St. Thomas-Minnesota Tommies": "St. Thomas",
    "Minnesota Golden Gophers": "Minnesota",
    "Delaware Blue Hens": "Delaware",
    "Middle Tennessee Blue Raiders": "Middle Tenn.",
    "Charleston Cougars": "Col. of Charleston",
    "South Carolina Upstate Spartans": "USC Upstate",
    "Gardner-Webb Runnin' Bulldogs": "Gardner-Webb",
    "Campbell Fighting Camels": "Campbell",
    "Marist Red Foxes": "Marist",
    "Oakland Golden Grizzlies": "Oakland",
    "Arkansas State Red Wolves": "Arkansas St.",
    "Mississippi Valley State Delta Devils": "Mississippi Valley St.",
    "Cal State Bakersfield Roadrunners": "CSU Bakersfield",
    "North Carolina Tar Heels": "North Carolina",
    "Texas Tech Red Raiders": "Texas Tech",
    "Arizona State Sun Devils": "Arizona St.",
    "Mississippi State Bulldogs": "Mississippi St.",
    "Oregon State Beavers": "Oregon St.",
    "Florida State Seminoles": "Florida St.",
    "Michigan State Spartans": "Michigan St.",
    "Washington State Cougars": "Washington St.",
    "Fresno State Bulldogs": "Fresno St.",
    "San Diego State Aztecs": "San Diego St.",
    "Boise State Broncos": "Boise St.",
    "Long Beach State Dirtbags": "Long Beach St.",
    "North Carolina State Wolfpack": "NC State",
    "Wichita State Shockers": "Wichita St.",
    "Appalachian State Mountaineers": "Appalachian St.",
    "Sam Houston Bearkats": "Sam Houston St.",
    "Kennesaw State Owls": "Kennesaw St.",
    "Nicholls Colonels": "Nicholls St.",
    "McNeese Cowboys": "McNeese St.",
    "Sacramento State Hornets": "Sacramento St.",
    "San José State Spartans": "San Jose St.",
    "Illinois Fighting Illini": "Illinois",
    "Tulane Green Wave": "Tulane",
    "Wake Forest Demon Deacons": "Wake Forest",
    "Coastal Carolina Chanticleers": "Coastal Carolina",
    "Boston College Eagles": "Boston College",
    "Virginia Commonwealth Rams": "VCU",
    "Kent State Golden Flashes": "Kent St.",
    "Ball State Cardinals": "Ball St.",
    "Youngstown State Penguins": "Youngstown St.",
    "Cleveland State Vikings": "Cleveland St.",
    "Alabama A&M Bulldogs": "Alabama A&M",
    "Alcorn State Braves": "Alcorn St.",
    "Grambling Tigers": "Grambling",
    "Jackson State Tigers": "Jackson St.",
    "Prairie View A&M Panthers": "Prairie View A&M",
    "Texas A&M-Corpus Christi Islanders": "Texas A&M-Corpus Christi",
    "Southeastern Louisiana Lions": "Southeastern Louisiana",
    "Northwestern State Demons": "Northwestern St.",
    "Abilene Christian Wildcats": "Abilene Christian",
    "Tarleton State Texans": "Tarleton St.",
    "Utah Tech Trailblazers": "Utah Tech",
    "Stephen F. Austin Lumberjacks": "Stephen F. Austin",
    "Central Connecticut Blue Devils": "Central Connecticut",
    "Purdue Fort Wayne Mastodons": "Purdue Fort Wayne",
    "Kentucky State Kentucky S": "Kentucky State",
    # Special characters and unusual mascot names
    "Evansville Purple Aces": "Evansville",
    "Florida International Panthers": "FIU",
    "Hawai'i Rainbow Warriors": "Hawaii",
    "Louisiana Ragin' Cajuns": "Louisiana",
    "Marshall Thundering Herd": "Marshall",
    "Penn State Nittany Lions": "Penn St.",
    "UL Monroe Warhawks": "ULM",
    "Purdue Boilermakers": "Purdue",
    "Indiana Hoosiers": "Indiana",
    "Ohio State Buckeyes": "Ohio St.",
    "Iowa Hawkeyes": "Iowa",
    "Nebraska Cornhuskers": "Nebraska",
    "Rutgers Scarlet Knights": "Rutgers",
    "Maryland Terrapins": "Maryland",
    "Northwestern Wildcats": "Northwestern",
    "Wisconsin Badgers": "Wisconsin",
    "Texas A&M Aggies": "Texas A&M",
    "South Carolina Gamecocks": "South Carolina",
    "Georgia Bulldogs": "Georgia",
    "Tennessee Volunteers": "Tennessee",
    "Vanderbilt Commodores": "Vanderbilt",
    "Kentucky Wildcats": "Kentucky",
    "Missouri Tigers": "Missouri",
    "Alabama Crimson Tide": "Alabama",
    "Auburn Tigers": "Auburn",
    "Florida Gators": "Florida",
    "UTSA Roadrunners": "UT San Antonio",
    "San José State Spartans": "San Jose St.",
    "LIU Sharks": "LIU Brooklyn",
    "FIU Panthers": "FIU",
}


def _resolve_espn_team(conn: sqlite3.Connection, display_name: str) -> int | None:
    """Resolve ESPN team displayName to our team ID.

    ESPN uses "Arkansas Razorbacks", we use "Arkansas".
    Strategy: try known map, then strip last word (mascot), then alias lookup.
    """
    if not display_name:
        return None

    # 1. Direct map
    if display_name in _ESPN_NAME_MAP:
        mapped = _ESPN_NAME_MAP[display_name]
        row = conn.execute("SELECT id FROM teams WHERE name=?", (mapped,)).fetchone()
        if row:
            return row[0]

    # 2. Exact match on display name
    row = conn.execute("SELECT id FROM teams WHERE name=?", (display_name,)).fetchone()
    if row:
        return row[0]

    # 3. Alias lookup on display name
    alias = conn.execute(
        "SELECT team_id FROM team_aliases WHERE alias=?", (display_name,)
    ).fetchone()
    if alias:
        return alias[0]

    # 4. Strip mascot (last word) — "Arkansas Razorbacks" → "Arkansas"
    parts = display_name.rsplit(" ", 1)
    if len(parts) == 2:
        short = parts[0]
        # Handle "St" → "St."
        if short.endswith(" St"):
            short += "."
        row = conn.execute("SELECT id FROM teams WHERE name=?", (short,)).fetchone()
        if row:
            _cache_alias(conn, display_name, row[0])
            return row[0]
        # Try alias on short name
        alias = conn.execute(
            "SELECT team_id FROM team_aliases WHERE alias=?", (short,)
        ).fetchone()
        if alias:
            _cache_alias(conn, display_name, alias[0])
            return alias[0]

    # 5. Multi-word mascot: strip last 2 words
    MULTI_WORD_MASCOTS = {
        "Blue Devils", "Tar Heels", "Red Raiders", "Green Wave",
        "Demon Deacons", "Fighting Illini", "Golden Bears", "Sun Devils",
        "Wolf Pack", "Black Bears", "Red Storm", "Golden Eagles",
        "Blue Jays", "Yellow Jackets", "Mean Green", "Golden Flashes",
        "Nittany Lions", "Horned Frogs", "Scarlet Knights",
        "Crimson Tide", "Orange Men", "Fighting Irish",
    }
    parts3 = display_name.rsplit(" ", 2)
    if len(parts3) == 3:
        candidate = f"{parts3[1]} {parts3[2]}"
        if candidate in MULTI_WORD_MASCOTS:
            short = parts3[0]
            if short.endswith(" St"):
                short += "."
            row = conn.execute("SELECT id FROM teams WHERE name=?", (short,)).fetchone()
            if row:
                _cache_alias(conn, display_name, row[0])
                return row[0]

    # 6. Abbreviation from ESPN team object (handled by caller)
    logger.warning("ESPN team resolution failed: %r", display_name)
    return None


def _cache_alias(conn: sqlite3.Connection, alias: str, team_id: int) -> None:
    """Cache a resolved alias for future lookups."""
    try:
        conn.execute(
            "INSERT OR IGNORE INTO team_aliases (alias, team_id) VALUES (?, ?)",
            (alias, team_id),
        )
        conn.commit()
    except sqlite3.OperationalError:
        pass


# ---------------------------------------------------------------------------
# Import game data
# ---------------------------------------------------------------------------

def _safe_int(val) -> int | None:
    """Safely convert to int."""
    if val is None:
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def _safe_float(val) -> float | None:
    """Safely convert to float."""
    if val is None:
        return None
    try:
        v = str(val).replace("%", "")
        return float(v)
    except (ValueError, TypeError):
        return None


def _parse_ip(ip_str: str | None) -> float | None:
    """Parse innings pitched (e.g. '6.2' means 6 and 2/3)."""
    if not ip_str:
        return None
    try:
        return float(ip_str)
    except (ValueError, TypeError):
        return None


def _find_or_create_game(
    conn: sqlite3.Connection,
    game_date: str,
    home_id: int,
    away_id: int,
    home_runs: int | None,
    away_runs: int | None,
    espn_game_id: str,
) -> int | None:
    """Find existing game or create new one. Returns game DB ID."""
    # Try exact match
    row = conn.execute(
        "SELECT id FROM games WHERE date=? AND home_team_id=? AND away_team_id=?",
        (game_date, home_id, away_id),
    ).fetchone()
    if row:
        # Update ESPN ID
        conn.execute(
            "UPDATE games SET espn_game_id=? WHERE id=? AND espn_game_id IS NULL",
            (espn_game_id, row[0]),
        )
        return row[0]

    # Try swapped (home/away disagreement between sources)
    row = conn.execute(
        "SELECT id FROM games WHERE date=? AND home_team_id=? AND away_team_id=?",
        (game_date, away_id, home_id),
    ).fetchone()
    if row:
        conn.execute(
            "UPDATE games SET espn_game_id=? WHERE id=? AND espn_game_id IS NULL",
            (espn_game_id, row[0]),
        )
        return row[0]

    # Create new game
    winner_id = None
    status = "final"
    if home_runs is not None and away_runs is not None:
        if home_runs > away_runs:
            winner_id = home_id
        elif away_runs > home_runs:
            winner_id = away_id

    try:
        conn.execute("""
            INSERT INTO games (date, home_team_id, away_team_id, home_runs, away_runs,
                               status, actual_winner_id, source, espn_game_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'espn', ?)
        """, (game_date, home_id, away_id, home_runs, away_runs,
              status, winner_id, espn_game_id))
        conn.commit()
        return conn.execute(
            "SELECT id FROM games WHERE date=? AND home_team_id=? AND away_team_id=?",
            (game_date, home_id, away_id),
        ).fetchone()[0]
    except sqlite3.IntegrityError:
        return None


def import_game_boxscore(conn: sqlite3.Connection, summary: dict, game_db_id: int) -> dict:
    """Import player batting, pitching, and fielding from ESPN summary.

    Returns {"batters": int, "pitchers": int, "fielding": bool}.
    """
    bs = summary.get("boxscore", {})
    batters_imported = 0
    pitchers_imported = 0
    fielding_imported = False

    for team_data in bs.get("players", []):
        team_info = team_data.get("team", {})
        team_name = team_info.get("displayName", "")
        team_id = _resolve_espn_team(conn, team_name)
        if not team_id:
            continue

        for stat_cat in team_data.get("statistics", []):
            labels = stat_cat.get("labels", [])
            if not labels:
                continue

            # Determine if batting or pitching by presence of key columns
            is_batting = "AB" in labels
            is_pitching = "IP" in labels

            for athlete_data in stat_cat.get("athletes", []):
                athlete = athlete_data.get("athlete", {})
                player_name = athlete.get("displayName", "")
                espn_pid = str(athlete.get("id", ""))
                is_starter = 1 if athlete_data.get("starter", False) else 0
                stats = athlete_data.get("stats", [])

                if not player_name or not stats:
                    continue

                # Build label→value map
                stat_map = dict(zip(labels, stats))

                if is_batting:
                    try:
                        conn.execute("""
                            INSERT INTO espn_game_batting
                                (game_id, team_id, player_name, espn_player_id, is_starter,
                                 ab, r, h, rbi, hr, bb, k, hbp, sb, cs,
                                 season_avg, season_obp, season_slg)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(game_id, player_name, team_id) DO UPDATE SET
                                season_avg=excluded.season_avg,
                                season_obp=excluded.season_obp,
                                season_slg=excluded.season_slg
                        """, (
                            game_db_id, team_id, player_name, espn_pid, is_starter,
                            _safe_int(stat_map.get("AB")),
                            _safe_int(stat_map.get("R")),
                            _safe_int(stat_map.get("H")),
                            _safe_int(stat_map.get("RBI")),
                            _safe_int(stat_map.get("HR")),
                            _safe_int(stat_map.get("BB")),
                            _safe_int(stat_map.get("K")),
                            _safe_int(stat_map.get("HBP")),
                            _safe_int(stat_map.get("SB")),
                            _safe_int(stat_map.get("CS")),
                            _safe_float(stat_map.get("AVG")),
                            _safe_float(stat_map.get("OBP")),
                            _safe_float(stat_map.get("SLG")),
                        ))
                        batters_imported += 1
                    except sqlite3.IntegrityError:
                        pass

                elif is_pitching:
                    # Parse pitches-strikes from "PC-ST" like "87-58"
                    pc_st = stat_map.get("PC-ST", "")
                    pitches = None
                    strikes = None
                    if pc_st and "-" in str(pc_st):
                        try:
                            parts = str(pc_st).split("-")
                            pitches = int(parts[0])
                            strikes = int(parts[1])
                        except (ValueError, IndexError):
                            pass

                    try:
                        conn.execute("""
                            INSERT INTO espn_game_pitching
                                (game_id, team_id, player_name, espn_player_id, is_starter,
                                 ip, h, r, er, bb, k, hr, pitches, strikes, season_era)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(game_id, player_name, team_id) DO UPDATE SET
                                season_era=excluded.season_era
                        """, (
                            game_db_id, team_id, player_name, espn_pid, is_starter,
                            _parse_ip(stat_map.get("IP")),
                            _safe_int(stat_map.get("H")),
                            _safe_int(stat_map.get("R")),
                            _safe_int(stat_map.get("ER")),
                            _safe_int(stat_map.get("BB")),
                            _safe_int(stat_map.get("K")),
                            _safe_int(stat_map.get("HR")),
                            pitches, strikes,
                            _safe_float(stat_map.get("ERA")),
                        ))
                        pitchers_imported += 1
                    except sqlite3.IntegrityError:
                        pass

    # Team-level fielding stats
    for team_data in bs.get("teams", []):
        team_info = team_data.get("team", {})
        team_name = team_info.get("displayName", "")
        team_id = _resolve_espn_team(conn, team_name)
        if not team_id:
            continue

        for cat in team_data.get("statistics", []):
            if cat.get("name") != "fielding":
                continue
            stat_list = cat.get("stats", [])
            fld = {s["abbreviation"]: s.get("displayValue", s.get("value"))
                   for s in stat_list if "abbreviation" in s}

            try:
                conn.execute("""
                    INSERT INTO espn_game_fielding
                        (game_id, team_id, dp, e, pb, a, po, tp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(game_id, team_id) DO UPDATE SET
                        dp=excluded.dp, e=excluded.e, pb=excluded.pb,
                        a=excluded.a, po=excluded.po, tp=excluded.tp
                """, (
                    game_db_id, team_id,
                    _safe_int(fld.get("DP")),
                    _safe_int(fld.get("E")),
                    _safe_int(fld.get("PB")),
                    _safe_int(fld.get("A")),
                    _safe_int(fld.get("PO")),
                    _safe_int(fld.get("TP")),
                ))
                fielding_imported = True
            except sqlite3.IntegrityError:
                pass

    conn.commit()
    return {
        "batters": batters_imported,
        "pitchers": pitchers_imported,
        "fielding": fielding_imported,
    }


# ---------------------------------------------------------------------------
# Date/season scrapers
# ---------------------------------------------------------------------------

def scrape_date(conn: sqlite3.Connection, d: date, rate_limit: float = 0.3) -> dict:
    """Scrape all completed games for a single date from ESPN.

    Returns {"games": int, "batters": int, "pitchers": int, "fielding": int, "skipped": int}.
    """
    events = fetch_scoreboard(d)
    total_games = 0
    total_batters = 0
    total_pitchers = 0
    total_fielding = 0
    skipped = 0

    for event in events:
        status_type = event.get("status", {}).get("type", {}).get("name", "")
        if status_type != "STATUS_FINAL":
            skipped += 1
            continue

        espn_game_id = event.get("id", "")
        if not espn_game_id:
            skipped += 1
            continue

        # Check if we already have ESPN data for this game
        existing = conn.execute(
            "SELECT id FROM games WHERE espn_game_id=?", (espn_game_id,)
        ).fetchone()
        if existing:
            # Check if box score data already imported
            has_batting = conn.execute(
                "SELECT COUNT(*) FROM espn_game_batting WHERE game_id=?",
                (existing[0],)
            ).fetchone()[0]
            if has_batting > 0:
                skipped += 1
                continue

        # Extract basic game info from scoreboard
        competitions = event.get("competitions", [])
        if not competitions:
            skipped += 1
            continue

        comp = competitions[0]
        game_date = d.isoformat()

        home_info = None
        away_info = None
        for team_data in comp.get("competitors", []):
            if team_data.get("homeAway") == "home":
                home_info = team_data
            else:
                away_info = team_data

        if not home_info or not away_info:
            skipped += 1
            continue

        home_name = home_info.get("team", {}).get("displayName", "")
        away_name = away_info.get("team", {}).get("displayName", "")
        home_score = _safe_int(home_info.get("score"))
        away_score = _safe_int(away_info.get("score"))

        home_id = _resolve_espn_team(conn, home_name)
        away_id = _resolve_espn_team(conn, away_name)

        if not home_id or not away_id:
            skipped += 1
            continue

        # Find or create game record
        game_db_id = _find_or_create_game(
            conn, game_date, home_id, away_id, home_score, away_score, espn_game_id
        )
        if not game_db_id:
            skipped += 1
            continue

        # Fetch full summary with box score
        summary = fetch_game_summary(espn_game_id)
        if not summary:
            skipped += 1
            continue

        result = import_game_boxscore(conn, summary, game_db_id)
        if result["batters"] > 0:
            total_games += 1
        total_batters += result["batters"]
        total_pitchers += result["pitchers"]
        if result["fielding"]:
            total_fielding += 1

        time.sleep(rate_limit)

    return {
        "games": total_games,
        "batters": total_batters,
        "pitchers": total_pitchers,
        "fielding": total_fielding,
        "skipped": skipped,
    }


def scrape_season(
    conn: sqlite3.Connection,
    start: date | None = None,
    end: date | None = None,
    rate_limit: float = 0.3,
    progress: bool = True,
    max_days: int = 0,
) -> dict:
    """Scrape ESPN box scores for a range of dates.

    Args:
        max_days: If > 0, stop after this many days (for incremental scraping)
    """
    if start is None:
        start = date(date.today().year, 2, 14)
    if end is None:
        end = date.today() - timedelta(days=1)

    total = {"games": 0, "batters": 0, "pitchers": 0, "fielding": 0, "skipped": 0}
    current = start
    days_scraped = 0

    while current <= end:
        result = scrape_date(conn, current, rate_limit)
        for k in total:
            total[k] += result[k]
        days_scraped += 1

        if progress and days_scraped % 7 == 0:
            print(f"  {current}: {total['games']} games, "
                  f"{total['batters']} batters, {total['fielding']} fielding")

        if max_days > 0 and days_scraped >= max_days:
            break

        current += timedelta(days=1)

    total["days_scraped"] = days_scraped
    return total
