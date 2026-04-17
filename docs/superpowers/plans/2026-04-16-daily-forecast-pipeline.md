# Daily Forecast Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the broken daily pipeline, add scheduled game import, expand to 7-day rolling forecast with tab-based navigation, and switch to 6-hour update cycle.

**Architecture:** Surgical extension of existing pipeline. Four files modified (`db.py`, `ncaa.py`, `__main__.py`, `predictions.html`), one script updated (`daily_update.sh`), crontab changed. No new files, no new dependencies, no schema migrations.

**Tech Stack:** Python 3.13 (SQLite, Jinja2, Click), static HTML/CSS/JS, GitHub Pages, cron.

**Spec:** `docs/superpowers/specs/2026-04-16-daily-forecast-pipeline-design.md`

---

### Task 1: Fix Python Version Bug in db.py

**Files:**
- Modify: `fsbb/db.py:1-4`
- Test: `tests/test_db.py`

This is the single-line fix that has killed the cron pipeline for 8+ days. The `Path | None` union type syntax requires Python 3.10+, but cron runs `/usr/bin/python3` which is Python 3.9.6. Adding `from __future__ import annotations` makes it work on 3.9+.

- [ ] **Step 1: Add the future annotations import**

In `fsbb/db.py`, add `from __future__ import annotations` as the very first line, before all other imports:

```python
"""SQLite database connection and schema management."""
from __future__ import annotations

import sqlite3
from pathlib import Path
```

- [ ] **Step 2: Verify the fix works under Python 3.9 syntax rules**

Run the existing test suite to confirm nothing breaks:

```bash
cd /Users/mghome/projects/college-baseball && python3 -m pytest tests/test_db.py -v
```

Expected: All 4 tests pass (test_init_creates_tables, test_foreign_keys_enforced, test_schema_version_tracks, test_apply_migrations_idempotent).

- [ ] **Step 3: Verify the module imports cleanly**

```bash
cd /Users/mghome/projects/college-baseball && python3 -c "from fsbb.db import init_db; print('OK')"
```

Expected: Prints `OK` with no errors.

- [ ] **Step 4: Commit**

```bash
cd /Users/mghome/projects/college-baseball && git add fsbb/db.py && git commit -m "fix: add future annotations to db.py — fixes Python 3.9 cron crash"
```

---

### Task 2: Add Scheduled Game Import to scrape_date()

**Files:**
- Modify: `fsbb/scraper/ncaa.py:82-160`
- Test: `tests/test_scraper.py` (create)

The scraper currently skips all non-final games. We need to import scheduled games so the prediction engine can generate forecasts for upcoming matchups.

- [ ] **Step 1: Write tests for scheduled game import**

Create `tests/test_scraper.py`:

```python
"""Tests for fsbb.scraper.ncaa scheduled game import."""

import sqlite3
from pathlib import Path
from fsbb.db import init_db


def _setup_test_db():
    """Create a test DB with two teams."""
    test_path = Path("/tmp/test_fsbb_scraper.db")
    if test_path.exists():
        test_path.unlink()
    conn = init_db(test_path)
    conn.execute("INSERT INTO teams (name, conference) VALUES ('Texas', 'Big 12')")
    conn.execute("INSERT INTO teams (name, conference) VALUES ('UCLA', 'Big Ten')")
    conn.commit()
    return conn, test_path


def test_scrape_date_skips_scheduled_by_default():
    """scrape_date with include_scheduled=False should skip non-final games."""
    conn, path = _setup_test_db()
    from unittest.mock import patch
    fake_games = [{"game": {
        "gameState": "pre",
        "home": {"names": {"short": "Texas"}, "score": ""},
        "away": {"names": {"short": "UCLA"}, "score": ""},
    }}]
    with patch("fsbb.scraper.ncaa._fetch_scoreboard", return_value=fake_games):
        from fsbb.scraper.ncaa import scrape_date
        from datetime import date
        result = scrape_date(conn, date(2026, 4, 20), include_scheduled=False)
    assert result["imported"] == 0
    assert result["skipped"] == 1
    count = conn.execute("SELECT COUNT(*) FROM games").fetchone()[0]
    assert count == 0
    conn.close()
    path.unlink()


def test_scrape_date_imports_scheduled_when_enabled():
    """scrape_date with include_scheduled=True should import pre-game entries."""
    conn, path = _setup_test_db()
    from unittest.mock import patch
    fake_games = [{"game": {
        "gameState": "pre",
        "home": {"names": {"short": "Texas"}, "score": ""},
        "away": {"names": {"short": "UCLA"}, "score": ""},
    }}]
    with patch("fsbb.scraper.ncaa._fetch_scoreboard", return_value=fake_games):
        from fsbb.scraper.ncaa import scrape_date
        from datetime import date
        result = scrape_date(conn, date(2026, 4, 20), include_scheduled=True)
    assert result["imported"] == 1
    game = conn.execute("SELECT status, home_runs, away_runs, actual_winner_id FROM games").fetchone()
    assert game[0] == "scheduled"
    assert game[1] is None
    assert game[2] is None
    assert game[3] is None
    conn.close()
    path.unlink()


def test_scrape_date_scheduled_to_final_upsert():
    """A scheduled game should update to final when scores arrive."""
    conn, path = _setup_test_db()
    from unittest.mock import patch
    from fsbb.scraper.ncaa import scrape_date
    from datetime import date

    # First: import as scheduled
    pre_games = [{"game": {
        "gameState": "pre",
        "home": {"names": {"short": "Texas"}, "score": ""},
        "away": {"names": {"short": "UCLA"}, "score": ""},
    }}]
    with patch("fsbb.scraper.ncaa._fetch_scoreboard", return_value=pre_games):
        scrape_date(conn, date(2026, 4, 20), include_scheduled=True)

    # Second: import as final with scores
    final_games = [{"game": {
        "gameState": "final",
        "home": {"names": {"short": "Texas"}, "score": "5"},
        "away": {"names": {"short": "UCLA"}, "score": "3"},
    }}]
    with patch("fsbb.scraper.ncaa._fetch_scoreboard", return_value=final_games):
        scrape_date(conn, date(2026, 4, 20), include_scheduled=False)

    # Should be exactly 1 game (upserted, not duplicated)
    count = conn.execute("SELECT COUNT(*) FROM games").fetchone()[0]
    assert count == 1
    game = conn.execute("SELECT status, home_runs, away_runs FROM games").fetchone()
    assert game[0] == "final"
    assert game[1] == 5
    assert game[2] == 3
    conn.close()
    path.unlink()


def test_scrape_date_re_import_scheduled_stays_scheduled():
    """Re-importing a scheduled game that's still scheduled should NOT flip to final."""
    conn, path = _setup_test_db()
    from unittest.mock import patch
    from fsbb.scraper.ncaa import scrape_date
    from datetime import date

    pre_games = [{"game": {
        "gameState": "pre",
        "home": {"names": {"short": "Texas"}, "score": ""},
        "away": {"names": {"short": "UCLA"}, "score": ""},
    }}]
    with patch("fsbb.scraper.ncaa._fetch_scoreboard", return_value=pre_games):
        scrape_date(conn, date(2026, 4, 20), include_scheduled=True)
        scrape_date(conn, date(2026, 4, 20), include_scheduled=True)

    game = conn.execute("SELECT status FROM games").fetchone()
    assert game[0] == "scheduled"
    conn.close()
    path.unlink()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/mghome/projects/college-baseball && python3 -m pytest tests/test_scraper.py -v
```

