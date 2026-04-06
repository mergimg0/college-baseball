# V0/V1 Implementation Specification — "Nightly Prediction Page"
**Date:** 2026-03-31 | **Version:** 1.0
**Target:** Build-ready spec. A developer who has never seen the project can code from this.
**Prerequisite:** Python 3.12+, `uv` installed, ForgeStream repo cloned

---

## V0: Nightly Prediction Page — Hour-by-Hour Build Plan

### Deliverable

A single static HTML page updated daily showing:
1. Tonight's DI games with predicted winner, win probability, and predicted run total
2. Yesterday's results filled in (✓/✗ on our prediction)
3. Running accuracy % after 3+ days
4. PEAR comparison column ("PEAR would have picked...")
5. Automated via cron/GitHub Actions

---

### Hour 0-2: Data Foundation

#### 0.1 Project Scaffolding

```bash
mkdir -p fsbb/{scraper,models,templates}
touch fsbb/__init__.py fsbb/__main__.py fsbb/db.py fsbb/schemas.py
touch fsbb/scraper/__init__.py fsbb/scraper/ncaa.py fsbb/scraper/pear.py fsbb/scraper/clean.py
touch fsbb/models/__init__.py fsbb/models/ratings.py fsbb/models/predict.py
```

Add to `pyproject.toml` (or create new):

```toml
[project]
name = "fsbb"
version = "0.1.0"
description = "ForgeStream Baseball — NCAA team ratings and predictions"
requires-python = ">=3.12"
dependencies = [
    "httpx>=0.27",
    "pydantic>=2.0",
    "click>=8.1",
    "tabulate>=0.9",
    "jinja2>=3.1",
]

[project.scripts]
fsbb = "fsbb.__main__:cli"
```

#### 0.2 SQLite Schema — `fsbb/db.py`

```python
"""SQLite database connection and schema management."""

import sqlite3
from pathlib import Path

DB_PATH = Path("data/fsbb.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,             -- Canonical: "North Carolina"
    conference TEXT NOT NULL,
    division TEXT NOT NULL DEFAULT 'D1',
    pear_power_rating REAL,                -- From PEAR import
    pear_net INTEGER,
    pear_elo REAL,
    pear_sos INTEGER,
    pear_rpi INTEGER,
    pear_rqi INTEGER,
    -- Our computed ratings (updated daily)
    total_rs INTEGER DEFAULT 0,            -- Season runs scored
    total_ra INTEGER DEFAULT 0,            -- Season runs allowed
    games_played INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    pythag_pct REAL,
    sos REAL,
    adj_rs_per_game REAL,
    adj_ra_per_game REAL,
    power_rating REAL,
    elo REAL DEFAULT 1500.0
);

CREATE TABLE IF NOT EXISTS team_aliases (
    alias TEXT PRIMARY KEY,                -- "UNC", "N. Carolina", etc.
    team_id INTEGER NOT NULL REFERENCES teams(id)
);

CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,                     -- "2026-03-31"
    home_team_id INTEGER NOT NULL REFERENCES teams(id),
    away_team_id INTEGER NOT NULL REFERENCES teams(id),
    home_runs INTEGER,                     -- NULL if not yet played
    away_runs INTEGER,
    status TEXT NOT NULL DEFAULT 'scheduled', -- scheduled | final | postponed | cancelled
    source TEXT NOT NULL DEFAULT 'pear',    -- pear | ncaa | manual
    scraped_at TEXT NOT NULL,
    UNIQUE(date, home_team_id, away_team_id)
);

CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL REFERENCES games(id),
    predicted_at TEXT NOT NULL,             -- ISO 8601
    home_win_prob REAL NOT NULL,            -- 0.0 - 1.0
    predicted_winner_id INTEGER NOT NULL REFERENCES teams(id),
    predicted_total_runs REAL,             -- Expected combined runs
    confidence TEXT NOT NULL,               -- high | moderate | low
    our_power_diff REAL,                   -- home.power - away.power
    pear_home_rank INTEGER,                -- PEAR NET rank
    pear_away_rank INTEGER,
    -- Filled after game completes:
    actual_winner_id INTEGER REFERENCES teams(id),
    correct INTEGER,                       -- 1 = correct, 0 = wrong, NULL = pending
    UNIQUE(game_id)
);

CREATE INDEX IF NOT EXISTS idx_games_date ON games(date);
CREATE INDEX IF NOT EXISTS idx_games_status ON games(status);
CREATE INDEX IF NOT EXISTS idx_predictions_correct ON predictions(correct);
"""

def get_db() -> sqlite3.Connection:
    """Get database connection with row factory."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db() -> None:
    """Create tables if they don't exist."""
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
```

#### 0.3 Pydantic Schemas — `fsbb/schemas.py`

```python
"""Data models for NCAA games and predictions."""

from __future__ import annotations
from datetime import date, datetime
from pydantic import BaseModel

class Team(BaseModel):
    id: int | None = None
    name: str
    conference: str
    division: str = "D1"
    pear_power_rating: float | None = None
    pear_net: int | None = None
    pear_elo: float | None = None
    pear_sos: int | None = None
    total_rs: int = 0
    total_ra: int = 0
    games_played: int = 0
    wins: int = 0
    losses: int = 0

class NcaaGame(BaseModel):
    date: date
    home_team: str                  # Canonical name
    away_team: str
    home_runs: int | None = None    # None if not played
    away_runs: int | None = None
    status: str = "scheduled"       # scheduled | final | postponed | cancelled

class Prediction(BaseModel):
    game_date: date
    home_team: str
    away_team: str
    home_win_prob: float
    predicted_winner: str
    predicted_total_runs: float | None = None
    confidence: str                 # high | moderate | low
    our_power_diff: float
    pear_home_rank: int | None = None
    pear_away_rank: int | None = None
    actual_winner: str | None = None
    correct: bool | None = None

class DailyReport(BaseModel):
    date: date
    predictions: list[Prediction]
    total_predictions: int = 0
    total_resolved: int = 0
    total_correct: int = 0
    accuracy_pct: float | None = None  # None if <3 resolved
    pear_accuracy_pct: float | None = None
```

#### 0.4 PEAR Import — `fsbb/scraper/pear.py`

