-- Migration 005: Odds columns + PEAR game-level fields
-- Stores currently-discarded PEAR game data and Vegas odds

ALTER TABLE games ADD COLUMN odds_home_ml INTEGER;
ALTER TABLE games ADD COLUMN odds_away_ml INTEGER;
ALTER TABLE games ADD COLUMN odds_spread REAL;
ALTER TABLE games ADD COLUMN odds_total REAL;
ALTER TABLE games ADD COLUMN odds_bookmaker TEXT;

-- PEAR game-level fields (38 fields per game, we store the key ones)
ALTER TABLE games ADD COLUMN pear_spread REAL;
ALTER TABLE games ADD COLUMN pear_elo_win_prob REAL;
ALTER TABLE games ADD COLUMN pear_gqi REAL;
ALTER TABLE games ADD COLUMN pear_tq REAL;
ALTER TABLE games ADD COLUMN pear_ned REAL;
