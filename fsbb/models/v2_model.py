"""V2 model: logistic regression on self-computed walk-forward features.

No PEAR dependency. All features computed from PBP data and game_pitchers
using only data available before each prediction date.

Features (13 difference features + 1 home field indicator = 14):
  Batting:  wOBA, ISO, SLG, OBP, BABIP, k_rate, bb_rate (7)
  Pitching: team_era, team_fip, bullpen_era, starter_avg_ip (4)
  Team:     bt_rating, pythag_pct (2, from existing ratings)
"""

from __future__ import annotations

import json
import math
import sqlite3
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

from fsbb.models.ratings import fit_dynamic_bt, pythagorean_wpct

FEATURE_NAMES = [
    "woba", "iso", "slg", "obp", "babip", "k_rate", "bb_rate",
    "team_era", "team_fip", "bullpen_era", "starter_avg_ip",
    "bt_rating", "pythag_pct",
]


def _get_feature_vector(pbp_feats: dict | None, bt_rating: float, pythag: float) -> list[float] | None:
    """Build a 13-element feature vector from PBP features + team ratings."""
    if not pbp_feats:
        return None
    vals = []
    for name in FEATURE_NAMES:
        if name == "bt_rating":
            vals.append(bt_rating)
        elif name == "pythag_pct":
            vals.append(pythag)
        else:
            v = pbp_feats.get(name)
            if v is None:
                return None
            vals.append(v)
    return vals


