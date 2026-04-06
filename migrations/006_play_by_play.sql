-- Migration 006: Play-by-play event storage
-- Stores parsed narrative play descriptions from NCAA API

CREATE TABLE IF NOT EXISTS play_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL REFERENCES games(id),
    inning INTEGER NOT NULL,
    is_top INTEGER NOT NULL,
    batting_team_id INTEGER NOT NULL REFERENCES teams(id),
    sequence_in_inning INTEGER NOT NULL,
    raw_text TEXT NOT NULL,
    event_type TEXT,
    batter_name TEXT,
    pitcher_sub_in TEXT,
    pitcher_sub_out TEXT,
    hit_direction TEXT,
    pitch_count TEXT,
    pitch_sequence TEXT,
    runs_scored INTEGER DEFAULT 0,
    rbi INTEGER DEFAULT 0,
    is_error INTEGER DEFAULT 0,
    is_sacrifice INTEGER DEFAULT 0,
    stolen_base INTEGER DEFAULT 0,
    caught_stealing INTEGER DEFAULT 0,
    wild_pitch INTEGER DEFAULT 0,
    home_score_after INTEGER,
    away_score_after INTEGER,
    UNIQUE(game_id, inning, is_top, sequence_in_inning)
);

CREATE INDEX IF NOT EXISTS idx_play_events_game ON play_events(game_id);
CREATE INDEX IF NOT EXISTS idx_play_events_batter ON play_events(batter_name);
CREATE INDEX IF NOT EXISTS idx_play_events_type ON play_events(event_type);
