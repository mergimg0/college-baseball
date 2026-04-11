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
from typing import Any

from fsbb.models.ratings import (
    fit_dynamic_bt,
    pythagorean_wpct,
)

_V1_MODEL_CACHE: dict | None = None


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
               g.home_runs, g.away_runs, g.pear_home_win_prob,
               g.series_position, g.neutral_site
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
    cached_bt_diff: dict[tuple[int, int], float] = {}
    cached_hfa: float = 0.16
    cal_a: float = 1.0
    cal_b: float = 0.0

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
            # Combine Pythagorean + BT for prediction
            h_pyth = pythagorean_wpct(rs[h_idx], ra[h_idx], gp[h_idx])
            a_pyth = pythagorean_wpct(rs[a_idx], ra[a_idx], gp[a_idx])

            # Log5 from Pythagorean
            denom = h_pyth + a_pyth - 2 * h_pyth * a_pyth
            pythag_prob = (h_pyth - h_pyth * a_pyth) / denom if denom != 0 else 0.5

            # BT component — uses cached ratings (refit every 100 games)
            bt_diff = cached_bt_diff.get((h_idx, a_idx), 0.0)
            is_neutral = game["neutral_site"] == 1
            hfa = 0.0 if is_neutral else cached_hfa

            # Blend Pythag + BT (matching production model logic)
            bt_logit = bt_diff + hfa
            bt_prob = 1.0 / (1.0 + math.exp(-max(-10, min(10, bt_logit))))
            bt_weight = 0.5 if cached_bt_diff else 0.0
            our_prob = (1 - bt_weight) * pythag_prob + bt_weight * bt_prob
            if bt_weight == 0 and not is_neutral:
                log_odds = math.log(max(our_prob, 1e-10) / max(1 - our_prob, 1e-10))
                log_odds += 0.16
                our_prob = 1.0 / (1.0 + math.exp(-log_odds))
            our_prob = max(0.05, min(0.95, our_prob))

            # Pitcher quality adjustment (mirrors predict.py:88-103)
            try:
                from fsbb.scraper.boxscore import get_starter_quality
                hq = get_starter_quality(conn, game["id"], h_id)
                aq = get_starter_quality(conn, game["id"], a_id)
                if hq is not None and aq is not None:
                    p_diff = (hq - aq) / 125.0
                    lo = math.log(max(our_prob, 1e-10) / max(1 - our_prob, 1e-10))
                    lo += p_diff
                    our_prob = 1.0 / (1.0 + math.exp(-lo))
                    our_prob = max(0.05, min(0.95, our_prob))
            except Exception:
                pass

            # Walk-forward Platt calibration: fit from prior games, apply to current
            if total_evaluated >= 200 and total_evaluated % 200 == 0:
                # Re-fit calibration from accumulated predictions
                if results:
                    best_a, best_b, best_brier = 1.0, 0.0, float("inf")
                    for a_c in [0.7, 0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1]:
                        for b_c in [-0.2, -0.1, -0.05, 0.0, 0.05, 0.1, 0.2]:
                            b = 0.0
                            for r in results:
                                p = max(0.01, min(0.99, r["our_prob"]))
                                lo = math.log(p / (1 - p))
                                z = a_c * lo + b_c
                                pc = 1.0 / (1.0 + math.exp(-max(-30, min(30, z))))
                                act = 1.0 if r["actual_home_won"] else 0.0
                                b += (pc - act) ** 2
                            b /= len(results)
                            if b < best_brier:
                                best_a, best_b, best_brier = a_c, b_c, b
                    cal_a, cal_b = best_a, best_b

            if cal_a != 1.0 or cal_b != 0.0:
                our_prob = max(0.01, min(0.99, our_prob))
                lo = math.log(our_prob / (1 - our_prob))
                z = cal_a * lo + cal_b
                our_prob = 1.0 / (1.0 + math.exp(-max(-30, min(30, z))))
                our_prob = max(0.05, min(0.95, our_prob))

            # V1 blend: after March 15, blend with V1 model (29 PEAR features)
            # V1 uses season-level PEAR features (some leakage), so blend 50/50 with V0
            global _V1_MODEL_CACHE
            if game["date"] >= "2026-03-15":
                try:
                    from fsbb.models.advanced import predict_v1
                    if _V1_MODEL_CACHE is None:
                        import json as _json
                        from pathlib import Path
                        mp = Path(__file__).parent.parent.parent / "data" / "model_v1.json"
                        if mp.exists():
                            with open(mp) as f:
                                _V1_MODEL_CACHE = _json.load(f)
                        else:
                            _V1_MODEL_CACHE = {}
                    if _V1_MODEL_CACHE:
                        v1_pred = predict_v1(
                            conn, team_names[h_idx], team_names[a_idx],
                            _V1_MODEL_CACHE,
                            series_position=game["series_position"],
                        )
                        if v1_pred:
                            v1_prob = v1_pred["home_win_prob"]
                            our_prob = 0.5 * our_prob + 0.5 * v1_prob
                            our_prob = max(0.05, min(0.95, our_prob))
                except Exception:
                    pass

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

        # Refit BT every 100 games to keep O(n) not O(n²)
        if len(game_history) >= 100 and len(game_history) % 100 == 0:
            bt_ratings, hfa_log = fit_dynamic_bt(
                game_history, n_teams, team_id_map, max_iter=100
            )
            cached_hfa = hfa_log
            # Pre-compute all pairwise diffs for fast lookup
            cached_bt_diff = {}
            for i in range(n_teams):
                for j in range(n_teams):
                    if i != j:
                        cached_bt_diff[(i, j)] = bt_ratings[i] - bt_ratings[j]

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
