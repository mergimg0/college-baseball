# Daily Forecast Pipeline — 7-Day Predictions System

**Date**: 2026-04-16
**Status**: Design Approved
**Stakeholder**: Ryan (wants daily pre-game predictions for upcoming matchups)
**Approach**: Surgical extension of existing pipeline (Approach 1)

---

## 1. Problem Statement

Ryan needs to pull up college baseball predictions each morning and see what the model says about that day's games before they play — plus a rolling 7-day forecast of upcoming matchups. The current system has the prediction engine, ratings, scraper, and renderer fully built, but:

1. **The daily cron has been dead for 8+ days.** A Python 3.9/3.10 compatibility bug in `db.py` crashes the pipeline at startup. Every log from April 8-15 shows the same `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'` at `db.py:99`.

2. **The scraper only imports finished games.** `scrape_date()` in `ncaa.py:96-99` filters out all non-final games (`if state not in ("final", "FIN"): skipped += 1; continue`). There is no code path to import scheduled/upcoming games into the database.

3. **The pipeline only looks at today.** `daily_update.sh` scrapes yesterday + today. No lookahead for future dates.

4. **The frontend shows one day.** The predictions template renders today's predictions and yesterday's results. No multi-day view.

## 2. Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Update frequency | Every 6 hours (4x/day) | Ratings stay fresh; afternoon games benefit from morning results; 6-hour cycle means broken runs surface quickly |
| Forecast window | Yesterday + today + 6 future days (8 tabs) | 7-day lookahead covers full weekend series; yesterday provides model grading |
| Day navigation | Tab-based selector | Clean navigation for 150+ game days; one day visible at a time |
| Today's games | Predictions transform in-place as results arrive | Ryan sees the model grading itself in real time |
| Yesterday's tab | Report card with accuracy summary | Daily feedback on model performance |
| Future days | Pure predictions | No results to show yet |
| Sorting | Top 25 matchups first, then by model confidence | Surfaces what matters; ranked matchups at top |
| Filtering | Conference dropdown (client-side JS) | Ryan can drill into specific leagues |
| Odds integration | Rolling — show edge data whenever odds are available | Odds API returns all futures in one call; free |
| Reliability | Client-side staleness banner | 8h = yellow warning, 24h = red warning |
| Architecture | Surgical extension of existing pipeline | 90% of infrastructure already works |

## 3. Pipeline Architecture

### 3.1 Cron Schedule

```cron
# From: once daily at 11 UTC
# 0 11 * * * /Users/mghome/projects/college-baseball/scripts/daily_update.sh

# To: every 6 hours — 03:00, 09:00, 15:00, 21:00 UTC
# (translates to 11pm, 5am, 11am, 5pm ET during EDT)
0 3,9,15,21 * * * /Users/mghome/projects/college-baseball/scripts/daily_update.sh
```

The 5am ET run gives Ryan fresh predictions before morning games. The 11am run captures early results and refreshes afternoon predictions. The 5pm run captures afternoon results. The 11pm run wraps up the day's results for tomorrow's report card.

### 3.2 Pipeline Steps (8-step, modified)

The existing `daily_update.sh` pipeline stays intact. Three steps change scope:

**Step 1 — Import NCAA scores (MODIFIED)**

```
Old: Scrape yesterday + today for FINAL games only
New: Scrape yesterday + today for FINAL games (results)
     Scrape today + next 7 days for ALL games (schedules)
```

Two loops:
- Results loop: `[today - 1, today]` with `include_scheduled=False` (existing behavior)
- Schedule loop: `[today, today+1, ..., today+7]` with `include_scheduled=True`

The NCAA API returns 150+ games per future day. At 1 request/day + 0.5s rate limit, the schedule loop takes ~4 seconds. Total Step 1 time: ~5 seconds.

**Step 5 — Fetch odds (MODIFIED)**

No code change needed. The Odds API already returns all available upcoming odds in a single call. The existing `store_odds()` function matches odds to games by team names and dates. Games for tomorrow and beyond that have odds will get matched automatically.

