"""64 Analytics CSV importer.

Imports team rankings, pitching stats, hitting stats from 64 Analytics CSV exports.
Key metrics: wRAE (pitcher quality), wRCE (hitter quality), FIP, xFIP, BABIP, LOB%.
"""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent.parent / "data" / "64analytics"


def _resolve_school(conn: sqlite3.Connection, school: str) -> int | None:
    """Resolve 64 Analytics school name to our team ID."""
    # Direct match
    row = conn.execute("SELECT id FROM teams WHERE name=?", (school,)).fetchone()
    if row:
        return row[0]

    # Alias
    alias = conn.execute(
        "SELECT team_id FROM team_aliases WHERE alias=?", (school,)
    ).fetchone()
    if alias:
        return alias[0]

    # Common 64 Analytics → PEAR name differences
    mappings = {
        "North Carolina": "North Carolina",
        "UNC": "North Carolina",
        "USC": "Southern California",
        "Mississippi State": "Mississippi St.",
        "Oregon State": "Oregon St.",
        "Florida State": "Florida St.",
        "Arizona State": "Arizona St.",
        "Michigan State": "Michigan St.",
        "Washington State": "Washington St.",
        "Fresno State": "Fresno St.",
        "San Diego State": "San Diego St.",
        "Boise State": "Boise St.",
        "Long Beach State": "Long Beach St.",
        "Sacramento State": "Sacramento St.",
    }
    mapped = mappings.get(school)
    if mapped:
        row = conn.execute("SELECT id FROM teams WHERE name=?", (mapped,)).fetchone()
        if row:
            return row[0]

    # Fuzzy: try adding/removing "St." / "State"
    for variant in [
        school.replace("State", "St."),
        school.replace("St.", "State"),
        school.replace(" University", ""),
    ]:
        row = conn.execute("SELECT id FROM teams WHERE name=?", (variant.strip(),)).fetchone()
        if row:
            return row[0]

    return None


def _safe_float(val: str | None) -> float | None:
    """Convert string to float, handling empty/invalid values."""
    if not val or val.strip() in ("", "-", "N/A", "nan"):
        return None
    try:
        return float(val.replace("%", ""))
    except ValueError:
        return None


def _safe_int(val: str | None) -> int | None:
    if not val or val.strip() in ("", "-"):
        return None
    try:
        return int(float(val))
    except ValueError:
        return None


def import_team_rankings(conn: sqlite3.Connection) -> int:
    """Import 64analytics_team_rankings_2026.csv."""
    path = DATA_DIR / "64analytics_team_rankings_2026.csv"
    if not path.exists():
        return 0

    count = 0
    with open(path) as f:
        for row in csv.DictReader(f):
            school = row.get("School", "").strip()
            team_id = _resolve_school(conn, school)
            if not team_id:
                continue

            conn.execute("""
                INSERT INTO analytics_team (team_id, rank_overall,
                    team_p_ops, team_whip, team_fip, team_ops, team_woba, team_r_per_pa)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(team_id) DO UPDATE SET
                    rank_overall=excluded.rank_overall,
                    team_p_ops=excluded.team_p_ops, team_whip=excluded.team_whip,
                    team_fip=excluded.team_fip, team_ops=excluded.team_ops,
                    team_woba=excluded.team_woba, team_r_per_pa=excluded.team_r_per_pa,
                    updated_at=datetime('now')
            """, (
                team_id, _safe_int(row.get("Team Rk", "")),
                _safe_float(row.get("P-OPS")), _safe_float(row.get("WHIP")),
                _safe_float(row.get("FIP")), _safe_float(row.get("OPS")),
                _safe_float(row.get("wOBA")), _safe_float(row.get("R/PA")),
            ))
            count += 1

    conn.commit()
    return count