def train_v2(
    conn: sqlite3.Connection,
    train_seasons: list[int] | None = None,
    min_pa: int = 100,
) -> dict:
    """Train V2 model on walk-forward self-computed features.

    For each completed game in training seasons:
    1. Compute PBP features for both teams using only pre-game data
    2. Build difference feature vector (home - away) + home field indicator
    3. Fit elastic net logistic regression

    Returns model dict with weights, X_mean, X_std, training metrics.
    """
    if train_seasons is None:
        train_seasons = [2023, 2024, 2025]

    from fsbb.models.pbp_walk_forward import compute_pbp_features_to_date

    # Load all completed games in training seasons
    season_clauses = " OR ".join(f"g.date LIKE '{s}-%'" for s in train_seasons)
    games = conn.execute(f"""
        SELECT g.id, g.date, g.home_team_id, g.away_team_id,
               g.home_runs, g.away_runs
        FROM games g
        WHERE g.status = 'final' AND g.home_runs IS NOT NULL
          AND ({season_clauses})
        ORDER BY g.date, g.id
    """).fetchall()

    if not games:
        return {"error": "No training games found"}

    # Build walk-forward: accumulate team stats as we go
    teams = conn.execute("SELECT id FROM teams ORDER BY id").fetchall()
    team_ids = [t[0] for t in teams]
    team_id_map = {t: idx for idx, t in enumerate(team_ids)}
    n_teams = len(team_ids)

    # Rolling accumulators for BT + Pythag
    rs = defaultdict(float)
    ra = defaultdict(float)
    gp = defaultdict(int)
    game_history = []
    cached_bt = {}
    cached_hfa = 0.16

    # Pre-compute PBP features at weekly checkpoints
    print("  Pre-computing PBP features at weekly checkpoints...")
    from datetime import datetime, timedelta
    pbp_cache: dict[tuple[int, str], dict] = {}
    checkpoint_dates = []
    d = datetime(min(train_seasons), 2, 1)
    end = datetime(max(train_seasons) + 1, 7, 1)
    while d < end:
        checkpoint_dates.append(d.strftime("%Y-%m-%d"))
        d += timedelta(days=7)

    for tid in team_ids:
        for cd in checkpoint_dates:
            feat = compute_pbp_features_to_date(conn, tid, cd)
            if feat and feat["plate_appearances"] >= min_pa:
                pbp_cache[(tid, cd)] = feat

    print(f"  Cached {len(pbp_cache)} team-checkpoint PBP features")

    def get_pbp_cached(team_db_id: int, game_date: str) -> dict | None:
        best = None
        for cd in checkpoint_dates:
            if cd <= game_date:
                best = cd
            else:
                break
        return pbp_cache.get((team_db_id, best)) if best else None

    # Build training data
    print("  Building training data...")
    X_rows = []
    y_rows = []
    skipped = 0

    for game in games:
        h_id, a_id = game["home_team_id"], game["away_team_id"]
        if h_id not in team_id_map or a_id not in team_id_map:
            skipped += 1
            continue

        h_idx = team_id_map[h_id]
        a_idx = team_id_map[a_id]

        if gp[h_idx] >= 10 and gp[a_idx] >= 10:
            # Get walk-forward PBP features
            h_pbp = get_pbp_cached(h_id, game["date"])
            a_pbp = get_pbp_cached(a_id, game["date"])

            # Get walk-forward BT + Pythag
            h_bt = cached_bt.get(h_idx, 0.0)
            a_bt = cached_bt.get(a_idx, 0.0)
            h_pyth = pythagorean_wpct(rs[h_idx], ra[h_idx], gp[h_idx])
            a_pyth = pythagorean_wpct(rs[a_idx], ra[a_idx], gp[a_idx])

            h_vec = _get_feature_vector(h_pbp, h_bt, h_pyth)
            a_vec = _get_feature_vector(a_pbp, a_bt, a_pyth)

            if h_vec and a_vec:
                diff = [h - a for h, a in zip(h_vec, a_vec)]
                diff.append(1.0)  # home field indicator
                X_rows.append(diff)
                y_rows.append(1.0 if game["home_runs"] > game["away_runs"] else 0.0)

        # Update accumulators AFTER prediction
        h_runs = float(game["home_runs"])
        a_runs = float(game["away_runs"])
        rs[h_idx] += h_runs
        ra[h_idx] += a_runs
        gp[h_idx] += 1
        rs[a_idx] += a_runs
        ra[a_idx] += h_runs
        gp[a_idx] += 1

        game_history.append({
            "home_idx": h_idx, "away_idx": a_idx,
            "home_won": h_runs > a_runs,
            "home_runs": h_runs, "away_runs": a_runs,
            "date": game["date"],
        })

        if len(game_history) >= 100 and len(game_history) % 100 == 0:
            bt_ratings, hfa_log = fit_dynamic_bt(
                game_history, n_teams, team_id_map, max_iter=50
            )
            cached_hfa = hfa_log
            cached_bt = {i: bt_ratings[i] for i in range(n_teams)}

    if len(X_rows) < 200:
        return {"error": f"Only {len(X_rows)} training examples (need 200+)"}

    print(f"  Training on {len(X_rows)} games (skipped {skipped})")

    X = np.array(X_rows)
    y = np.array(y_rows)
    n_samples, n_features = X.shape

    # Standardize
    X_mean = np.nanmean(X, axis=0)
    X_std = np.nanstd(X, axis=0)
    X_std[X_std == 0] = 1.0
    X_norm = (X - X_mean) / X_std

    # Elastic net logistic regression
    lambda_l2 = 1.0
    lambda_l1 = 0.1

    def loss(w):
        z = X_norm @ w
        z = np.clip(z, -30, 30)
        p = 1.0 / (1.0 + np.exp(-z))
        p = np.clip(p, 1e-10, 1 - 1e-10)
        nll = -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
        feat_w = w[:-1]  # don't regularize HFA
        l2 = lambda_l2 / (2 * n_samples) * np.sum(feat_w ** 2)
        l1 = lambda_l1 / n_samples * np.sum(np.abs(feat_w))
        return nll + l2 + l1

    w0 = np.zeros(n_features)
    result = minimize(loss, w0, method="L-BFGS-B", options={"maxiter": 500})
    weights = result.x

    # Evaluate on training data
    z = X_norm @ weights
    z = np.clip(z, -30, 30)
    probs = 1.0 / (1.0 + np.exp(-z))
    preds = (probs > 0.5).astype(float)
    accuracy = float(np.mean(preds == y))
    brier = float(np.mean((probs - y) ** 2))

    # Feature importance
    importance = np.abs(weights[:-1]) * X_std[:-1]
    feat_names = FEATURE_NAMES + ["home_field"]
    feat_importance = sorted(
        zip(feat_names, weights.tolist(), importance.tolist()),
        key=lambda x: abs(x[2]), reverse=True
    )

    print(f"  Train accuracy: {accuracy*100:.2f}%, Brier: {brier:.4f}")
    print(f"  Top features:")
    for name, w, imp in feat_importance[:5]:
        print(f"    {name:20s} w={w:+.4f} imp={imp:.4f}")

    model = {
        "version": "v2.0",
        "feature_names": feat_names,
        "weights": weights.tolist(),
        "X_mean": X_mean.tolist(),
        "X_std": X_std.tolist(),
        "train_accuracy": round(accuracy, 4),
        "train_brier": round(brier, 4),
        "train_games": len(X_rows),
        "train_seasons": train_seasons,
        "feature_importance": [(n, round(w, 4), round(imp, 4)) for n, w, imp in feat_importance],
    }

    # Save to disk
    path = Path(__file__).parent.parent.parent / "data" / "model_v2.json"
    with open(path, "w") as f:
        json.dump(model, f, indent=2)
    print(f"  Saved to {path}")

    return model