**Step 7 — Predict + render (MODIFIED)**

```
Old: predict_date(today) → render single-day template
New: predict_date(yesterday) through predict_date(today+6)
     → render 8-day tabbed template
```

Eight calls to `predict_date()`, each ~0.5s for 150 games = ~4 seconds total. The render function passes all 8 day-buckets to the template.

**Steps 2, 3, 4, 6, 8 — Unchanged.**

Box scores (step 2), play-by-play (step 3), game features (step 4), ratings (step 6), and git push (step 8) operate on whatever data exists and require no modifications.

### 3.3 Scheduled Game Lifecycle

```
Day -7:  NCAA API returns game as gameState="pre"
         → INSERT INTO games (status='scheduled', runs=NULL)
         → predict_date() generates win probability
         → Page shows prediction on Day -7's tab

Day -6 to -1:  Each 6-hour cycle:
         → ON CONFLICT DO UPDATE (no-op, data unchanged)
         → predict_date() regenerates (ratings may have shifted)
         → Prediction may drift slightly as ratings update

Day 0 (game day):
         → Morning cycle: still "pre", prediction shown
         → Game plays during the day
         → Next cycle: NCAA API returns gameState="final" with scores
         → ON CONFLICT DO UPDATE SET status='final', scores filled
         → predict_date() marks correct/incorrect
         → Page shows prediction + actual result side by side

Day +1:  Game appears in yesterday's report card tab
```

## 4. Data Layer Changes

### 4.1 Bug Fix: `fsbb/db.py`

Add `from __future__ import annotations` as the first import. This enables PEP 604 union syntax (`X | Y`) on Python 3.9, which is what cron's `/usr/bin/python3` resolves to. This is the single line that killed the pipeline.

The import already exists in `ncaa.py` (line 9) and `predict.py` (line 9). It was missed in `db.py`.

### 4.2 Scraper Modification: `fsbb/scraper/ncaa.py`

**`scrape_date()` signature change:**

```python
def scrape_date(conn, d, include_scheduled=False):
```

**Behavior change in the filter block (lines 96-99):**

```python
# Current:
if state not in ("final", "FIN"):
    skipped += 1
    continue

# New:
is_final = state in ("final", "FIN")
if not is_final and not include_scheduled:
    skipped += 1
    continue
```

For scheduled games (`include_scheduled=True`, game not final):
- `home_runs` = NULL
- `away_runs` = NULL
- `status` = 'scheduled'
- `actual_winner_id` = NULL
- All other fields populated normally (date, team IDs, source)

The existing upsert handles the `scheduled → final` transition:

```sql
ON CONFLICT(date, home_team_id, away_team_id) DO UPDATE SET
    home_runs=excluded.home_runs,
    away_runs=excluded.away_runs,
    status='final',
    actual_winner_id=excluded.actual_winner_id
```

When a game transitions from scheduled to final, the upsert overwrites NULL scores with actual scores and flips status to 'final'.

**One fix needed in the upsert for scheduled games:** The current upsert always sets `status='final'` in the DO UPDATE clause. For scheduled games re-imported as still scheduled, this would incorrectly flip them to final. The fix:

```sql
ON CONFLICT(date, home_team_id, away_team_id) DO UPDATE SET
    home_runs=excluded.home_runs,
    away_runs=excluded.away_runs,
    status=excluded.status,
    actual_winner_id=excluded.actual_winner_id,
    source=excluded.source
```

Using `excluded.status` instead of the hardcoded `'final'` string ensures scheduled games stay scheduled until they actually finish.

### 4.3 No Schema Changes

The existing `games` table already supports everything needed:

| Column | Type | Scheduled game value |
|--------|------|---------------------|
| `status` | TEXT | `'scheduled'` |
| `home_runs` | INTEGER (nullable) | NULL |
| `away_runs` | INTEGER (nullable) | NULL |
| `actual_winner_id` | INTEGER (nullable) | NULL |
| `our_home_win_prob` | REAL (nullable) | Filled by `predict_date()` |
| `our_predicted_winner_id` | INTEGER (nullable) | Filled by `predict_date()` |

