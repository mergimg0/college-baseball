"""Pitcher quality ratings — hybrid 64 Analytics + box score formula.

Two-tier rating system:
  Tier 1 (matched to 64A): FIP/xFIP/SIERA/K9/WHIP weighted composite
  Tier 2 (box-score only): ERA/K9/BB9/WHIP weighted composite

Starters and relievers are z-scored SEPARATELY.
Scale: 0-100 where 50=average, 70+=elite, 30-=poor.
"""

from __future__ import annotations

import sqlite3

import numpy as np


def match_64a_pitchers(conn: sqlite3.Connection) -> dict:
    """Match analytics_pitcher records to our pitchers table.

    Strategy (in order of confidence):
      1. Exact: same team_id + identical name (case-insensitive)
      2. Last-name: our "Crossland" matches their "Brett Crossland"
      3. Abbreviated: our "A. Murray" matches their "Alec Murray"

    Updates analytics_pitcher.pitcher_id for each match.
    Returns {"exact": N, "lastname": N, "abbreviated": N, "unmatched": N}
    """
    stats = {"exact": 0, "lastname": 0, "abbreviated": 0, "unmatched": 0}

    unmatched = conn.execute("""
        SELECT ap.id, ap.name, ap.team_id
        FROM analytics_pitcher ap
        WHERE ap.pitcher_id IS NULL AND ap.team_id IS NOT NULL
    """).fetchall()

    for ap_id, ap_name, team_id in unmatched:
        ap_lower = ap_name.strip().lower()

        # Strategy 1: Exact match
        match = conn.execute(
            "SELECT id FROM pitchers WHERE team_id = ? AND LOWER(TRIM(name)) = ?",
            (team_id, ap_lower),
        ).fetchone()
        if match:
            conn.execute("UPDATE analytics_pitcher SET pitcher_id = ? WHERE id = ?",
                         (match[0], ap_id))
            stats["exact"] += 1
            continue

        # Strategy 2: Last-name substring
        parts = ap_lower.split()
        if len(parts) >= 2:
            last_name = parts[-1]
            candidates = conn.execute(
                "SELECT id FROM pitchers WHERE team_id = ? AND LOWER(TRIM(name)) = ?",
                (team_id, last_name),
            ).fetchall()
            if len(candidates) == 1:
                conn.execute("UPDATE analytics_pitcher SET pitcher_id = ? WHERE id = ?",
                             (candidates[0][0], ap_id))
                stats["lastname"] += 1
                continue

        # Strategy 3: Abbreviated — our "A. Murray" → their "Alec Murray"
        if len(parts) >= 2:
            first_initial = parts[0][0].lower()
            last = parts[-1]
            match = conn.execute("""
                SELECT id FROM pitchers
                WHERE team_id = ? AND LOWER(TRIM(name)) LIKE ? AND LOWER(TRIM(name)) LIKE ?
            """, (team_id, first_initial + ".%", "%" + last)).fetchone()
            if match:
                conn.execute("UPDATE analytics_pitcher SET pitcher_id = ? WHERE id = ?",
                             (match[0], ap_id))
                stats["abbreviated"] += 1
                continue

            # Also: our "J DELGADO" format
            match2 = conn.execute("""
                SELECT id FROM pitchers
                WHERE team_id = ? AND LENGTH(TRIM(name)) > 1
                  AND LOWER(SUBSTR(TRIM(name), 1, 1)) = ?
                  AND LOWER(TRIM(name)) LIKE ?
            """, (team_id, first_initial, "%" + last)).fetchone()
            if match2:
                conn.execute("UPDATE analytics_pitcher SET pitcher_id = ? WHERE id = ?",
                             (match2[0], ap_id))
                stats["abbreviated"] += 1
                continue

        stats["unmatched"] += 1

    conn.commit()
    return stats


