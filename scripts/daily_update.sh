#!/bin/bash
# ForgeStream Baseball — Daily Update Pipeline
# Runs: scrape → box scores → series positions → odds → rate → render → deploy
#
# Usage: ./scripts/daily_update.sh
# Cron:  0 16 * * * cd /path/to/college-baseball && ./scripts/daily_update.sh >> logs/daily.log 2>&1

set -e

PROJ_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DEPLOY_DIR="/tmp/fsbb-deploy"
cd "$PROJ_DIR"

echo "$(date '+%Y-%m-%d %H:%M:%S') — Starting daily update"

# Step 1: Scrape latest PEAR ratings + team details (stores game-level PEAR data)
echo "  [1/9] Refreshing PEAR ratings..."
python3 -m fsbb scrape 2>&1 | tail -2

# Step 2: Scrape yesterday's + today's NCAA scores
echo "  [2/9] Importing NCAA scores..."
python3 -c "
from fsbb.db import init_db
from fsbb.scraper.ncaa import scrape_date
from datetime import date, timedelta
conn = init_db()
for d in [date.today() - timedelta(days=1), date.today()]:
    result = scrape_date(conn, d)
    print(f'    {d}: {result[\"imported\"]} games imported')
conn.close()
"

# Step 3: Scrape yesterday's box scores (pitcher data) — ~15-25 games, ~8 seconds
echo "  [3/11] Scraping pitcher box scores..."
python3 -m fsbb pitchers --days 1 2>&1 | tail -3

# Step 3.5: Scrape yesterday's play-by-play data
echo "  [3.5/11] Scraping play-by-play..."
python3 -m fsbb scrape-pbp --start "$(date -v-1d '+%Y-%m-%d')" --end "$(date -v-1d '+%Y-%m-%d')" 2>&1 | tail -1

# Step 4: Compute series positions
echo "  [4/9] Computing series positions..."
python3 -c "
from fsbb.db import init_db
from datetime import datetime
import sqlite3

conn = init_db()
games = conn.execute('''
    SELECT id, date, home_team_id, away_team_id
    FROM games WHERE status=\"final\" AND series_position IS NULL
    ORDER BY home_team_id, away_team_id, date
''').fetchall()

updated = 0
i = 0
while i < len(games):
    series = [games[i]]
    j = i + 1
    while j < len(games):
        g = games[j]
        prev = series[-1]
        if g[2] == prev[2] and g[3] == prev[3]:
            d1 = datetime.fromisoformat(series[0][1]).date()
            d2 = datetime.fromisoformat(g[1]).date()
            if (d2 - d1).days <= 3:
                series.append(g)
                j += 1
                continue
        break
    for pos, sg in enumerate(series, 1):
        if pos <= 3:
            conn.execute('UPDATE games SET series_position=? WHERE id=?', (pos, sg[0]))
            updated += 1
    i = j
conn.commit()
print(f'    Tagged {updated} new games with series position')
conn.close()
"

# Step 5: Compute day_of_week and rest days for new games
echo "  [5/9] Computing game features..."
python3 -c "
from fsbb.db import init_db
from datetime import datetime
conn = init_db()
# Day of week
for g in conn.execute('SELECT id, date FROM games WHERE day_of_week IS NULL').fetchall():
    d = datetime.fromisoformat(g[1]).date()
    conn.execute('UPDATE games SET day_of_week=? WHERE id=?', (d.weekday(), g[0]))
conn.commit()
print('    Game features updated')
conn.close()
"

# Step 6: Fetch today's odds (if API key set)
echo "  [6/9] Fetching odds..."
if [ -n "$ODDS_API_KEY" ]; then
    python3 -c "
from fsbb.db import init_db
from fsbb.scraper.odds import fetch_odds, parse_odds, store_odds
conn = init_db()
raw = fetch_odds()
if raw:
    parsed = parse_odds(raw)
    n = store_odds(conn, parsed)
    print(f'    Stored odds for {n} games')
else:
    print('    No odds available')
conn.close()
"
else
    echo "    Skipped (ODDS_API_KEY not set)"
fi

# Step 7: Recompute ratings
echo "  [7/11] Computing ratings..."
python3 -m fsbb rate 2>&1 | tail -3

# Step 8: Compute PBP stats + pitcher ratings
echo "  [8/11] Computing PBP stats + pitcher ratings..."
python3 -c "
from fsbb.db import init_db
from fsbb.models.pbp_stats import compute_team_pbp_stats, compute_bullpen_stats
from fsbb.models.pitcher_ratings import compute_pitcher_ratings
conn = init_db()
t = compute_team_pbp_stats(conn)
b = compute_bullpen_stats(conn)
p = compute_pitcher_ratings(conn)
print(f'    {t} team stats, {b} bullpen stats, {p} pitchers rated')
conn.close()
"

# Step 9: Render prediction page
echo "  [9/11] Rendering prediction page..."
python3 -m fsbb render -o docs/index.html

# Step 10: Deploy to GitHub Pages
echo "  [10/11] Deploying..."
if [ -d "$DEPLOY_DIR/.git" ]; then
    cp docs/index.html "$DEPLOY_DIR/index.html"
    cd "$DEPLOY_DIR"
    git add index.html
    git commit -m "Daily update $(date '+%Y-%m-%d')" 2>/dev/null && git push origin main 2>&1 || echo "    No changes to deploy"
else
    echo "    Deploy dir not found. Run initial deployment first."
fi

cd "$PROJ_DIR"
echo "$(date '+%Y-%m-%d %H:%M:%S') — Daily update complete"
