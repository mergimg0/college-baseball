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

    # Fit Platt calibration from completed games
    from fsbb.models.predict import fit_calibration
    click.echo("Fitting calibration...")
    cal = fit_calibration(conn)
    click.echo(f"  Platt scaling: a={cal['a']:.2f}, b={cal['b']:.2f}")

    # Recompute pitcher quality ratings
    from fsbb.models.pitcher_ratings import compute_pitcher_ratings
    click.echo("Computing pitcher ratings...")
    n_rated = compute_pitcher_ratings(conn)
    click.echo(f"  {n_rated} pitchers rated")

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
@click.option("--simulate", is_flag=True, help="Run Monte Carlo simulation for spread/total distributions")
def predict(target_date: str | None, simulate: bool):
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
        row = [
            p["home_team"],
            p["away_team"],
            f"{p['home_win_prob']*100:.1f}%",
            winner,
            f"{conf*100:.1f}%",
            f"{p['predicted_total_runs']:.1f}",
            p["confidence"],
            status,
        ]
        table.append(row)

    headers = ["Home", "Away", "Home %", "Pick", "Conf", "Total", "Trust", "Result"]
    click.echo(tabulate(table, headers=headers, tablefmt="simple"))

    if simulate:
        from fsbb.models.simulator import simulate_game, compute_over_under
        click.echo(f"\n{'='*60}")
        click.echo(f"  Monte Carlo Simulation (10,000 sims per game)")
        click.echo(f"{'='*60}\n")
        sim_table = []
        for p in predictions:
            total = p.get("predicted_total_runs") or 12.0  # college avg ~12 RPG
            home_rpg = total / 2 + 0.5
            away_rpg = total / 2 - 0.5
            sim = simulate_game(home_rpg, away_rpg, p["home_win_prob"])
            sim_table.append([
                f"{p['home_team'][:15]} v {p['away_team'][:15]}",
                f"{sim['home_win_pct']*100:.1f}%",
                f"{sim['avg_total_runs']:.1f}",
                f"{sim['spread_median']:+.1f}",
                f"{sim['total_dist']['p10']}-{sim['total_dist']['p90']}",
            ])
        sim_headers = ["Game", "Sim Win%", "Sim Total", "Spread", "Total 80% CI"]
        click.echo(tabulate(sim_table, headers=sim_headers, tablefmt="simple"))


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


@cli.command(name="backtest-multi")
@click.option("--seasons", default=None, help="Comma-separated seasons (e.g., 2023,2024,2025,2026)")
def backtest_multi(seasons: str | None):
    """Run walk-forward backtest across multiple seasons."""
    from fsbb.models.multi_season import run_multi_season_backtest

    conn = init_db()
    s_list = [int(s) for s in seasons.split(",")] if seasons else None
    result = run_multi_season_backtest(conn, seasons=s_list, progress=True)
    conn.close()

    if result.get("aggregate"):
        agg = result["aggregate"]
        click.echo(f"\nAggregate: {agg['accuracy']:.1%} on {agg['total_games']} games (Brier: {agg['brier']:.4f})")
        if agg.get("exponents"):
            click.echo(f"Exponents: {agg['exponents']}")


@cli.command()
def odds():
    """Fetch and display current college baseball betting odds."""
    from fsbb.scraper.odds import fetch_odds, parse_odds, display_odds, store_odds

    click.echo("Fetching college baseball odds (The Odds API)...")
    raw = fetch_odds()
    if not raw:
        click.echo("No odds data. Set ODDS_API_KEY env var.")
        click.echo("Get a free key at: https://the-odds-api.com")
        return

    parsed = parse_odds(raw)
    game_count = len(set(p["home_team"] + " vs " + p["away_team"] for p in parsed))
    click.echo(f"\n{game_count} games with odds:")
    display_odds(parsed)

    # Store odds to database
    conn = init_db()
    stored = store_odds(conn, parsed)
    conn.close()
    click.echo(f"\n  {stored} games matched and stored to database")


