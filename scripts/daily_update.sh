#!/bin/bash
# College Baseball Predictions — Daily Update Pipeline
# Runs: scrape → box scores → PBP → features → odds → rate → render → push
#
# Usage:   ./scripts/daily_update.sh
# Cron:    0 3,9,15,21 * * * /Users/mghome/projects/college-baseball/scripts/daily_update.sh
# Logs:    logs/daily-YYYY-MM-DD.log (auto-created)

set -euo pipefail

PROJ_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJ_DIR"

# Activate project venv so all dependencies (click, tabulate, etc.) are available
# shellcheck disable=SC1091
source "$PROJ_DIR/.venv/bin/activate"

# Logging
mkdir -p logs
LOG="logs/daily-$(date '+%Y-%m-%d').log"
exec > >(tee -a "$LOG") 2>&1

echo "========================================"
echo "$(date '+%Y-%m-%d %H:%M:%S') — Starting daily update"
echo "========================================"

# Load env (for ODDS_API_KEY)
[ -f .env ] && export $(grep -v '^#' .env | xargs)

# Step 1: Scrape results (yesterday+today) and schedules (today+7 days)
echo "[1/8] Importing NCAA scores and schedules..."
python3 -c "
from fsbb.db import init_db
from fsbb.scraper.ncaa import scrape_date
from datetime import date, timedelta
conn = init_db()
today = date.today()

# Results: yesterday and today (final games only)
for d in [today - timedelta(days=1), today]:
    result = scrape_date(conn, d, include_scheduled=False)
    print(f'  Results {d}: {result[\"imported\"]} imported, {result[\"skipped\"]} skipped')

# Schedules: today through today+7 (includes scheduled games)
for offset in range(0, 8):
    d = today + timedelta(days=offset)
    result = scrape_date(conn, d, include_scheduled=True)
    print(f'  Schedule {d}: {result[\"imported\"]} imported, {result[\"skipped\"]} skipped')

conn.close()
"

# Step 2: Scrape box scores (last 2 days)
echo "[2/8] Scraping pitcher box scores..."
python3 -m fsbb pitchers --days 2 2>&1 | tail -4

# Step 3: Scrape play-by-play (yesterday)
echo "[3/8] Scraping play-by-play..."
YESTERDAY=$(python3 -c "from datetime import date, timedelta; print((date.today()-timedelta(days=1)).isoformat())")
python3 -m fsbb scrape-pbp --start "$YESTERDAY" --end "$YESTERDAY" 2>&1 | tail -2

# Step 4: Compute series positions + game features
echo "[4/8] Computing game features..."
python3 -c "
from fsbb.db import init_db
from datetime import datetime
conn = init_db()

# Series positions
games = conn.execute('''
    SELECT id, date, home_team_id, away_team_id
    FROM games WHERE status='final' AND series_position IS NULL
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

# Day of week
for g in conn.execute('SELECT id, date FROM games WHERE day_of_week IS NULL').fetchall():
    d = datetime.fromisoformat(g[1]).date()
    conn.execute('UPDATE games SET day_of_week=? WHERE id=?', (d.weekday(), g[0]))
conn.commit()
print(f'  {updated} series positions, features updated')
conn.close()
"

# Step 5: Fetch odds (if API key available)
echo "[5/8] Fetching odds..."
if [ -n "${ODDS_API_KEY:-}" ]; then
    python3 -c "
from fsbb.db import init_db
from fsbb.scraper.odds import fetch_odds, parse_odds, store_odds
conn = init_db()
raw = fetch_odds()
if raw:
    parsed = parse_odds(raw)
    n = store_odds(conn, parsed)
    print(f'  Stored odds for {n} games')
else:
    print('  No odds available')
conn.close()
" || echo "  Odds fetch failed (non-fatal)"
else
    echo "  Skipped (ODDS_API_KEY not set)"
fi

# Step 6: Compute ratings + PBP stats + pitcher ratings
echo "[6/8] Computing ratings..."
python3 -m fsbb rate 2>&1 | tail -3
python3 -c "
from fsbb.db import init_db
from fsbb.models.pbp_stats import compute_team_pbp_stats, compute_bullpen_stats
from fsbb.models.pitcher_ratings import compute_pitcher_ratings
conn = init_db()
t = compute_team_pbp_stats(conn)
b = compute_bullpen_stats(conn)
p = compute_pitcher_ratings(conn)
print(f'  {t} team stats, {b} bullpen stats, {p} pitchers rated')
conn.close()
"

# Step 7: Generate predictions (yesterday through today+6) + render all pages
echo "[7/8] Generating predictions + rendering..."
python3 -c "
from fsbb.db import init_db
from fsbb.models.predict import predict_date
from datetime import date, timedelta
conn = init_db()
today = date.today()
for offset in range(-1, 7):
    d = today + timedelta(days=offset)
    preds = predict_date(conn, d)
    print(f'  {d}: {len(preds)} predictions')
conn.close()
"
python3 -m fsbb render 2>&1

# Step 8: Push to GitHub (triggers Pages auto-deploy)
echo "[8/8] Pushing to GitHub..."
cd "$PROJ_DIR"
git add docs/index.html docs/predictions.html docs/rankings.html docs/edge.html docs/backtest.html docs/wp.html docs/top25.html docs/history.html

alert() {
    local msg="$1"
    echo "  !! $msg"
    mkdir -p logs
    echo "$(date '+%Y-%m-%d %H:%M:%S') $msg" >> logs/push-failures.log
    # macOS desktop notification (best-effort, ignore if unavailable)
    osascript -e "display notification \"$msg\" with title \"college-baseball cron\"" 2>/dev/null || true
    # Visible marker file the developer can spot in `git status`
    date '+%Y-%m-%d %H:%M:%S' > .deploy-stuck
}

clear_stuck_marker() {
    [ -f .deploy-stuck ] && rm -f .deploy-stuck
}

# Disable -e for the push block so we can handle failures explicitly
set +e
if git diff --staged --quiet; then
    echo "  No changes to deploy"
    clear_stuck_marker
else
    git commit -m "daily: predictions update $(date '+%Y-%m-%d')"
    if git push origin main; then
        echo "  Pushed — Pages will auto-deploy"
        clear_stuck_marker
    else
        alert "git push origin main FAILED — commit is local only"
    fi
fi

# Final reconciliation: even if push said OK, verify HEAD matches origin
git fetch origin main --quiet 2>/dev/null
ahead=$(git rev-list --count origin/main..HEAD 2>/dev/null || echo "?")
if [ "$ahead" != "0" ]; then
    alert "Local is $ahead commits ahead of origin/main — site is STALE"
else
    clear_stuck_marker
fi
set -e

echo "========================================"
echo "$(date '+%Y-%m-%d %H:%M:%S') — Daily update complete"
echo "========================================"
