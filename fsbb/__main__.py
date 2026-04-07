"""ForgeStream Baseball CLI.

Commands:
    fsbb init          — Initialize database and import PEAR data
    fsbb scrape        — Refresh PEAR ratings from API
    fsbb rate          — Compute all ratings (Pythagorean, BT, SOS)
    fsbb rank          — Print team rankings
    fsbb matchup       — Predict a specific matchup
    fsbb predict       — Generate predictions for a date
    fsbb results       — Fill in results for completed games
    fsbb accuracy      — Show model accuracy vs PEAR
    fsbb render        — Render prediction page to HTML
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

import click
from tabulate import tabulate

from fsbb.db import DB_PATH, init_db, reset_db


@click.group()
def cli():
    """ForgeStream Baseball — NCAA D1 ratings and predictions."""
    pass


@cli.command()
@click.option("--fresh", is_flag=True, help="Reset database before init")
def init(fresh: bool):
    """Initialize database and import PEAR data."""
    from fsbb.scraper.pear import import_from_file

    if fresh:
        click.echo("Resetting database...")
        conn = reset_db()
    else:
        conn = init_db()

    # Import PEAR ratings
    pear_path = Path(__file__).parent.parent / "data" / "pear" / "pear_ratings.json"
    if pear_path.exists():
        count = import_from_file(conn, pear_path)
        click.echo(f"Imported {count} teams from PEAR ratings")
    else:
        click.echo(f"PEAR file not found at {pear_path}")

    click.echo(f"Database initialized at {DB_PATH}")
    conn.close()


@cli.command()
@click.option("--full", is_flag=True, help="Scrape all team details (slow, ~3 min)")
def scrape(full: bool):
    """Refresh PEAR ratings from API."""
    from fsbb.scraper.pear import fetch_ratings, import_from_file, scrape_all_team_details

    conn = init_db()

    click.echo("Fetching PEAR ratings...")
    teams = fetch_ratings()
    if teams:
        # Save to file
        pear_path = Path(__file__).parent.parent / "data" / "pear" / "pear_ratings.json"
        pear_path.parent.mkdir(parents=True, exist_ok=True)
        with open(pear_path, "w") as f:
            json.dump({"teams": teams}, f, indent=2)
        click.echo(f"Saved {len(teams)} teams to {pear_path}")

        # Import to database
        count = import_from_file(conn, pear_path)
        click.echo(f"Imported {count} teams into database")
    else:
        click.echo("Failed to fetch ratings from PEAR API")

    if full:
        click.echo("\nScraping all team details (RS/RA/games + schedules)...")
        summary = scrape_all_team_details(conn, progress=True)
        click.echo(f"Done: {summary['teams']} teams, {summary['games']} games imported")

    conn.close()


@cli.command()
def rate():
    """Compute all ratings (Pythagorean, Bradley-Terry, SOS)."""
    from fsbb.models.ratings import compute_all_ratings

    conn = init_db()
    click.echo("Computing ratings...")
    result = compute_all_ratings(conn)
    conn.close()

    click.echo(f"\nRating summary:")
    for k, v in result.items():
        if isinstance(v, float):
            click.echo(f"  {k}: {v:.4f}")
        else:
            click.echo(f"  {k}: {v}")


@cli.command()
@click.option("-n", "--top", default=25, help="Number of teams to show")
@click.option("--by", "sort_by", default="power_rating",
              type=click.Choice(["power_rating", "pythag_pct", "bt_rating", "sos",
                                 "pear_net", "pear_elo", "wins"]))
@click.option("--conference", "-c", help="Filter by conference")
@click.option("--json-out", is_flag=True, help="Output as JSON")
def rank(top: int, sort_by: str, conference: str | None, json_out: bool):
    """Print team rankings."""
    conn = init_db()

    query = "SELECT * FROM teams"
    params: list = []
    if conference:
        query += " WHERE conference = ?"
        params.append(conference)

    if sort_by in ("pear_net",):
        query += f" ORDER BY {sort_by} ASC"
    else:
        query += f" ORDER BY {sort_by} DESC NULLS LAST"
    query += " LIMIT ?"
    params.append(top)

    rows = conn.execute(query, params).fetchall()
    conn.close()

    if not rows:
        click.echo("No teams found. Run 'fsbb init' first.")
        return

    if json_out:
        click.echo(json.dumps([dict(r) for r in rows], indent=2))
        return

    table = []
    for i, r in enumerate(rows):
        table.append([
            i + 1,
            r["name"],
            r["conference"],
            f"{r['wins']}-{r['losses']}" if r["wins"] else "—",
            f"{r['pythag_pct']:.3f}" if r["pythag_pct"] else "—",
            f"{r['bt_rating']:.3f}" if r["bt_rating"] else "—",
            f"{r['power_rating']:.3f}" if r["power_rating"] else "—",
            r["pear_net"] or "—",
            f"{r['pear_elo']:.0f}" if r["pear_elo"] else "—",
        ])

    headers = ["#", "Team", "Conf", "Record", "Pythag", "BT", "Power", "PEAR NET", "PEAR ELO"]
    click.echo(tabulate(table, headers=headers, tablefmt="simple"))
    click.echo(f"\n{len(rows)} teams shown (sorted by {sort_by})")


@cli.command()
@click.argument("home")
@click.argument("away")
def matchup(home: str, away: str):
    """Predict a specific matchup (e.g., fsbb matchup Texas UCLA)."""
    from fsbb.models.predict import predict_matchup

    conn = init_db()
    result = predict_matchup(conn, home, away)
    conn.close()

    if not result:
        click.echo(f"Could not find one or both teams: '{home}', '{away}'")
        click.echo("Use exact PEAR names (e.g., 'Mississippi St.' not 'Mississippi State')")
        return

    click.echo(f"\n{'='*50}")
    click.echo(f"  {result['home_team']} vs {result['away_team']}")
    click.echo(f"{'='*50}")
    click.echo(f"  {result['home_team']:20s}  {result['home_win_prob']*100:5.1f}%  ({result['home_record']})")
    click.echo(f"  {result['away_team']:20s}  {result['away_win_prob']*100:5.1f}%  ({result['away_record']})")
    click.echo(f"  Predicted total runs: {result['predicted_total_runs']}")
    click.echo(f"  Confidence: {result['confidence']}")
    click.echo(f"  Model: {result['model_version']}")
    click.echo(f"\n  BT ratings: {result['home_team']} {result['home_bt_rating']:.3f} | "
               f"{result['away_team']} {result['away_bt_rating']:.3f}")
    click.echo(f"  Pythag:     {result['home_team']} {result['home_pythag']:.3f} | "
               f"{result['away_team']} {result['away_pythag']:.3f}")


@cli.command()
@click.option("--date", "target_date", default=None, help="Date to predict (YYYY-MM-DD)")
def predict(target_date: str | None):
    """Generate predictions for a date's games."""
    from fsbb.models.predict import predict_date

    conn = init_db()
    d = date.fromisoformat(target_date) if target_date else date.today()

    predictions = predict_date(conn, d)
    conn.close()

    if not predictions:
        click.echo(f"No games found for {d.isoformat()}")
        return

    click.echo(f"\nPredictions for {d.isoformat()} ({len(predictions)} games):\n")
    table = []
    for p in predictions:
        winner = p["home_team"] if p["home_win_prob"] > 0.5 else p["away_team"]
        conf = max(p["home_win_prob"], p["away_win_prob"])
        status = "✓" if p.get("correct") is True else ("✗" if p.get("correct") is False else "—")
        table.append([
            p["home_team"],
            p["away_team"],
            f"{p['home_win_prob']*100:.1f}%",
            winner,
            f"{conf*100:.1f}%",
            f"{p['predicted_total_runs']:.1f}",
            p["confidence"],
            status,
        ])

    headers = ["Home", "Away", "Home %", "Pick", "Conf", "Total", "Trust", "Result"]
    click.echo(tabulate(table, headers=headers, tablefmt="simple"))


