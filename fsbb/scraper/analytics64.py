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
    """Import 64analytics_team_pitching_2026.csv.

    CSV has raw counting stats — we compute advanced metrics:
      WHIP = (H + BB) / IP
      K/9  = (SO / IP) * 9
      BB/9 = (BB / IP) * 9
      FIP  = ((13*HR + 3*BB - 2*K) / IP) + FIP_constant
      P-BABIP = (H - HR) / (BF - SO - HR)  (approx)
    """
    path = DATA_DIR / "64analytics_team_pitching_2026.csv"
    if not path.exists():
        return 0

    FIP_CONSTANT = 3.10  # NCAA D1 approximate

    count = 0
    with open(path) as f:
        for row in csv.DictReader(f):
            school = row.get("School", "").strip()
            team_id = _resolve_school(conn, school)
            if not team_id:
                continue

            era = _safe_float(row.get("ERA"))
            ip = _safe_float(row.get("IP"))
            h = _safe_float(row.get("P-H"))
            bb = _safe_float(row.get("P-BB"))
            so = _safe_float(row.get("P-SO"))
            hr = _safe_float(row.get("P-HR"))
            bf = _safe_float(row.get("P-BF"))
            # Compute advanced metrics from raw stats
            whip = None
            k9 = None
            bb9 = None
            fip = None
            p_babip = None

            if ip and ip > 0:
                if h is not None and bb is not None:
                    whip = (h + bb) / ip
                if so is not None:
                    k9 = (so / ip) * 9.0
                if bb is not None:
                    bb9 = (bb / ip) * 9.0
                if hr is not None and bb is not None and so is not None:
                    fip = ((13 * hr + 3 * bb - 2 * so) / ip) + FIP_CONSTANT

            if h is not None and hr is not None and bf is not None and so is not None:
                denom = bf - so - hr
                if denom > 0:
                    p_babip = (h - hr) / denom

            # wRAE rank (proprietary metric, value not in CSV)
            wrae_rank = _safe_int(row.get("64 Rank - wRA35"))

            conn.execute("""
                UPDATE analytics_team SET
                    team_era=?, team_fip=COALESCE(?, team_fip),
                    team_whip=COALESCE(?, team_whip),
                    team_p_babip=?,
                    team_k9=?, team_bb9=?,
                    team_wrae=?,
                    updated_at=datetime('now')
                WHERE team_id=?
            """, (
                era, fip,
                whip,
                p_babip,
                k9, bb9,
                wrae_rank,  # store rank since value isn't available
                team_id,
            ))
            count += 1

    conn.commit()
    return count