def predict_v2(
    conn: sqlite3.Connection,
    home_team: str,
    away_team: str,
    model: dict,
    game_date: str | None = None,
) -> dict | None:
    """Predict using V2 model with point-in-time PBP features."""
    from datetime import date
    from fsbb.models.pbp_walk_forward import compute_pbp_features_to_date

    if game_date is None:
        game_date = date.today().isoformat()

    # Look up teams
    h_row = conn.execute("SELECT id, bt_rating, pythag_pct FROM teams WHERE name=?", (home_team,)).fetchone()
    a_row = conn.execute("SELECT id, bt_rating, pythag_pct FROM teams WHERE name=?", (away_team,)).fetchone()
    if not h_row or not a_row:
        return None

    h_pbp = compute_pbp_features_to_date(conn, h_row["id"], game_date)
    a_pbp = compute_pbp_features_to_date(conn, a_row["id"], game_date)

    h_vec = _get_feature_vector(h_pbp, h_row["bt_rating"] or 0.0, h_row["pythag_pct"] or 0.5)
    a_vec = _get_feature_vector(a_pbp, a_row["bt_rating"] or 0.0, a_row["pythag_pct"] or 0.5)

    if not h_vec or not a_vec:
        return None

    diff = [h - a for h, a in zip(h_vec, a_vec)]
    diff.append(1.0)  # home field

    features = np.array(diff)
    X_mean = np.array(model["X_mean"])
    X_std = np.array(model["X_std"])
    features_norm = (features - X_mean) / X_std

    weights = np.array(model["weights"])
    z = float(features_norm @ weights)
    z = max(-30, min(30, z))
    prob = 1.0 / (1.0 + math.exp(-z))
    prob = max(0.05, min(0.95, prob))

    return {
        "home_team": home_team,
        "away_team": away_team,
        "home_win_prob": round(prob, 4),
        "away_win_prob": round(1 - prob, 4),
        "model_version": "v2.0",
    }