Expected: All 4 tests FAIL — `scrape_date()` does not accept `include_scheduled` parameter.

- [ ] **Step 3: Modify scrape_date() to accept scheduled games**

In `fsbb/scraper/ncaa.py`, replace the `scrape_date` function (lines 82-160) with:

```python
def scrape_date(conn: sqlite3.Connection, d: date, include_scheduled: bool = False) -> dict:
    """Scrape and import all D1 games for a single date.

    Args:
        conn: Database connection
        d: Date to scrape
        include_scheduled: If True, also import games that haven't started yet

    Returns: {"date": str, "found": int, "imported": int, "skipped": int}
    """
    raw_games = _fetch_scoreboard(d)
    date_str = d.isoformat()
    imported = 0
    skipped = 0

    for entry in raw_games:
        g = entry.get("game", {})
        state = g.get("gameState", "")

        is_final = state in ("final", "FIN")

        # Skip non-final games unless include_scheduled is True
        if not is_final and not include_scheduled:
            skipped += 1
            continue

        home_info = g.get("home", {})
        away_info = g.get("away", {})

        home_name = home_info.get("names", {}).get("short") or home_info.get("names", {}).get("full", "")
        away_name = away_info.get("names", {}).get("short") or away_info.get("names", {}).get("full", "")

        if not home_name or not away_name:
            skipped += 1
            continue

        # For final games, require scores
        if is_final:
            home_score = home_info.get("score")
            away_score = away_info.get("score")

            if home_score is None or away_score is None:
                skipped += 1
                continue

            try:
                home_runs = int(home_score)
                away_runs = int(away_score)
            except (ValueError, TypeError):
                skipped += 1
                continue

            if home_runs > away_runs:
                winner_id_value = "home"
            elif away_runs > home_runs:
                winner_id_value = "away"
            else:
                winner_id_value = None
            game_status = "final"
        else:
            # Scheduled game — no scores yet
            home_runs = None
            away_runs = None
            winner_id_value = None
            game_status = "scheduled"

        # Resolve team IDs
        home_id = _resolve_team(conn, home_name)
        away_id = _resolve_team(conn, away_name)

        if not home_id or not away_id:
            skipped += 1
            continue

        # Determine winner ID
        if winner_id_value == "home":
            winner_id = home_id
        elif winner_id_value == "away":
            winner_id = away_id
        else:
            winner_id = None

        try:
            conn.execute("""
                INSERT INTO games (date, home_team_id, away_team_id, home_runs, away_runs,
                                   status, actual_winner_id, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'ncaa')
                ON CONFLICT(date, home_team_id, away_team_id) DO UPDATE SET
                    home_runs=excluded.home_runs,
                    away_runs=excluded.away_runs,
                    status=excluded.status,
                    actual_winner_id=excluded.actual_winner_id,
                    source=excluded.source
            """, (date_str, home_id, away_id, home_runs, away_runs, game_status, winner_id))
            imported += 1
        except sqlite3.IntegrityError:
            skipped += 1

    conn.commit()
    return {"date": date_str, "found": len(raw_games), "imported": imported, "skipped": skipped}
```

Key changes from the original:
1. New `include_scheduled` parameter (default `False` for backward compatibility)
2. Non-final games imported as `status='scheduled'` with NULL scores
3. Upsert uses `excluded.status` instead of hardcoded `'final'` — prevents scheduled games from being incorrectly flipped to final on re-import

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /Users/mghome/projects/college-baseball && python3 -m pytest tests/test_scraper.py -v
```

Expected: All 4 tests PASS.

- [ ] **Step 5: Run full test suite to verify no regressions**

```bash
cd /Users/mghome/projects/college-baseball && python3 -m pytest tests/ -v --tb=short
```

Expected: 34 passed (30 original + 4 new), 1 failed (pre-existing HFA threshold).

- [ ] **Step 6: Commit**

```bash
cd /Users/mghome/projects/college-baseball && git add fsbb/scraper/ncaa.py tests/test_scraper.py && git commit -m "feat: add scheduled game import to scrape_date()

scrape_date(conn, d, include_scheduled=True) now imports games with
gameState='pre' as status='scheduled' with NULL scores. The upsert
uses excluded.status so scheduled games stay scheduled until the NCAA
API reports them as final."
```

---

### Task 3: Update daily_update.sh for 7-Day Lookahead

**Files:**
- Modify: `scripts/daily_update.sh`

The daily script needs two changes: Step 1 imports schedules for today+7, Step 7 predicts all 8 days.

- [ ] **Step 1: Replace Step 1 in daily_update.sh**

In `scripts/daily_update.sh`, replace the Step 1 block (lines 27-37) with:

```bash
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
```

- [ ] **Step 2: Replace Step 7 in daily_update.sh**

In `scripts/daily_update.sh`, replace the Step 7 block (lines 127-131) with:

```bash
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
```

- [ ] **Step 3: Update the header comment**

Replace line 6 of `scripts/daily_update.sh`:

```bash
# Cron:    0 3,9,15,21 * * * /Users/mghome/projects/college-baseball/scripts/daily_update.sh
```

- [ ] **Step 4: Test the script runs without error**

```bash
cd /Users/mghome/projects/college-baseball && bash scripts/daily_update.sh 2>&1 | tail -30
```

Expected: All 8 steps complete. Step 1 shows results + schedule imports. Step 7 shows predictions for 8 dates.

- [ ] **Step 5: Commit**

```bash
cd /Users/mghome/projects/college-baseball && git add scripts/daily_update.sh && git commit -m "feat: expand daily pipeline to 7-day lookahead with scheduled games

