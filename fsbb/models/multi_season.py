"""Multi-season backtest framework.

Scrapes historical seasons from NCAA API and runs walk-forward backtests
to validate model robustness across years. Also tests Pythagenport
exponent stability.
"""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta

from fsbb.models.ratings import pythagenport_exponent


def scrape_historical_season(
    conn: sqlite3.Connection,
    season: int,
    progress: bool = True,
) -> dict:
    """Scrape a complete historical season from NCAA API.

    Season dates: Feb 14 to Jun 30 (covers regionals/CWS).
    Returns {"games_found": N, "games_imported": N, "days_scraped": N}.
    """
    from fsbb.scraper.ncaa import scrape_date
    import time

    start = date(season, 2, 14)
    end = date(season, 6, 30)
    current = start
    total_found = 0
    total_imported = 0
    days = 0

    while current <= end:
        result = scrape_date(conn, current)
        total_found += result["found"]
        total_imported += result["imported"]
        days += 1

        if progress and days % 14 == 0:
            print(f"  {current}: {total_imported} games imported so far")

        current += timedelta(days=1)
        time.sleep(0.3)

    return {
        "season": season,
        "days_scraped": days,
        "games_found": total_found,
        "games_imported": total_imported,
    }


def compute_season_exponent(conn: sqlite3.Connection, season: int) -> float | None:
    """Compute Pythagenport exponent for a single season."""
    row = conn.execute("""
        SELECT SUM(home_runs + away_runs) as total_runs,
               COUNT(*) as total_games
        FROM games
        WHERE status = 'final' AND home_runs IS NOT NULL
        AND date LIKE ?
    """, (f"{season}-%",)).fetchone()

    if not row or not row[0] or not row[1] or row[1] < 100:
        return None

    total_rs = row[0] / 2  # Approximate (each run scored by one team)
    total_ra = row[0] / 2
    return pythagenport_exponent(total_rs, total_ra, row[1])


def run_multi_season_backtest(
    conn: sqlite3.Connection,
    seasons: list[int] | None = None,
    min_games: int = 10,
    progress: bool = True,
) -> dict:
    """Run walk-forward backtest across multiple seasons.

    Returns per-season and aggregate metrics.
    """
    from fsbb.models.backtest import run_backtest

    if seasons is None:
        # Find all seasons with data
        rows = conn.execute("""
            SELECT DISTINCT CAST(substr(date, 1, 4) AS INTEGER) as season
            FROM games WHERE status = 'final'
            ORDER BY season
        """).fetchall()
        seasons = [r[0] for r in rows]

    results = {}
    total_correct = 0
    total_evaluated = 0
    total_brier = 0.0

    for season in seasons:
        if progress:
            print(f"\n  Season {season}:")

        # Run backtest filtered to this season
        bt = run_backtest(
            conn,
            start_date=f"{season}-02-01",
            end_date=f"{season}-06-30",
            min_games=min_games,
        )

        games_eval = bt.get("games_evaluated", 0)
        if games_eval == 0:
            if progress:
                print(f"    No games to evaluate")
            continue

        exponent = compute_season_exponent(conn, season)

        season_result = {
            "games_evaluated": games_eval,
            "our_accuracy": bt.get("our_accuracy", 0),
            "our_brier": bt.get("our_brier", 0),
            "our_correct": bt.get("our_correct", 0),
            "exponent": round(exponent, 4) if exponent else None,
        }

        if bt.get("pear_accuracy") is not None:
            season_result["pear_accuracy"] = bt["pear_accuracy"]
            season_result["edge"] = bt.get("edge_accuracy", 0)

        results[season] = season_result
        total_correct += season_result["our_correct"]
        total_evaluated += games_eval
        total_brier += bt.get("our_brier", 0) * games_eval

        if progress:
            print(f"    Games: {games_eval}")
            print(f"    Accuracy: {season_result['our_accuracy']:.1%}")
            print(f"    Brier: {season_result['our_brier']:.4f}")
            if exponent:
                print(f"    Pythagenport exp: {exponent:.4f}")

    aggregate = {}
    if total_evaluated > 0:
        aggregate = {
            "total_games": total_evaluated,
            "total_correct": total_correct,
            "accuracy": round(total_correct / total_evaluated, 4),
            "brier": round(total_brier / total_evaluated, 4),
            "exponents": {s: r.get("exponent") for s, r in results.items() if r.get("exponent")},
        }

    return {
        "seasons": results,
        "aggregate": aggregate,
    }