@cli.command(name="scrape-ncaa")
@click.option("--start", default=None, help="Start date (YYYY-MM-DD, default: Feb 14)")
@click.option("--end", default=None, help="End date (YYYY-MM-DD, default: yesterday)")
@click.option("--season", default=None, type=int, help="Scrape an entire historical season (e.g., 2025)")
def scrape_ncaa(start: str | None, end: str | None, season: int | None):
    """Scrape NCAA scoreboard for game scores."""
    from fsbb.scraper.ncaa import scrape_season

    conn = init_db()
    if season:
        s = date(season, 2, 14)
        e = date(season, 6, 30)
        click.echo(f"Scraping {season} season ({s} to {e})...")
    else:
        s = date.fromisoformat(start) if start else date(date.today().year, 2, 14)
        e = date.fromisoformat(end) if end else date.today() - timedelta(days=1)
        click.echo(f"Scraping {s} to {e}...")

    result = scrape_season(conn, start=s, end=e)
    conn.close()
    click.echo(f"Done: {result['games_imported']} games imported, {result['games_skipped']} skipped ({result['days_scraped']} days)")


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
    """Run honest walk-forward backtest for the accuracy banner.

    Uses the chronological backtest engine (no data leakage) rather than
    predicting with current ratings. This gives the true model accuracy.
    """
    from fsbb.models.backtest import run_backtest

    result = run_backtest(conn)
    if result.get("games_evaluated", 0) == 0:
        return {"games": 0}
    return {
        "games": result["games_evaluated"],
        "our_correct": result.get("our_correct", 0),
        "our_accuracy": result.get("our_accuracy", 0),
        "our_brier": result.get("our_brier", 0),
    }


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

    # 2. Rankings page
    html = env.get_template("rankings.html").render(
        rankings=all_rankings,
        conferences=conferences,
        total_teams=len(all_rankings),
        generated_at=generated_at,
    )
    (docs_dir / "rankings.html").write_text(html)
    click.echo(f"Rendered rankings → {docs_dir / 'rankings.html'}")

    # 3. Edge calculator page
    html = env.get_template("edge.html").render(
        all_edges=all_edges,
        value_picks=value_picks,
        total_edges=len(all_edges),
        value_bets=len(value_picks),
        avg_edge=sum(e["abs_edge"] for e in all_edges) / max(len(all_edges), 1),
        model_agrees=agree_count / max(len(all_edges), 1) * 100,
        generated_at=generated_at,
    )
    (docs_dir / "edge.html").write_text(html)
    click.echo(f"Rendered edge → {docs_dir / 'edge.html'}")

    # 4. Backtest/accuracy page
    from fsbb.models.backtest import run_backtest
    bt = run_backtest(conn_bt := init_db())
    conn_bt.close()
    html = env.get_template("backtest.html").render(
        backtest=bt,
        generated_at=generated_at,
    )
    (docs_dir / "backtest.html").write_text(html)
    click.echo(f"Rendered backtest → {docs_dir / 'backtest.html'}")

    # 5. Win probability page
    from fsbb.models.advanced import compute_win_probability_by_inning
    conn_wp = init_db()
    yesterday = today - timedelta(days=1)
    yesterday_wp = []
    for gm in conn_wp.execute("""
        SELECT g.id, h.name, a.name, g.home_runs, g.away_runs
        FROM games g JOIN teams h ON g.home_team_id=h.id JOIN teams a ON g.away_team_id=a.id
        WHERE g.date=? AND g.status='final'
        AND EXISTS (SELECT 1 FROM play_events pe WHERE pe.game_id=g.id)
        LIMIT 10
    """, (yesterday.isoformat(),)).fetchall():
        wp_curve = compute_win_probability_by_inning(conn_wp, gm[0])
        if not wp_curve:
            continue
        # Summarize to one entry per inning (last play)
        inning_summary = []
        for wp in wp_curve:
            if not inning_summary or wp["inning"] != inning_summary[-1]["inning"]:
                inning_summary.append(wp)
            else:
                inning_summary[-1] = wp
        # Find biggest swing
        swing = None
        max_delta = 0
        for i in range(1, len(wp_curve)):
            delta = abs(wp_curve[i]["home_wp"] - wp_curve[i-1]["home_wp"]) * 100
            if delta > max_delta:
                max_delta = delta
                swing = {"inning": wp_curve[i]["inning"], "event": wp_curve[i]["event"], "delta": delta}
        yesterday_wp.append({
            "home": gm[1], "away": gm[2],
            "home_runs": gm[3], "away_runs": gm[4],
            "wp_curve": inning_summary,
            "swing": swing,
        })
    conn_wp.close()
    html = env.get_template("wp.html").render(
        yesterday=yesterday.isoformat(),
        games=yesterday_wp,
        generated_at=generated_at,
    )
    (docs_dir / "wp.html").write_text(html)
    click.echo(f"Rendered wp → {docs_dir / 'wp.html'} ({len(yesterday_wp)} games)")

    # 6. Top-25 comparison page
    conn_t25 = init_db()
    top25_rows = conn_t25.execute("""
        SELECT t.name, t.conference, t.wins, t.losses, t.power_rating,
               t.pear_net, t.pear_elo, t.pear_sos,
               tf.wOBA, tf.OPS, tf.SLG, tf.ERA, tf.FIP,
               tf.KillshotOffEff, tf.KSHOT_Ratio,
               at.rank_overall as a64_rank,
               ps.bullpen_era
        FROM teams t
        LEFT JOIN team_features tf ON tf.team_id = t.id
        LEFT JOIN analytics_team at ON at.team_id = t.id
        LEFT JOIN team_pbp_stats ps ON ps.team_id = t.id
        WHERE t.games_played >= 10 AND t.total_ra > 0
        ORDER BY t.power_rating DESC LIMIT 25
    """).fetchall()
    top25 = []
    for i, r in enumerate(top25_rows):
        fsbb_rank = i + 1
        pear_net = r["pear_net"] or 999
        a64_rank = r["a64_rank"] or 999
        pear_diff = pear_net - fsbb_rank
        a64_diff = (a64_rank - fsbb_rank) if r["a64_rank"] else None
        max_div = max(abs(pear_diff), abs(a64_diff) if a64_diff is not None else 0)
        top25.append({
            "fsbb_rank": fsbb_rank, "name": r["name"], "conference": r["conference"],
            "wins": r["wins"], "losses": r["losses"],
            "pear_net": pear_net, "pear_diff": pear_diff,
            "a64_rank": r["a64_rank"], "a64_diff": a64_diff,
            "max_divergence": max_div,
            "woba": r["wOBA"], "ops": r["OPS"], "slg": r["SLG"],
            "era": r["ERA"], "fip": r["FIP"], "bp_era": r["bullpen_era"],
            "ks_eff": r["KillshotOffEff"], "ks_ratio": r["KSHOT_Ratio"],
        })
    conn_t25.close()
    html = env.get_template("top25.html").render(teams=top25, generated_at=generated_at)
    (docs_dir / "top25.html").write_text(html)
    click.echo(f"Rendered top25 → {docs_dir / 'top25.html'}")


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