The `predictions` table also works unchanged — `predict_date()` inserts predictions for any game regardless of status.

## 5. Prediction Engine

### 5.1 No Changes to Core Model

`predict_matchup()` and `predict_date()` in `fsbb/models/predict.py` require zero modifications. They already:

- Query games by date regardless of status (line 199-207)
- Generate predictions for any game where both teams have ratings
- Handle missing data gracefully (NULL pitcher data, missing features)
- Write predictions to both `predictions` and `games` tables

All 308 D1 teams currently have computed ratings (BT, Pythagorean, ELO). Any matchup between two known teams can be predicted immediately.

### 5.2 Prediction Updates Across Cycles

When `predict_date()` runs on the same date in a subsequent cycle, the existing upsert in `predict.py:252-259` updates the prediction:

```sql
ON CONFLICT(game_id, model_version) DO UPDATE SET
    home_win_prob=excluded.home_win_prob,
    predicted_total_runs=excluded.predicted_total_runs,
    created_at=datetime('now')
```

This means predictions naturally drift as ratings change. A game 7 days out gets predicted 28 times (4 cycles/day x 7 days). Each prediction uses the latest ratings. This is correct behavior — predictions should improve as more data comes in.

### 5.3 Accuracy Computation for Yesterday's Report Card

The existing `compute_accuracy()` function computes aggregate accuracy. For the yesterday report card, we need per-date accuracy. `predict_date()` already returns a `correct` field per prediction (line 243-248):

```python
if g["status"] == "final" and g["home_runs"] is not None:
    actual_home_won = g["home_runs"] > g["away_runs"]
    predicted_home_wins = pred["home_win_prob"] > 0.5
    pred["correct"] = actual_home_won == predicted_home_wins
```

The render function sums these to produce the report card stats. No new code needed.

## 6. Render Pipeline Changes

### 6.1 `render()` Command Modifications

The `render()` function in `__main__.py` currently calls `predict_date()` for today and yesterday. New behavior:

```python
from datetime import date, timedelta

today = date.today()
days = []
for offset in range(-1, 7):  # yesterday through today+6
    d = today + timedelta(days=offset)
    preds = predict_date(conn, d)
    
    # Compute daily accuracy for days with results
    correct = sum(1 for p in preds if p.get("correct") is True)
    total_final = sum(1 for p in preds if p.get("correct") is not None)
    
    days.append({
        "date": d.isoformat(),
        "date_label": d.strftime("%a %m/%d"),  # "Wed 04/16"
        "predictions": preds,
        "is_today": offset == 0,
        "is_yesterday": offset == -1,
        "games_correct": correct,
        "games_total": total_final,
        "accuracy": round(correct / total_final, 3) if total_final > 0 else None,
    })
```

The render function also enriches each prediction dict with conference data (not returned by `predict_date()`):

```python
for pred in preds:
    home_conf = conn.execute(
        "SELECT conference FROM teams WHERE name=?", (pred["home_team"],)
    ).fetchone()
    away_conf = conn.execute(
        "SELECT conference FROM teams WHERE name=?", (pred["away_team"],)
    ).fetchone()
    pred["home_conference"] = home_conf[0] if home_conf else ""
    pred["away_conference"] = away_conf[0] if away_conf else ""
```

The template receives `days` instead of separate `today_preds` / `yesterday_preds`.

### 6.2 Game Sorting: Marquee Score

Within each day, games are sorted by a marquee score before being passed to the template:

```python
def marquee_score(pred, rankings_top25):
    """Higher score = more prominent placement."""
    home_rank = rankings_top25.get(pred["home_team"], 999)
    away_rank = rankings_top25.get(pred["away_team"], 999)
    best_rank = min(home_rank, away_rank)
    
    if best_rank <= 25:
        return 1000 - best_rank  # Top 25 matchups first, #1 > #25
    else:
        return max(pred["home_win_prob"], 1 - pred["home_win_prob"]) * 100
```