def import_team_pitching(conn: sqlite3.Connection) -> int:
    """Import 64analytics_team_pitching_2026.csv."""
    path = DATA_DIR / "64analytics_team_pitching_2026.csv"
    if not path.exists():
        return 0

    count = 0
    with open(path) as f:
        for row in csv.DictReader(f):
            school = row.get("School", "").strip()
            team_id = _resolve_school(conn, school)
            if not team_id:
                continue

            conn.execute("""
                UPDATE analytics_team SET
                    team_era=?, team_fip=COALESCE(?, team_fip),
                    team_xfip=?, team_whip=COALESCE(?, team_whip),
                    team_p_babip=?, team_p_lob_pct=?,
                    team_k9=?, team_bb9=?,
                    team_wrae=?,
                    updated_at=datetime('now')
                WHERE team_id=?
            """, (
                _safe_float(row.get("ERA")), _safe_float(row.get("FIP")),
                _safe_float(row.get("xFIP")), _safe_float(row.get("WHIP")),
                _safe_float(row.get("P-BABIP")), _safe_float(row.get("LOB%")),
                _safe_float(row.get("K/9")), _safe_float(row.get("BB/9")),
                _safe_float(row.get("wRAE")),
                team_id,
            ))
            count += 1

    conn.commit()
    return count


def import_team_hitting(conn: sqlite3.Connection) -> int:
    """Import 64analytics_team_hitting_2026.csv."""
    path = DATA_DIR / "64analytics_team_hitting_2026.csv"
    if not path.exists():
        return 0

    count = 0
    with open(path) as f:
        for row in csv.DictReader(f):
            school = row.get("School", "").strip()
            team_id = _resolve_school(conn, school)
            if not team_id:
                continue

            conn.execute("""
                UPDATE analytics_team SET
                    team_avg=?, team_obp=?, team_slg=?,
                    team_ops=COALESCE(?, team_ops),
                    team_woba=COALESCE(?, team_woba),
                    team_babip_hit=?, team_iso=?,
                    team_bb_pct=?, team_k_pct=?,
                    team_wrce=?,
                    updated_at=datetime('now')
                WHERE team_id=?
            """, (
                _safe_float(row.get("AVG")), _safe_float(row.get("OBP")),
                _safe_float(row.get("SLG")), _safe_float(row.get("OPS")),
                _safe_float(row.get("wOBA")), _safe_float(row.get("BABIP")),
                _safe_float(row.get("ISO")),
                _safe_float(row.get("BB%")), _safe_float(row.get("K%")),
                _safe_float(row.get("wRCE")),
                team_id,
            ))
            count += 1

    conn.commit()
    return count


def import_pitcher_stats(conn: sqlite3.Connection) -> int:
    """Import 64analytics_pitcher_stats_2026.csv — 5,199 individual pitchers."""
    path = DATA_DIR / "64analytics_pitcher_stats_2026.csv"
    if not path.exists():
        return 0

    count = 0
    with open(path) as f:
        for row in csv.DictReader(f):
            name = row.get("Name", "").strip()
            school = row.get("School", "").strip()
            if not name or not school:
                continue

            team_id = _resolve_school(conn, school)

            conn.execute("""
                INSERT INTO analytics_pitcher (name, school, rank_wrae, classification,
                    p_ops, p_babip, p_bb_pct, k9, fip, xfip, siera,
                    whip, team_id, position,
                    lob_pct, p_hr_fb, p_ip, p_k_pct, p_k_bb_pct, p_k_bb, p_go_ao,
                    k_l_pct, k_s_pct)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name, school) DO UPDATE SET
                    rank_wrae=excluded.rank_wrae, p_ops=excluded.p_ops,
                    fip=excluded.fip, xfip=excluded.xfip, siera=excluded.siera,
                    whip=excluded.whip, team_id=excluded.team_id,
                    position=excluded.position,
                    lob_pct=excluded.lob_pct, p_hr_fb=excluded.p_hr_fb,
                    p_ip=excluded.p_ip, p_k_pct=excluded.p_k_pct,
                    p_k_bb_pct=excluded.p_k_bb_pct, p_k_bb=excluded.p_k_bb,
                    p_go_ao=excluded.p_go_ao,
                    k_l_pct=excluded.k_l_pct, k_s_pct=excluded.k_s_pct
            """, (
                name, school, _safe_int(row.get("64 Rk - wRAE")),
                row.get("Classification", "").strip(),
                _safe_float(row.get("P-OPS")), _safe_float(row.get("P-BABIP")),
                _safe_float(row.get("P-BB%")), _safe_float(row.get("K/9")),
                _safe_float(row.get("FIP")), _safe_float(row.get("xFIP")),
                _safe_float(row.get("SIERA")),
                _safe_float(row.get("WHIP")),
                team_id,
                row.get("Position", "").strip(),
                _safe_float(row.get("LOB%")),
                _safe_float(row.get("P-HR/FB")),
                _safe_float(row.get("P/IP")),
                _safe_float(row.get("P-K%")),
                _safe_float(row.get("P-K-BB%")),
                _safe_float(row.get("P-K/BB")),
                _safe_float(row.get("P-GO/AO")),
                _safe_float(row.get("K-L%")),
                _safe_float(row.get("K-S%")),
            ))
            count += 1

    conn.commit()
    return count


