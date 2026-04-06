-- Migration 008: Add pitcher quality rating column
ALTER TABLE pitchers ADD COLUMN quality_rating REAL;