@cli.command()
@click.option("--start", default=None, help="Start date (YYYY-MM-DD)")
@click.option("--end", default=None, help="End date (YYYY-MM-DD)")
@click.option("--min-games", default=10, help="Minimum games per team before predicting")
@click.option("--detail", is_flag=True, help="Show per-game details")
def backtest(start: str | None, end: str | None, min_games: int, detail: bool):
    """Backtest model against historical game outcomes."""
    from fsbb.models.backtest import run_backtest

    conn = init_db()
    click.echo(f"Running backtest (min {min_games} games per team)...")
    result = run_backtest(conn, start_date=start, end_date=end, min_games=min_games)
    conn.close()

    if "error" in result:
        click.echo(f"Error: {result['error']}")
        return

    click.echo(f"\n{'='*55}")
    click.echo(f"  Backtest Results")
    click.echo(f"{'='*55}")
    click.echo(f"  Games in DB:    {result['total_games_in_db']}")
    click.echo(f"  Evaluated:      {result['games_evaluated']}")
    click.echo(f"  Skipped:        {result['games_skipped']} (< {min_games} games played)")

    if result.get("our_accuracy") is not None:
        click.echo(f"\n  Our accuracy:   {result['our_accuracy']*100:.1f}% ({result['our_correct']}/{result['games_evaluated']})")
        click.echo(f"  Our Brier:      {result['our_brier']:.4f}")

    if result.get("pear_accuracy") is not None:
        click.echo(f"  PEAR accuracy:  {result['pear_accuracy']*100:.1f}%")
        click.echo(f"  PEAR Brier:     {result['pear_brier']:.4f}")
        edge = result.get("edge_accuracy", 0)
        click.echo(f"  Edge:           {edge*100:+.1f}%")

    if result.get("calibration"):
        click.echo(f"\n  Calibration:")
        for c in result["calibration"]:
            bar = "█" * int(c["count"] / 5)
            click.echo(f"    {c['bin']:>8s}: predicted={c['predicted']:.0%} actual={c['actual']:.0%} "
                       f"n={c['count']:3d} {bar}")

    if detail and result.get("detail"):
        click.echo(f"\n  Per-game details ({len(result['detail'])} games):")
        for r in result["detail"][-20:]:  # Last 20
            mark = "✓" if r["our_correct"] else "✗"
            click.echo(f"    {mark} {r['date'][:10]} {r['home']:18s} vs {r['away']:18s} "
                       f"prob={r['our_prob']:.0%} score={r['score']}")