Games sorted by `marquee_score` descending within each day. #1 vs #5 (score=999) sorts above #24 vs unranked (score=976), which sorts above unranked-vs-unranked at 72% confidence (score=72).

### 6.3 Odds Edge Data

Each prediction dict already contains `home_win_prob`. For games with odds, the render function adds edge data by joining against the games table:

```python
# For each prediction, check if odds exist
odds_row = conn.execute("""
    SELECT odds_implied_home_prob, odds_home_ml, odds_away_ml, odds_bookmaker
    FROM games WHERE id = ?
""", (pred["game_id"],)).fetchone()

if odds_row and odds_row["odds_implied_home_prob"]:
    pred["has_odds"] = True
    pred["vegas_prob"] = odds_row["odds_implied_home_prob"]
    pred["edge"] = pred["home_win_prob"] - odds_row["odds_implied_home_prob"]
    pred["home_ml"] = odds_row["odds_home_ml"]
    pred["away_ml"] = odds_row["odds_away_ml"]
    pred["bookmaker"] = odds_row["odds_bookmaker"]
```

The template conditionally shows the edge column when `has_odds` is true.

## 7. Frontend Template: `predictions.html`

### 7.1 Tab Bar Structure

```html
<div class="day-tabs">
  {% for day in days %}
  <button class="day-tab {% if day.is_today %}active{% endif %}"
          data-date="{{ day.date }}"
          onclick="showDay('{{ day.date }}')">
    {{ day.date_label }}
    {% if day.is_yesterday and day.accuracy is not none %}
      <span class="accuracy-badge">{{ (day.accuracy * 100)|round(0) }}%</span>
    {% endif %}
  </button>
  {% endfor %}
</div>
```

Today's tab is active by default. Yesterday's tab shows accuracy as a small badge.

### 7.2 Tab Content Panels

Each day gets a `<div class="day-panel" data-date="...">`:

**Yesterday panel**: Report card header + full results table.

```html
<div class="report-card">
  <span class="rc-stat">{{ day.games_correct }}/{{ day.games_total }} correct</span>
  <span class="rc-pct">{{ (day.accuracy * 100)|round(1) }}%</span>
</div>
```

Every game row shows: Home, Away, Prediction (original %), Pick, Actual Score, Result (check/X).

**Today panel**: Split into completed and upcoming sections.

```html
{% set completed = day.predictions|selectattr("status", "equalto", "final")|list %}
{% set upcoming = day.predictions|rejectattr("status", "equalto", "final")|list %}

{% if completed %}
<h3>Completed ({{ completed|length }})</h3>
<!-- Table with scores + correct/incorrect -->
{% endif %}

{% if upcoming %}
<h3>Upcoming ({{ upcoming|length }})</h3>
<!-- Table with predictions only -->
{% endif %}
```

**Future day panels**: Pure prediction table.

Each row: Home, Away, Pick, Win%, Confidence badge, Predicted Total, Edge (if odds available).

### 7.3 Conference Filter

```html
<select id="conf-filter" onchange="filterConference(this.value)">
  <option value="">All Conferences</option>
  {% for conf in conferences %}
  <option value="{{ conf }}">{{ conf }}</option>
  {% endfor %}
</select>
```

Each table row gets `data-home-conf="{{ pred.home_conference }}"` and `data-away-conf="{{ pred.away_conference }}"`. The JS filter matches games where **either** team is in the selected conference:

```javascript
function filterConference(conf) {
  document.querySelectorAll('.day-panel.active tr[data-home-conf]').forEach(tr => {
    var match = !conf || tr.dataset.homeConf === conf || tr.dataset.awayConf === conf;
    tr.style.display = match ? '' : 'none';
  });
}
```

### 7.4 Staleness Banner

Embedded in the page as a self-checking script:

