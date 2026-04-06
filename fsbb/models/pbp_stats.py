"""Compute team-level statistics from play-by-play data.

Aggregates play_events into team_pbp_stats table.
Each stat is computed from actual plate appearance outcomes,
not from PEAR's pre-aggregated numbers.
"""

from __future__ import annotations

import sqlite3


def compute_team_pbp_stats(conn: sqlite3.Connection) -> int:
    """Recompute all team PBP statistics from play_events.

    Returns number of teams updated.
    """
    teams = conn.execute("SELECT id FROM teams").fetchall()
    count = 0

    for (team_id,) in teams:
        events = conn.execute("""
            SELECT event_type, COUNT(*) as cnt
            FROM play_events
            WHERE batting_team_id = ? AND event_type NOT IN ('no_play', 'pitcher_sub', 'other')
            GROUP BY event_type
        """, (team_id,)).fetchall()

        if not events:
            continue

        counts = {e[0]: e[1] for e in events}

        singles = counts.get("single", 0)
        doubles = counts.get("double", 0)
        triples = counts.get("triple", 0)
        homers = counts.get("homer", 0)
        walks = counts.get("walk", 0)
        hbp = counts.get("hbp", 0)
        strikeouts = counts.get("strikeout", 0)
        groundouts = counts.get("groundout", 0)
        flyouts = counts.get("flyout", 0)
        lineouts = counts.get("lineout", 0)
        popouts = counts.get("popout", 0)
        foulouts = counts.get("foulout", 0)
        errors = counts.get("error", 0)
        sac_bunts = counts.get("sac_bunt", 0)
        sac_flies = counts.get("sac_fly", 0)
        stolen = counts.get("stolen_base", 0)
        caught = counts.get("caught_stealing", 0)

        hits = singles + doubles + triples + homers
        outs = groundouts + flyouts + lineouts + popouts + foulouts + strikeouts
        at_bats = hits + outs + errors
        plate_apps = at_bats + walks + hbp + sac_bunts + sac_flies
        total_bases = singles + 2 * doubles + 3 * triples + 4 * homers

        if plate_apps == 0:
            continue

        k_rate = strikeouts / plate_apps
        bb_rate = walks / plate_apps
        k_bb = strikeouts / max(walks, 1)

        avg = hits / max(at_bats, 1)
        slg = total_bases / max(at_bats, 1)
        iso = slg - avg

        babip_denom = at_bats - strikeouts - homers + sac_flies
        babip = (hits - homers) / max(babip_denom, 1) if babip_denom > 0 else None

        sb_attempts = stolen + caught
        sb_rate = stolen / max(sb_attempts, 1) if sb_attempts > 0 else None

        first_inn_runs = conn.execute("""
            SELECT COALESCE(SUM(runs_scored), 0) FROM play_events
            WHERE batting_team_id = ? AND inning = 1
        """, (team_id,)).fetchone()[0]

        games_with_pbp = conn.execute("""
            SELECT COUNT(DISTINCT game_id) FROM play_events WHERE batting_team_id = ?
        """, (team_id,)).fetchone()[0]

        first_inn_rpg = first_inn_runs / max(games_with_pbp, 1)

        late_runs = conn.execute("""
            SELECT COALESCE(SUM(runs_scored), 0) FROM play_events
            WHERE batting_team_id = ? AND inning >= 7
        """, (team_id,)).fetchone()[0]
        late_rpg = late_runs / max(games_with_pbp, 1)

        avg_pitches = conn.execute("""
            SELECT AVG(LENGTH(pitch_sequence)) FROM play_events
            WHERE batting_team_id = ? AND pitch_sequence IS NOT NULL AND pitch_sequence != ''
        """, (team_id,)).fetchone()[0] or 0

        errors_committed = conn.execute("""
            SELECT COUNT(*) FROM play_events
            WHERE batting_team_id != ? AND is_error = 1
              AND game_id IN (SELECT DISTINCT game_id FROM play_events WHERE batting_team_id = ?)
        """, (team_id, team_id)).fetchone()[0]
        error_rate = errors_committed / max(games_with_pbp, 1)

        sb_attempt_rate = sb_attempts / max(plate_apps, 1) if sb_attempts > 0 else 0

        conn.execute("""
            INSERT INTO team_pbp_stats (
                team_id, k_rate, bb_rate, k_bb_ratio,
                batting_avg, slg_computed, iso_computed, babip_computed,
                first_inning_runs_per_game, late_inning_runs_per_game,
                sb_attempt_rate, sb_success_rate,
                pitches_per_pa, error_rate,
                plate_appearances, at_bats, games_with_pbp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(team_id) DO UPDATE SET
                k_rate=excluded.k_rate, bb_rate=excluded.bb_rate,
                k_bb_ratio=excluded.k_bb_ratio,
                batting_avg=excluded.batting_avg, slg_computed=excluded.slg_computed,
                iso_computed=excluded.iso_computed, babip_computed=excluded.babip_computed,
                first_inning_runs_per_game=excluded.first_inning_runs_per_game,
                late_inning_runs_per_game=excluded.late_inning_runs_per_game,
                sb_attempt_rate=excluded.sb_attempt_rate, sb_success_rate=excluded.sb_success_rate,
                pitches_per_pa=excluded.pitches_per_pa, error_rate=excluded.error_rate,
                plate_appearances=excluded.plate_appearances, at_bats=excluded.at_bats,
                games_with_pbp=excluded.games_with_pbp, updated_at=datetime('now')
        """, (
            team_id, k_rate, bb_rate, k_bb,
            avg, slg, iso, babip,
            first_inn_rpg, late_rpg,
            sb_attempt_rate, sb_rate,
            avg_pitches, error_rate,
            plate_apps, at_bats, games_with_pbp,
        ))
        count += 1

    conn.commit()
    return count


def compute_bullpen_stats(conn: sqlite3.Connection) -> int:
    """Compute bullpen ERA per team from game_pitchers data."""
    teams = conn.execute("SELECT id FROM teams").fetchall()
    count = 0

    for (team_id,) in teams:
        bp = conn.execute("""
            SELECT SUM(ip) as total_ip, SUM(earned_runs) as total_er
            FROM game_pitchers
            WHERE team_id = ? AND is_starter = 0 AND ip > 0
        """, (team_id,)).fetchone()

        if bp and bp[0] and bp[0] > 0:
            bp_era = (bp[1] / bp[0]) * 9.0
            conn.execute("""
                UPDATE team_pbp_stats SET bullpen_era = ? WHERE team_id = ?
            """, (round(bp_era, 2), team_id))
            count += 1

        starter = conn.execute("""
            SELECT AVG(ip) FROM game_pitchers WHERE team_id = ? AND is_starter = 1 AND ip > 0
        """, (team_id,)).fetchone()
        if starter and starter[0]:
            conn.execute("""
                UPDATE team_pbp_stats SET starter_avg_ip = ? WHERE team_id = ?
            """, (round(starter[0], 1), team_id))

    conn.commit()
    return count