@cli.command()
def odds():
    """Fetch and display current college baseball betting odds."""
    from fsbb.scraper.odds import fetch_odds, parse_odds, display_odds

    click.echo("Fetching college baseball odds (The Odds API)...")
    raw = fetch_odds()
    if not raw:
        click.echo("No odds data. Set ODDS_API_KEY env var.")
        click.echo("Get a free key at: https://the-odds-api.com")
        return

    parsed = parse_odds(raw)
    click.echo(f"\n{len(set(f'{p['home_team']} vs {p['away_team']}' for p in parsed))} games with odds:")
    display_odds(parsed)


@cli.command()
@click.option("--days", default=3, help="Days of box scores to scrape (0=full season)")
def pitchers(days: int):
    """Scrape pitcher box scores from NCAA API."""
    from fsbb.scraper.boxscore import scrape_season_boxscores, scrape_date_boxscores
    from datetime import timedelta

    conn = init_db()

    if days == 0:
        click.echo("Scraping full season box scores (this takes a while)...")
        result = scrape_season_boxscores(conn, max_days=50, progress=True)
    else:
        click.echo(f"Scraping last {days} days of box scores...")
        total_g, total_p = 0, 0
        for i in range(days):
            d = date.today() - timedelta(days=i+1)
            r = scrape_date_boxscores(conn, d)
            total_g += r["games"]
            total_p += r["pitchers"]
            click.echo(f"  {d}: {r['games']} games, {r['pitchers']} pitchers")
        result = {"games": total_g, "pitchers": total_p}

    click.echo(f"\nScraped {result['games']} games, {result['pitchers']} pitcher entries")

    # Show summary
    total = conn.execute("SELECT COUNT(*) FROM pitchers").fetchone()[0]
    starters = conn.execute(
        "SELECT COUNT(DISTINCT pitcher_id) FROM game_pitchers WHERE is_starter=1"
    ).fetchone()[0]
    click.echo(f"Database: {total} pitchers total, {starters} unique starters identified")
    conn.close()


@cli.command()
@click.option("--start", default=None, help="Start date YYYY-MM-DD")
@click.option("--end", default=None, help="End date YYYY-MM-DD")
@click.option("--limit", default=0, help="Max days to scrape (0=all)")
def scrape_pbp(start: str | None, end: str | None, limit: int):
    """Backfill play-by-play data from NCAA API."""
    from fsbb.scraper.boxscore import scrape_date_pbp

    conn = init_db()
    s = date.fromisoformat(start) if start else date(date.today().year, 2, 14)
    e = date.fromisoformat(end) if end else date.today() - timedelta(days=1)

    total_events = 0
    total_games = 0
    current = s
    days = 0

    while current <= e:
        result = scrape_date_pbp(conn, current)
        total_events += result["events"]
        total_games += result["games"]
        days += 1

        if days % 7 == 0:
            click.echo(f"  {current}: {total_games} games, {total_events} events")

        if limit > 0 and days >= limit:
            break

        current += timedelta(days=1)

    click.echo(f"Done: {total_games} games, {total_events} play events across {days} days")

    total = conn.execute("SELECT COUNT(*) FROM play_events").fetchone()[0]
    click.echo(f"Database: {total} total play events")
    conn.close()


