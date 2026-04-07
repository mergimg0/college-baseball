-- Odds history table for closing line value (CLV) tracking
CREATE TABLE IF NOT EXISTS odds_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL REFERENCES games(id),
    bookmaker TEXT NOT NULL,
    market TEXT NOT NULL DEFAULT 'h2h',
    home_ml INTEGER,
    away_ml INTEGER,
    spread REAL,
    total REAL,
    implied_home_prob REAL,
    fetched_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(game_id, bookmaker, market, fetched_at)
);

CREATE INDEX IF NOT EXISTS idx_odds_history_game ON odds_history(game_id);