def compute_pitcher_ratings(conn: sqlite3.Connection, min_ip: float = 15.0) -> int:
    """Rate every pitcher with sufficient IP using hybrid 64A + box-score formula.

    For pitchers matched to 64 Analytics (pitcher_id IS NOT NULL):
      composite_z = 0.30×FIP_z + 0.25×xFIP_z + 0.20×SIERA_z + 0.15×K9_z + 0.10×WHIP_z

    For unmatched pitchers (box-score data only):
      composite_z = 0.35×ERA_z + 0.25×K9_z + 0.20×BB9_z + 0.20×WHIP_z

    quality_rating = 50 + 10 × composite_z (clamped to 0-100)
    Starters and relievers z-scored SEPARATELY.

    Returns number of pitchers rated.
    """
    pitchers = conn.execute("""
        SELECT p.id, p.season_ip, p.season_era, p.season_k, p.season_bb,
               p.season_hits_allowed, p.season_er, p.games_started, p.games_relieved,
               ap.fip, ap.xfip, ap.siera, ap.k9 as a64_k9, ap.whip as a64_whip
        FROM pitchers p
        LEFT JOIN analytics_pitcher ap ON ap.pitcher_id = p.id
        WHERE p.season_ip >= ?
    """, (min_ip,)).fetchall()

    if len(pitchers) < 20:
        return 0

    starters = [p for p in pitchers if (p[7] or 0) > (p[8] or 0)]
    relievers = [p for p in pitchers if (p[7] or 0) <= (p[8] or 0)]

    rated = 0
    for group in [starters, relievers]:
        if len(group) < 5:
            continue

        matched = [p for p in group if p[9] is not None and 0 < p[9] < 15]
        unmatched = [p for p in group if p[9] is None or p[9] <= 0 or p[9] >= 15]

        # Tier 1: 64A metrics
        if len(matched) >= 10:
            fips = np.array([max(0, min(15, p[9])) for p in matched])
            xfips = np.array([max(0, min(15, p[10] or p[9])) for p in matched])
            sieras = np.array([max(0, min(10, p[11] or p[9])) for p in matched])
            k9s = np.array([p[12] if p[12] else (p[3] * 9.0 / p[1] if p[1] > 0 else 0) for p in matched])
            whips = np.array([p[13] if p[13] else ((p[5] + p[4]) / p[1] if p[1] > 0 else 3.0) for p in matched])

            for i, p in enumerate(matched):
                z_fip = -(fips[i] - fips.mean()) / max(fips.std(), 0.01)
                z_xfip = -(xfips[i] - xfips.mean()) / max(xfips.std(), 0.01)
                z_siera = -(sieras[i] - sieras.mean()) / max(sieras.std(), 0.01)
                z_k9 = (k9s[i] - k9s.mean()) / max(k9s.std(), 0.01)
                z_whip = -(whips[i] - whips.mean()) / max(whips.std(), 0.01)

                composite = 0.30 * z_fip + 0.25 * z_xfip + 0.20 * z_siera + 0.15 * z_k9 + 0.10 * z_whip
                rating = max(0, min(100, 50 + 10 * composite))
                conn.execute("UPDATE pitchers SET quality_rating=? WHERE id=?",
                             (round(rating, 1), p[0]))
                rated += 1

        # Tier 2: Box-score fallback
        if len(unmatched) >= 5:
            eras = np.array([p[2] if p[2] else (p[6] * 9.0 / p[1] if p[1] > 0 else 9.0) for p in unmatched])
            k9s_u = np.array([p[3] * 9.0 / p[1] if p[1] > 0 else 0 for p in unmatched])
            bb9s = np.array([p[4] * 9.0 / p[1] if p[1] > 0 else 9.0 for p in unmatched])
            whips_u = np.array([(p[5] + p[4]) / p[1] if p[1] > 0 else 3.0 for p in unmatched])

            eras = np.clip(eras, 0, 15)
            whips_u = np.clip(whips_u, 0, 5)

            for i, p in enumerate(unmatched):
                z_era = -(eras[i] - eras.mean()) / max(eras.std(), 0.01)
                z_k9 = (k9s_u[i] - k9s_u.mean()) / max(k9s_u.std(), 0.01)
                z_bb9 = -(bb9s[i] - bb9s.mean()) / max(bb9s.std(), 0.01)
                z_whip = -(whips_u[i] - whips_u.mean()) / max(whips_u.std(), 0.01)

                composite = 0.35 * z_era + 0.25 * z_k9 + 0.20 * z_bb9 + 0.20 * z_whip
                rating = max(0, min(100, 50 + 10 * composite))
                conn.execute("UPDATE pitchers SET quality_rating=? WHERE id=?",
                             (round(rating, 1), p[0]))
                rated += 1

    conn.commit()
    return rated