```python
"""Import PEAR ratings from scraped JSON files."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

# Known PEAR team name → canonical name mappings
PEAR_NAME_FIXES: dict[str, str] = {
    "UConn": "Connecticut",
    "UCSB": "UC Santa Barbara",
    "UNCW": "UNC Wilmington",
    "UNCG": "UNC Greensboro",
    "UNC": "North Carolina",
    "Ole Miss": "Mississippi",
    "Miss St.": "Mississippi St.",
    # Add more as discovered during import
}

def import_pear_ratings(conn: sqlite3.Connection, ratings_path: str = "data/pear/pear_ratings.json") -> int:
    """Import PEAR ratings JSON into teams table.

    Returns number of teams imported.
    """
    data = json.loads(Path(ratings_path).read_text())
    teams = data["teams"]
    now = datetime.now(timezone.utc).isoformat()
    imported = 0

    for t in teams:
        name = t["Team"]
        canonical = PEAR_NAME_FIXES.get(name, name)

        conn.execute("""
            INSERT INTO teams (name, conference, pear_power_rating, pear_net, pear_elo, pear_sos, pear_rpi, pear_rqi, elo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                conference = excluded.conference,
                pear_power_rating = excluded.pear_power_rating,
                pear_net = excluded.pear_net,
                pear_elo = excluded.pear_elo,
                pear_sos = excluded.pear_sos,
                pear_rpi = excluded.pear_rpi,
                pear_rqi = excluded.pear_rqi
        """, (canonical, t["Conference"], t["power_rating"], t["NET"],
              t["ELO"], t["SOS"], t["RPI"], t["RQI"], t["ELO"]))

        # Add the PEAR name as an alias if different
        if name != canonical:
            conn.execute(
                "INSERT OR IGNORE INTO team_aliases (alias, team_id) VALUES (?, (SELECT id FROM teams WHERE name = ?))",
                (name, canonical),
            )

        imported += 1

    conn.commit()
    return imported


def import_pear_team_games(conn: sqlite3.Connection, teams_dir: str = "data/pear/teams") -> int:
    """Import recent/upcoming games from PEAR per-team JSON files.

    Each file has: team.RS, team.RA, team.G, team.Record,
    recent_games[], upcoming_games[].

    Returns number of games imported.
    """
    teams_path = Path(teams_dir)
    if not teams_path.exists():
        return 0

    now = datetime.now(timezone.utc).isoformat()
    game_count = 0

    for team_file in teams_path.glob("team_*.json"):
        data = json.loads(team_file.read_text())
        team_data = data["team"]
        team_name = team_data["Team"]
        canonical = PEAR_NAME_FIXES.get(team_name, team_name)

        # Update team aggregates
        conn.execute("""
            UPDATE teams SET
                total_rs = ?, total_ra = ?, games_played = ?,
                wins = ?, losses = ?
            WHERE name = ?
        """, (
            int(team_data.get("RS", 0)),
            int(team_data.get("RA", 0)),
            int(team_data.get("G", 0)),
            int(team_data.get("Wins", team_data.get("Record", "0-0").split("-")[0])),
            int(team_data.get("Losses", team_data.get("Record", "0-0").split("-")[1])),
            canonical,
        ))

        # Import games (both recent and upcoming)
        for game_list in [data.get("recent_games", []), data.get("upcoming_games", [])]:
            for g in game_list:
                home = g.get("home_team", "")
                away = g.get("away_team", "")
                if not home or not away:
                    continue

                home_canonical = PEAR_NAME_FIXES.get(home, home)
                away_canonical = PEAR_NAME_FIXES.get(away, away)
                game_date = g.get("Date", "")[:10]  # "2026-03-29T00:00:00" → "2026-03-29"
                status = "final" if g.get("Result", "SCH") != "SCH" else "scheduled"
                home_runs = int(g["home_score"]) if g.get("home_score") and status == "final" else None
                away_runs = int(g["away_score"]) if g.get("away_score") and status == "final" else None

                try:
                    conn.execute("""
                        INSERT INTO games (date, home_team_id, away_team_id, home_runs, away_runs, status, source, scraped_at)
                        SELECT ?, h.id, a.id, ?, ?, ?, 'pear', ?
                        FROM teams h, teams a
                        WHERE h.name = ? AND a.name = ?
                        ON CONFLICT(date, home_team_id, away_team_id) DO UPDATE SET
                            home_runs = COALESCE(excluded.home_runs, games.home_runs),
                            away_runs = COALESCE(excluded.away_runs, games.away_runs),
                            status = CASE WHEN excluded.status = 'final' THEN 'final' ELSE games.status END
                    """, (game_date, home_runs, away_runs, status, now,
                          home_canonical, away_canonical))
                    game_count += 1
                except sqlite3.IntegrityError:
                    pass  # Team not in teams table — skip

    conn.commit()
    return game_count
```

#### 0.5 NCAA Schedule Scraper — `fsbb/scraper/ncaa.py`

```python
"""Scrape NCAA DI baseball schedule and results.

Primary source: henrygd/ncaa-api (JSON proxy for stats.ncaa.org)
Rate limit: 5 requests/second

URL patterns:
  Schedule:   https://ncaa-api.henrygd.me/scoreboard/baseball-men/d1/{YYYY}/{MM}/{DD}
  Game detail: https://ncaa-api.henrygd.me/game/{game_id}/baseball-men
"""

import asyncio
from datetime import date, timedelta
from typing import Any

import httpx

from ..schemas import NcaaGame

BASE_URL = "https://ncaa-api.henrygd.me"
RATE_LIMIT = 0.2  # seconds between requests (5 req/s)

async def fetch_scoreboard(client: httpx.AsyncClient, game_date: date) -> list[dict[str, Any]]:
    """Fetch NCAA scoreboard for a specific date.

    Returns raw game dicts from the API.
    Handles: no games (empty list), API errors (raises), rate limiting.
    """
    url = f"{BASE_URL}/scoreboard/baseball-men/d1/{game_date.year}/{game_date.month:02d}/{game_date.day:02d}"
    response = await client.get(url, timeout=30.0)
    response.raise_for_status()
    data = response.json()

    # The API returns: {"games": [...]} or similar structure
    # Adapt based on actual response format (test first)
    games = data.get("games", data.get("scoreboard", []))
    if isinstance(games, dict):
        games = games.get("games", [])
    return games


def parse_ncaa_game(raw: dict) -> NcaaGame | None:
    """Parse a raw NCAA API game dict into our NcaaGame model.

    Expected fields (from henrygd/ncaa-api — verify against actual response):
      game.home.names.full     → "North Carolina"
      game.away.names.full     → "Duke"
      game.home.score          → "5" or None
      game.away.score          → "3" or None
      game.gameState           → "final", "pre", "live", "postponed"
      game.startDate           → "2026-03-31"

    Returns None if the game can't be parsed (missing fields, non-DI, etc).
    """
    try:
        home_info = raw.get("game", raw).get("home", {})
        away_info = raw.get("game", raw).get("away", {})

        home_name = (
            home_info.get("names", {}).get("full")
            or home_info.get("teamName")
            or home_info.get("nameShort", "")
        )
        away_name = (
            away_info.get("names", {}).get("full")
            or away_info.get("teamName")
            or away_info.get("nameShort", "")
        )

        if not home_name or not away_name:
            return None

        game_state = raw.get("game", raw).get("gameState", raw.get("status", "pre"))
        status_map = {"final": "final", "pre": "scheduled", "live": "scheduled",
                      "postponed": "postponed", "cancelled": "cancelled",
                      "delayed": "scheduled"}
        status = status_map.get(game_state.lower(), "scheduled")

        home_score = home_info.get("score")
        away_score = away_info.get("score")

        game_date_str = raw.get("game", raw).get("startDate", raw.get("date", ""))[:10]

        return NcaaGame(
            date=date.fromisoformat(game_date_str) if game_date_str else date.today(),
            home_team=home_name,
            away_team=away_name,
            home_runs=int(home_score) if home_score and status == "final" else None,
            away_runs=int(away_score) if away_score and status == "final" else None,
            status=status,
        )
    except (KeyError, ValueError, TypeError):
        return None


async def scrape_date_range(
    start: date,
    end: date,
) -> list[NcaaGame]:
    """Scrape all DI games in a date range.

    Args:
        start: First date (inclusive).
        end: Last date (inclusive).

    Returns list of parsed NcaaGame objects.
    """
    games: list[NcaaGame] = []
    async with httpx.AsyncClient() as client:
        current = start
        while current <= end:
            try:
                raw_games = await fetch_scoreboard(client, current)
                for raw in raw_games:
                    game = parse_ncaa_game(raw)
                    if game:
                        games.append(game)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    pass  # No games on this date
                else:
                    raise
            current += timedelta(days=1)
            await asyncio.sleep(RATE_LIMIT)
    return games


async def scrape_today() -> list[NcaaGame]:
    """Scrape today's scheduled games."""
    return await scrape_date_range(date.today(), date.today())


async def scrape_yesterday_results() -> list[NcaaGame]:
    """Scrape yesterday's completed games."""
    yesterday = date.today() - timedelta(days=1)
    return await scrape_date_range(yesterday, yesterday)
```

**NOTE on the NCAA API:** The exact response format from `henrygd/ncaa-api` needs to be verified by running a test request before coding the parser. Run this first:

```bash
curl -s "https://ncaa-api.henrygd.me/scoreboard/baseball-men/d1/2026/03/30" | python3 -m json.tool | head -50
```

Adapt `parse_ncaa_game()` to match the actual response structure. The function above is a best-guess skeleton.

**If the NCAA API is down or returns unexpected format:** Fall back to PEAR data. The per-team files (`data/pear/teams/team_*.json`) already contain `upcoming_games` and `recent_games` with scores. This is enough for V0.

#### 0.6 Entity Resolution — `fsbb/scraper/clean.py`

