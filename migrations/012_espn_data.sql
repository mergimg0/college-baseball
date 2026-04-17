-- Migration 012: ESPN Hidden API data tables

-- ESPN game IDs for cross-referencing
ALTER TABLE games ADD COLUMN espn_game_id TEXT;
CREATE INDEX IF NOT EXISTS idx_games_espn_id ON games(espn_game_id);

-- Individual player batting lines per game (from ESPN box score)
CREATE TABLE IF NOT EXISTS espn_game_batting (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL REFERENCES games(id),
    team_id INTEGER NOT NULL REFERENCES teams(id),
    player_name TEXT NOT NULL,
    espn_player_id TEXT,
    is_starter INTEGER DEFAULT 0,
    -- Raw box score line
    ab INTEGER, r INTEGER, h INTEGER, rbi INTEGER,
    hr INTEGER, bb INTEGER, k INTEGER, hbp INTEGER,
    sb INTEGER, cs INTEGER,
    -- Season cumulative (ESPN includes these per-game)
    season_avg REAL, season_obp REAL, season_slg REAL,
    UNIQUE(game_id, player_name, team_id)
);

-- Individual player pitching lines per game
CREATE TABLE IF NOT EXISTS espn_game_pitching (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL REFERENCES games(id),
    team_id INTEGER NOT NULL REFERENCES teams(id),
    player_name TEXT NOT NULL,
    espn_player_id TEXT,
    is_starter INTEGER DEFAULT 0,
    -- Raw box score line
    ip REAL, h INTEGER, r INTEGER, er INTEGER,
    bb INTEGER, k INTEGER, hr INTEGER,
    pitches INTEGER, strikes INTEGER,
    -- Season cumulative
    season_era REAL,
    UNIQUE(game_id, player_name, team_id)
);

-- Team-level fielding stats per game (ESPN-exclusive — we have zero fielding data)
CREATE TABLE IF NOT EXISTS espn_game_fielding (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL REFERENCES games(id),
    team_id INTEGER NOT NULL REFERENCES teams(id),
    dp INTEGER,    -- double plays
    e INTEGER,     -- errors
    pb INTEGER,    -- passed balls
    a INTEGER,     -- assists
    po INTEGER,    -- putouts
    tp INTEGER,    -- triple plays
    UNIQUE(game_id, team_id)
);

CREATE INDEX IF NOT EXISTS idx_espn_batting_game ON espn_game_batting(game_id);
CREATE INDEX IF NOT EXISTS idx_espn_batting_player ON espn_game_batting(player_name, team_id);
CREATE INDEX IF NOT EXISTS idx_espn_pitching_game ON espn_game_pitching(game_id);
CREATE INDEX IF NOT EXISTS idx_espn_fielding_game ON espn_game_fielding(game_id);
