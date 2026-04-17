"""D1 Baseball CSV importer — WAR, DRS, and Synergy plate discipline data.

Data is extracted from d1baseball.com via browser console scripts
(site is Cloudflare-protected, no programmatic access possible).

Console scripts output CSV files which this module imports into the database.

Expected CSV files (in data/d1baseball/):
    d1baseball_war_{season}.csv     — WAR leaderboard
    d1baseball_drs_{season}.csv     — DRS leaderboard (14 components)
    d1baseball_synergy_{season}.csv — Synergy plate discipline by pitch type
"""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "d1baseball"


def _resolve_team(conn: sqlite3.Connection, team_name: str) -> int | None:
    """Resolve D1 Baseball team name to our team ID."""
    if not team_name or not team_name.strip():
        return None
    team_name = team_name.strip()

    row = conn.execute("SELECT id FROM teams WHERE name=?", (team_name,)).fetchone()
    if row:
        return row[0]

    alias = conn.execute(
        "SELECT team_id FROM team_aliases WHERE alias=?", (team_name,)
    ).fetchone()
    if alias:
        return alias[0]

    # Common D1Baseball → PEAR name differences
    for variant in [
        team_name.replace("State", "St."),
        team_name.replace("St.", "State"),
        team_name.replace(" St", " St.") if team_name.endswith(" St") else None,
    ]:
        if variant is None:
            continue
        row = conn.execute("SELECT id FROM teams WHERE name=?", (variant.strip(),)).fetchone()
        if row:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO team_aliases (alias, team_id) VALUES (?, ?)",
                    (team_name, row[0]),
                )
                conn.commit()
            except sqlite3.OperationalError:
                pass
            return row[0]

    return None


def _safe_float(val: str | None) -> float | None:
    """Convert string to float, handling empty/invalid values."""
    if not val or val.strip() in ("", "-", "N/A", "nan", "—"):
        return None
    try:
        return float(val.replace("%", "").strip())
    except ValueError:
        return None


def _safe_int(val: str | None) -> int | None:
    if not val or val.strip() in ("", "-", "N/A", "—"):
        return None
    try:
        return int(float(val.strip()))
    except ValueError:
        return None


def import_war(conn: sqlite3.Connection, season: int = 2026) -> int:
    """Import WAR leaderboard CSV.

    Expected columns: Player, Team, Position, oRAR, oWAR, DRS, dWAR, pRAR, pWAR, WAR
    """
    path = DATA_DIR / f"d1baseball_war_{season}.csv"
    if not path.exists():
        return 0

    count = 0
    with open(path) as f:
        for row in csv.DictReader(f):
            player = row.get("Player", "").strip()
            team = row.get("Team", "").strip()
            if not player or not team:
                continue

            team_id = _resolve_team(conn, team)

            conn.execute("""
                INSERT INTO player_war
                    (player_name, team_name, position, season,
                     orar, owar, drs, dwar, prar, pwar, war, team_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(player_name, team_name, season) DO UPDATE SET
                    position=excluded.position,
                    orar=excluded.orar, owar=excluded.owar,
                    drs=excluded.drs, dwar=excluded.dwar,
                    prar=excluded.prar, pwar=excluded.pwar,
                    war=excluded.war, team_id=excluded.team_id,
                    updated_at=datetime('now')
            """, (
                player, team, row.get("Position", "").strip(), season,
                _safe_float(row.get("oRAR")), _safe_float(row.get("oWAR")),
                _safe_float(row.get("DRS")), _safe_float(row.get("dWAR")),
                _safe_float(row.get("pRAR")), _safe_float(row.get("pWAR")),
                _safe_float(row.get("WAR")),
                team_id,
            ))
            count += 1

    conn.commit()
    return count