def import_team_hitting(conn: sqlite3.Connection) -> int:
    """Import 64analytics_team_hitting_2026.csv.

    CSV has raw counting stats — we compute advanced metrics:
      OPS   = OBP + SLG
      ISO   = SLG - AVG
      BABIP = (H - HR) / (AB - SO - HR + SF)
      BB%   = BB / PA
      K%    = SO / PA
      wOBA  = (0.69*BB + 0.72*HBP + 0.89*1B + 1.27*2B + 1.62*3B + 2.10*HR) / PA
    """
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

            avg = _safe_float(row.get("AVG"))
            obp = _safe_float(row.get("OBP"))
            slg = _safe_float(row.get("SLG"))
            ab = _safe_float(row.get("AB"))
            h = _safe_float(row.get("H"))
            hr = _safe_float(row.get("HR"))
            bb = _safe_float(row.get("BB"))
            hbp = _safe_float(row.get("HBP"))
            sf = _safe_float(row.get("SF"))
            so = _safe_float(row.get("SO"))
            pa = _safe_float(row.get("PA"))
            doubles = _safe_float(row.get("2B"))
            triples = _safe_float(row.get("3B"))

            # Compute advanced metrics
            ops = (obp + slg) if obp is not None and slg is not None else None
            iso = (slg - avg) if slg is not None and avg is not None else None

            babip = None
            if h is not None and hr is not None and ab is not None and so is not None:
                denom = ab - so - hr + (sf or 0)
                if denom > 0:
                    babip = (h - hr) / denom

            bb_pct = None
            k_pct = None
            if pa and pa > 0:
                if bb is not None:
                    bb_pct = bb / pa
                if so is not None:
                    k_pct = so / pa

            # wOBA using NCAA D1 linear weights (approximation)
            woba = None
            if pa and pa > 0 and h is not None and hr is not None:
                singles = h - (doubles or 0) - (triples or 0) - hr
                woba = (0.69 * (bb or 0) + 0.72 * (hbp or 0) +
                        0.89 * singles + 1.27 * (doubles or 0) +
                        1.62 * (triples or 0) + 2.10 * hr) / pa

            wrce_rank = _safe_int(row.get("64 Rank - wRC35"))

            conn.execute("""
                UPDATE analytics_team SET
                    team_avg=?, team_obp=?, team_slg=?,
                    team_ops=?, team_woba=?,
                    team_babip_hit=?, team_iso=?,
                    team_bb_pct=?, team_k_pct=?,
                    team_wrce=?,
                    updated_at=datetime('now')
                WHERE team_id=?
            """, (
                avg, obp, slg, ops, woba,
                babip, iso,
                bb_pct, k_pct,
                wrce_rank,
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
    """Import 64analytics_player_hitting_2026.csv — 5,144 individual hitters.

    CSV has raw counting stats — we compute advanced metrics:
      OPS   = OBP + SLG
      ISO   = SLG - AVG
      BABIP = (H - HR) / (AB - SO - HR + SF)
      BB%   = BB / PA
      K%    = SO / PA
      wOBA  = (0.69*BB + 0.72*HBP + 0.89*1B + 1.27*2B + 1.62*3B + 2.10*HR) / PA
    """
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

            avg = _safe_float(row.get("AVG"))
            obp = _safe_float(row.get("OBP"))
            slg = _safe_float(row.get("SLG"))
            g = _safe_int(row.get("G"))
            ab = _safe_int(row.get("AB"))
            h = _safe_int(row.get("H"))
            doubles = _safe_int(row.get("2B"))
            triples = _safe_int(row.get("3B"))
            hr = _safe_int(row.get("HR"))
            rbi = _safe_int(row.get("RBI"))
            bb = _safe_int(row.get("BB"))
            hbp = _safe_int(row.get("HBP"))
            sf = _safe_int(row.get("SF"))
            so = _safe_int(row.get("SO"))
            sb = _safe_int(row.get("SB"))
            pa = _safe_int(row.get("PA"))

            # Compute advanced metrics
            ops = (obp + slg) if obp is not None and slg is not None else None
            iso = (slg - avg) if slg is not None and avg is not None else None

            babip = None
            if h is not None and hr is not None and ab is not None and so is not None:
                denom = ab - so - hr + (sf or 0)
                if denom > 0:
                    babip = (h - hr) / denom

            bb_pct = None
            k_pct = None
            if pa and pa > 0:
                if bb is not None:
                    bb_pct = bb / pa
                if so is not None:
                    k_pct = so / pa

            woba = None
            if pa and pa > 0 and h is not None and hr is not None:
                singles = h - (doubles or 0) - (triples or 0) - hr
                woba = (0.69 * (bb or 0) + 0.72 * (hbp or 0) +
                        0.89 * singles + 1.27 * (doubles or 0) +
                        1.62 * (triples or 0) + 2.10 * hr) / pa

            wrce_rank = _safe_int(row.get("64 Rk - wRCE"))

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
                name, school, wrce_rank,
                row.get("Classification", "").strip(),
                avg, obp, slg, ops, woba, babip, iso,
                bb_pct, k_pct,
                wrce_rank,  # store rank since value isn't in CSV
                team_id,
                g, ab, h, hr, rbi, bb, so, sb,
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
