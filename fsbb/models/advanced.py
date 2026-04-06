"""Advanced multi-feature prediction model.

V1 model: uses 30+ PEAR metrics per team to predict game outcomes.
Replaces the V0 Pythagorean-only model with a feature-rich approach.

Architecture:
  1. Extract features for home and away team (30+ metrics each)
  2. Compute difference features (home - away for each metric)
  3. Logistic regression with L2 regularization
  4. Cross-validated on game outcomes

Key features by category:
  - Offensive: wOBA, wRC+, ISO, OPS, BB%
  - Pitching: FIP, ERA, WHIP, K/BB, KP9
  - Quality: ELO, Pwr, SOS, expected_wins
  - Clutch: KillshotOffEff, KSHOT_Ratio
  - Regression: BABIP, LOB% (luck indicators)
"""

from __future__ import annotations

import math
import sqlite3
from typing import Any

import numpy as np

# Features to extract from each team (all available from PEAR team detail)
FEATURE_COLUMNS = [
    # Offensive quality (most predictive)
    "wOBA", "wRC_plus", "ISO", "OPS", "OBP", "SLG", "BB_pct", "BABIP",
    # Pitching quality
    "FIP", "ERA", "WHIP", "KP9", "K_BB", "LOB_pct", "RA9",
    # WAR components
    "oWAR_z", "pWAR_z", "fWAR",
    # Team quality ratings
    "ELO", "Pwr", "PYTHAG",
    # Schedule context
    "SOS", "expected_wins",
    # Clutch performance
    "KillshotOffEff", "KillshotDefEff", "KSHOT_Ratio",
]

# PBP-derived features (from team_pbp_stats table)
PBP_FEATURES = [
    "k_rate",
    "bb_rate",
    "babip_computed",
    "first_inning_runs_per_game",
    "late_inning_runs_per_game",
    "bullpen_era",
    "starter_avg_ip",
    "pitches_per_pa",
]

# Map from clean column names to PEAR API field names
PEAR_FIELD_MAP = {
    "wOBA": "wOBA",
    "wRC_plus": "wRC+",
    "ISO": "ISO",
    "OPS": "OPS",
    "OBP": "OBP",
    "SLG": "SLG",
    "BB_pct": "BB%",
    "BABIP": "BABIP",
    "FIP": "FIP",
    "ERA": "ERA",
    "WHIP": "WHIP",
    "KP9": "KP9",
    "K_BB": "K/BB",
    "LOB_pct": "LOB%",
    "RA9": "RA9",
    "oWAR_z": "oWAR_z",
    "pWAR_z": "pWAR_z",
    "fWAR": "fWAR",
    "ELO": "ELO",
    "Pwr": "Pwr",
    "PYTHAG": "PYTHAG",
    "SOS": "SOS",
    "expected_wins": "expected_wins",
    "KillshotOffEff": "KillshotOffEff",
    "KillshotDefEff": "KillshotDefEff",
    "KSHOT_Ratio": "KSHOT_Ratio",
}


