-- Migration 007: Team-level statistics derived from play-by-play data

CREATE TABLE IF NOT EXISTS team_pbp_stats (
    team_id INTEGER PRIMARY KEY REFERENCES teams(id),
    k_rate REAL,
    bb_rate REAL,
    k_bb_ratio REAL,
    batting_avg REAL,
    slg_computed REAL,
    iso_computed REAL,
    babip_computed REAL,
    first_inning_runs_per_game REAL,
    late_inning_runs_per_game REAL,
    sb_attempt_rate REAL,
    sb_success_rate REAL,
    bullpen_era REAL,
    starter_avg_ip REAL,
    pitches_per_pa REAL,
    error_rate REAL,
    plate_appearances INTEGER DEFAULT 0,
    at_bats INTEGER DEFAULT 0,
    games_with_pbp INTEGER DEFAULT 0,
    updated_at TEXT DEFAULT (datetime('now'))
);
