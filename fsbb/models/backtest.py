"""Backtest module: replay the season chronologically and measure prediction accuracy.

Methodology:
  1. Sort all completed games by date
  2. For each game, compute prediction using only data available BEFORE that game
  3. Compare against actual outcome
  4. Track running accuracy, Brier score, and comparison vs PEAR

This answers Ryan's question #11: "Can we backtest and have history?"
"""

from __future__ import annotations

import math
import sqlite3
from collections import defaultdict
from datetime import date, datetime
from typing import Any

import numpy as np

from fsbb.models.ratings import (
    compute_sos,
    fit_dynamic_bt,
    pythagorean_wpct,
    pythagenport_exponent,
)


def run_backtest(
    conn: sqlite3.Connection,
    start_date: str | None = None,
    end_date: str | None = None,
    min_games: int = 10,
    model_version: str = "v0.1-backtest",
) -> dict:
    """Backtest our model vs PEAR on historical outcomes.

    For each completed game (chronologically):
      1. Compute team ratings using only games before this one
      2. Generate win probability
      3. Compare against actual outcome
      4. Compare against PEAR's implied probability

    Args:
        conn: Database connection
        start_date: Start backtesting from this date (default: first game)
        end_date: Stop backtesting at this date (default: last game)
        min_games: Minimum games per team before including in backtest
        model_version: Version tag for predictions

    Returns:
        Dictionary with accuracy metrics and per-game details
    """
    # Load all completed games ordered by date
    query = """
        SELECT g.id, g.date, g.home_team_id, g.away_team_id,
               g.home_runs, g.away_runs, g.pear_home_win_prob
        FROM games g
        WHERE g.status = 'final' AND g.home_runs IS NOT NULL
    """
    params: list = []
    if start_date:
        query += " AND g.date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND g.date <= ?"
        params.append(end_date)
    query += " ORDER BY g.date, g.id"

    all_games = conn.execute(query, params).fetchall()
    if not all_games:
        return {"error": "No completed games found for backtesting"}

    # Load team info
    teams = conn.execute("SELECT id, name FROM teams").fetchall()
    team_id_map = {}
    team_names = {}
    for idx, t in enumerate(teams):
        team_id_map[t["id"]] = idx
        team_names[idx] = t["name"]
    n_teams = len(teams)

    # Rolling accumulators
    rs: dict[int, float] = defaultdict(float)   # runs scored per team
    ra: dict[int, float] = defaultdict(float)   # runs allowed per team
    gp: dict[int, int] = defaultdict(int)       # games played per team
    wins: dict[int, int] = defaultdict(int)
    game_history: list[dict] = []  # games seen so far (for BT fitting)

    # Results
    results = []
    our_correct = 0
    our_brier_sum = 0.0
    pear_correct = 0
    pear_brier_sum = 0.0
    pear_count = 0
    total_evaluated = 0

    for game in all_games:
        h_id = game["home_team_id"]
        a_id = game["away_team_id"]

        if h_id not in team_id_map or a_id not in team_id_map:
            continue

        h_idx = team_id_map[h_id]
        a_idx = team_id_map[a_id]

        # Only predict if both teams have minimum games
        if gp[h_idx] >= min_games and gp[a_idx] >= min_games:
            # Compute ratings from historical data (before this game)
            h_pythag = pythagorean_wpct(rs[h_idx], ra[h_idx], gp[h_idx])
            a_pythag = pythagorean_wpct(rs[a_idx], ra[a_idx], gp[a_idx])

            # BT ratings from game history
            if len(game_history) >= 50:
                bt_ratings, hfa_log = fit_dynamic_bt(
                    game_history, n_teams, team_id_map, max_iter=100
                )
                bt_diff = bt_ratings[h_idx] - bt_ratings[a_idx]
                hfa = hfa_log
            else:
                bt_diff = 0.0
                hfa = 0.16  # default HFA

            # Predict: logistic on BT diff + HFA
            logit = bt_diff + hfa
            our_prob = 1.0 / (1.0 + math.exp(-logit))
            our_prob = max(0.05, min(0.95, our_prob))

            # Actual outcome
            actual_home_won = game["home_runs"] > game["away_runs"]
            actual = 1.0 if actual_home_won else 0.0

            # Our accuracy
            our_predicted_home = our_prob > 0.5
            is_correct = our_predicted_home == actual_home_won
            if is_correct:
                our_correct += 1
            our_brier_sum += (our_prob - actual) ** 2
            total_evaluated += 1

            # PEAR comparison
            pear_prob = game["pear_home_win_prob"]
            pear_was_correct = None
            if pear_prob is not None:
                pear_predicted_home = pear_prob > 0.5
                pear_was_correct = pear_predicted_home == actual_home_won
                if pear_was_correct:
                    pear_correct += 1
                pear_brier_sum += (pear_prob - actual) ** 2
                pear_count += 1

            results.append({
                "date": game["date"],
                "home": team_names[h_idx],
                "away": team_names[a_idx],
                "our_prob": round(our_prob, 4),
                "actual_home_won": actual_home_won,
                "our_correct": is_correct,
                "pear_prob": pear_prob,
                "pear_correct": pear_was_correct,
                "score": f"{game['home_runs']}-{game['away_runs']}",
            })

        # Update accumulators (AFTER prediction, to avoid data leakage)
        h_runs = int(game["home_runs"])
        a_runs = int(game["away_runs"])
        rs[h_idx] += float(h_runs)
        ra[h_idx] += float(a_runs)
        gp[h_idx] += 1
        rs[a_idx] += float(a_runs)
        ra[a_idx] += float(h_runs)
        gp[a_idx] += 1

        if h_runs > a_runs:
            wins[h_idx] += 1
        else:
            wins[a_idx] += 1

        game_history.append({
            "home_idx": h_idx,
            "away_idx": a_idx,
            "home_won": h_runs > a_runs,
            "date": game["date"],
        })

    # Summary
    summary: dict[str, Any] = {
        "total_games_in_db": len(all_games),
        "games_evaluated": total_evaluated,
        "games_skipped": len(all_games) - total_evaluated,
        "min_games_threshold": min_games,
    }

    if total_evaluated > 0:
        summary["our_correct"] = our_correct
        summary["our_accuracy"] = round(our_correct / total_evaluated, 4)
        summary["our_brier"] = round(our_brier_sum / total_evaluated, 4)

    if pear_count > 0:
        summary["pear_correct"] = pear_correct
        summary["pear_accuracy"] = round(pear_correct / pear_count, 4)
        summary["pear_brier"] = round(pear_brier_sum / pear_count, 4)
        summary["edge_accuracy"] = round(
            summary.get("our_accuracy", 0) - summary["pear_accuracy"], 4
        )
        summary["edge_brier"] = round(
            summary["pear_brier"] - summary.get("our_brier", 0), 4
        )

    # Calibration: how well do probabilities match actual outcomes?
    if results:
        calibration = _compute_calibration(results)
        summary["calibration"] = calibration

    summary["model_version"] = model_version
    summary["detail"] = results

    return summary


def _compute_calibration(results: list[dict], n_bins: int = 10) -> list[dict]:
    """Compute calibration: predicted probability vs actual outcome rate.

    Groups predictions into bins and compares predicted vs actual win rate.
    Perfect calibration: predicted 60% → actual 60%.
    """
    bins: dict[int, list] = {i: [] for i in range(n_bins)}

    for r in results:
        prob = r["our_prob"]
        bin_idx = min(int(prob * n_bins), n_bins - 1)
        bins[bin_idx].append(1.0 if r["actual_home_won"] else 0.0)

    calibration = []
    for i in range(n_bins):
        if bins[i]:
            actual_rate = sum(bins[i]) / len(bins[i])
            predicted_center = (i + 0.5) / n_bins
            calibration.append({
                "bin": f"{i*10}-{(i+1)*10}%",
                "predicted": round(predicted_center, 2),
                "actual": round(actual_rate, 4),
                "count": len(bins[i]),
                "error": round(abs(actual_rate - predicted_center), 4),
            })

    return calibration