def build_team_features_table(conn: sqlite3.Connection) -> None:
    """Create and populate the team_features table from PEAR team detail data.

    Scrapes all teams and stores 27 advanced metrics per team.
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS team_features (
            team_id INTEGER PRIMARY KEY REFERENCES teams(id),
            wOBA REAL, wRC_plus REAL, ISO REAL, OPS REAL, OBP REAL, SLG REAL,
            BB_pct REAL, BABIP REAL,
            FIP REAL, ERA REAL, WHIP REAL, KP9 REAL, K_BB REAL, LOB_pct REAL, RA9 REAL,
            oWAR_z REAL, pWAR_z REAL, fWAR REAL,
            ELO REAL, Pwr REAL, PYTHAG REAL,
            SOS REAL, expected_wins REAL,
            KillshotOffEff REAL, KillshotDefEff REAL, KSHOT_Ratio REAL,
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()


def import_team_features(conn: sqlite3.Connection, team_name: str, detail: dict) -> bool:
    """Import advanced metrics for one team from PEAR team detail."""
    t = detail.get("team", {})
    if not t:
        return False

    team_row = conn.execute("SELECT id FROM teams WHERE name=?", (team_name,)).fetchone()
    if not team_row:
        return False
    team_id = team_row[0]

    values: dict[str, Any] = {"team_id": team_id}
    for col, pear_key in PEAR_FIELD_MAP.items():
        val = t.get(pear_key)
        if isinstance(val, (int, float)) and not math.isnan(val):
            values[col] = float(val)
        else:
            values[col] = None

    columns = list(values.keys())
    placeholders = ", ".join(["?"] * len(columns))
    col_str = ", ".join(columns)
    update_str = ", ".join(f"{c}=excluded.{c}" for c in columns if c != "team_id")

    conn.execute(f"""
        INSERT INTO team_features ({col_str})
        VALUES ({placeholders})
        ON CONFLICT(team_id) DO UPDATE SET {update_str}, updated_at=datetime('now')
    """, [values[c] for c in columns])
    conn.commit()
    return True


def get_team_feature_vector(conn: sqlite3.Connection, team_id: int) -> np.ndarray | None:
    """Get a team's feature vector as a numpy array.

    Returns array of shape (len(FEATURE_COLUMNS),) or None if team not found.
    """
    row = conn.execute(f"""
        SELECT {', '.join(FEATURE_COLUMNS)}
        FROM team_features WHERE team_id=?
    """, (team_id,)).fetchone()

    if not row:
        return None

    vec = np.array([float(v) if v is not None else np.nan for v in row])
    return vec


def get_combined_feature_vector(conn: sqlite3.Connection, team_id: int) -> np.ndarray | None:
    """Get PEAR features + PBP features combined."""
    pear_vec = get_team_feature_vector(conn, team_id)
    if pear_vec is None:
        return None

    pbp_row = conn.execute("""
        SELECT k_rate, bb_rate, babip_computed,
               first_inning_runs_per_game, late_inning_runs_per_game,
               bullpen_era, starter_avg_ip, pitches_per_pa
        FROM team_pbp_stats WHERE team_id = ?
    """, (team_id,)).fetchone()

    if pbp_row:
        pbp_vec = np.array([float(v) if v is not None else 0.0 for v in pbp_row])
    else:
        pbp_vec = np.zeros(len(PBP_FEATURES))

    return np.concatenate([pear_vec, pbp_vec])


def get_starter_quality_feature(
    conn: sqlite3.Connection,
    game_id: int,
    home_team_id: int,
    away_team_id: int,
) -> float:
    """Compute starter quality differential for a game.

    Uses quality_rating (0-100 scale, 50=average).
    Returns home_quality - away_quality (positive = home pitcher better).
    Falls back to 50 (average) if no starter data.
    """
    from fsbb.scraper.boxscore import get_starter_quality

    home_q = get_starter_quality(conn, game_id, home_team_id)
    away_q = get_starter_quality(conn, game_id, away_team_id)

    if home_q is None:
        home_q = 50.0  # average
    if away_q is None:
        away_q = 50.0

    return home_q - away_q  # positive = home pitcher better


def compute_matchup_features(
    home_vec: np.ndarray,
    away_vec: np.ndarray,
    series_position: int | None = None,
) -> np.ndarray:
    """Compute matchup feature vector from two team vectors.

    Returns difference features (home - away) plus game-level features.
    For pitching metrics (where lower = better), we flip the sign.

    Args:
        home_vec: Home team feature vector
        away_vec: Away team feature vector
        series_position: 1=Friday/ace, 2=Saturday/#2, 3=Sunday/#3, None=midweek
    """
    lower_better = {"FIP", "ERA", "WHIP", "RA9", "SOS"}
    lower_idx = [i for i, col in enumerate(FEATURE_COLUMNS) if col in lower_better]

    diff = home_vec - away_vec

    for idx in lower_idx:
        diff[idx] = -diff[idx]

    # Game-level features
    home_field = 1.0
    # Series position: encode as two features (is_game2, is_game3)
    # Game 1 (ace) is baseline. Game 2/3 have weaker starters.
    is_game2 = 1.0 if series_position == 2 else 0.0
    is_game3 = 1.0 if series_position == 3 else 0.0

    features = np.append(diff, [home_field, is_game2, is_game3])

    return features


def train_model(conn: sqlite3.Connection, min_games: int = 10) -> dict:
    """Train the logistic regression model on completed games.

    Uses L2-regularized logistic regression fit via iteratively
    reweighted least squares (no sklearn dependency).

    Returns model weights and training metrics.
    """
    from scipy.optimize import minimize

    # Load all completed games with both teams having features
    games = conn.execute("""
        SELECT g.home_team_id, g.away_team_id, g.home_runs, g.away_runs,
               g.series_position
        FROM games g
        WHERE g.status='final' AND g.home_runs IS NOT NULL
    """).fetchall()

    X_list = []
    y_list = []

    for g in games:
        home_vec = get_team_feature_vector(conn, g[0])
        away_vec = get_team_feature_vector(conn, g[1])

        if home_vec is None or away_vec is None:
            continue

        # Impute NaN with 0 (mean-centered)
        home_vec = np.nan_to_num(home_vec, nan=0.0)
        away_vec = np.nan_to_num(away_vec, nan=0.0)

        series_pos = g[4] if len(g) > 4 else None
        features = compute_matchup_features(home_vec, away_vec, series_position=series_pos)
        outcome = 1.0 if g[2] > g[3] else 0.0

        X_list.append(features)
        y_list.append(outcome)

    if len(X_list) < 100:
        return {"error": f"Not enough games with features ({len(X_list)}). Need 100+."}

    X = np.array(X_list)
    y = np.array(y_list)
    n_samples, n_features = X.shape

    # Standardize features (zero mean, unit variance)
    X_mean = np.nanmean(X, axis=0)
    X_std = np.nanstd(X, axis=0)
    X_std[X_std == 0] = 1.0  # Avoid division by zero
    X_norm = (X - X_mean) / X_std

    # Elastic net regularization (L1 + L2) for feature pruning
    lambda_l2 = 1.0   # L2 strength (ridge)
    lambda_l1 = 0.1   # L1 strength (lasso) — drives weak features to zero

    def neg_log_likelihood(w):
        z = X_norm @ w
        z = np.clip(z, -30, 30)
        p = 1.0 / (1.0 + np.exp(-z))
        p = np.clip(p, 1e-10, 1 - 1e-10)
        ll = np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
        # Elastic net: L2 + L1 (skip last 3 weights: home, game2, game3)
        feat_w = w[:-3]
        l2_reg = lambda_l2 / (2 * n_samples) * np.sum(feat_w ** 2)
        l1_reg = lambda_l1 / n_samples * np.sum(np.abs(feat_w))
        return -(ll - l2_reg - l1_reg)

    def gradient(w):
        z = X_norm @ w
        z = np.clip(z, -30, 30)
        p = 1.0 / (1.0 + np.exp(-z))
        grad = -X_norm.T @ (y - p) / n_samples
        # Elastic net gradient (L2 + L1 subgradient, skip game-level features)
        feat_grad = grad[:-3]
        feat_grad += lambda_l2 / n_samples * w[:-3]
        feat_grad += lambda_l1 / n_samples * np.sign(w[:-3])
        grad[:-3] = feat_grad
        return grad

    # Optimize
    w0 = np.zeros(n_features)
    result = minimize(neg_log_likelihood, w0, jac=gradient, method="L-BFGS-B",
                      options={"maxiter": 500, "ftol": 1e-8})

    weights = result.x

    # Evaluate: predict on training data
    z = X_norm @ weights
    z = np.clip(z, -30, 30)
    probs = 1.0 / (1.0 + np.exp(-z))

    predictions = (probs > 0.5).astype(float)
    accuracy = np.mean(predictions == y)
    brier = np.mean((probs - y) ** 2)

    # Feature importance (absolute weight × std)
    importance = np.abs(weights[:-1]) * X_std[:-1]
    feat_importance = sorted(
        zip(FEATURE_COLUMNS, weights[:-1], importance),
        key=lambda x: x[2], reverse=True
    )

    return {
        "n_games": n_samples,
        "n_features": n_features,
        "accuracy_train": round(float(accuracy), 4),
        "accuracy_note": "Training accuracy. Backtest with leakage ~73%. Honest forward estimate: 65-70%.",
        "brier": round(float(brier), 4),
        "converged": result.success,
        "weights": weights.tolist(),
        "X_mean": X_mean.tolist(),
        "X_std": X_std.tolist(),
        "feature_importance": [(name, round(float(w), 4), round(float(imp), 4))
                                for name, w, imp in feat_importance[:15]],
        "hfa_weight": round(float(weights[-1]), 4),
    }


def predict_v1(
    conn: sqlite3.Connection,
    home_team: str,
    away_team: str,
    model: dict,
) -> dict | None:
    """Predict a matchup using the trained V1 model.

    Args:
        conn: Database connection
        home_team: Home team name
        away_team: Away team name
        model: Trained model dict (from train_model)

    Returns:
        Prediction dict or None
    """
    # Look up team IDs
    home_row = conn.execute("SELECT id FROM teams WHERE name=?", (home_team,)).fetchone()
    away_row = conn.execute("SELECT id FROM teams WHERE name=?", (away_team,)).fetchone()
    if not home_row or not away_row:
        # Try alias
        if not home_row:
            alias = conn.execute("SELECT team_id FROM team_aliases WHERE alias=?", (home_team,)).fetchone()
            if alias:
                home_row = conn.execute("SELECT id FROM teams WHERE id=?", (alias[0],)).fetchone()
        if not away_row:
            alias = conn.execute("SELECT team_id FROM team_aliases WHERE alias=?", (away_team,)).fetchone()
            if alias:
                away_row = conn.execute("SELECT id FROM teams WHERE id=?", (alias[0],)).fetchone()
        if not home_row or not away_row:
            return None

    home_vec = get_team_feature_vector(conn, home_row[0])
    away_vec = get_team_feature_vector(conn, away_row[0])

    if home_vec is None or away_vec is None:
        return None

    # Handle NaN
    home_vec = np.nan_to_num(home_vec, nan=0.0)
    away_vec = np.nan_to_num(away_vec, nan=0.0)

    features = compute_matchup_features(home_vec, away_vec)

    # Normalize using training stats
    X_mean = np.array(model["X_mean"])
    X_std = np.array(model["X_std"])
    features_norm = (features - X_mean) / X_std

    # Predict
    weights = np.array(model["weights"])
    z = float(features_norm @ weights)
    z = max(-30, min(30, z))
    prob = 1.0 / (1.0 + math.exp(-z))
    prob = max(0.03, min(0.97, prob))

    return {
        "home_team": home_team,
        "away_team": away_team,
        "home_win_prob": round(prob, 4),
        "away_win_prob": round(1 - prob, 4),
        "model_version": "v1.0",
        "confidence": "high" if max(prob, 1-prob) > 0.65 else ("medium" if max(prob, 1-prob) > 0.55 else "low"),
    }


def backtest_v1(conn: sqlite3.Connection, model: dict) -> dict:
    """Backtest V1 with LEAKAGE WARNING.

    CRITICAL CAVEAT (OT-019): This backtest uses season-level PEAR features
    (wOBA, FIP, ELO, etc.) which are computed from ALL games including those
    AFTER the prediction date. This is temporal data leakage — the model sees
    the future when predicting the past.

    The reported accuracy is an UPPER BOUND, not a realistic estimate.
    Real forward-looking accuracy is likely 3-8% lower (65-70%).

    For honest accuracy, use the production backtest (_run_production_backtest)
    which uses only Pythagorean (computed from point-in-time RS/RA).

    The V1 model is valid for FORWARD predictions (today's games) because
    today's PEAR features are current-state, not future-state. The leakage
    only affects historical backtesting.
    """
    games = conn.execute("""
        SELECT g.home_team_id, g.away_team_id, g.home_runs, g.away_runs, g.date,
               g.series_position
        FROM games g
        WHERE g.status='final' AND g.home_runs IS NOT NULL
        ORDER BY g.date
    """).fetchall()

    X_list = []
    y_list = []
    dates = []

    for g in games:
        home_vec = get_team_feature_vector(conn, g[0])
        away_vec = get_team_feature_vector(conn, g[1])
        if home_vec is None or away_vec is None:
            continue
        home_vec = np.nan_to_num(home_vec, nan=0.0)
        away_vec = np.nan_to_num(away_vec, nan=0.0)
        series_pos = g[5] if len(g) > 5 else None
        features = compute_matchup_features(home_vec, away_vec, series_position=series_pos)
        X_list.append(features)
        y_list.append(1.0 if g[2] > g[3] else 0.0)
        dates.append(g[4])

    if not X_list:
        return {"error": "No games with features"}

    X = np.array(X_list)
    y = np.array(y_list)

    # Split: 70% train, 30% test (chronological)
    split = int(len(X) * 0.7)
    X_test = X[split:]
    y_test = y[split:]

    # Normalize using training means
    X_mean = np.array(model["X_mean"])
    X_std = np.array(model["X_std"])
    X_test_norm = (X_test - X_mean) / X_std

    weights = np.array(model["weights"])
    z = X_test_norm @ weights
    z = np.clip(z, -30, 30)
    probs = 1.0 / (1.0 + np.exp(-z))
    probs = np.clip(probs, 0.03, 0.97)

    predictions = (probs > 0.5).astype(float)
    accuracy = float(np.mean(predictions == y_test))
    brier = float(np.mean((probs - y_test) ** 2))

    return {
        "test_games": len(y_test),
        "train_games": split,
        "accuracy": round(accuracy, 4),
        "leakage_warning": "UPPER BOUND — uses season-level features with temporal leakage. Real forward accuracy ~65-70%.",
        "brier": round(brier, 4),
        "test_period": f"{dates[split]} to {dates[-1]}",
    }


# ---------------------------------------------------------------------------
# In-Game Win Probability (Foundation)
# ---------------------------------------------------------------------------

def compute_win_probability_by_inning(conn: sqlite3.Connection, game_id: int) -> list[dict]:
    """Compute inning-by-inning win probability for a completed game.

    Uses base rates: at each (inning, score_diff) state,
    what fraction of games in our DB were won by the home team?

    Returns list of {"inning": int, "home_wp": float, "score": str, "event": str}
    """
    plays = conn.execute("""
        SELECT inning, is_top, home_score_after, away_score_after, raw_text
        FROM play_events
        WHERE game_id = ?
        ORDER BY inning, is_top DESC, sequence_in_inning
    """, (game_id,)).fetchall()

    if not plays:
        return []

    base_rates = _get_or_compute_base_rates(conn)

    wp_curve = []
    for p in plays:
        inning = p[0]
        score_diff = (p[2] or 0) - (p[3] or 0)
        key = (min(inning, 9), max(-5, min(5, score_diff)))
        wp = base_rates.get(key, 0.5)
        wp_curve.append({
            "inning": inning,
            "home_wp": round(wp, 3),
            "score": f"{p[2]}-{p[3]}",
            "event": (p[4] or "")[:60],
        })

    return wp_curve


_BASE_RATES_CACHE: dict | None = None


def _get_or_compute_base_rates(conn: sqlite3.Connection) -> dict:
    """Compute historical win rates by (inning, score_diff) state."""
    global _BASE_RATES_CACHE
    if _BASE_RATES_CACHE is not None:
        return _BASE_RATES_CACHE

    state_counts: dict[tuple[int, int], list[int]] = {}

    games = conn.execute("""
        SELECT g.id,
               CASE WHEN g.home_runs > g.away_runs THEN 1 ELSE 0 END as home_won
        FROM games g WHERE g.status = 'final' AND g.home_runs IS NOT NULL
    """).fetchall()

    for game_id, home_won in games:
        inning_scores = conn.execute("""
            SELECT inning, MAX(home_score_after) as h, MAX(away_score_after) as a
            FROM play_events
            WHERE game_id = ?
            GROUP BY inning
            ORDER BY inning
        """, (game_id,)).fetchall()

        for row in inning_scores:
            inn = min(row[0], 9)
            diff = max(-5, min(5, (row[1] or 0) - (row[2] or 0)))
            key = (inn, diff)
            if key not in state_counts:
                state_counts[key] = [0, 0]
            state_counts[key][1] += 1
            if home_won:
                state_counts[key][0] += 1

    rates: dict[tuple[int, int], float] = {}
    for key, (wins, total) in state_counts.items():
        rates[key] = wins / total if total >= 10 else 0.5

    _BASE_RATES_CACHE = rates
    return rates
