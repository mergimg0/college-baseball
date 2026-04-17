-- Migration 013: D1 Baseball Synergy data (WAR, DRS, plate discipline)

-- Player-level WAR decomposition (from D1Baseball/643 Charts)
CREATE TABLE IF NOT EXISTS player_war (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL,
    team_name TEXT NOT NULL,
    position TEXT,
    season INTEGER NOT NULL,
    -- WAR components
    orar REAL,     -- Offensive Runs Above Replacement
    owar REAL,     -- Offensive WAR
    drs REAL,      -- Defensive Runs Saved
    dwar REAL,     -- Defensive WAR
    prar REAL,     -- Pitching Runs Above Replacement
    pwar REAL,     -- Pitching WAR
    war REAL,      -- Total WAR (QoC-adjusted)
    -- Resolved IDs
    team_id INTEGER REFERENCES teams(id),
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(player_name, team_name, season)
);

-- Player-level DRS decomposition (14 defensive components)
CREATE TABLE IF NOT EXISTS player_drs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL,
    team_name TEXT NOT NULL,
    position TEXT,
    season INTEGER NOT NULL,
    -- DRS total
    drs REAL,
    -- Catcher-specific
    framing_runs REAL,
    pitches_framed INTEGER,
    blocking_runs REAL,
    -- Baserunning defense
    sb_runs REAL,
    pickoff_runs REAL,
    -- Infield
    throwing_runs REAL,
    inf_gb_runs REAL,
    dp_runs_start REAL,
    dp_runs_pivot REAL,
    iffb_runs REAL,
    bunt_runs REAL,
    -- Outfield
    of_flyball_runs REAL,
    of_arm_runs REAL,
    -- Resolved IDs
    team_id INTEGER REFERENCES teams(id),
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(player_name, team_name, season)
);

-- Synergy plate discipline metrics (by pitch type)
CREATE TABLE IF NOT EXISTS player_synergy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL,
    team_name TEXT NOT NULL,
    season INTEGER NOT NULL,
    stat_type TEXT NOT NULL,      -- 'batting' or 'pitching'
    pitch_type TEXT NOT NULL,     -- 'all', 'fastball', 'slider', 'changeup', 'curveball', 'cutter'
    metric_name TEXT NOT NULL,    -- 'contact_pct', 'whiff_pct', etc.
    metric_value REAL,
    rank INTEGER,
    -- Resolved IDs
    team_id INTEGER REFERENCES teams(id),
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(player_name, team_name, season, stat_type, pitch_type, metric_name)
);

CREATE INDEX IF NOT EXISTS idx_player_war_team ON player_war(team_id);
CREATE INDEX IF NOT EXISTS idx_player_war_season ON player_war(season);
CREATE INDEX IF NOT EXISTS idx_player_drs_team ON player_drs(team_id);
CREATE INDEX IF NOT EXISTS idx_player_synergy_type ON player_synergy(stat_type, pitch_type, metric_name);