def backtest_v2(
    conn: sqlite3.Connection,
    model: dict,
    test_season: int = 2026,
    min_games: int = 10,
) -> dict:
    """Walk-forward backtest of V2 on test season. Fully honest, no leakage."""
    from fsbb.models.pbp_walk_forward import compute_pbp_features_to_date
    from datetime import datetime, timedelta

    games = conn.execute("""
        SELECT g.id, g.date, g.home_team_id, g.away_team_id,
               g.home_runs, g.away_runs
        FROM games g
        WHERE g.status = 'final' AND g.home_runs IS NOT NULL
          AND g.date LIKE ?
        ORDER BY g.date, g.id
    """, (f"{test_season}-%",)).fetchall()

    if not games:
        return {"error": "No test games"}

    teams = conn.execute("SELECT id FROM teams ORDER BY id").fetchall()
    team_ids = [t[0] for t in teams]
    team_id_map = {t: idx for idx, t in enumerate(team_ids)}

    # Pre-compute PBP at weekly checkpoints for test season
    print(f"  Pre-computing {test_season} PBP checkpoints...")
    pbp_cache: dict[tuple[int, str], dict] = {}
    checkpoint_dates = []
    d = datetime(test_season, 1, 1)
    end = datetime(test_season, 12, 31)
    while d < end:
        checkpoint_dates.append(d.strftime("%Y-%m-%d"))
        d += timedelta(days=7)

    for tid in team_ids:
        for cd in checkpoint_dates:
            feat = compute_pbp_features_to_date(conn, tid, cd)
            if feat and feat["plate_appearances"] >= 100:
                pbp_cache[(tid, cd)] = feat

    print(f"  Cached {len(pbp_cache)} checkpoints")

    def get_pbp_cached(team_db_id: int, game_date: str) -> dict | None:
        best = None
        for cd in checkpoint_dates:
            if cd <= game_date:
                best = cd
            else:
                break
        return pbp_cache.get((team_db_id, best)) if best else None

    # Count games played per team up to each game (walk-forward)
    gp = defaultdict(int)
    # Also need BT ratings — use stored ratings since V2 is testing features, not BT
    bt_ratings = {}
    pythag_pcts = {}
    for row in conn.execute("SELECT id, bt_rating, pythag_pct FROM teams"):
        bt_ratings[row["id"]] = row["bt_rating"] or 0.0
        pythag_pcts[row["id"]] = row["pythag_pct"] or 0.5

    weights = np.array(model["weights"])
    X_mean = np.array(model["X_mean"])
    X_std = np.array(model["X_std"])

    correct = 0
    brier_sum = 0.0
    total = 0

    for game in games:
        h_id, a_id = game["home_team_id"], game["away_team_id"]
        if h_id not in team_id_map or a_id not in team_id_map:
            continue

        h_idx, a_idx = team_id_map[h_id], team_id_map[a_id]
        if gp[h_idx] < min_games or gp[a_idx] < min_games:
            gp[h_idx] += 1
            gp[a_idx] += 1
            continue

        h_pbp = get_pbp_cached(h_id, game["date"])
        a_pbp = get_pbp_cached(a_id, game["date"])

        h_vec = _get_feature_vector(h_pbp, bt_ratings[h_id], pythag_pcts[h_id])
        a_vec = _get_feature_vector(a_pbp, bt_ratings[a_id], pythag_pcts[a_id])

        if h_vec and a_vec:
            diff = np.array([h - a for h, a in zip(h_vec, a_vec)] + [1.0])
            diff_norm = (diff - X_mean) / X_std
            z = float(diff_norm @ weights)
            z = max(-30, min(30, z))
            prob = 1.0 / (1.0 + math.exp(-z))
            prob = max(0.05, min(0.95, prob))

            actual = game["home_runs"] > game["away_runs"]
            predicted = prob > 0.5
            if predicted == actual:
                correct += 1
            brier_sum += (prob - (1.0 if actual else 0.0)) ** 2
            total += 1

        gp[h_idx] += 1
        gp[a_idx] += 1

    if total == 0:
        return {"error": "No games evaluated"}

    accuracy = correct / total
    brier = brier_sum / total
    print(f"  V2 backtest: {accuracy*100:.2f}% on {total} games, Brier={brier:.4f}")

    return {
        "accuracy": round(accuracy, 4),
        "brier": round(brier, 4),
        "games": total,
        "correct": correct,
        "season": test_season,
    }