@cli.command()
@click.argument("game_id", type=int)
def wp(game_id: int):
    """Show inning-by-inning win probability for a game."""
    from fsbb.models.advanced import compute_win_probability_by_inning

    conn = init_db()

    # Get game info
    game = conn.execute("""
        SELECT h.name, a.name, g.home_runs, g.away_runs
        FROM games g JOIN teams h ON g.home_team_id=h.id JOIN teams a ON g.away_team_id=a.id
        WHERE g.id=?
    """, (game_id,)).fetchone()

    if not game:
        click.echo(f"Game {game_id} not found")
        conn.close()
        return

    wp_curve = compute_win_probability_by_inning(conn, game_id)
    conn.close()

    if not wp_curve:
        click.echo(f"No play-by-play data for game {game_id}")
        return

    click.echo(f"\n{game[0]} vs {game[1]} — Final: {game[2]}-{game[3]}")
    click.echo(f"{'='*60}\n")

    # Show inning-level summary (last play per half-inning)
    prev_inning = 0
    for wp in wp_curve:
        if wp["inning"] != prev_inning:
            bar_len = int(wp["home_wp"] * 40)
            bar = "#" * bar_len + "." * (40 - bar_len)
            label = f"Inn {wp['inning']:2d}"
            click.echo(f"  {label} [{bar}] {wp['home_wp']*100:5.1f}% {game[0]:>15s}  ({wp['score']})")
            prev_inning = wp["inning"]

    final_wp = wp_curve[-1]["home_wp"]
    click.echo(f"\n  Final WP: {final_wp*100:.1f}% {game[0]}")
    click.echo(f"  Events: {len(wp_curve)}")