```python
"""Team name normalization and entity resolution."""

# Master alias table: map all known variations to canonical name.
# Start with PEAR's 308 names, add NCAA API variations as discovered.
ALIASES: dict[str, str] = {
    # Common abbreviations
    "UNC": "North Carolina",
    "N. Carolina": "North Carolina",
    "UConn": "Connecticut",
    "UCSB": "UC Santa Barbara",
    "Ole Miss": "Mississippi",
    "Miss St.": "Mississippi St.",
    "Miss. St.": "Mississippi St.",
    "Mississippi State": "Mississippi St.",
    "Ga. Tech": "Georgia Tech",
    "Fla. St.": "Florida St.",
    "Florida State": "Florida St.",
    "Oregon St.": "Oregon St.",
    "Oregon State": "Oregon St.",
    "N.C. State": "NC State",
    "Texas A&M": "Texas A&M",
    "TAMU": "Texas A&M",
    # Add more as NCAA scraper discovers mismatches
}

def normalize_team_name(name: str) -> str:
    """Normalize a team name to canonical form.

    1. Check alias table
    2. Strip common suffixes ("University", "State University")
    3. Return as-is if no match (will be caught by missing team_id lookup)
    """
    name = name.strip()
    if name in ALIASES:
        return ALIASES[name]
    # Common suffix removal
    for suffix in [" University", " State University", " College"]:
        if name.endswith(suffix):
            stripped = name[:-len(suffix)]
            if stripped in ALIASES:
                return ALIASES[stripped]
    return name


def fuzzy_match(name: str, candidates: list[str], threshold: int = 3) -> str | None:
    """Levenshtein fuzzy match against candidate list.

    Returns closest match if distance <= threshold, else None.
    Simple implementation — no external dependency.
    """
    def levenshtein(s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)
        prev_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            curr_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = prev_row[j + 1] + 1
                deletions = curr_row[j] + 1
                substitutions = prev_row[j] + (c1 != c2)
                curr_row.append(min(insertions, deletions, substitutions))
            prev_row = curr_row
        return prev_row[-1]

    best_match = None
    best_dist = threshold + 1
    for candidate in candidates:
        dist = levenshtein(name.lower(), candidate.lower())
        if dist < best_dist:
            best_dist = dist
            best_match = candidate
    return best_match if best_dist <= threshold else None
```

---

### Hour 2-6: Rating Engine

#### `fsbb/models/ratings.py`

```python
"""Team rating computations: Pythagorean, SOS, adjusted runs, Elo, power rating."""

from __future__ import annotations
import math
import sqlite3


# ── Pythagorean Win Percentage ───────────────────────────────────────

PYTHAG_EXPONENT = 1.83  # Calibrate later from historical data

def pythagorean_pct(runs_scored: int, runs_allowed: int, exponent: float = PYTHAG_EXPONENT) -> float:
    """Pythagorean expected win percentage.

    Formula: RS^exp / (RS^exp + RA^exp)

    Args:
        runs_scored: Total season runs scored.
        runs_allowed: Total season runs allowed.
        exponent: Pythagorean exponent (default 1.83 for college baseball).

    Returns: Expected win percentage (0.0 to 1.0).
    """
    if runs_scored <= 0 and runs_allowed <= 0:
        return 0.5
    if runs_allowed <= 0:
        return 0.99
    if runs_scored <= 0:
        return 0.01
    rs_exp = runs_scored ** exponent
    return rs_exp / (rs_exp + runs_allowed ** exponent)


# ── Strength of Schedule ────────────────────────────────────────────

def compute_sos(conn: sqlite3.Connection, iterations: int = 3, convergence_threshold: float = 0.001) -> dict[int, float]:
    """Iterative Strength of Schedule computation.

    Algorithm:
      1. Initialize: each team's rating = their Pythagorean win%
      2. For each iteration:
         a. For each team, SOS = average rating of their opponents
         b. Update team rating = f(pythag_pct, SOS)
      3. Converge when max delta between iterations < threshold

    Args:
        conn: Database connection.
        iterations: Maximum iterations.
        convergence_threshold: Stop if max SOS delta < this.

    Returns: dict of team_id → SOS value (0.0 to 1.0, higher = harder schedule).
    """
    # Step 1: Get all teams and their Pythagorean win%
    teams = conn.execute("""
        SELECT id, total_rs, total_ra, games_played
        FROM teams WHERE games_played >= 5
    """).fetchall()

    ratings: dict[int, float] = {}
    for t in teams:
        ratings[t["id"]] = pythagorean_pct(t["total_rs"], t["total_ra"])

    # Step 2: Get opponent lists from games table
    opponents: dict[int, list[int]] = {}
    games = conn.execute("""
        SELECT home_team_id, away_team_id FROM games WHERE status = 'final'
    """).fetchall()
    for g in games:
        h, a = g["home_team_id"], g["away_team_id"]
        opponents.setdefault(h, []).append(a)
        opponents.setdefault(a, []).append(h)

    # Step 3: Iterate
    sos: dict[int, float] = {tid: 0.5 for tid in ratings}

    for iteration in range(iterations):
        new_sos: dict[int, float] = {}
        max_delta = 0.0

        for tid in ratings:
            opps = opponents.get(tid, [])
            if not opps:
                new_sos[tid] = 0.5
                continue
            opp_ratings = [ratings.get(oid, 0.5) for oid in opps]
            new_sos[tid] = sum(opp_ratings) / len(opp_ratings)
            max_delta = max(max_delta, abs(new_sos[tid] - sos.get(tid, 0.5)))

        sos = new_sos

        # Update ratings incorporating SOS
        for tid in ratings:
            pythag = pythagorean_pct(
                dict(teams[i] for i, t in enumerate(teams) if t["id"] == tid).get("total_rs", 0),
                dict(teams[i] for i, t in enumerate(teams) if t["id"] == tid).get("total_ra", 0),
            )
            # Not needed in the iteration — SOS is about opponents' ratings
            pass

        if max_delta < convergence_threshold:
            break

    return sos


# ── Adjusted Runs ───────────────────────────────────────────────────

def compute_adjusted_runs(conn: sqlite3.Connection) -> dict[int, tuple[float, float]]:
    """Compute SOS-adjusted runs scored and allowed per game.

    adj_RS = RS/G × (league_avg_RA / avg_opponent_RA)
    adj_RA = RA/G × (league_avg_RS / avg_opponent_RS)

    Returns: dict of team_id → (adj_rs_per_game, adj_ra_per_game).
    """
    teams = conn.execute("""
        SELECT id, total_rs, total_ra, games_played
        FROM teams WHERE games_played >= 5
    """).fetchall()

    # League averages
    total_league_rs = sum(t["total_rs"] for t in teams)
    total_league_g = sum(t["games_played"] for t in teams)
    league_avg_rs = total_league_rs / max(total_league_g, 1)
    league_avg_ra = league_avg_rs  # RS and RA are symmetric across the league

    # Per-team opponent averages
    results: dict[int, tuple[float, float]] = {}
    for t in teams:
        tid = t["id"]
        rs_g = t["total_rs"] / max(t["games_played"], 1)
        ra_g = t["total_ra"] / max(t["games_played"], 1)

        # Get opponents' RS and RA
        opp_stats = conn.execute("""
            SELECT
                SUM(CASE WHEN g.home_team_id = ? THEN t2.total_ra ELSE t2.total_rs END) as opp_ra_sum,
                SUM(CASE WHEN g.home_team_id = ? THEN t2.total_rs ELSE t2.total_ra END) as opp_rs_sum,
                COUNT(*) as opp_count
            FROM games g
            JOIN teams t2 ON t2.id = CASE WHEN g.home_team_id = ? THEN g.away_team_id ELSE g.home_team_id END
            WHERE (g.home_team_id = ? OR g.away_team_id = ?) AND g.status = 'final'
        """, (tid, tid, tid, tid, tid)).fetchone()

        opp_count = opp_stats["opp_count"] or 1
        avg_opp_ra = (opp_stats["opp_ra_sum"] or 0) / opp_count / max(t["games_played"], 1)
        avg_opp_rs = (opp_stats["opp_rs_sum"] or 0) / opp_count / max(t["games_played"], 1)

        # Avoid division by zero
        adj_rs = rs_g * (league_avg_ra / max(avg_opp_ra, 0.1))
        adj_ra = ra_g * (league_avg_rs / max(avg_opp_rs, 0.1))

        results[tid] = (adj_rs, adj_ra)

    return results


# ── Elo Rating ──────────────────────────────────────────────────────

K_FACTOR = 20.0
HOME_ADVANTAGE = 30.0  # Elo points for home team

def elo_expected(rating_a: float, rating_b: float) -> float:
    """Expected score for player A against player B."""
    return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))


def elo_update(
    winner_elo: float,
    loser_elo: float,
    margin_of_victory: int,
    winner_is_home: bool,
) -> tuple[float, float]:
    """Update Elo ratings after a game.

    Uses margin-of-victory multiplier: ln(abs(MOV) + 1) × 0.6

    Args:
        winner_elo: Current Elo of the winner.
        loser_elo: Current Elo of the loser.
        margin_of_victory: Absolute run differential.
        winner_is_home: Whether the winner was the home team.

    Returns: (new_winner_elo, new_loser_elo).
    """
    # Adjust for home advantage
    adj_winner = winner_elo + (HOME_ADVANTAGE if winner_is_home else -HOME_ADVANTAGE)
    adj_loser = loser_elo + (-HOME_ADVANTAGE if winner_is_home else HOME_ADVANTAGE)

    expected_w = elo_expected(adj_winner, adj_loser)
    mov_multiplier = math.log(abs(margin_of_victory) + 1) * 0.6 + 0.4  # floor at 0.4

    k = K_FACTOR * mov_multiplier
    new_winner = winner_elo + k * (1.0 - expected_w)
    new_loser = loser_elo + k * (0.0 - (1.0 - expected_w))

    return (new_winner, new_loser)


# ── Power Rating ────────────────────────────────────────────────────

WEIGHT_PYTHAG = 0.40
WEIGHT_SOS = 0.30
WEIGHT_ELO = 0.30

def compute_power_rating(pythag_pct: float, sos: float, elo: float) -> float:
    """Composite power rating.

    Weighted combination of:
      - Pythagorean win% (0.40)
      - SOS (0.30)
      - Elo normalized to 0-1 scale (0.30)

    Output: scaled to approximately match PEAR's range (-11 to +7).
    """
    elo_norm = (elo - 1000) / 400  # Rough normalization: 1000→0, 1400→1, 1800→2
    composite = (WEIGHT_PYTHAG * pythag_pct + WEIGHT_SOS * sos + WEIGHT_ELO * elo_norm)
    # Scale to PEAR-like range: composite is roughly 0-1, PEAR is -11 to +7
    return (composite - 0.5) * 18.0


# ── Run All Ratings ─────────────────────────────────────────────────

def update_all_ratings(conn: sqlite3.Connection) -> int:
    """Recompute all ratings for all teams. Returns number of teams updated."""
    sos_map = compute_sos(conn)
    adj_runs_map = compute_adjusted_runs(conn)

    teams = conn.execute("SELECT id, total_rs, total_ra, games_played, elo FROM teams WHERE games_played >= 5").fetchall()
    updated = 0

    for t in teams:
        tid = t["id"]
        ppct = pythagorean_pct(t["total_rs"], t["total_ra"])
        sos_val = sos_map.get(tid, 0.5)
        adj_rs, adj_ra = adj_runs_map.get(tid, (0, 0))
        power = compute_power_rating(ppct, sos_val, t["elo"])

        conn.execute("""
            UPDATE teams SET
                pythag_pct = ?, sos = ?, adj_rs_per_game = ?,
                adj_ra_per_game = ?, power_rating = ?
            WHERE id = ?
        """, (ppct, sos_val, adj_rs, adj_ra, power, tid))
        updated += 1

    conn.commit()
    return updated
```

