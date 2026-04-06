-- Migration 003: Add game-level features for prediction model
-- Home/away splits stored per team, rest days computed per game
ALTER TABLE games ADD COLUMN home_rest_days INTEGER;
ALTER TABLE games ADD COLUMN away_rest_days INTEGER;
ALTER TABLE games ADD COLUMN odds_implied_home_prob REAL;
