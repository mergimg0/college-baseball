-- Migration 009: 64 Analytics data tables

CREATE TABLE IF NOT EXISTS analytics_team (
    team_id INTEGER PRIMARY KEY REFERENCES teams(id),
    -- Rankings
    rank_overall INTEGER,
    -- Pitching (team)
    team_era REAL, team_fip REAL, team_xfip REAL, team_whip REAL,
    team_p_ops REAL, team_p_babip REAL, team_p_lob_pct REAL,
    team_k9 REAL, team_bb9 REAL,
    team_wrae REAL,  -- weighted runs above expected (pitching quality)
    -- Hitting (team)
    team_avg REAL, team_obp REAL, team_slg REAL, team_ops REAL,
    team_woba REAL, team_babip_hit REAL, team_iso REAL,
    team_bb_pct REAL, team_k_pct REAL,
    team_wrce REAL,  -- weighted runs created expected (hitting quality)
    team_r_per_pa REAL,
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS analytics_pitcher (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    school TEXT NOT NULL,
    rank_wrae INTEGER,
    classification TEXT,
    p_ops REAL, p_babip REAL, p_bb_pct REAL,
    k9 REAL, bb9 REAL, fip REAL, xfip REAL, siera REAL,
    era REAL, whip REAL, ip REAL,
    wrae REAL,  -- the key metric: pitcher quality above expected
    pitcher_id INTEGER REFERENCES pitchers(id),  -- link to our pitcher table if matched
    team_id INTEGER REFERENCES teams(id),
    UNIQUE(name, school)
);

CREATE TABLE IF NOT EXISTS analytics_hitter (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    school TEXT NOT NULL,
    rank_wrce INTEGER,
    classification TEXT,
    avg REAL, obp REAL, slg REAL, ops REAL,
    woba REAL, babip REAL, iso REAL,
    bb_pct REAL, k_pct REAL,
    wrce REAL,  -- the key metric: hitter quality above expected
    team_id INTEGER REFERENCES teams(id),
    UNIQUE(name, school)
);