```html
<div id="stale-banner" style="display:none" class="stale-warning"></div>
<script>
(function() {
  var generated = new Date("{{ generated_at_iso }}");
  var age = (Date.now() - generated.getTime()) / 3600000; // hours
  var banner = document.getElementById('stale-banner');
  if (age > 24) {
    banner.textContent = 'Pipeline may be down — predictions last updated ' +
      Math.round(age) + ' hours ago';
    banner.className = 'stale-warning stale-critical';
    banner.style.display = 'block';
  } else if (age > 8) {
    banner.textContent = 'Data may be stale — last updated ' +
      Math.round(age) + ' hours ago';
    banner.className = 'stale-warning stale-warn';
    banner.style.display = 'block';
  }
})();
</script>
```

### 7.5 Existing CSS Framework

The template already uses a dark theme with established CSS classes (`.prob-strong`, `.correct`, `.incorrect`, `.conf-high`, etc.). New elements follow the same design language:

- Tab bar: `.day-tabs` — flex row, dark background, matching `.navbar` styling
- Active tab: highlighted with existing `.nav-link.active` blue/purple scheme
- Report card: uses existing `.accuracy-banner` gradient styling
- Staleness banner: yellow/red using existing `.finding` component as base

No external CSS frameworks. No JavaScript frameworks. Pure static HTML/CSS/JS matching the existing design system.

## 8. Script Changes: `daily_update.sh`

### 8.1 Step 1 Modification

```bash
# Step 1: Scrape results (yesterday + today) and schedules (today + 7 days)
echo "[1/8] Importing NCAA scores and schedules..."
python3 -c "
from fsbb.db import init_db
from fsbb.scraper.ncaa import scrape_date
from datetime import date, timedelta

conn = init_db()
today = date.today()

# Import results (final games only)
for d in [today - timedelta(days=1), today]:
    result = scrape_date(conn, d, include_scheduled=False)
    print(f'  Results {d}: {result[\"imported\"]} imported, {result[\"skipped\"]} skipped')

# Import schedules (today + 7 days)
for offset in range(0, 8):
    d = today + timedelta(days=offset)
    result = scrape_date(conn, d, include_scheduled=True)
    print(f'  Schedule {d}: {result[\"imported\"]} imported, {result[\"skipped\"]} skipped')

conn.close()
"
```

### 8.2 Step 7 Modification

```bash
# Step 7: Generate predictions (yesterday through today+6) + render
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
```

### 8.3 No Other Step Changes

Steps 2-6 and 8 remain exactly as they are.

## 9. Backfill Strategy

One-time recovery before the new pipeline goes live:

```bash
# 1. Fix the Python bug (add import to db.py)
# Already done as part of implementation

# 2. Backfill 8 days of missing results
python3 -m fsbb scrape-ncaa --start 2026-04-08 --end 2026-04-15

# 3. Recompute ratings with fresh data
python3 -m fsbb rate

# 4. Run the new pipeline once manually
./scripts/daily_update.sh

# 5. Verify the page renders correctly
open docs/index.html
```

This is a manual one-time operation, not part of the automated pipeline.

## 10. NCAA API Contract

The system depends on a single external API:

- **Endpoint**: `https://ncaa-api.henrygd.me/scoreboard/baseball/d1/{yyyy}/{mm}/{dd}`
- **Rate limit**: 5 req/s (we use 1 req/0.5s)
- **Authentication**: None required
- **Cost**: Free
- **Data returned**: All D1 baseball games for a given date, including scheduled (gameState="pre") and completed (gameState="final")
- **Schedule availability**: Future dates return scheduled games with team names but no scores. Verified: April 17 returns 150 games, April 18 returns 159, April 19 returns 147.
- **Team name format**: `names.short` (e.g., "Mississippi St.", "South Carolina"). Same format for scheduled and final games. Compatible with existing `_resolve_team()` alias system.

**Failure mode**: If the API is down, `_fetch_scoreboard()` returns an empty list (line 37-39). The pipeline continues with zero games imported for that date. Next cycle retries. No crash, no data corruption.

**Pipeline request count per cycle**: 2 (results) + 8 (schedules) = 10 API calls. At 4 cycles/day = 40 calls/day. Well within rate limits.

