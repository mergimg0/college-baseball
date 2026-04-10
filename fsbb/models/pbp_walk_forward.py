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

    Returns dict with batting features (wOBA, ISO, SLG, OBP, BABIP, k_rate, bb_rate)
    and pitching features (bullpen_era, starter_avg_ip, team_era, team_fip)
    or None if insufficient data (<50 plate appearances).
    """
    row = conn.execute("""
        SELECT
            SUM(CASE WHEN event_type = 'walk' THEN 1 ELSE 0 END) as bb,
            SUM(CASE WHEN event_type = 'hbp' THEN 1 ELSE 0 END) as hbp,
            SUM(CASE WHEN event_type = 'single' THEN 1 ELSE 0 END) as singles,
            SUM(CASE WHEN event_type = 'double' THEN 1 ELSE 0 END) as doubles,
            SUM(CASE WHEN event_type = 'triple' THEN 1 ELSE 0 END) as triples,
            SUM(CASE WHEN event_type = 'homer' THEN 1 ELSE 0 END) as hr,
            SUM(CASE WHEN event_type = 'strikeout' THEN 1 ELSE 0 END) as k,
            SUM(CASE WHEN event_type IN ('groundout','flyout','lineout','popout',
                'foulout','fielder_choice','double_play') THEN 1 ELSE 0 END) as outs_in_play,
            SUM(CASE WHEN event_type = 'sac_fly' THEN 1 ELSE 0 END) as sf,
            SUM(CASE WHEN event_type = 'sac_bunt' THEN 1 ELSE 0 END) as sh,
            SUM(CASE WHEN event_type = 'error' THEN 1 ELSE 0 END) as errors
        FROM play_events pe
        WHERE pe.batting_team_id = ? AND pe.game_date < ?
        AND pe.event_type NOT IN ('no_play', 'pitcher_sub', 'other')
    """, (team_id, cutoff_date)).fetchone()

    if not row or row[0] is None:
        return None

    bb = row[0] or 0
    hbp = row[1] or 0
    singles = row[2] or 0
    doubles = row[3] or 0
    triples = row[4] or 0
    hr = row[5] or 0
    k = row[6] or 0
    outs_in_play = row[7] or 0
    sf = row[8] or 0
    sh = row[9] or 0
    errors = row[10] or 0

    hits = singles + doubles + triples + hr
    outs = outs_in_play + k
    ab = hits + outs + errors
    pa = ab + bb + hbp + sf + sh
    tb = singles + 2 * doubles + 3 * triples + 4 * hr

    if pa < 50:
        return None

    # Batting features
    k_rate = k / pa
    bb_rate = bb / pa
    avg = hits / max(ab, 1)
    slg = tb / max(ab, 1)
    iso = slg - avg
    obp = (hits + bb + hbp) / pa

    babip_denom = ab - k - hr + sf
    babip = (hits - hr) / babip_denom if babip_denom > 0 else None

    # wOBA (NCAA linear weights approximation)
    woba_num = 0.69 * bb + 0.72 * hbp + 0.88 * singles + 1.27 * doubles + 1.62 * triples + 2.10 * hr
    woba = woba_num / pa

    # Pitching features: team ERA from game_pitchers
    pitching = conn.execute("""
        SELECT SUM(gp.ip) as total_ip, SUM(gp.earned_runs) as total_er,
               SUM(gp.walks) as total_bb, SUM(gp.strikeouts) as total_k,
               SUM(gp.hits_allowed) as total_ha
        FROM game_pitchers gp
        JOIN games g ON gp.game_id = g.id
        WHERE gp.team_id = ? AND gp.ip > 0 AND g.date < ?
    """, (team_id, cutoff_date)).fetchone()

    team_era = None
    team_fip = None
    if pitching and pitching[0] and pitching[0] > 0:
        ip = pitching[0]
        er = pitching[1] or 0
        p_bb = pitching[2] or 0
        p_k = pitching[3] or 0
        team_era = (er / ip) * 9.0
        # FIP = (13*HR_est + 3*BB - 2*K) / IP + 3.10
        # Estimate HR from ER as ~10% of ER (rough NCAA estimate)
        hr_est = er * 0.10
        team_fip = (13 * hr_est + 3 * p_bb - 2 * p_k) / ip + 3.10

    # Bullpen ERA
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
        "batting_avg": round(avg, 4),
        "slg": round(slg, 4),
        "iso": round(iso, 4),
        "obp": round(obp, 4),
        "woba": round(woba, 4),
        "babip": round(babip, 4) if babip is not None else None,
        "team_era": round(team_era, 2) if team_era is not None else None,
        "team_fip": round(team_fip, 2) if team_fip is not None else None,
        "bullpen_era": round(bullpen_era, 2) if bullpen_era is not None else None,
        "starter_avg_ip": round(starter_avg_ip, 1) if starter_avg_ip is not None else None,
        "plate_appearances": pa,
    }

    # RISP features (optional — adds ~1s per call)
    try:
        from fsbb.models.risp import compute_team_risp
        risp = compute_team_risp(conn, team_id, cutoff_date)
        if risp and team_id in risp:
            r = risp[team_id]
            result["risp_avg"] = round(r["risp_avg"], 4) if r.get("risp_avg") is not None else None
            result["two_out_risp_avg"] = round(r["two_out_risp_avg"], 4) if r.get("two_out_risp_avg") is not None else None
            result["leadoff_obp"] = round(r["leadoff_obp"], 4) if r.get("leadoff_obp") is not None else None
            result["strand_rate"] = round(r["strand_rate"], 4) if r.get("strand_rate") is not None else None
    except Exception:
        pass

    return result
