-- Migration 002: Add series_position column for pitcher proxy
-- Friday = 1 (ace), Saturday = 2, Sunday = 3
ALTER TABLE games ADD COLUMN series_position INTEGER;