def import_drs(conn: sqlite3.Connection, season: int = 2026) -> int:
    """Import DRS leaderboard CSV with 14 defensive components.

    Expected columns: Player, Team, Position, DRS, Framing Runs Saved,
    Pitches Framed, Stolen Base Runs, Pickoff Runs, Throwing Runs,
    INF GB Runs, DP Runs Start, DP Runs Pivot, IFFB Runs, Bunt Runs,
    OF FlyBall Runs, OF Arm Runs, Blocking Runs
    """
    path = DATA_DIR / f"d1baseball_drs_{season}.csv"
    if not path.exists():
        return 0

    count = 0
    with open(path) as f:
        for row in csv.DictReader(f):
            player = row.get("Player", "").strip()
            team = row.get("Team", "").strip()
            if not player or not team:
                continue

            team_id = _resolve_team(conn, team)

            conn.execute("""
                INSERT INTO player_drs
                    (player_name, team_name, position, season, drs,
                     framing_runs, pitches_framed, blocking_runs,
                     sb_runs, pickoff_runs,
                     throwing_runs, inf_gb_runs, dp_runs_start, dp_runs_pivot,
                     iffb_runs, bunt_runs,
                     of_flyball_runs, of_arm_runs,
                     team_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(player_name, team_name, season) DO UPDATE SET
                    position=excluded.position, drs=excluded.drs,
                    framing_runs=excluded.framing_runs,
                    pitches_framed=excluded.pitches_framed,
                    blocking_runs=excluded.blocking_runs,
                    sb_runs=excluded.sb_runs, pickoff_runs=excluded.pickoff_runs,
                    throwing_runs=excluded.throwing_runs,
                    inf_gb_runs=excluded.inf_gb_runs,
                    dp_runs_start=excluded.dp_runs_start,
                    dp_runs_pivot=excluded.dp_runs_pivot,
                    iffb_runs=excluded.iffb_runs, bunt_runs=excluded.bunt_runs,
                    of_flyball_runs=excluded.of_flyball_runs,
                    of_arm_runs=excluded.of_arm_runs,
                    team_id=excluded.team_id,
                    updated_at=datetime('now')
            """, (
                player, team, row.get("Position", "").strip(), season,
                _safe_float(row.get("DRS")),
                _safe_float(row.get("FramingRuns Saved") or row.get("Framing Runs Saved")),
                _safe_int(row.get("PitchesFramed") or row.get("Pitches Framed")),
                _safe_float(row.get("BlockingRuns") or row.get("Blocking Runs")),
                _safe_float(row.get("StolenBase Runs") or row.get("Stolen Base Runs")),
                _safe_float(row.get("PickoffRuns") or row.get("Pickoff Runs")),
                _safe_float(row.get("ThrowingRuns") or row.get("Throwing Runs")),
                _safe_float(row.get("INF GBRuns") or row.get("INF GB Runs")),
                _safe_float(row.get("DP RunsStart") or row.get("DP Runs Start")),
                _safe_float(row.get("DP RunsPivot") or row.get("DP Runs Pivot")),
                _safe_float(row.get("IFFBRuns") or row.get("IFFB Runs")),
                _safe_float(row.get("BuntRuns") or row.get("Bunt Runs")),
                _safe_float(row.get("OF FlyBallRuns") or row.get("OF FlyBall Runs")),
                _safe_float(row.get("OF ArmRuns") or row.get("OF Arm Runs")),
                team_id,
            ))
            count += 1

    conn.commit()
    return count


def import_synergy(conn: sqlite3.Connection, season: int = 2026) -> int:
    """Import Synergy plate discipline CSV.

    Expected columns: Player, Team, Season, Type, PitchType, Metric, Value, Rank
    """
    path = DATA_DIR / f"d1baseball_synergy_{season}.csv"
    if not path.exists():
        return 0

    count = 0
    with open(path) as f:
        for row in csv.DictReader(f):
            player = row.get("Player", "").strip()
            team = row.get("Team", "").strip()
            if not player or not team:
                continue

            team_id = _resolve_team(conn, team)

            conn.execute("""
                INSERT INTO player_synergy
                    (player_name, team_name, season, stat_type, pitch_type,
                     metric_name, metric_value, rank, team_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(player_name, team_name, season, stat_type, pitch_type, metric_name)
                DO UPDATE SET
                    metric_value=excluded.metric_value,
                    rank=excluded.rank,
                    team_id=excluded.team_id,
                    updated_at=datetime('now')
            """, (
                player, team, season,
                row.get("Type", "").strip(),
                row.get("PitchType", "").strip(),
                row.get("Metric", "").strip(),
                _safe_float(row.get("Value")),
                _safe_int(row.get("Rank")),
                team_id,
            ))
            count += 1

    conn.commit()
    return count


def import_all(conn: sqlite3.Connection, season: int = 2026) -> dict:
    """Import all D1 Baseball data for a season."""
    war = import_war(conn, season)
    drs = import_drs(conn, season)
    synergy = import_synergy(conn, season)
    return {"war": war, "drs": drs, "synergy": synergy}