@cli.command()
@click.option("--date", "target_date", default=None, help="Date to analyze (YYYY-MM-DD)")
@click.option("--bankroll", default=1000.0, help="Bankroll in dollars")
@click.option("--min-edge", default=0.05, help="Minimum edge to recommend (0.05 = 5%)")
@click.option("--kelly", default=0.25, help="Kelly multiplier (0.25 = quarter-Kelly)")
def bet(target_date: str | None, bankroll: float, min_edge: float, kelly: float):
    """Show Kelly criterion bet recommendations."""
    from fsbb.models.kelly import recommend_bets

    conn = init_db()
    d = date.fromisoformat(target_date) if target_date else date.today()

    recs = recommend_bets(conn, d, bankroll, min_edge, kelly)
    conn.close()

    if not recs:
        click.echo(f"No bets with >{min_edge*100:.0f}% edge for {d}")
        click.echo("(Need both model predictions AND odds data for the date)")
        return

    click.echo(f"\nBet Recommendations for {d} (bankroll: ${bankroll:,.0f}, {kelly:.0%} Kelly)\n")
    table = []
    total_bet = 0
    for r in recs:
        table.append([
            r["team"],
            f"{r['home']} vs {r['away']}",
            f"{r['model_prob']*100:.1f}%",
            f"{r['market_prob']*100:.1f}%",
            f"{r['edge']*100:+.1f}%",
            f"{r['moneyline']:+d}" if r['moneyline'] else "—",
            f"${r['recommended_bet']:.2f}",
            r["confidence"],
        ])
        total_bet += r["recommended_bet"]

    headers = ["Pick", "Game", "Model", "Market", "Edge", "ML", "Bet", "Size"]
    click.echo(tabulate(table, headers=headers, tablefmt="simple"))
    click.echo(f"\nTotal wagered: ${total_bet:.2f} ({total_bet/bankroll*100:.1f}% of bankroll)")
    click.echo(f"Bets: {len(recs)}")


@cli.command(name="scrape-espn")
@click.option("--days", default=3, help="Days to scrape (0=full season)")
@click.option("--start", default=None, help="Start date YYYY-MM-DD")
@click.option("--end", default=None, help="End date YYYY-MM-DD")
@click.option("--season", default=None, type=int, help="Scrape full historical season")
def scrape_espn(days: int, start: str | None, end: str | None, season: int | None):
    """Scrape ESPN box scores (batting, pitching, fielding)."""
    from fsbb.scraper.espn import scrape_date, scrape_season

    conn = init_db()

    if season:
        s = date(season, 2, 14)
        e = date(season, 6, 30)
        click.echo(f"Scraping ESPN {season} season ({s} to {e})...")
        result = scrape_season(conn, start=s, end=e, progress=True)
    elif start or end:
        s = date.fromisoformat(start) if start else date(date.today().year, 2, 14)
        e = date.fromisoformat(end) if end else date.today() - timedelta(days=1)
        click.echo(f"Scraping ESPN {s} to {e}...")
        result = scrape_season(conn, start=s, end=e, progress=True)
    elif days == 0:
        click.echo("Scraping ESPN full season...")
        result = scrape_season(conn, progress=True)
    else:
        click.echo(f"Scraping ESPN last {days} days...")
        total = {"games": 0, "batters": 0, "pitchers": 0, "fielding": 0, "skipped": 0}
        for i in range(days):
            d = date.today() - timedelta(days=i + 1)
            r = scrape_date(conn, d)
            for k in total:
                total[k] += r[k]
            click.echo(f"  {d}: {r['games']} games, {r['batters']} batters, {r['fielding']} fielding")
        result = total

    click.echo(f"\nESPN scrape complete:")
    click.echo(f"  Games:    {result['games']}")
    click.echo(f"  Batters:  {result['batters']}")
    click.echo(f"  Pitchers: {result['pitchers']}")
    click.echo(f"  Fielding: {result['fielding']}")
    click.echo(f"  Skipped:  {result['skipped']}")

    # Show DB totals
    try:
        n = conn.execute("SELECT COUNT(*) FROM espn_game_batting").fetchone()[0]
        click.echo(f"  DB total ESPN batting entries: {n}")
        n = conn.execute("SELECT COUNT(*) FROM espn_game_pitching").fetchone()[0]
        click.echo(f"  DB total ESPN pitching entries: {n}")
        n = conn.execute("SELECT COUNT(*) FROM espn_game_fielding").fetchone()[0]
        click.echo(f"  DB total ESPN fielding entries: {n}")
    except Exception:
        pass

    conn.close()


