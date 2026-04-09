"""Walk-forward PBP feature computation.

Computes team-level PBP stats using only events before a cutoff date,
enabling leakage-free feature computation for backtesting.
"""

from __future__ import annotations

import sqlite3


def compute_pbp_features_to_date(
    conn: sqlite3.Connection,
    team_id: int,
    cutoff_date: str,
) -> dict | None:
    """Compute PBP-derived team stats using only events before cutoff_date.

    Returns dict with k_rate, bb_rate, babip, bullpen_era, starter_avg_ip
    or None if insufficient data (<50 plate appearances).
    """
    row = conn.execute("""
        SELECT
            COUNT(*) as total_events,
            SUM(CASE WHEN event_type = 'strikeout' THEN 1 ELSE 0 END) as k,
            SUM(CASE WHEN event_type = 'walk' THEN 1 ELSE 0 END) as bb,
            SUM(CASE WHEN event_type IN ('single','double','triple','homer') THEN 1 ELSE 0 END) as hits,
            SUM(CASE WHEN event_type = 'homer' THEN 1 ELSE 0 END) as hr,
            SUM(CASE WHEN event_type IN ('groundout','flyout','lineout','popout','foulout','strikeout') THEN 1 ELSE 0 END) as outs,
            SUM(CASE WHEN event_type = 'sac_fly' THEN 1 ELSE 0 END) as sf
        FROM play_events pe
        JOIN games g ON pe.game_id = g.id
        WHERE pe.batting_team_id = ? AND g.date < ?
        AND pe.event_type NOT IN ('no_play', 'pitcher_sub', 'other')
    """, (team_id, cutoff_date)).fetchone()

    if not row or row[0] < 50:
        return None

    total = row[0]
    k = row[1] or 0
    bb = row[2] or 0
    hits = row[3] or 0
    hr = row[4] or 0
    outs = row[5] or 0
    sf = row[6] or 0

    at_bats = hits + outs
    plate_apps = at_bats + bb + sf
    if plate_apps == 0:
        return None

    k_rate = k / plate_apps
    bb_rate = bb / plate_apps

    babip_denom = at_bats - k - hr + sf
    babip = (hits - hr) / max(babip_denom, 1) if babip_denom > 0 else None

    # Bullpen ERA from game_pitchers
    bp = conn.execute("""
        SELECT SUM(gp.ip), SUM(gp.earned_runs)
        FROM game_pitchers gp
        JOIN games g ON gp.game_id = g.id
        WHERE gp.team_id = ? AND gp.is_starter = 0 AND gp.ip > 0 AND g.date < ?
    """, (team_id, cutoff_date)).fetchone()

    bullpen_era = None
    if bp and bp[0] and bp[0] > 0:
        bullpen_era = (bp[1] / bp[0]) * 9.0

    # Starter avg IP
    starter = conn.execute("""
        SELECT AVG(gp.ip)
        FROM game_pitchers gp
        JOIN games g ON gp.game_id = g.id
        WHERE gp.team_id = ? AND gp.is_starter = 1 AND gp.ip > 0 AND g.date < ?
    """, (team_id, cutoff_date)).fetchone()

    starter_avg_ip = starter[0] if starter and starter[0] else None

    return {
        "k_rate": round(k_rate, 4),
        "bb_rate": round(bb_rate, 4),
        "babip": round(babip, 4) if babip is not None else None,
        "bullpen_era": round(bullpen_era, 2) if bullpen_era is not None else None,
        "starter_avg_ip": round(starter_avg_ip, 1) if starter_avg_ip is not None else None,
        "plate_appearances": plate_apps,
    }