## 11. Files Modified

| File | Change | Lines affected |
|------|--------|----------------|
| `fsbb/db.py` | Add `from __future__ import annotations` | +1 line at top |
| `fsbb/scraper/ncaa.py` | Add `include_scheduled` param to `scrape_date()` | ~15 lines modified |
| `fsbb/__main__.py` | Expand `render()` to 8-day predictions | ~40 lines in render command |
| `fsbb/templates/predictions.html` | Tab-based 7-day view, conference filter, staleness banner | Full template rewrite |
| `scripts/daily_update.sh` | Expand Step 1 (schedules) and Step 7 (multi-day predict) | ~20 lines |
| Crontab | Change schedule from daily to every 6 hours | 1 line |

No new files. No new dependencies. No schema migrations. No new tables.

## 12. Testing Plan

### 12.1 Data Layer Tests

- Verify `scrape_date(conn, d, include_scheduled=True)` imports scheduled games with NULL scores
- Verify `scrape_date(conn, d, include_scheduled=False)` skips scheduled games (backward compatible)
- Verify the upsert correctly transitions `scheduled → final` when scores arrive
- Verify re-importing a scheduled game as still scheduled does NOT flip status to 'final'

### 12.2 Prediction Tests

- Verify `predict_date()` generates predictions for scheduled games (both teams have ratings)
- Verify predictions update on subsequent cycles (upsert overwrites)
- Verify accuracy computation works for mixed scheduled/final days

### 12.3 Render Tests

- Verify 8 day-buckets are generated and passed to template
- Verify marquee scoring sorts Top 25 matchups first
- Verify conference filter shows/hides correct rows (manual browser test)
- Verify staleness banner appears when timestamp is >8 hours old

### 12.4 Pipeline Integration Test

- Run `daily_update.sh` manually end-to-end
- Verify all 8 steps complete without error
- Verify `docs/index.html` contains tab-based multi-day predictions
- Open in browser and verify tab switching, filtering, styling

### 12.5 Cron Test

- Install new crontab entry
- Verify next scheduled run executes and pushes to GitHub
- Verify GitHub Pages deploys the updated HTML

## 13. Rollback Plan

If the new pipeline causes issues:

1. Revert `daily_update.sh` to the previous version (git checkout)
2. Revert crontab to `0 11 * * *`
3. The `from __future__ import annotations` fix in `db.py` is safe to keep regardless — it's a no-op on Python 3.10+
4. Scheduled games in the database are inert — they don't affect ratings, backtests, or accuracy computation since those all filter on `status='final'`

## 14. Performance Budget

| Operation | Time per cycle | Notes |
|-----------|---------------|-------|
| NCAA API (10 calls) | ~5s | 0.5s rate limit between calls |
| Box score scrape | ~10s | Last 2 days only |
| PBP scrape | ~5s | Yesterday only |
| Rating computation | ~3s | BT convergence over 26K games |
| Calibration fit | ~2s | Grid search over completed games |
| Predictions (8 days) | ~4s | ~150 games/day x 8 days |
| Template render | ~1s | Jinja2 static render |
| Git commit + push | ~5s | HTML files only |
| **Total** | **~35s** | Well under 2-minute budget |

4 cycles/day x 35 seconds = 2.3 minutes of compute per day. Negligible.

## 15. Future Considerations (Not in Scope)

These are explicitly out of scope for this spec but noted for future reference:

- **Prediction drift tracking**: Storing historical prediction snapshots to show "this pick moved from 62% to 58% over the past 3 days." Would require a new table or removing the UNIQUE constraint on predictions. Deferred.
- **Push notifications**: Alerting Ryan when a high-value edge appears. Requires server infrastructure. Deferred.
- **Live in-game updates**: Real-time win probability during games. Requires abandoning static site architecture. Deferred.
- **Multi-model comparison**: Running V0 and V1 predictions side by side on the same games. The table already has `model_version` but the template doesn't expose it. Deferred.