Step 1 now imports schedules for today+7 days. Step 7 generates
predictions for yesterday through today+6. Pipeline runs every 6 hours."
```

---

### Task 4: Update render() for 8-Day Prediction Buckets

**Files:**
- Modify: `fsbb/__main__.py:499-621` (render command)

The render function needs to generate predictions for 8 dates and pass them to the template as a structured list.

- [ ] **Step 1: Rewrite the render command's prediction section**

In `fsbb/__main__.py`, replace the render command (from `@cli.command()` at line 499 through the end of the `# 1. Predictions page` block ending at line 621) with:

```python
@cli.command()
@click.option("--output", "-o", default=None, help="Output HTML file path")
def render(output: str | None):
    """Render the prediction page to static HTML."""
    from fsbb.models.predict import predict_date
    from jinja2 import Environment, FileSystemLoader

    conn = init_db()
    today = date.today()

    # Build Top 25 lookup for marquee sorting
    top25_rows = conn.execute("""
        SELECT name FROM teams WHERE games_played >= 10 AND total_ra > 0
        ORDER BY power_rating DESC LIMIT 25
    """).fetchall()
    rankings_top25 = {row["name"]: i + 1 for i, row in enumerate(top25_rows)}

    def marquee_score(pred):
        """Higher score = more prominent placement."""
        home_rank = rankings_top25.get(pred["home_team"], 999)
        away_rank = rankings_top25.get(pred["away_team"], 999)
        best_rank = min(home_rank, away_rank)
        if best_rank <= 25:
            return 1000 - best_rank
        else:
            return max(pred["home_win_prob"], 1 - pred["home_win_prob"]) * 100

    # Generate predictions for 8 days: yesterday through today+6
    days = []
    for offset in range(-1, 7):
        d = today + timedelta(days=offset)
        preds = predict_date(conn, d)

        # Enrich with conference data and odds
        for pred in preds:
            home_conf = conn.execute(
                "SELECT conference FROM teams WHERE name=?", (pred["home_team"],)
            ).fetchone()
            away_conf = conn.execute(
                "SELECT conference FROM teams WHERE name=?", (pred["away_team"],)
            ).fetchone()
            pred["home_conference"] = home_conf["conference"] if home_conf else ""
            pred["away_conference"] = away_conf["conference"] if away_conf else ""

            # Add odds edge data if available
            if pred.get("game_id"):
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
                    pred["bookmaker"] = odds_row["odds_bookmaker"] or ""
                else:
                    pred["has_odds"] = False
            else:
                pred["has_odds"] = False

        # Sort by marquee score
        preds.sort(key=marquee_score, reverse=True)

        # Compute daily accuracy for days with results
        correct = sum(1 for p in preds if p.get("correct") is True)
        total_final = sum(1 for p in preds if p.get("correct") is not None)

        days.append({
            "date": d.isoformat(),
            "date_label": d.strftime("%a %m/%d"),
            "predictions": preds,
            "is_today": offset == 0,
            "is_yesterday": offset == -1,
            "games_correct": correct,
            "games_total": total_final,
            "accuracy": round(correct / total_final, 3) if total_final > 0 else None,
        })

    # Get accuracy (production model backtest)
    acc = _run_production_backtest(conn)

    # Get rankings
    rankings = [dict(r) for r in conn.execute("""
        SELECT name, conference, wins, losses, pythag_pct, power_rating, pear_net
        FROM teams WHERE games_played >= 10 AND total_ra > 0
        ORDER BY power_rating DESC LIMIT 25
    """).fetchall()]

    # Model stats
    stats_row = conn.execute("""
        SELECT AVG(total_rs + total_ra) * 1.0 / AVG(games_played) as rpg,
               COUNT(*) as total_teams
        FROM teams WHERE games_played > 0 AND total_ra > 0
    """).fetchone()
    rpg = stats_row[0] if stats_row and stats_row[0] else 12.0
    total_teams = stats_row[1] if stats_row else 308

    # Pythagenport exponent
    from fsbb.models.ratings import pythagenport_exponent
    total_rs = conn.execute("SELECT SUM(total_rs) FROM teams WHERE total_ra > 0").fetchone()[0] or 1
    total_ra = conn.execute("SELECT SUM(total_ra) FROM teams WHERE total_ra > 0").fetchone()[0] or 1
    total_gp = conn.execute("SELECT SUM(games_played) FROM teams WHERE total_ra > 0").fetchone()[0] or 1
    pythag_exp = pythagenport_exponent(total_rs, total_ra, total_gp)

    # Full rankings (all teams)
    all_rankings = [dict(r) for r in conn.execute("""
        SELECT name, conference, wins, losses, pythag_pct, power_rating, pear_net,
               elo, bt_rating, sos
        FROM teams WHERE games_played >= 5 AND total_ra > 0
        ORDER BY power_rating DESC
    """).fetchall()]

    conferences = sorted(set(r["conference"] for r in all_rankings))

    # Edge calculator data
    edge_rows = conn.execute("""
        SELECT h.name as home, a.name as away,
               g.our_home_win_prob, g.odds_implied_home_prob,
               g.odds_home_ml, g.odds_away_ml, g.odds_bookmaker
        FROM games g
        JOIN teams h ON g.home_team_id = h.id
        JOIN teams a ON g.away_team_id = a.id
        WHERE g.our_home_win_prob IS NOT NULL AND g.odds_implied_home_prob IS NOT NULL
        ORDER BY ABS(g.our_home_win_prob - g.odds_implied_home_prob) DESC
    """).fetchall()

    all_edges = []
    value_picks = []
    agree_count = 0
    for e in edge_rows:
        our_pct = e["our_home_win_prob"] * 100
        vegas_pct = e["odds_implied_home_prob"] * 100
        edge = our_pct - vegas_pct
        our_pick = e["home"] if our_pct > 50 else e["away"]
        vegas_pick = e["home"] if vegas_pct > 50 else e["away"]
        if our_pick == vegas_pick:
            agree_count += 1
        entry = {
            "home": e["home"], "away": e["away"],
            "our_pct": our_pct, "vegas_pct": vegas_pct,
            "edge": edge, "abs_edge": abs(edge),
            "pick": our_pick,
            "home_ml": e["odds_home_ml"], "bookmaker": e["odds_bookmaker"] or "",
        }
        all_edges.append(entry)
        if abs(edge) > 5:
            value_picks.append(entry)

    conn.close()

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    generated_at_iso = datetime.now().isoformat()

    # Render all pages
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    docs_dir = Path(output).parent if output else Path(__file__).parent.parent / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    # System stats for the home page
    conn2 = init_db()
    sys_stats = {
        "total_games": f"{conn2.execute('SELECT COUNT(*) FROM games WHERE status=\"final\"').fetchone()[0]:,}",
        "pbp_events": f"{conn2.execute('SELECT COUNT(*) FROM play_events').fetchone()[0] / 1_000_000:.2f}M",
        "rated_pitchers": f"{conn2.execute('SELECT COUNT(*) FROM pitchers WHERE quality_rating IS NOT NULL').fetchone()[0]:,}",
        "seasons": 4,
        "pitcher_appearances": f"{conn2.execute('SELECT COUNT(*) FROM game_pitchers').fetchone()[0]:,}",
    }
    conn2.close()

    # 1. Predictions page
    html = env.get_template("predictions.html").render(
        days=days,
        accuracy=acc,
        rankings=rankings,
        conferences=conferences,
        pythag_exp=pythag_exp,
        rpg=rpg,
        total_teams=total_teams,
        generated_at=generated_at,
        generated_at_iso=generated_at_iso,
        sys_stats=sys_stats,
    )
    (docs_dir / "predictions.html").write_text(html)
    (docs_dir / "index.html").write_text(html)
    click.echo(f"Rendered predictions -> {docs_dir / 'index.html'}")
```

