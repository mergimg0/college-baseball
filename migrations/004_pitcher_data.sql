-- Migration 004: Pitcher data infrastructure
-- Enables starting pitcher identification and quality features

ALTER TABLE games ADD COLUMN day_of_week INTEGER;

CREATE TABLE IF NOT EXISTS pitchers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    team_id INTEGER NOT NULL REFERENCES teams(id),
    number INTEGER,
    season_ip REAL DEFAULT 0,
    season_era REAL,
    season_k INTEGER DEFAULT 0,
    season_bb INTEGER DEFAULT 0,
    season_hits_allowed INTEGER DEFAULT 0,
    season_er INTEGER DEFAULT 0,
    games_started INTEGER DEFAULT 0,
    games_relieved INTEGER DEFAULT 0,
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(name, team_id)
);

CREATE TABLE IF NOT EXISTS game_pitchers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL REFERENCES games(id),
    pitcher_id INTEGER NOT NULL REFERENCES pitchers(id),
    team_id INTEGER NOT NULL REFERENCES teams(id),
    is_starter INTEGER NOT NULL DEFAULT 0,
    ip REAL,
    hits_allowed INTEGER,
    runs_allowed INTEGER,
    earned_runs INTEGER,
    walks INTEGER,
    strikeouts INTEGER,
    pitches INTEGER,
    got_win INTEGER DEFAULT 0,
    got_loss INTEGER DEFAULT 0,
    got_save INTEGER DEFAULT 0,
    UNIQUE(game_id, pitcher_id)
);

CREATE INDEX IF NOT EXISTS idx_game_pitchers_game ON game_pitchers(game_id);
CREATE INDEX IF NOT EXISTS idx_game_pitchers_pitcher ON game_pitchers(pitcher_id);
CREATE INDEX IF NOT EXISTS idx_pitchers_team ON pitchers(team_id);