**Handling teams with <5 games played:** They are excluded from `compute_sos` and `update_all_ratings` queries via `WHERE games_played >= 5`. Their ratings remain at defaults (Elo 1500, no power rating). Predictions involving these teams get `confidence: "low"` and a note: "Insufficient data (<5 games)."

---

### Hour 6-10: Prediction Engine

#### `fsbb/models/predict.py`

```python
"""Win probability prediction and game prediction generation."""

from __future__ import annotations
import math
import sqlite3
from datetime import date, datetime, timezone


# ── Logistic Win Probability ────────────────────────────────────────

# Heuristic coefficients (fit from MLB literature, adjusted for college)
# β0: intercept (0 = no inherent home advantage beyond Elo's)
# β1: power rating difference coefficient
# β2: home advantage bonus (beyond what Elo captures)
# β3: SOS difference coefficient
BETA_0 = 0.0
BETA_1 = 0.15   # Each 1.0 power rating diff → ~15% probability shift
BETA_2 = 0.08   # Home field advantage residual
BETA_3 = 0.05   # SOS difference matters slightly

def sigmoid(x: float) -> float:
    """Numerically stable sigmoid."""
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    else:
        exp_x = math.exp(x)
        return exp_x / (1.0 + exp_x)


def win_probability(
    home_power: float,
    away_power: float,
    home_sos: float,
    away_sos: float,
) -> float:
    """Predicted home team win probability.

    P(home_win) = sigmoid(β0 + β1 × power_diff + β2 × home_adv + β3 × sos_diff)

    Args:
        home_power: Home team's power rating.
        away_power: Away team's power rating.
        home_sos: Home team's SOS.
        away_sos: Away team's SOS.

    Returns: Probability of home team winning (0.05 to 0.95, clamped).
    """
    power_diff = home_power - away_power
    sos_diff = home_sos - away_sos

    logit = BETA_0 + BETA_1 * power_diff + BETA_2 + BETA_3 * sos_diff
    prob = sigmoid(logit)

    # Clamp to prevent absurd predictions
    return max(0.05, min(0.95, prob))


def predicted_total_runs(
    home_adj_rs: float, home_adj_ra: float,
    away_adj_rs: float, away_adj_ra: float,
) -> float:
    """Predicted total combined runs.

    Rough estimate: average of (home offense vs away defense) and (away offense vs home defense).
    total = (home_adj_RS + away_adj_RA) / 2 + (away_adj_RS + home_adj_RA) / 2

    This double-counts slightly but gives a reasonable number.
    Better formula: total = home_adj_RS × (away_adj_RA / league_avg) + away_adj_RS × (home_adj_RA / league_avg)
    For V0 we use the simple average.
    """
    home_expected = (home_adj_rs + away_adj_ra) / 2.0
    away_expected = (away_adj_rs + home_adj_ra) / 2.0
    return round(home_expected + away_expected, 1)


def confidence_label(prob: float) -> str:
    """Convert win probability to confidence label.

    ≥ 0.65 or ≤ 0.35: high confidence
    0.55-0.65 or 0.35-0.45: moderate
    0.45-0.55: low (coin flip territory)
    """
    deviation = abs(prob - 0.5)
    if deviation >= 0.15:
        return "high"
    elif deviation >= 0.05:
        return "moderate"
    else:
        return "low"


# ── Generate Predictions ────────────────────────────────────────────

def generate_predictions(conn: sqlite3.Connection, game_date: date) -> list[dict]:
    """Generate predictions for all games on a given date.

    Returns list of prediction dicts ready for DB insertion and HTML rendering.
    """
    games = conn.execute("""
        SELECT g.id, g.date,
               h.id as home_id, h.name as home_name, h.power_rating as home_power,
               h.sos as home_sos, h.adj_rs_per_game as home_adj_rs,
               h.adj_ra_per_game as home_adj_ra, h.pear_net as pear_home_rank,
               a.id as away_id, a.name as away_name, a.power_rating as away_power,
               a.sos as away_sos, a.adj_rs_per_game as away_adj_rs,
               a.adj_ra_per_game as away_adj_ra, a.pear_net as pear_away_rank
        FROM games g
        JOIN teams h ON h.id = g.home_team_id
        JOIN teams a ON a.id = g.away_team_id
        WHERE g.date = ? AND g.status = 'scheduled'
    """, (game_date.isoformat(),)).fetchall()

    now = datetime.now(timezone.utc).isoformat()
    predictions = []

    for g in games:
        # Skip if either team has no power rating
        if g["home_power"] is None or g["away_power"] is None:
            continue

        home_wp = win_probability(
            g["home_power"], g["away_power"],
            g["home_sos"] or 0.5, g["away_sos"] or 0.5,
        )

        total = predicted_total_runs(
            g["home_adj_rs"] or 0, g["home_adj_ra"] or 0,
            g["away_adj_rs"] or 0, g["away_adj_ra"] or 0,
        )

        winner_id = g["home_id"] if home_wp >= 0.5 else g["away_id"]
        winner_name = g["home_name"] if home_wp >= 0.5 else g["away_name"]
        conf = confidence_label(home_wp)
        power_diff = (g["home_power"] or 0) - (g["away_power"] or 0)

        # PEAR implied pick: lower NET rank = better team
        pear_home = g["pear_home_rank"]
        pear_away = g["pear_away_rank"]
        pear_pick = None
        if pear_home and pear_away:
            pear_pick = g["home_name"] if pear_home < pear_away else g["away_name"]

        pred = {
            "game_id": g["id"],
            "predicted_at": now,
            "home_win_prob": round(home_wp, 3),
            "predicted_winner_id": winner_id,
            "predicted_winner": winner_name,
            "predicted_total_runs": total,
            "confidence": conf,
            "our_power_diff": round(power_diff, 2),
            "pear_home_rank": pear_home,
            "pear_away_rank": pear_away,
            "pear_pick": pear_pick,
            # Display fields
            "date": g["date"],
            "home_name": g["home_name"],
            "away_name": g["away_name"],
        }
        predictions.append(pred)

    # Sort by confidence (high first), then by power_diff (biggest mismatch first)
    predictions.sort(key=lambda p: (
        {"high": 0, "moderate": 1, "low": 2}[p["confidence"]],
        -abs(p["our_power_diff"]),
    ))

    return predictions


def save_predictions(conn: sqlite3.Connection, predictions: list[dict]) -> int:
    """Save predictions to the database. Returns count saved."""
    saved = 0
    for p in predictions:
        try:
            conn.execute("""
                INSERT INTO predictions (game_id, predicted_at, home_win_prob, predicted_winner_id,
                    predicted_total_runs, confidence, our_power_diff, pear_home_rank, pear_away_rank)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(game_id) DO UPDATE SET
                    home_win_prob = excluded.home_win_prob,
                    predicted_winner_id = excluded.predicted_winner_id,
                    predicted_total_runs = excluded.predicted_total_runs,
                    confidence = excluded.confidence,
                    our_power_diff = excluded.our_power_diff
            """, (p["game_id"], p["predicted_at"], p["home_win_prob"],
                  p["predicted_winner_id"], p["predicted_total_runs"],
                  p["confidence"], p["our_power_diff"],
                  p["pear_home_rank"], p["pear_away_rank"]))
            saved += 1
        except Exception:
            pass
    conn.commit()
    return saved


# ── Resolve Results ─────────────────────────────────────────────────

def resolve_predictions(conn: sqlite3.Connection) -> int:
    """Check completed games and mark predictions as correct/incorrect.

    Returns number of predictions resolved.
    """
    resolved = 0
    pending = conn.execute("""
        SELECT p.id, p.game_id, p.predicted_winner_id,
               g.home_team_id, g.away_team_id, g.home_runs, g.away_runs
        FROM predictions p
        JOIN games g ON g.id = p.game_id
        WHERE p.correct IS NULL AND g.status = 'final'
            AND g.home_runs IS NOT NULL AND g.away_runs IS NOT NULL
    """).fetchall()

    for p in pending:
        actual_winner_id = p["home_team_id"] if p["home_runs"] > p["away_runs"] else p["away_team_id"]
        correct = 1 if actual_winner_id == p["predicted_winner_id"] else 0

        conn.execute("""
            UPDATE predictions SET actual_winner_id = ?, correct = ? WHERE id = ?
        """, (actual_winner_id, correct, p["id"]))
        resolved += 1

    conn.commit()
    return resolved
```