Note: Everything after `# 2. Rankings page` (line 623 onward) stays exactly the same. Only the predictions page rendering changes.

- [ ] **Step 2: Verify the render command runs**

```bash
cd /Users/mghome/projects/college-baseball && python3 -m fsbb render 2>&1
```

Expected: "Rendered predictions -> .../docs/index.html" plus all other pages. May show warnings about missing scheduled games (until backfill in Task 6).

- [ ] **Step 3: Commit**

```bash
cd /Users/mghome/projects/college-baseball && git add fsbb/__main__.py && git commit -m "feat: expand render() to 8-day predictions with marquee sorting and odds

render() now generates predictions for yesterday through today+6,
enriches each with conference data and odds edge, sorts by marquee
score (Top 25 first), and passes structured day-buckets to template."
```

---

### Task 5: Rewrite predictions.html Template

**Files:**
- Modify: `fsbb/templates/predictions.html`

Full template rewrite for tab-based 7-day navigation. The template receives `days` (list of 8 day-buckets) instead of `today_predictions`/`yesterday_predictions`.

- [ ] **Step 1: Write the new predictions.html template**

Replace the entire contents of `fsbb/templates/predictions.html` with:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>College Baseball Predictions -- NCAA D1</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, 'Segoe UI', system-ui, sans-serif; background: #0a0e17; color: #c8ccd4; line-height: 1.5; }
  a { color: #4fc3f7; text-decoration: none; }
  a:hover { text-decoration: underline; }
  .container { max-width: 1100px; margin: 0 auto; padding: 16px 20px; }
  .header { border-bottom: 1px solid #1a2035; padding-bottom: 16px; margin-bottom: 20px; }
  .header h1 { color: #e8eaed; font-size: 1.5em; font-weight: 700; letter-spacing: -0.5px; }
  .header .tagline { color: #6b7280; font-size: 0.85em; margin-top: 2px; }
  .header .meta { color: #4b5563; font-size: 0.75em; margin-top: 8px; }
  .accuracy-banner { background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); border: 1px solid #312e81;
    border-radius: 10px; padding: 20px; margin: 16px 0 24px; display: flex; gap: 40px; flex-wrap: wrap; align-items: center; }
  .accuracy-banner .stat { text-align: center; min-width: 80px; }
  .accuracy-banner .stat .value { font-size: 2em; font-weight: 800; color: #a5b4fc; line-height: 1.1; }
  .accuracy-banner .stat .label { font-size: 0.7em; color: #6b7280; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }
  .accuracy-banner .stat.edge .value { color: #34d399; }
  .accuracy-banner .stat.negative .value { color: #f87171; }
  .accuracy-banner .divider { width: 1px; height: 48px; background: #312e81; }
  table { width: 100%; border-collapse: collapse; }
  thead th { background: #111827; color: #9ca3af; padding: 8px 12px; text-align: left;
    font-size: 0.7em; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 600; position: sticky; top: 48px; z-index: 50; }
  tbody td { padding: 10px 12px; border-bottom: 1px solid #111827; font-size: 0.88em; }
  tbody tr:hover { background: #0f172a; }
  .prob { font-weight: 700; font-variant-numeric: tabular-nums; }
  .prob-strong { color: #34d399; }
  .prob-mid { color: #fbbf24; }
  .prob-weak { color: #9ca3af; }
  .pick { font-weight: 600; color: #e8eaed; }
  .pick-away { color: #a5b4fc; }
  .correct { color: #34d399; font-weight: 700; }
  .incorrect { color: #f87171; font-weight: 700; }
  .pending { color: #4b5563; }
  .score { font-variant-numeric: tabular-nums; color: #9ca3af; }
  .conf { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.7em; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
  .conf-high { background: #064e3b; color: #34d399; }
  .conf-medium { background: #451a03; color: #fbbf24; }
  .conf-low { background: #1f2937; color: #6b7280; }
  .rankings-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 8px; }
  .rank-card { background: #111827; border: 1px solid #1f2937; border-radius: 6px; padding: 10px 14px;
    display: flex; align-items: center; gap: 12px; transition: border-color 0.2s; }
  .rank-card:hover { border-color: #312e81; }
  .rank-num { font-size: 1.1em; font-weight: 800; color: #4b5563; min-width: 28px; text-align: right; }
  .rank-num.top5 { color: #a5b4fc; }
  .rank-num.top10 { color: #818cf8; }
  .rank-team { flex: 1; }
  .rank-name { font-weight: 600; color: #e8eaed; font-size: 0.9em; }
  .rank-conf { font-size: 0.7em; color: #6b7280; }
  .rank-stats { text-align: right; font-size: 0.8em; }
  .rank-record { color: #9ca3af; font-weight: 600; }
  .rank-pythag { color: #6b7280; font-size: 0.75em; }
  .finding { background: linear-gradient(135deg, #1e1b4b 0%, #172554 100%); border: 1px solid #312e81;
    border-radius: 8px; padding: 16px 20px; margin: 16px 0; }
  .finding .label { font-size: 0.7em; text-transform: uppercase; letter-spacing: 1.5px; color: #818cf8; font-weight: 700; margin-bottom: 4px; }
  .finding .text { color: #c7d2fe; font-size: 0.9em; }
  .finding .number { font-size: 1.4em; font-weight: 800; color: #a5b4fc; }
  .about { background: #111827; border: 1px solid #1f2937; border-radius: 8px; padding: 20px; margin: 32px 0; }
  .about h3 { color: #e8eaed; margin-bottom: 12px; font-size: 1em; }
  .about p { color: #9ca3af; font-size: 0.85em; margin-bottom: 8px; }
  .navbar { background: #111827; border-bottom: 1px solid #1f2937; position: sticky; top: 0; z-index: 100; }
  .nav-container { max-width: 1100px; margin: 0 auto; padding: 0 20px; display: flex; align-items: center; height: 48px; gap: 32px; }
  .nav-brand { font-weight: 800; font-size: 1em; color: #a5b4fc; letter-spacing: -0.5px; }
  .nav-brand:hover { text-decoration: none; color: #c7d2fe; }
  .nav-links { display: flex; gap: 4px; }
  .nav-link { padding: 6px 14px; border-radius: 6px; font-size: 0.8em; font-weight: 500; color: #9ca3af; transition: all 0.15s; }
  .nav-link:hover { background: #1f2937; color: #e8eaed; text-decoration: none; }
  .nav-link.active { background: #312e81; color: #c7d2fe; }
  .footer { margin-top: 40px; padding-top: 16px; border-top: 1px solid #111827; color: #374151; font-size: 0.75em; text-align: center; }

  /* Day tabs */
  .day-tabs { display: flex; gap: 4px; margin: 20px 0 16px; overflow-x: auto; padding-bottom: 4px; }
  .day-tab { padding: 8px 16px; border-radius: 8px; font-size: 0.82em; font-weight: 600; color: #9ca3af;
    background: #111827; border: 1px solid #1f2937; cursor: pointer; white-space: nowrap; transition: all 0.15s; }
  .day-tab:hover { background: #1f2937; color: #e8eaed; }
  .day-tab.active { background: #312e81; color: #c7d2fe; border-color: #4338ca; }
  .day-tab .badge { display: inline-block; margin-left: 6px; padding: 1px 6px; border-radius: 10px;
    font-size: 0.75em; font-weight: 700; }
  .badge-accuracy { background: #064e3b; color: #34d399; }
  .badge-today { background: #4338ca; color: #c7d2fe; }

  /* Report card */
  .report-card { background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); border: 1px solid #312e81;
    border-radius: 10px; padding: 16px 24px; margin-bottom: 16px; display: flex; gap: 32px; align-items: center; flex-wrap: wrap; }
  .rc-stat { font-size: 1.1em; color: #a5b4fc; font-weight: 700; }
  .rc-pct { font-size: 2em; font-weight: 800; color: #34d399; }

  /* Section divider */
  .section-divider { color: #6b7280; font-size: 0.8em; font-weight: 600; text-transform: uppercase;
    letter-spacing: 1px; margin: 24px 0 12px; padding-bottom: 6px; border-bottom: 1px solid #1f2937; }

  /* Staleness */
  .stale-warning { padding: 10px 20px; text-align: center; font-size: 0.85em; font-weight: 600; border-radius: 6px; margin-bottom: 12px; }
  .stale-warn { background: #451a03; color: #fbbf24; border: 1px solid #92400e; }
  .stale-critical { background: #450a0a; color: #f87171; border: 1px solid #991b1b; }

  /* Conference filter */
  .filter-bar { margin-bottom: 12px; }
  .filter-bar select { background: #111827; color: #c8ccd4; border: 1px solid #1f2937; border-radius: 6px;
    padding: 6px 12px; font-size: 0.82em; cursor: pointer; }

  /* Day panel */
  .day-panel { display: none; }
  .day-panel.active { display: block; }

  @media (max-width: 640px) {
    .accuracy-banner { gap: 20px; padding: 14px; }
    .accuracy-banner .stat .value { font-size: 1.5em; }
    .accuracy-banner .divider { display: none; }
    .rankings-grid { grid-template-columns: 1fr; }
    table { font-size: 0.82em; }
    td, th { padding: 6px 8px; }
    .day-tabs { gap: 2px; }
    .day-tab { padding: 6px 10px; font-size: 0.75em; }
  }
</style>
</head>
<body>
<nav class="navbar">
  <div class="nav-container">
    <a href="index.html" class="nav-brand">CBP</a>
    <div class="nav-links">
      <a href="index.html" class="nav-link active">Predictions</a>
      <a href="rankings.html" class="nav-link">Rankings</a>
      <a href="edge.html" class="nav-link">Edge</a>
      <a href="backtest.html" class="nav-link">Accuracy</a>
      <a href="wp.html" class="nav-link">Win Prob</a>
      <a href="top25.html" class="nav-link">Top 25</a>
    </div>
  </div>
</nav>

<div id="stale-banner" style="display:none" class="stale-warning"></div>

<div class="container">
  <div class="header">
    <h1>College Baseball Predictions</h1>
    <div class="tagline">NCAA D1 Game Predictions &mdash; 7-Day Rolling Forecast</div>
    <div class="meta">Updated {{ generated_at }} | {{ total_teams }} teams | {{ sys_stats.total_games|default('26,052') }} games | {{ sys_stats.seasons|default(4) }} seasons | Refreshes every 6 hours</div>
  </div>

  {% if accuracy and accuracy.games > 0 %}
  <div class="accuracy-banner">
    <div class="stat">
      <div class="value">{{ (accuracy.our_accuracy * 100) | round(1) }}%</div>
      <div class="label">Accuracy</div>
    </div>
    <div class="divider"></div>
    <div class="stat">
      <div class="value">{{ accuracy.games }}</div>
      <div class="label">Games Tested</div>
    </div>
    <div class="divider"></div>
    <div class="stat">
      <div class="value">{{ accuracy.our_brier | round(3) }}</div>
      <div class="label">Brier Score</div>
    </div>
    {% if accuracy.pear_accuracy is defined %}
    <div class="divider"></div>
    <div class="stat {% if accuracy.edge_accuracy > 0 %}edge{% else %}negative{% endif %}">
      <div class="value">{{ "%+.1f" | format(accuracy.edge_accuracy * 100) }}%</div>
      <div class="label">vs PEAR ELO</div>
    </div>
    {% endif %}
  </div>
  {% endif %}

  <!-- Day tabs -->
  <div class="day-tabs">
    {% for day in days %}
    <button class="day-tab {% if day.is_today %}active{% endif %}" onclick="showDay('{{ day.date }}')" data-date="{{ day.date }}">
      {% if day.is_yesterday %}Yest{% else %}{{ day.date_label }}{% endif %}
      {% if day.is_today %}<span class="badge badge-today">Today</span>{% endif %}
      {% if day.is_yesterday and day.accuracy is not none %}<span class="badge badge-accuracy">{{ (day.accuracy * 100)|round(0)|int }}%</span>{% endif %}
      {% if not day.is_yesterday and not day.is_today %}({{ day.predictions|length }}){% endif %}
    </button>
    {% endfor %}
  </div>

  <!-- Conference filter -->
  <div class="filter-bar">
    <select id="conf-filter" onchange="filterConference(this.value)">
      <option value="">All Conferences</option>
      {% for conf in conferences %}
      <option value="{{ conf }}">{{ conf }}</option>
      {% endfor %}
    </select>
  </div>

  <!-- Day panels -->
  {% for day in days %}
  <div class="day-panel {% if day.is_today %}active{% endif %}" data-date="{{ day.date }}">

    {% if day.is_yesterday %}
    <!-- Yesterday: Report card -->
    {% if day.games_total > 0 %}
    <div class="report-card">
      <div><span class="rc-stat">Yesterday's Results</span></div>
      <div><span class="rc-pct">{{ (day.accuracy * 100)|round(1) }}%</span></div>
      <div><span class="rc-stat">{{ day.games_correct }}/{{ day.games_total }} correct</span></div>
    </div>
    {% endif %}
    <table>
      <thead><tr><th></th><th>Home</th><th>Away</th><th>Our Pick</th><th>Win %</th><th>Score</th><th></th></tr></thead>
      <tbody>
      {% for p in day.predictions %}
        {% set winner = p.home_team if p.home_win_prob > 0.5 else p.away_team %}
        {% set conf_pct = [p.home_win_prob, p.away_win_prob] | max %}
        <tr data-home-conf="{{ p.home_conference }}" data-away-conf="{{ p.away_conference }}">
          <td class="{% if p.correct is sameas true %}correct{% elif p.correct is sameas false %}incorrect{% else %}pending{% endif %}">{% if p.correct is sameas true %}&#10003;{% elif p.correct is sameas false %}&#10007;{% else %}&mdash;{% endif %}</td>
          <td>{{ p.home_team }}</td>
          <td>{{ p.away_team }}</td>
          <td class="{% if p.home_win_prob > 0.5 %}pick{% else %}pick-away{% endif %}">{{ winner }}</td>
          <td class="prob {% if conf_pct > 0.65 %}prob-strong{% elif conf_pct > 0.55 %}prob-mid{% else %}prob-weak{% endif %}">{{ (conf_pct * 100)|round(1) }}%</td>
          <td class="score">{% if p.actual_home_runs is not none %}{{ p.actual_home_runs }}&ndash;{{ p.actual_away_runs }}{% else %}&mdash;{% endif %}</td>
          <td class="{% if p.correct is sameas true %}correct{% elif p.correct is sameas false %}incorrect{% else %}pending{% endif %}">{% if p.correct is sameas true %}Correct{% elif p.correct is sameas false %}Wrong{% else %}Pending{% endif %}</td>
        </tr>
      {% endfor %}
      </tbody>
    </table>

    {% elif day.is_today %}
    <!-- Today: Split completed/upcoming -->
    {% set completed = [] %}
    {% set upcoming = [] %}
    {% for p in day.predictions %}
      {% if p.status == "final" %}
        {% if completed.append(p) %}{% endif %}
      {% else %}
        {% if upcoming.append(p) %}{% endif %}
      {% endif %}
    {% endfor %}

    {% if completed|length > 0 %}
    <div class="section-divider">Completed ({{ completed|length }})</div>
    <table>
      <thead><tr><th></th><th>Home</th><th>Away</th><th>Pick</th><th>Win %</th><th>Score</th><th></th></tr></thead>
      <tbody>
      {% for p in completed %}
        {% set winner = p.home_team if p.home_win_prob > 0.5 else p.away_team %}
        {% set conf_pct = [p.home_win_prob, p.away_win_prob] | max %}
        <tr data-home-conf="{{ p.home_conference }}" data-away-conf="{{ p.away_conference }}">
          <td class="{% if p.correct is sameas true %}correct{% elif p.correct is sameas false %}incorrect{% else %}pending{% endif %}">{% if p.correct is sameas true %}&#10003;{% elif p.correct is sameas false %}&#10007;{% else %}&mdash;{% endif %}</td>
          <td>{{ p.home_team }}</td>
          <td>{{ p.away_team }}</td>
          <td class="{% if p.home_win_prob > 0.5 %}pick{% else %}pick-away{% endif %}">{{ winner }}</td>
          <td class="prob {% if conf_pct > 0.65 %}prob-strong{% elif conf_pct > 0.55 %}prob-mid{% else %}prob-weak{% endif %}">{{ (conf_pct * 100)|round(1) }}%</td>
          <td class="score">{{ p.actual_home_runs }}&ndash;{{ p.actual_away_runs }}</td>
          <td class="{% if p.correct is sameas true %}correct{% elif p.correct is sameas false %}incorrect{% endif %}">{% if p.correct is sameas true %}Correct{% elif p.correct is sameas false %}Wrong{% endif %}</td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
    {% endif %}

    {% if upcoming|length > 0 %}
    <div class="section-divider">Upcoming ({{ upcoming|length }})</div>
    <table>
      <thead><tr><th>Home</th><th>Away</th><th>Pick</th><th>Win %</th><th>Conf</th><th>Total</th>{% if upcoming|selectattr("has_odds")|list|length > 0 %}<th>Edge</th>{% endif %}</tr></thead>
      <tbody>
      {% for p in upcoming %}
        {% set winner = p.home_team if p.home_win_prob > 0.5 else p.away_team %}
        {% set conf_pct = [p.home_win_prob, p.away_win_prob] | max %}
        <tr data-home-conf="{{ p.home_conference }}" data-away-conf="{{ p.away_conference }}">
          <td>{{ p.home_team }}</td>
          <td>{{ p.away_team }}</td>
          <td class="{% if p.home_win_prob > 0.5 %}pick{% else %}pick-away{% endif %}">{{ winner }}</td>
          <td class="prob {% if conf_pct > 0.65 %}prob-strong{% elif conf_pct > 0.55 %}prob-mid{% else %}prob-weak{% endif %}">{{ (conf_pct * 100)|round(1) }}%</td>
          <td><span class="conf conf-{{ p.confidence }}">{{ p.confidence }}</span></td>
          <td class="score">{{ p.predicted_total_runs }}</td>
          {% if upcoming|selectattr("has_odds")|list|length > 0 %}
          <td>{% if p.has_odds %}<span style="color:{% if p.edge > 0.05 %}#34d399{% elif p.edge < -0.05 %}#f87171{% else %}#9ca3af{% endif %}">{{ "%+.1f"|format(p.edge * 100) }}%</span>{% else %}&mdash;{% endif %}</td>
          {% endif %}
        </tr>
      {% endfor %}
      </tbody>
    </table>
    {% endif %}

    {% if completed|length == 0 and upcoming|length == 0 %}
    <p style="color: #4b5563; padding: 20px 0;">No games scheduled for today.</p>
    {% endif %}

    {% else %}
    <!-- Future day: Pure predictions -->
    {% if day.predictions|length > 0 %}
    <table>
      <thead><tr><th>Home</th><th>Away</th><th>Pick</th><th>Win %</th><th>Conf</th><th>Total</th>{% if day.predictions|selectattr("has_odds")|list|length > 0 %}<th>Edge</th>{% endif %}</tr></thead>
      <tbody>
      {% for p in day.predictions %}
        {% set winner = p.home_team if p.home_win_prob > 0.5 else p.away_team %}
        {% set conf_pct = [p.home_win_prob, p.away_win_prob] | max %}
        <tr data-home-conf="{{ p.home_conference }}" data-away-conf="{{ p.away_conference }}">
          <td>{{ p.home_team }}</td>
          <td>{{ p.away_team }}</td>
          <td class="{% if p.home_win_prob > 0.5 %}pick{% else %}pick-away{% endif %}">{{ winner }}</td>
          <td class="prob {% if conf_pct > 0.65 %}prob-strong{% elif conf_pct > 0.55 %}prob-mid{% else %}prob-weak{% endif %}">{{ (conf_pct * 100)|round(1) }}%</td>
          <td><span class="conf conf-{{ p.confidence }}">{{ p.confidence }}</span></td>
          <td class="score">{{ p.predicted_total_runs }}</td>
          {% if day.predictions|selectattr("has_odds")|list|length > 0 %}
          <td>{% if p.has_odds %}<span style="color:{% if p.edge > 0.05 %}#34d399{% elif p.edge < -0.05 %}#f87171{% else %}#9ca3af{% endif %}">{{ "%+.1f"|format(p.edge * 100) }}%</span>{% else %}&mdash;{% endif %}</td>
          {% endif %}
        </tr>
      {% endfor %}
      </tbody>
    </table>
    {% else %}
    <p style="color: #4b5563; padding: 20px 0;">No games scheduled. Schedule data typically appears 3-5 days in advance.</p>
    {% endif %}

    {% endif %}
  </div>
  {% endfor %}

  <!-- Power Rankings -->
  <div style="margin-top: 32px; border-bottom: 1px solid #1a2035; padding-bottom: 6px;">
    <h2 style="color: #e8eaed; font-size: 1.1em; font-weight: 600;">Power Rankings <span style="color: #6b7280; font-size: 0.85em; font-weight: 400;">Top 25</span></h2>
  </div>
  <div class="rankings-grid" style="margin-top: 12px;">
    {% for t in rankings[:25] %}
    <div class="rank-card">
      <div class="rank-num {% if loop.index <= 5 %}top5{% elif loop.index <= 10 %}top10{% endif %}">{{ loop.index }}</div>
      <div class="rank-team">
        <div class="rank-name">{{ t.name }}</div>
        <div class="rank-conf">{{ t.conference }}</div>
      </div>
      <div class="rank-stats">
        <div class="rank-record">{{ t.wins }}-{{ t.losses }}</div>
        <div class="rank-pythag">{{ (t.pythag_pct * 100) | round(1) }}%</div>
      </div>
    </div>
    {% endfor %}
  </div>

  <div class="about" id="about">
    <h3>How It Works</h3>
    <p>College Baseball Predictions uses a three-layer prediction model to generate calibrated win probabilities for every NCAA D1 baseball game.</p>
    <p><strong>Layer 1:</strong> Pythagenport Expected Win% with variable exponent calibrated for college baseball ({{ "%.2f" | format(pythag_exp) }}, not MLB's 1.83).</p>
    <p><strong>Layer 2:</strong> Dynamic Bradley-Terry ratings via MM algorithm with temporal decay.</p>
    <p><strong>Layer 3:</strong> Log5 matchup probability with home-field adjustment (~53% baseline).</p>
    <p style="margin-top: 12px;">Predictions refresh every 6 hours. Ratings update as new results come in, so predictions for future games improve over time.</p>
  </div>

  <div class="footer">
    <p>College Baseball Predictions | Data: NCAA, PEAR, The Odds API | Model: Pythagenport + Bradley-Terry + Platt Calibration</p>
  </div>
</div>

<script>
function showDay(date) {
  document.querySelectorAll('.day-tab').forEach(function(t) {
    t.classList.toggle('active', t.dataset.date === date);
  });
  document.querySelectorAll('.day-panel').forEach(function(p) {
    p.classList.toggle('active', p.dataset.date === date);
  });
  // Reset conference filter when switching days
  document.getElementById('conf-filter').value = '';
  filterConference('');
}

function filterConference(conf) {
  document.querySelectorAll('.day-panel.active tr[data-home-conf]').forEach(function(tr) {
    var match = !conf || tr.dataset.homeConf === conf || tr.dataset.awayConf === conf;
    tr.style.display = match ? '' : 'none';
  });
}

// Staleness check
(function() {
  var generated = new Date("{{ generated_at_iso }}");
  var age = (Date.now() - generated.getTime()) / 3600000;
  var banner = document.getElementById('stale-banner');
  if (age > 24) {
    banner.textContent = 'Pipeline may be down \u2014 predictions last updated ' + Math.round(age) + ' hours ago';
    banner.className = 'stale-warning stale-critical';
    banner.style.display = 'block';
  } else if (age > 8) {
    banner.textContent = 'Data may be stale \u2014 last updated ' + Math.round(age) + ' hours ago';
    banner.className = 'stale-warning stale-warn';
    banner.style.display = 'block';
  }
})();
</script>
</body>
</html>
```

- [ ] **Step 2: Verify the template renders without Jinja2 errors**

```bash
cd /Users/mghome/projects/college-baseball && python3 -m fsbb render 2>&1
```

Expected: "Rendered predictions -> .../docs/index.html" with no Jinja2 template errors.

- [ ] **Step 3: Open in browser and verify**

```bash
open /Users/mghome/projects/college-baseball/docs/index.html
```

Expected: Page loads with dark theme, tab bar showing 8 days, today's tab active, conference filter dropdown visible. Content may be sparse until backfill (Task 6).

- [ ] **Step 4: Commit**

```bash
cd /Users/mghome/projects/college-baseball && git add fsbb/templates/predictions.html && git commit -m "feat: tab-based 7-day predictions template

8-day tab navigation (yesterday + today + 6 future days). Yesterday
shows report card with accuracy. Today splits completed/upcoming.
Future days show pure predictions. Conference filter, marquee sorting,
staleness banner, odds edge column."
```

---

### Task 6: Backfill Missing Data and First Full Run

**Files:**
- None (operational commands only)

One-time recovery to bring the database current after the 8-day outage.

- [ ] **Step 1: Backfill April 8-15 results**

```bash
cd /Users/mghome/projects/college-baseball && python3 -m fsbb scrape-ncaa --start 2026-04-08 --end 2026-04-15
```

Expected: ~700-800 games imported across 8 days.

- [ ] **Step 2: Recompute all ratings with fresh data**

```bash
cd /Users/mghome/projects/college-baseball && python3 -m fsbb rate
```

Expected: Ratings recomputed, Platt calibration refitted, pitcher ratings updated.

- [ ] **Step 3: Run the full pipeline manually**

```bash
cd /Users/mghome/projects/college-baseball && bash scripts/daily_update.sh 2>&1 | tail -40
```

Expected: All 8 steps complete successfully. Step 1 imports schedules for today+7. Step 7 generates predictions for 8 dates. Step 8 pushes to GitHub.

- [ ] **Step 4: Verify the page in browser**

```bash
open /Users/mghome/projects/college-baseball/docs/index.html
```

Expected: Tab bar shows 8 days with game counts. Today and future tabs show predictions. Yesterday tab shows report card. Conference filter works. No staleness banner (just generated).

- [ ] **Step 5: Verify specific dates Ryan asked about**

```bash
cd /Users/mghome/projects/college-baseball && python3 -c "
import sqlite3
conn = sqlite3.connect('data/fsbb.db')
for d in ['2026-04-16', '2026-04-17', '2026-04-18', '2026-04-19']:
    total = conn.execute('SELECT COUNT(*) FROM games WHERE date=?', (d,)).fetchone()[0]
    predicted = conn.execute('SELECT COUNT(*) FROM games WHERE date=? AND our_home_win_prob IS NOT NULL', (d,)).fetchone()[0]
    print(f'{d}: {total} games, {predicted} with predictions')
conn.close()
"
```

Expected: April 17-19 each show 140-160 games with predictions.

---

### Task 7: Update Crontab to 6-Hour Cycle

**Files:**
- System crontab

- [ ] **Step 1: Show current crontab**

```bash
crontab -l
```

Expected: Shows the old `0 11 * * *` entry.

- [ ] **Step 2: Update crontab**

Update the college baseball cron entry from daily to every 6 hours. The user will need to confirm this change:

```bash
crontab -l | sed 's|0 11 \* \* \* /Users/mghome/projects/college-baseball/scripts/daily_update.sh|0 3,9,15,21 * * * /Users/mghome/projects/college-baseball/scripts/daily_update.sh|' | crontab -
```

- [ ] **Step 3: Verify updated crontab**

```bash
crontab -l
```

Expected: Shows `0 3,9,15,21 * * * /Users/mghome/projects/college-baseball/scripts/daily_update.sh`.

- [ ] **Step 4: Commit the pipeline changes**

```bash
cd /Users/mghome/projects/college-baseball && git add -A docs/ && git commit -m "daily: first 7-day forecast pipeline run — predictions for $(date '+%Y-%m-%d') through $(date -v+6d '+%Y-%m-%d')"
```

---

### Task 8: Run Full Test Suite and Final Verification

**Files:**
- Test: `tests/`

- [ ] **Step 1: Run all tests**

```bash
cd /Users/mghome/projects/college-baseball && python3 -m pytest tests/ -v --tb=short
```

Expected: 34+ passed (30 original + 4 new scraper tests), 1 pre-existing marginal fail (HFA threshold).

- [ ] **Step 2: Verify cron Python compatibility**

```bash
/usr/bin/python3 -c "from fsbb.db import init_db; print('OK')"
```

Expected: Prints `OK`. This confirms the `from __future__ import annotations` fix works under the cron Python (3.9.6).

- [ ] **Step 3: Verify the NCAA API import for future dates**

```bash
cd /Users/mghome/projects/college-baseball && python3 -c "
from fsbb.db import init_db
from fsbb.scraper.ncaa import scrape_date
from datetime import date, timedelta
conn = init_db()
for offset in range(1, 8):
    d = date.today() + timedelta(days=offset)
    result = scrape_date(conn, d, include_scheduled=True)
    print(f'{d}: {result[\"imported\"]} scheduled games imported')
conn.close()
"
```

Expected: Each future date shows 100-160 scheduled games imported.

- [ ] **Step 4: Verify prediction generation for future dates**

```bash
cd /Users/mghome/projects/college-baseball && python3 -c "
from fsbb.db import init_db
from fsbb.models.predict import predict_date
from datetime import date, timedelta
conn = init_db()
for offset in range(0, 7):
    d = date.today() + timedelta(days=offset)
    preds = predict_date(conn, d)
    print(f'{d}: {len(preds)} predictions')
conn.close()
"
```

Expected: Today + next 6 days each show predictions. Future days should have 100-160 predictions each.