@cli.command()
def accuracy():
    """Show model accuracy metrics vs PEAR."""
    from fsbb.models.predict import compute_accuracy

    conn = init_db()
    result = compute_accuracy(conn)
    conn.close()

    if result.get("games", 0) == 0:
        click.echo("No completed games with predictions yet.")
        click.echo("Run 'fsbb predict' on past dates, then 'fsbb results' to fill in outcomes.")
        return

    click.echo(f"\n{'='*50}")
    click.echo(f"  Model Accuracy Report")
    click.echo(f"{'='*50}")
    click.echo(f"  Games evaluated: {result['games']}")
    click.echo(f"  Our accuracy:    {result['our_accuracy']*100:.1f}% ({result['our_correct']}/{result['games']})")
    click.echo(f"  Our Brier score: {result['our_brier']:.4f}")

    if "pear_accuracy" in result:
        click.echo(f"\n  PEAR accuracy:   {result['pear_accuracy']*100:.1f}% ({result['pear_correct']}/{result['pear_games']})")
        click.echo(f"  PEAR Brier:      {result['pear_brier']:.4f}")
        click.echo(f"\n  Edge (accuracy): {result['edge_accuracy']*100:+.1f}%")
        click.echo(f"  Edge (Brier):    {result['edge_brier']:+.4f} (positive = we're better)")
    else:
        click.echo("\n  No PEAR comparison data available")


def _run_production_backtest(conn) -> dict:
    """Backtest using the PRODUCTION predict_matchup function.

    This ensures the accuracy number on the page reflects exactly
    what the live prediction system would produce — no model divergence.
    """
    from fsbb.models.predict import predict_matchup

    games = conn.execute("""
        SELECT h.name as home, a.name as away, g.home_runs, g.away_runs
        FROM games g
        JOIN teams h ON g.home_team_id = h.id
        JOIN teams a ON g.away_team_id = a.id
        WHERE g.status='final' AND g.home_runs IS NOT NULL
              AND h.games_played >= 10 AND a.games_played >= 10
              AND h.total_ra > 0 AND a.total_ra > 0
    """).fetchall()
    if not games:
        return {"games": 0}
    correct = 0
    brier = 0.0
    evaluated = 0
    for g in games:
        pred = predict_matchup(conn, g[0], g[1])
        if not pred:
            continue
        prob = pred["home_win_prob"]
        actual = 1.0 if g[2] > g[3] else 0.0
        if (prob > 0.5) == (actual == 1.0):
            correct += 1
        brier += (prob - actual) ** 2
        evaluated += 1
    if evaluated == 0:
        return {"games": 0}
    return {
        "games": evaluated,
        "our_correct": correct,
        "our_accuracy": round(correct / evaluated, 4),
        "our_brier": round(brier / evaluated, 4),
    }


