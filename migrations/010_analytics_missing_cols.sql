-- Migration 010: Add missing 64 Analytics columns that were dropped during initial import

-- Pitcher missing columns
ALTER TABLE analytics_pitcher ADD COLUMN lob_pct REAL;
ALTER TABLE analytics_pitcher ADD COLUMN p_hr_fb REAL;
ALTER TABLE analytics_pitcher ADD COLUMN p_ip REAL;
ALTER TABLE analytics_pitcher ADD COLUMN p_k_pct REAL;
ALTER TABLE analytics_pitcher ADD COLUMN p_k_bb_pct REAL;
ALTER TABLE analytics_pitcher ADD COLUMN p_k_bb REAL;
ALTER TABLE analytics_pitcher ADD COLUMN p_go_ao REAL;
ALTER TABLE analytics_pitcher ADD COLUMN position TEXT;
ALTER TABLE analytics_pitcher ADD COLUMN k_l_pct REAL;
ALTER TABLE analytics_pitcher ADD COLUMN k_s_pct REAL;

-- Team pitching missing columns
ALTER TABLE analytics_team ADD COLUMN team_wra35_rank INTEGER;
ALTER TABLE analytics_team ADD COLUMN team_go_fo REAL;
ALTER TABLE analytics_team ADD COLUMN team_hr9 REAL;
ALTER TABLE analytics_team ADD COLUMN team_p_k_pct REAL;
ALTER TABLE analytics_team ADD COLUMN team_p_hr_fb REAL;
ALTER TABLE analytics_team ADD COLUMN team_lob_pct REAL;

-- Team hitting missing columns
ALTER TABLE analytics_team ADD COLUMN team_wrc35_rank INTEGER;
ALTER TABLE analytics_team ADD COLUMN team_hr INTEGER;
ALTER TABLE analytics_team ADD COLUMN team_sb INTEGER;
ALTER TABLE analytics_team ADD COLUMN team_rbi INTEGER;

-- Hitter missing columns
ALTER TABLE analytics_hitter ADD COLUMN g INTEGER;
ALTER TABLE analytics_hitter ADD COLUMN ab INTEGER;
ALTER TABLE analytics_hitter ADD COLUMN h INTEGER;
ALTER TABLE analytics_hitter ADD COLUMN hr INTEGER;
ALTER TABLE analytics_hitter ADD COLUMN rbi INTEGER;
ALTER TABLE analytics_hitter ADD COLUMN bb INTEGER;
ALTER TABLE analytics_hitter ADD COLUMN so INTEGER;
ALTER TABLE analytics_hitter ADD COLUMN sb INTEGER;
