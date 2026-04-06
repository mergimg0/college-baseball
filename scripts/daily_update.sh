#!/bin/bash
# ForgeStream Baseball — Daily Update Pipeline
# Runs: scrape → rate → predict → render → deploy
#
# Usage: ./scripts/daily_update.sh
# Cron:  0 16 * * * cd /Users/mghome/projects/college-baseball && ./scripts/daily_update.sh >> logs/daily.log 2>&1

set -e

PROJ_DIR="/Users/mghome/projects/college-baseball"
DEPLOY_DIR="/tmp/fsbb-deploy"
cd "$PROJ_DIR"

echo "$(date '+%Y-%m-%d %H:%M:%S') — Starting daily update"

# Step 1: Scrape latest PEAR ratings
echo "  [1/5] Refreshing PEAR ratings..."
python3 -m fsbb scrape 2>&1 | tail -2

# Step 2: Scrape yesterday's NCAA scores
echo "  [2/5] Importing NCAA scores..."
python3 -c "
from fsbb.db import init_db
from fsbb.scraper.ncaa import scrape_date
from datetime import date, timedelta
conn = init_db()
yesterday = date.today() - timedelta(days=1)
result = scrape_date(conn, yesterday)
print(f'    {yesterday}: {result[\"imported\"]} games imported')
# Also today's completed games
today_result = scrape_date(conn, date.today())
print(f'    {date.today()}: {today_result[\"imported\"]} games imported')
conn.close()
"

# Step 3: Recompute ratings
echo "  [3/5] Computing ratings..."
python3 -m fsbb rate 2>&1 | tail -3

# Step 4: Render prediction page
echo "  [4/5] Rendering prediction page..."
python3 -m fsbb render -o docs/index.html

# Step 5: Deploy to GitHub Pages
echo "  [5/5] Deploying..."
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