def import_hitter_stats(conn: sqlite3.Connection) -> int:
    """Import 64analytics_player_hitting_2026.csv — 5,144 individual hitters."""
    path = DATA_DIR / "64analytics_player_hitting_2026.csv"
    if not path.exists():
        return 0

    count = 0
    with open(path) as f:
        for row in csv.DictReader(f):
            name = row.get("Name", "").strip()
            school = row.get("School", "").strip()
            if not name or not school:
                continue

            team_id = _resolve_school(conn, school)

            conn.execute("""
                INSERT INTO analytics_hitter (name, school, rank_wrce, classification,
                    avg, obp, slg, ops, woba, babip, iso, bb_pct, k_pct, wrce, team_id,
                    g, ab, h, hr, rbi, bb, so, sb)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name, school) DO UPDATE SET
                    rank_wrce=excluded.rank_wrce, avg=excluded.avg,
                    obp=excluded.obp, slg=excluded.slg,
                    ops=excluded.ops, woba=excluded.woba, wrce=excluded.wrce,
                    babip=excluded.babip, iso=excluded.iso,
                    bb_pct=excluded.bb_pct, k_pct=excluded.k_pct,
                    team_id=excluded.team_id,
                    g=excluded.g, ab=excluded.ab, h=excluded.h,
                    hr=excluded.hr, rbi=excluded.rbi, bb=excluded.bb,
                    so=excluded.so, sb=excluded.sb
            """, (
                name, school, _safe_int(row.get("64 Rk - wRCE")),
                row.get("Classification", "").strip(),
                _safe_float(row.get("AVG")), _safe_float(row.get("OBP")),
                _safe_float(row.get("SLG")), _safe_float(row.get("OPS")),
                _safe_float(row.get("wOBA")), _safe_float(row.get("BABIP")),
                _safe_float(row.get("ISO")),
                _safe_float(row.get("BB%")), _safe_float(row.get("K%")),
                _safe_float(row.get("wRCE")),
                team_id,
                _safe_int(row.get("G")), _safe_int(row.get("AB")),
                _safe_int(row.get("H")), _safe_int(row.get("HR")),
                _safe_int(row.get("RBI")), _safe_int(row.get("BB")),
                _safe_int(row.get("SO")), _safe_int(row.get("SB")),
            ))
            count += 1

    conn.commit()
    return count


def import_all(conn: sqlite3.Connection) -> dict:
    """Import all 64 Analytics data."""
    rankings = import_team_rankings(conn)
    pitching = import_team_pitching(conn)
    hitting = import_team_hitting(conn)
    pitchers = import_pitcher_stats(conn)
    hitters = import_hitter_stats(conn)

    return {
        "team_rankings": rankings,
        "team_pitching": pitching,
        "team_hitting": hitting,
        "pitchers": pitchers,
        "hitters": hitters,
    }