@cli.command(name="import-d1bb")
@click.option("--season", default=2026, help="Season year")
def import_d1bb(season: int):
    """Import D1 Baseball CSVs (WAR, DRS, Synergy plate discipline).

    First run the console scripts on d1baseball.com/synergy/ to generate CSVs,
    then place them in data/d1baseball/ and run this command.
    """
    from fsbb.scraper.d1baseball import import_all, DATA_DIR

    conn = init_db()
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    result = import_all(conn, season)
    conn.close()

    click.echo(f"\nD1 Baseball import ({season}):")
    click.echo(f"  WAR entries:     {result['war']}")
    click.echo(f"  DRS entries:     {result['drs']}")
    click.echo(f"  Synergy entries: {result['synergy']}")

    if result["war"] == 0 and result["drs"] == 0 and result["synergy"] == 0:
        click.echo(f"\nNo CSV files found in {DATA_DIR}/")
        click.echo("Run the console scripts first:")
        click.echo("  1. Open https://d1baseball.com/synergy/ in Chrome")
        click.echo("  2. Paste scripts/scrape_d1baseball_war.js in DevTools console")
        click.echo("  3. Paste scripts/scrape_d1baseball_drs.js in DevTools console")
        click.echo("  4. Paste scripts/scrape_d1baseball_synergy.js in DevTools console")
        click.echo(f"  5. Move downloaded CSVs to {DATA_DIR}/")
        click.echo("  6. Re-run: fsbb import-d1bb")


@cli.command()
@click.option("--from-v1", is_flag=True, help="Initialize from V1 model weights (warm start)")
def learn(from_v1: bool):
    """Update online learner from completed game results."""
    from fsbb.models.online_learner import OnlineLogisticRegressor
    from fsbb.models.advanced import get_team_feature_vector, compute_matchup_features
    import numpy as np

    conn = init_db()
    model_dir = Path(__file__).parent.parent / "data"
    learner_path = model_dir / "online_learner.json"

    # Load or create learner
    if learner_path.exists() and not from_v1:
        learner = OnlineLogisticRegressor.load(learner_path)
        click.echo(f"Loaded learner ({learner.n_updates} prior updates)")
    elif from_v1:
        v1_path = model_dir / "model_v1.json"
        if not v1_path.exists():
            click.echo("No model_v1.json found. Run train_model() first.")
            conn.close()
            return
        learner = OnlineLogisticRegressor.from_v1_model(v1_path)
        click.echo(f"Initialized from V1 model ({len(learner.weights)} features)")
    else:
        learner = OnlineLogisticRegressor(n_features=29)
        click.echo("Created new learner (29 features)")

    # Get completed games that haven't been used for learning
    # Use games after the V1 training cutoff (approximate: last 500 games)
    games = conn.execute("""
        SELECT g.home_team_id, g.away_team_id, g.home_runs, g.away_runs, g.series_position
        FROM games g
        WHERE g.status='final' AND g.home_runs IS NOT NULL
        ORDER BY g.date ASC
    """).fetchall()

    updated = 0
    for g in games:
        home_vec = get_team_feature_vector(conn, g[0])
        away_vec = get_team_feature_vector(conn, g[1])
        if home_vec is None or away_vec is None:
            continue
        home_vec = np.nan_to_num(home_vec, nan=0.0)
        away_vec = np.nan_to_num(away_vec, nan=0.0)
        features = compute_matchup_features(home_vec, away_vec, series_position=g[4])
        outcome = 1.0 if g[2] > g[3] else 0.0

        # Normalize using V1 training stats if available
        v1_path = model_dir / "model_v1.json"
        if v1_path.exists():
            import json as _json
            with open(v1_path) as f:
                v1 = _json.load(f)
            X_mean = np.array(v1["X_mean"])
            X_std = np.array(v1["X_std"])
            features = (features - X_mean) / X_std

        learner.update(features, outcome)
        updated += 1

    learner.save(learner_path)
    conn.close()

    brier = learner.rolling_brier(50)
    click.echo(f"Updated on {updated} games (total updates: {learner.n_updates})")
    if brier is not None:
        click.echo(f"Rolling Brier (last 50): {brier:.4f}")
    click.echo(f"Saved to {learner_path}")


if __name__ == "__main__":
    cli()