@cli.command()
@click.option("--output", "-o", default=None, help="Output HTML file path")
def render(output: str | None):
    """Render the prediction page to static HTML."""
    from fsbb.models.predict import predict_date
    from jinja2 import Environment, FileSystemLoader

    conn = init_db()

    # Get today's predictions
    today = date.today()
    today_preds = predict_date(conn, today)

    # Get yesterday's results
    yesterday = today - timedelta(days=1)
    yesterday_preds = predict_date(conn, yesterday)

    # Get accuracy (production model backtest — same function as live predictions)
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

    conn.close()

    # Render template
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template("predictions.html")

    html = template.render(
        today=today.isoformat(),
        yesterday=yesterday.isoformat(),
        today_predictions=today_preds,
        yesterday_predictions=yesterday_preds,
        accuracy=acc,
        rankings=rankings,
        pythag_exp=pythag_exp,
        rpg=rpg,
        total_teams=total_teams,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    out_path = Path(output) if output else Path(__file__).parent.parent / "docs" / "predictions.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html)
    click.echo(f"Rendered to {out_path}")


@cli.command()
@click.option("--start", default=None, help="Start date YYYY-MM-DD")
@click.option("--end", default=None, help="End date YYYY-MM-DD")
@click.option("--threshold", default=100.0, help="Coverage % threshold for flagging gaps (default: 100)")
def coverage(start: str | None, end: str | None, threshold: float):
    """Audit box score coverage across the season."""
    conn = init_db()

    s = date.fromisoformat(start) if start else date(date.today().year, 2, 14)
    e = date.fromisoformat(end) if end else date.today() - timedelta(days=1)

    # Per-date breakdown
    rows = conn.execute("""
        SELECT g.date,
               COUNT(DISTINCT g.id) as total,
               COUNT(DISTINCT CASE WHEN gp.id IS NOT NULL THEN g.id END) as with_box
        FROM games g
        LEFT JOIN game_pitchers gp ON gp.game_id = g.id
        WHERE g.date >= ? AND g.date <= ? AND g.status = 'final'
        GROUP BY g.date
        ORDER BY g.date
    """, (s.isoformat(), e.isoformat())).fetchall()

    # Duplicate check
    dupes = conn.execute("""
        SELECT COUNT(*) FROM (
            SELECT date, home_team_id, away_team_id, COUNT(*) as cnt
            FROM games GROUP BY date, home_team_id, away_team_id HAVING cnt > 1
        )
    """).fetchone()[0]

    # Summary stats
    total_games = sum(r["total"] for r in rows)
    total_with_box = sum(r["with_box"] for r in rows)
    coverage_pct = (total_with_box / total_games * 100) if total_games else 0

    # Display per-date table
    gap_dates = []
    table = []
    for r in rows:
        total = r["total"]
        with_box = r["with_box"]
        pct = with_box / total * 100 if total else 0
        flag = "GAP" if pct < threshold and total > 0 else ""
        if flag:
            gap_dates.append(r["date"])
        table.append([r["date"], total, with_box, f"{pct:.1f}%", flag])

    click.echo(f"\n{'='*60}")
    click.echo(f"  Box Score Coverage Audit: {s} to {e}")
    click.echo(f"  Threshold: {threshold:.0f}%")
    click.echo(f"{'='*60}\n")

    headers = ["Date", "Games", "Box Scores", "Coverage", "Status"]
    click.echo(tabulate(table, headers=headers, tablefmt="simple"))

    # --- Missing Games Section (always shown) ---
    unmatched = conn.execute("""
        SELECT g.date, h.name as home, a.name as away, g.source
        FROM games g
        JOIN teams h ON g.home_team_id = h.id
        JOIN teams a ON g.away_team_id = a.id
        WHERE g.date >= ? AND g.date <= ? AND g.status = 'final'
        AND NOT EXISTS (SELECT 1 FROM game_pitchers gp WHERE gp.game_id = g.id)
        ORDER BY g.date
    """, (s.isoformat(), e.isoformat())).fetchall()

    total_missing = len(unmatched)

    click.echo(f"\n{'='*60}")
    click.echo(f"  Missing Games: {total_missing}")
    click.echo(f"{'='*60}")

    if unmatched:
        for u in unmatched:
            click.echo(f"  {u['date']}: {u['home']} vs {u['away']} (source: {u['source']})")
    else:
        click.echo("  None — all games have box score data.")

    # --- Summary ---
    click.echo(f"\n{'='*60}")
    click.echo(f"  Summary")
    click.echo(f"{'='*60}")
    click.echo(f"  Date range:        {s} to {e}")
    click.echo(f"  Total games:       {total_games}")
    click.echo(f"  With box scores:   {total_with_box}")
    click.echo(f"  Missing:           {total_missing}")
    click.echo(f"  Coverage:          {coverage_pct:.1f}%")
    click.echo(f"  Duplicate pairs:   {dupes}")
    click.echo(f"  Dates with gaps:   {len(gap_dates)} (below {threshold:.0f}%)")

    if gap_dates:
        click.echo(f"\n  Gap dates (<{threshold:.0f}% coverage):")
        for d in gap_dates:
            row = next(r for r in rows if r["date"] == d)
            click.echo(f"    {d}: {row['with_box']}/{row['total']} ({row['with_box']/row['total']*100:.1f}%)")

    conn.close()


if __name__ == "__main__":
    cli()