---

### Hour 10-14: Output & Display

#### `fsbb/templates/predictions.html` (Jinja2 template)

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ForgeStream Baseball — Nightly Predictions</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
         max-width: 900px; margin: 0 auto; padding: 16px; background: #f8f9fa; color: #1a1a1a; }
  h1 { font-size: 1.5rem; margin-bottom: 4px; }
  .subtitle { color: #666; font-size: 0.9rem; margin-bottom: 16px; }
  .accuracy-box { background: #fff; border: 1px solid #ddd; border-radius: 8px;
                   padding: 16px; margin-bottom: 20px; display: flex; gap: 24px; flex-wrap: wrap; }
  .accuracy-box .stat { text-align: center; }
  .accuracy-box .stat .num { font-size: 2rem; font-weight: 700; }
  .accuracy-box .stat .label { font-size: 0.75rem; color: #666; text-transform: uppercase; }
  .green { color: #16a34a; }
  .red { color: #dc2626; }
  .amber { color: #d97706; }
  table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px;
          overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 24px; }
  th { background: #1e293b; color: #fff; padding: 10px 8px; text-align: left; font-size: 0.8rem;
       text-transform: uppercase; letter-spacing: 0.5px; }
  td { padding: 10px 8px; border-bottom: 1px solid #eee; font-size: 0.9rem; }
  tr:last-child td { border-bottom: none; }
  .conf-high { font-weight: 700; }
  .conf-moderate { font-weight: 500; }
  .conf-low { font-weight: 400; color: #999; }
  .result-correct { color: #16a34a; font-weight: 700; }
  .result-wrong { color: #dc2626; font-weight: 700; }
  .result-pending { color: #999; }
  .pear-col { color: #666; font-size: 0.8rem; }
  footer { text-align: center; color: #999; font-size: 0.75rem; padding: 16px 0; }
  @media (max-width: 600px) {
    td, th { padding: 6px 4px; font-size: 0.8rem; }
    .accuracy-box { flex-direction: column; gap: 12px; }
  }
</style>
</head>
<body>
<h1>ForgeStream Baseball</h1>
<p class="subtitle">NCAA DI Game Predictions &mdash; Updated {{ last_updated }}</p>

{% if accuracy is not none %}
<div class="accuracy-box">
  <div class="stat">
    <div class="num {% if accuracy >= 60 %}green{% elif accuracy >= 50 %}amber{% else %}red{% endif %}">{{ "%.1f"|format(accuracy) }}%</div>
    <div class="label">Our Accuracy</div>
  </div>
  <div class="stat">
    <div class="num">{{ total_resolved }}</div>
    <div class="label">Games Resolved</div>
  </div>
  <div class="stat">
    <div class="num">{{ total_correct }} / {{ total_resolved }}</div>
    <div class="label">Correct</div>
  </div>
  {% if pear_accuracy is not none %}
  <div class="stat">
    <div class="num {% if pear_accuracy < accuracy %}red{% else %}green{% endif %}">{{ "%.1f"|format(pear_accuracy) }}%</div>
    <div class="label">PEAR Implied</div>
  </div>
  {% endif %}
</div>
{% endif %}

{% for day in days %}
<h2 style="font-size:1.1rem; margin: 16px 0 8px;">{{ day.date }}</h2>
<table>
<thead>
<tr>
  <th>Matchup</th>
  <th>Our Pick</th>
  <th>Win %</th>
  <th>Runs</th>
  <th>PEAR</th>
  <th>Result</th>
</tr>
</thead>
<tbody>
{% for p in day.predictions %}
<tr>
  <td>{{ p.away_name }} @ {{ p.home_name }}</td>
  <td class="conf-{{ p.confidence }}">{{ p.predicted_winner }}</td>
  <td>{{ "%.0f"|format(p.home_win_prob * 100) }}%</td>
  <td>{{ p.predicted_total_runs if p.predicted_total_runs else "—" }}</td>
  <td class="pear-col">{{ p.pear_pick or "—" }} ({{ p.pear_away_rank or "?" }} vs {{ p.pear_home_rank or "?" }})</td>
  <td class="{% if p.correct == true %}result-correct{% elif p.correct == false %}result-wrong{% else %}result-pending{% endif %}">
    {% if p.correct == true %}&#10003;{% elif p.correct == false %}&#10007;{% else %}—{% endif %}
  </td>
</tr>
{% endfor %}
</tbody>
</table>
{% endfor %}

<footer>
  ForgeStream Baseball v0.1 &mdash; Powered by Pythagorean + Elo + SOS model
  <br>Data: stats.ncaa.org &amp; PEARatings.com &mdash; Not affiliated with NCAA
</footer>
</body>
</html>
```

#### HTML Generator — `fsbb/render.py`

```python
"""Generate static HTML predictions page."""

from datetime import date, timedelta
from pathlib import Path

from jinja2 import Template

from .db import get_db

TEMPLATE_PATH = Path(__file__).parent / "templates" / "predictions.html"
OUTPUT_PATH = Path("data/predictions.html")


def render_predictions_page(output_path: str | None = None) -> str:
    """Render the predictions HTML page.

    Includes: last 7 days of predictions + today's upcoming.
    Returns the output file path.
    """
    conn = get_db()
    out = Path(output_path or OUTPUT_PATH)

    # Get predictions from last 7 days + today
    start_date = (date.today() - timedelta(days=7)).isoformat()
    rows = conn.execute("""
        SELECT p.*, g.date as game_date, g.home_runs, g.away_runs, g.status,
               h.name as home_name, a.name as away_name,
               w.name as predicted_winner_name
        FROM predictions p
        JOIN games g ON g.id = p.game_id
        JOIN teams h ON h.id = g.home_team_id
        JOIN teams a ON a.id = g.away_team_id
        LEFT JOIN teams w ON w.id = p.predicted_winner_id
        WHERE g.date >= ?
        ORDER BY g.date DESC, p.confidence ASC, ABS(p.our_power_diff) DESC
    """, (start_date,)).fetchall()

    # Group by date
    days_map: dict[str, list] = {}
    for r in rows:
        d = r["game_date"]
        if d not in days_map:
            days_map[d] = []
        days_map[d].append({
            "home_name": r["home_name"],
            "away_name": r["away_name"],
            "predicted_winner": r["predicted_winner_name"],
            "home_win_prob": r["home_win_prob"],
            "predicted_total_runs": r["predicted_total_runs"],
            "confidence": r["confidence"],
            "pear_pick": None,  # TODO: compute from pear ranks
            "pear_home_rank": r["pear_home_rank"],
            "pear_away_rank": r["pear_away_rank"],
            "correct": True if r["correct"] == 1 else (False if r["correct"] == 0 else None),
        })

    days = [{"date": d, "predictions": preds} for d, preds in sorted(days_map.items(), reverse=True)]

    # Overall accuracy
    accuracy_rows = conn.execute("""
        SELECT correct FROM predictions WHERE correct IS NOT NULL
    """).fetchall()
    total_resolved = len(accuracy_rows)
    total_correct = sum(1 for r in accuracy_rows if r["correct"] == 1)
    accuracy = (total_correct / total_resolved * 100) if total_resolved >= 3 else None

    # PEAR accuracy (how often the lower-ranked PEAR team won)
    pear_rows = conn.execute("""
        SELECT p.pear_home_rank, p.pear_away_rank, g.home_team_id, g.away_team_id,
               g.home_runs, g.away_runs
        FROM predictions p
        JOIN games g ON g.id = p.game_id
        WHERE p.correct IS NOT NULL AND p.pear_home_rank IS NOT NULL AND p.pear_away_rank IS NOT NULL
    """).fetchall()
    pear_correct = 0
    for pr in pear_rows:
        pear_pick_id = pr["home_team_id"] if pr["pear_home_rank"] < pr["pear_away_rank"] else pr["away_team_id"]
        actual_winner = pr["home_team_id"] if (pr["home_runs"] or 0) > (pr["away_runs"] or 0) else pr["away_team_id"]
        if pear_pick_id == actual_winner:
            pear_correct += 1
    pear_accuracy = (pear_correct / len(pear_rows) * 100) if len(pear_rows) >= 3 else None

    # Render
    template = Template(TEMPLATE_PATH.read_text())
    html = template.render(
        days=days,
        last_updated=date.today().isoformat(),
        accuracy=accuracy,
        total_resolved=total_resolved,
        total_correct=total_correct,
        pear_accuracy=pear_accuracy,
    )

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)
    conn.close()
    return str(out)
```

---

### Hour 14-18: CLI, Automation, and PEAR Comparison

#### CLI Entry Point — `fsbb/__main__.py`

```python
"""CLI entry point for ForgeStream Baseball."""

import asyncio
from datetime import date, timedelta

import click

from .db import get_db, init_db


@click.group()
def cli():
    """ForgeStream Baseball — NCAA DI predictions."""
    pass


@cli.command()
def setup():
    """Initialize database and import PEAR data."""
    init_db()
    click.echo("Database initialized.")

    from .scraper.pear import import_pear_ratings, import_pear_team_games
    conn = get_db()
    n_teams = import_pear_ratings(conn)
    click.echo(f"Imported {n_teams} teams from PEAR.")

    n_games = import_pear_team_games(conn)
    click.echo(f"Imported {n_games} games from PEAR team files.")
    conn.close()


@cli.command()
def rate():
    """Recompute all team ratings."""
    from .models.ratings import update_all_ratings
    conn = get_db()
    n = update_all_ratings(conn)
    click.echo(f"Updated ratings for {n} teams.")
    conn.close()


@cli.command()
@click.option("--date", "game_date", default=None, help="Date to scrape (YYYY-MM-DD). Default: today.")
def scrape(game_date: str | None):
    """Scrape NCAA games for a date."""
    from .scraper.ncaa import scrape_date_range
    from .scraper.clean import normalize_team_name

    target = date.fromisoformat(game_date) if game_date else date.today()
    games = asyncio.run(scrape_date_range(target, target))
    click.echo(f"Found {len(games)} games for {target}.")

    conn = get_db()
    inserted = 0
    for g in games:
        home = normalize_team_name(g.home_team)
        away = normalize_team_name(g.away_team)
        try:
            conn.execute("""
                INSERT INTO games (date, home_team_id, away_team_id, home_runs, away_runs, status, source, scraped_at)
                SELECT ?, h.id, a.id, ?, ?, ?, 'ncaa', datetime('now')
                FROM teams h, teams a WHERE h.name = ? AND a.name = ?
                ON CONFLICT(date, home_team_id, away_team_id) DO UPDATE SET
                    home_runs = COALESCE(excluded.home_runs, games.home_runs),
                    away_runs = COALESCE(excluded.away_runs, games.away_runs),
                    status = CASE WHEN excluded.status = 'final' THEN 'final' ELSE games.status END
            """, (target.isoformat(), g.home_runs, g.away_runs, g.status, home, away))
            inserted += 1
        except Exception:
            pass
    conn.commit()
    click.echo(f"Inserted/updated {inserted} games.")
    conn.close()


@cli.command()
@click.option("--date", "game_date", default=None, help="Date to predict. Default: today.")
def predict(game_date: str | None):
    """Generate predictions for a date's games."""
    from .models.predict import generate_predictions, save_predictions

    target = date.fromisoformat(game_date) if game_date else date.today()
    conn = get_db()
    preds = generate_predictions(conn, target)
    saved = save_predictions(conn, preds)
    click.echo(f"Generated {len(preds)} predictions, saved {saved}.")

    for p in preds[:10]:  # Show top 10
        prob_display = f"{p['home_win_prob']*100:.0f}%"
        click.echo(f"  {p['away_name']:20s} @ {p['home_name']:20s}  →  {p['predicted_winner']:20s} ({prob_display}, {p['confidence']})")
    conn.close()


@cli.command()
def resolve():
    """Resolve pending predictions against actual results."""
    from .models.predict import resolve_predictions
    conn = get_db()
    n = resolve_predictions(conn)
    click.echo(f"Resolved {n} predictions.")
    conn.close()


@cli.command()
def render():
    """Generate the HTML predictions page."""
    from .render import render_predictions_page
    path = render_predictions_page()
    click.echo(f"HTML page written to {path}")


@cli.command()
def daily():
    """Full daily cycle: scrape yesterday → resolve → scrape today → rate → predict → render."""
    from .models.predict import generate_predictions, save_predictions, resolve_predictions
    from .models.ratings import update_all_ratings
    from .render import render_predictions_page
    from .scraper.ncaa import scrape_date_range
    from .scraper.clean import normalize_team_name

    conn = get_db()
    yesterday = date.today() - timedelta(days=1)
    today = date.today()

    # 1. Scrape yesterday's results
    click.echo(f"Scraping results for {yesterday}...")
    results = asyncio.run(scrape_date_range(yesterday, yesterday))
    for g in results:
        home = normalize_team_name(g.home_team)
        away = normalize_team_name(g.away_team)
        try:
            conn.execute("""
                INSERT INTO games (date, home_team_id, away_team_id, home_runs, away_runs, status, source, scraped_at)
                SELECT ?, h.id, a.id, ?, ?, ?, 'ncaa', datetime('now')
                FROM teams h, teams a WHERE h.name = ? AND a.name = ?
                ON CONFLICT(date, home_team_id, away_team_id) DO UPDATE SET
                    home_runs = COALESCE(excluded.home_runs, games.home_runs),
                    away_runs = COALESCE(excluded.away_runs, games.away_runs),
                    status = CASE WHEN excluded.status = 'final' THEN 'final' ELSE games.status END
            """, (yesterday.isoformat(), g.home_runs, g.away_runs, g.status, home, away))
        except Exception:
            pass
    conn.commit()
    click.echo(f"  {len(results)} games scraped.")

    # 2. Resolve yesterday's predictions
    n_resolved = resolve_predictions(conn)
    click.echo(f"  {n_resolved} predictions resolved.")

    # 3. Update ratings
    n_rated = update_all_ratings(conn)
    click.echo(f"  {n_rated} teams re-rated.")

    # 4. Scrape today's schedule
    click.echo(f"Scraping schedule for {today}...")
    schedule = asyncio.run(scrape_date_range(today, today))
    for g in schedule:
        home = normalize_team_name(g.home_team)
        away = normalize_team_name(g.away_team)
        try:
            conn.execute("""
                INSERT INTO games (date, home_team_id, away_team_id, status, source, scraped_at)
                SELECT ?, h.id, a.id, 'scheduled', 'ncaa', datetime('now')
                FROM teams h, teams a WHERE h.name = ? AND a.name = ?
                ON CONFLICT(date, home_team_id, away_team_id) DO NOTHING
            """, (today.isoformat(), home, away))
        except Exception:
            pass
    conn.commit()
    click.echo(f"  {len(schedule)} games scheduled.")

    # 5. Predict
    preds = generate_predictions(conn, today)
    saved = save_predictions(conn, preds)
    click.echo(f"  {len(preds)} predictions generated.")

    # 6. Render HTML
    path = render_predictions_page()
    click.echo(f"  HTML: {path}")

    conn.close()
    click.echo("Daily cycle complete.")


@cli.command()
def accuracy():
    """Show running accuracy statistics."""
    conn = get_db()
    rows = conn.execute("""
        SELECT correct, confidence FROM predictions WHERE correct IS NOT NULL
    """).fetchall()

    total = len(rows)
    correct = sum(1 for r in rows if r["correct"] == 1)

    if total == 0:
        click.echo("No resolved predictions yet.")
        return

    click.echo(f"Overall: {correct}/{total} ({correct/total*100:.1f}%)")

    for conf in ["high", "moderate", "low"]:
        subset = [r for r in rows if r["confidence"] == conf]
        if subset:
            c = sum(1 for r in subset if r["correct"] == 1)
            click.echo(f"  {conf:10s}: {c}/{len(subset)} ({c/len(subset)*100:.1f}%)")

    conn.close()


if __name__ == "__main__":
    cli()
```

#### Daily Automation — Cron

```bash
# Add to crontab: crontab -e

# 06:00 UTC — Scrape yesterday's results, resolve, update ratings
# 14:00 UTC — Scrape today's schedule, predict, render HTML
0 6 * * * cd /path/to/forgestream && uv run python -m fsbb daily >> data/fsbb_cron.log 2>&1
```

Or use GitHub Actions (`.github/workflows/daily.yml`):

```yaml
name: Daily Predictions
on:
  schedule:
    - cron: '0 14 * * *'   # 14:00 UTC
  workflow_dispatch: {}
jobs:
  predict:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: uv run python -m fsbb daily
      - run: |
          git config user.name "fsbb-bot"
          git config user.email "bot@forgestream.ai"
          git add data/predictions.html data/fsbb.db
          git commit -m "Update predictions $(date +%Y-%m-%d)" || true
          git push
```

---

### V0 Deliverable Checklist

```
[x] fsbb/db.py — SQLite schema (teams, games, predictions)
[x] fsbb/schemas.py — Pydantic models (NcaaGame, Prediction, Team)
[x] fsbb/scraper/pear.py — Import PEAR ratings + games from JSON
[x] fsbb/scraper/ncaa.py — NCAA API scraper (henrygd/ncaa-api)
[x] fsbb/scraper/clean.py — Entity resolution + fuzzy matching
[x] fsbb/models/ratings.py — Pythagorean, SOS, Elo, adjusted runs, power rating
[x] fsbb/models/predict.py — Logistic win probability, total runs, confidence
[x] fsbb/render.py — Jinja2 HTML page generator
[x] fsbb/templates/predictions.html — Mobile-responsive static page
[x] fsbb/__main__.py — CLI (setup, rate, scrape, predict, resolve, render, daily, accuracy)
[x] Cron / GitHub Actions for daily automation
[x] PEAR comparison column in predictions table
[x] Running accuracy tracker (after 3+ resolved predictions)
```

---

## V1: Full Model — Component Specifications

### V1.1: Bayesian Prior-Posterior Update (20-30 hours)

#### Mathematical Specification

**Model:** Conjugate Normal-Normal.

```
Prior:      θ ~ N(μ_prior, σ²_prior)
Likelihood: each game result x_i ~ N(θ, σ²_obs)
Posterior:  θ | x_1,...,x_n ~ N(μ_post, σ²_post)

Where:
  μ_prior = last_season_power_rating × decay + transfer_adjustment
  σ²_prior = (1.5)² for returning teams, (3.0)² for teams with major transfers
  σ²_obs = (2.0)² (game-to-game variance in run differential)

Conjugate update:
  precision_prior = 1 / σ²_prior
  precision_obs = n / σ²_obs
  precision_post = precision_prior + precision_obs
  σ²_post = 1 / precision_post
  μ_post = (precision_prior × μ_prior + precision_obs × x̄) / precision_post

Where x̄ = mean(observed_run_differentials)
```

**95% credible interval on rank:** Sample from posterior N(μ_post, σ²_post) 1000 times. For each sample, compute rank among all teams' samples. CI = [rank_025, rank_975].

#### Interface

```python
# fsbb/models/bayesian.py

class BayesianRater:
    """Bayesian team rating with conjugate normal-normal updates."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def set_prior(self, team_id: int, mu: float, sigma: float) -> None:
        """Set prior for a team (from last season or expert input)."""

    def update(self, team_id: int, run_differential: float) -> tuple[float, float, tuple[int, int]]:
        """Update posterior with a new game result.

        Args:
            team_id: Team database ID.
            run_differential: (RS - RA) for this game.

        Returns: (posterior_mean, posterior_std, rank_ci_95)
        """

    def get_rating(self, team_id: int) -> tuple[float, float]:
        """Get current posterior (mean, std) for a team."""

    def rank_all(self) -> list[tuple[int, float, float, int, int]]:
        """Rank all teams by posterior mean.

        Returns: [(team_id, mu_post, sigma_post, rank_ci_lower, rank_ci_upper), ...]
        """
```

#### Dependencies

None beyond stdlib. The conjugate update is ~15 lines of math. Rank CI sampling uses `random.gauss`.

#### What it changes about the prediction

- Every prediction includes: "UCLA 62% **± 8%** to win" (CI from posterior uncertainty)
- Early-season predictions are wide: "Texas 58% ± 14%" (honest about limited data)
- Late-season predictions tighten: "Texas 63% ± 5%" (more data, more confidence)
- Rankings include CI: "UCLA ranked #1 (95% CI: #1-#3)"

---

### V1.2: Starting Pitcher Adjustment (30-40 hours)

#### Data Requirement

Identify starting pitcher per game from box score: **the pitcher with the most IP** in that game. NCAA box scores list all pitchers who appeared; the starter is typically listed first with the most IP.

Sources:
- `stats.ncaa.org` game detail pages → pitching lines
- PEAR per-team files may include pitcher stats (check `data/pear/teams/team_*.json`)
- `henrygd/ncaa-api` game detail endpoint (if available)

#### Pitcher Rating

```python
# fsbb/models/pitcher.py

class PitcherRating(BaseModel):
    name: str
    team_id: int
    games_started: int
    innings_pitched: float
    era: float
    whip: float
    k_per_9: float
    bb_per_9: float
    adj_era: float            # SOS-adjusted ERA
    runs_above_avg: float     # Runs saved vs league-avg starter (per start)

def pitcher_adjustment_factor(
    home_pitcher: PitcherRating | None,
    away_pitcher: PitcherRating | None,
    league_avg_era: float,
) -> float:
    """Compute game win probability shift from starting pitchers.

    Adjustment:
      1. Compute each pitcher's RAA (runs above average) per start
         RAA = (league_avg_ERA - pitcher_adj_ERA) × (IP/start) / 9
      2. Compute RAA differential = home_RAA - away_RAA
      3. Convert to probability shift: each 1.0 RAA diff ≈ 9% win prob shift

    Returns: additive shift to home_win_prob (positive = home pitcher better).
    """
    if home_pitcher is None or away_pitcher is None:
        return 0.0  # No adjustment without pitcher data

    # Bayesian shrinkage: weight toward league average when few starts
    def shrink(era: float, starts: int, league_avg: float) -> float:
        weight = min(starts / 15.0, 1.0)
        return weight * era + (1 - weight) * league_avg

    home_era = shrink(home_pitcher.adj_era, home_pitcher.games_started, league_avg_era)
    away_era = shrink(away_pitcher.adj_era, away_pitcher.games_started, league_avg_era)

    # RAA per start (assuming ~5.5 IP per college start)
    ip_per_start = 5.5
    home_raa = (league_avg_era - home_era) * ip_per_start / 9.0
    away_raa = (league_avg_era - away_era) * ip_per_start / 9.0

    raa_diff = home_raa - away_raa
    return raa_diff * 0.09  # ~9% per 1.0 RAA difference
```

#### The Killer Feature Display

```
PEAR says:    Texas 55% to win (same for all 3 games in the series)
Our model:    Game 1 (Friday):  Texas 68% — their ace (2.10 ERA) vs Stanford #3 (5.40)
              Game 2 (Saturday): Texas 52% — #2 starter vs #2 starter (comparable)
              Game 3 (Sunday):   Stanford 54% — Texas bullpen day vs Stanford's ace
```

---

### V1.3: RL Self-Learning Agent (60-80 hours)

#### Architecture

**Contextual bandit** (simpler than PPO, sufficient for V1):

```python
# fsbb/models/rl_agent.py

class PredictionAgent:
    """Self-learning prediction agent using contextual bandit with linear Thompson Sampling.

    State (6 features):
      [power_diff, home_adv, pitcher_quality_diff, sos_diff, recent_form_diff, rest_days_diff]

    Action: predicted win probability (continuous 0-1)

    Reward: negative Brier score → -((predicted_prob - actual_outcome)²)
      actual_outcome: 1.0 (home win) or 0.0 (away win)

    Update: after each day's results, update linear weights via Bayesian ridge regression.
    """

    def __init__(self, n_features: int = 6):
        self.n_features = n_features
        self.mu = [0.0] * n_features      # Weight means
        self.sigma = [1.0] * n_features   # Weight uncertainties
        self.history: list[tuple] = []     # (features, outcome) pairs

    def predict(self, features: list[float]) -> float:
        """Thompson Sampling: sample weights from posterior, compute prediction."""
        import random
        sampled_weights = [random.gauss(m, s) for m, s in zip(self.mu, self.sigma)]
        logit = sum(w * f for w, f in zip(sampled_weights, features))
        return 1.0 / (1.0 + math.exp(-logit))

    def update(self, features: list[float], outcome: float) -> None:
        """Update weights after observing game outcome.

        Uses online Bayesian linear regression update.
        """
        self.history.append((features, outcome))
        # Re-fit weights from full history (simple for V1)
        if len(self.history) >= 20:
            self._refit()

    def _refit(self) -> None:
        """Bayesian ridge regression on accumulated history."""
        from scipy.optimize import minimize
        # ... (fit weights to minimize Brier score)

    def save(self, path: str) -> None: ...
    def load(self, path: str) -> None: ...
```

#### The Moat

By tournament time (late May), the agent has trained on 3+ months of daily predictions and outcomes. It has learned which features matter in which contexts. A competitor starting in May has zero training data. The agent's Brier score should improve measurably from March → May.

---

### V1.4: Monte Carlo Game Simulation (20-30 hours)

#### Interface

```python
# fsbb/models/simulate.py

class GameSimulator:
    """Monte Carlo game simulation using team-specific run distributions."""

    def simulate(
        self,
        home: TeamRating,
        away: TeamRating,
        home_pitcher: PitcherRating | None = None,
        away_pitcher: PitcherRating | None = None,
        n_sims: int = 10_000,
    ) -> SimulationResult:
        """Simulate n games.

        Per simulation:
          1. home_runs ~ NegBinomial(mean=adj_rs × pitcher_factor, r=overdispersion)
          2. away_runs ~ NegBinomial(mean=adj_rs × pitcher_factor, r=overdispersion)
          3. If tied after 9: extra innings via geometric(p=0.45) runs per half-inning
          4. Record: winner, margin, total_runs

        Returns SimulationResult with distributions.
        """

class SimulationResult(BaseModel):
    home_win_pct: float           # From simulations
    expected_home_runs: float
    expected_away_runs: float
    expected_total: float
    total_runs_ci_90: tuple[float, float]  # 5th and 95th percentile
    margin_ci_90: tuple[float, float]
    extra_innings_pct: float      # % of sims that went extras
    n_sims: int
```

#### The "Wow Factor" Display

```
We simulated Texas vs UCLA 10,000 times:
  UCLA wins 62.3% of simulations
  Expected score: UCLA 5.2 — Texas 3.8
  Total runs: 9.0 (90% CI: 4-15)
  Extra innings: 8.7% of simulations
  UCLA wins by 3+: 31.2% | Texas upset: 37.7%
```

---

## Dependencies Summary

### V0 (install now)

```
httpx>=0.27        # HTTP client for NCAA API
pydantic>=2.0      # Data validation
click>=8.1         # CLI
tabulate>=0.9      # Terminal tables
jinja2>=3.1        # HTML templating
```

### V1 additions

```
scipy>=1.14        # Bayesian ridge regression, optimization
playwright>=1.45   # [optional] PEAR JS scraping
```

### File tree (complete)

```
fsbb/
├── __init__.py
├── __main__.py           # CLI: setup, rate, scrape, predict, resolve, render, daily, accuracy
├── db.py                 # SQLite connection + schema
├── schemas.py            # Pydantic models
├── render.py             # Jinja2 HTML generator
├── scraper/
│   ├── __init__.py
│   ├── ncaa.py           # NCAA API scraper
│   ├── pear.py           # PEAR JSON importer
│   └── clean.py          # Entity resolution
├── models/
│   ├── __init__.py
│   ├── ratings.py        # Pythagorean, SOS, Elo, adjusted runs, power rating
│   ├── predict.py        # Logistic win probability, total runs
│   ├── bayesian.py       # [V1.1] Bayesian prior-posterior
│   ├── pitcher.py        # [V1.2] Starting pitcher adjustment
│   ├── rl_agent.py       # [V1.3] Self-learning contextual bandit
│   └── simulate.py       # [V1.4] Monte Carlo game simulation
└── templates/
    └── predictions.html  # Static HTML template
```

### First-run sequence

```bash
cd /path/to/forgestream
uv add httpx pydantic click tabulate jinja2

# 1. Initialize database + import PEAR
uv run python -m fsbb setup
# → "Imported 308 teams from PEAR."
# → "Imported ~3000 games from PEAR team files."

# 2. Compute ratings
uv run python -m fsbb rate
# → "Updated ratings for 280 teams."  (teams with ≥5 games)

# 3. Predict today's games
uv run python -m fsbb predict
# → Shows top 10 predictions

# 4. Generate HTML
uv run python -m fsbb render
# → "HTML page written to data/predictions.html"

# 5. Open in browser
open data/predictions.html
```
