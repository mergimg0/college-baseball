"""Win probability model and game prediction engine.

Layer 3 of the architecture: logistic regression combining BT ratings
with game-specific features to produce calibrated win probabilities.

V0 features:
  - BT rating difference (home - away)
  - Home field advantage
  - Rest days differential (schedule density)

V1 additions (future):
  - Starting pitcher adjustment
  - Conference vs non-conference
  - Weather / park factors
  - Travel distance
"""

from __future__ import annotations

import math
import sqlite3
from datetime import date


def predict_matchup(
    conn: sqlite3.Connection,
    home_team: str,
    away_team: str,
    model_version: str = "v0.1",
    game_id: int | None = None,
) -> dict | None:
    """Predict a single matchup between two teams.

    Returns dict with:
        home_win_prob, away_win_prob, predicted_total_runs,
        home_bt_rating, away_bt_rating, home_pythag, away_pythag,
        confidence, model_version
    """
    home = _get_team(conn, home_team)
    away = _get_team(conn, away_team)

    if not home or not away:
        return None

    # Load calibration + HFA from disk if not yet loaded in this process
    if _CALIBRATION["a"] == 1.0 and _CALIBRATION["b"] == 0.0:
        _load_calibration()

    # Blended prediction: combine Pythagorean-based and BT-based estimates
    home_pythag = home["pythag_pct"] or 0.5
    away_pythag = away["pythag_pct"] or 0.5

    # Pythagorean-based win probability (log5 method)
    # P(A beats B) = (pA - pA*pB) / (pA + pB - 2*pA*pB)
    pa, pb = home_pythag, away_pythag
    if pa + pb - 2 * pa * pb != 0:
        pythag_prob = (pa - pa * pb) / (pa + pb - 2 * pa * pb)
    else:
        pythag_prob = 0.5

    # BT-based win probability
    bt_diff = (home["bt_rating"] or 0.0) - (away["bt_rating"] or 0.0)
    # Check neutral site — zero out HFA for postseason/neutral games
    is_neutral = False
    if game_id:
        ns_row = conn.execute("SELECT neutral_site FROM games WHERE id=?", (game_id,)).fetchone()
        if ns_row and ns_row[0]:
            is_neutral = True
    hfa = 0.0 if is_neutral else _estimate_hfa(conn)
    bt_logit = bt_diff + hfa
    bt_prob = 1.0 / (1.0 + math.exp(-max(-10, min(10, bt_logit))))

    # Determine BT reliability: if either team has no games in BT model,
    # rely more on Pythagorean. Weight BT by data coverage.
    home_in_bt = abs(home["bt_rating"] or 0.0) > 0.01
    away_in_bt = abs(away["bt_rating"] or 0.0) > 0.01

    if home_in_bt and away_in_bt:
        bt_weight = 0.5  # Equal blend when both have BT data
    elif home_in_bt or away_in_bt:
        bt_weight = 0.2  # Mostly Pythag when one team lacks BT data
    else:
        bt_weight = 0.0  # Pure Pythag when neither has BT data

    # Blend: weighted average of Pythag and BT probabilities
    home_win_prob = (1 - bt_weight) * pythag_prob + bt_weight * bt_prob

    # Single HFA source: apply log-odds adjustment when NOT using BT
    # (BT already incorporates HFA via _estimate_hfa in bt_logit)
    # For pure Pythag path (bt_weight=0), apply HFA as log-odds shift
    if bt_weight == 0 and not is_neutral:
        # Convert to log-odds, add HFA, convert back
        eps = 1e-10
        log_odds = math.log(max(home_win_prob, eps) / max(1 - home_win_prob, eps))
        log_odds += 0.16  # ~54% baseline home advantage in log-odds
        home_win_prob = 1.0 / (1.0 + math.exp(-log_odds))

    # Pitcher quality adjustment (if game_id provided and starter data available)
    pitcher_adj = 0.0
    if game_id:
        from fsbb.scraper.boxscore import get_starter_quality
        home_tid = home["id"]
        away_tid = away["id"]
        hq = get_starter_quality(conn, game_id, home_tid)
        aq = get_starter_quality(conn, game_id, away_tid)
        if hq is not None and aq is not None:
            pitcher_diff = hq - aq  # [-100, +100] scale
            # 20-point quality difference ≈ 4% win probability shift
            pitcher_adj = pitcher_diff / 125.0
            eps = 1e-10
            log_odds = math.log(max(home_win_prob, eps) / max(1 - home_win_prob, eps))
            log_odds += pitcher_adj
            home_win_prob = 1.0 / (1.0 + math.exp(-log_odds))

    # Platt calibration (shrinks overconfident probabilities toward center)
    if _CALIBRATION["a"] != 1.0 or _CALIBRATION["b"] != 0.0:
        home_win_prob = calibrate_probability(home_win_prob, _CALIBRATION["a"], _CALIBRATION["b"])

    # Clamp to reasonable range
    home_win_prob = max(0.05, min(0.95, home_win_prob))

    # Bayesian confidence interval
    ci_lower, ci_upper = None, None
    try:
        from fsbb.models.bayesian import predict_with_ci
        ci_result = predict_with_ci(conn, home["name"], away["name"])
        if ci_result:
            ci_lower = ci_result["ci_lower"]
            ci_upper = ci_result["ci_upper"]
    except Exception:
        pass

    # Predicted total runs (simple: average of both teams' RPG)
    home_rpg = home["total_rs"] / max(home["games_played"], 1)
    away_rpg = away["total_rs"] / max(away["games_played"], 1)
    # Adjust for opponent quality via BT ratings
    predicted_total = home_rpg + away_rpg

    # Confidence based on games played
    min_games = min(home["games_played"] or 0, away["games_played"] or 0)
    if min_games >= 25:
        confidence = "high"
    elif min_games >= 15:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "home_team": home["name"],
        "away_team": away["name"],
        "home_win_prob": round(home_win_prob, 4),
        "away_win_prob": round(1 - home_win_prob, 4),
        "ci_lower": round(ci_lower, 4) if ci_lower is not None else None,
        "ci_upper": round(ci_upper, 4) if ci_upper is not None else None,
        "predicted_total_runs": round(predicted_total, 1),
        "home_bt_rating": round(home["bt_rating"] or 0.0, 4),
        "away_bt_rating": round(away["bt_rating"] or 0.0, 4),
        "home_pythag": round(home["pythag_pct"] or 0.5, 4),
        "away_pythag": round(away["pythag_pct"] or 0.5, 4),
        "home_record": f"{home['wins']}-{home['losses']}",
        "away_record": f"{away['wins']}-{away['losses']}",
        "confidence": confidence,
        "pitcher_adjustment": round(pitcher_adj, 4),
        "model_version": model_version,
    }


def predict_date(
    conn: sqlite3.Connection,
    target_date: date | None = None,
    model_version: str = "v0.1",
) -> list[dict]:
    """Predict all games on a given date.

    Uses V1 model when available (29-feature logistic regression with PEAR metrics),
    falls back to V0 (Pythag+BT blend with pitcher adjustment) for teams without features.
    Writes predictions to the predictions table and updates games table.
    Returns list of prediction dicts.
    """
    import json
    from pathlib import Path

    if target_date is None:
        target_date = date.today()

    date_str = target_date.isoformat()

    # Load V1 model if available
    model_v1 = None
    model_path = Path(__file__).parent.parent.parent / "data" / "model_v1.json"
    if model_path.exists():
        try:
            with open(model_path) as f:
                model_v1 = json.load(f)
        except (json.JSONDecodeError, KeyError):
            model_v1 = None

    # Get all scheduled/upcoming games for this date
    games = conn.execute("""
        SELECT g.id, g.date, h.name as home_team, a.name as away_team,
               g.home_runs, g.away_runs, g.status, g.series_position
        FROM games g
        JOIN teams h ON g.home_team_id = h.id
        JOIN teams a ON g.away_team_id = a.id
        WHERE g.date = ?
        ORDER BY g.id
    """, (date_str,)).fetchall()

    predictions = []
    for g in games:
        pred = None

        # Try V1 model first
        if model_v1:
            try:
                from fsbb.models.advanced import predict_v1
                pred = predict_v1(conn, g["home_team"], g["away_team"], model_v1,
                                  series_position=g["series_position"])
            except Exception:
                pred = None

        # Fall back to V0 with pitcher adjustment
        if not pred:
            pred = predict_matchup(conn, g["home_team"], g["away_team"], model_version, game_id=g["id"])
        if not pred:
            continue

        # Ensure required fields exist (V1 model may not return all fields)
        pred.setdefault("predicted_total_runs", 0.0)
        pred.setdefault("pitcher_adjustment", 0.0)
        pred.setdefault("home_bt_rating", 0.0)
        pred.setdefault("away_bt_rating", 0.0)
        pred.setdefault("home_pythag", 0.5)
        pred.setdefault("away_pythag", 0.5)
        pred.setdefault("home_record", "")
        pred.setdefault("away_record", "")
        pred["game_id"] = g["id"]
        pred["status"] = g["status"]
        pred["actual_home_runs"] = g["home_runs"]
        pred["actual_away_runs"] = g["away_runs"]

        # Determine if prediction was correct (for completed games)
        if g["status"] == "final" and g["home_runs"] is not None:
            actual_home_won = g["home_runs"] > g["away_runs"]
            predicted_home_wins = pred["home_win_prob"] > 0.5
            pred["correct"] = actual_home_won == predicted_home_wins
        else:
            pred["correct"] = None

        # Store prediction
        try:
            conn.execute("""
                INSERT INTO predictions (game_id, model_version, home_win_prob, predicted_total_runs)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(game_id, model_version) DO UPDATE SET
                    home_win_prob=excluded.home_win_prob,
                    predicted_total_runs=excluded.predicted_total_runs,
                    created_at=datetime('now')
            """, (g["id"], pred.get("model_version", model_version), pred["home_win_prob"], pred["predicted_total_runs"]))

            # Update games table
            predicted_winner_id = conn.execute(
                "SELECT id FROM teams WHERE name=?",
                (pred["home_team"] if pred["home_win_prob"] > 0.5 else pred["away_team"],)
            ).fetchone()

            if predicted_winner_id:
                conn.execute("""
                    UPDATE games SET our_home_win_prob=?, our_predicted_total=?,
                                     our_predicted_winner_id=?
                    WHERE id=?
                """, (pred["home_win_prob"], pred["predicted_total_runs"],
                      predicted_winner_id["id"], g["id"]))
        except sqlite3.OperationalError as e:
            print(f"  WARNING: Failed to store prediction for game {g['id']}: {e}")

        predictions.append(pred)

    conn.commit()
    return predictions


def compute_accuracy(conn: sqlite3.Connection, model_version: str = "v0.1") -> dict:
    """Compute model accuracy across all predicted games with results.

    Returns accuracy metrics including Brier score comparison vs PEAR.
    """
    rows = conn.execute("""
        SELECT p.home_win_prob, g.home_runs, g.away_runs,
               g.pear_home_win_prob
        FROM predictions p
        JOIN games g ON p.game_id = g.id
        WHERE g.status = 'final' AND g.home_runs IS NOT NULL
              AND p.model_version = ?
    """, (model_version,)).fetchall()

    if not rows:
        return {"games": 0, "note": "No completed games with predictions"}

    our_correct = 0
    pear_correct = 0
    our_brier_sum = 0.0
    pear_brier_sum = 0.0
    pear_available = 0
    n = len(rows)

    for r in rows:
        actual_home_won = 1.0 if r["home_runs"] > r["away_runs"] else 0.0
        our_prob = r["home_win_prob"]

        # Our accuracy
        predicted_home = our_prob > 0.5
        if predicted_home == (actual_home_won == 1.0):
            our_correct += 1

        # Brier score: mean squared error of probability predictions
        our_brier_sum += (our_prob - actual_home_won) ** 2

        # PEAR comparison (if available)
        pear_prob = r["pear_home_win_prob"]
        if pear_prob is not None:
            pear_available += 1
            pear_predicted_home = pear_prob > 0.5
            if pear_predicted_home == (actual_home_won == 1.0):
                pear_correct += 1
            pear_brier_sum += (pear_prob - actual_home_won) ** 2

    result = {
        "games": n,
        "our_correct": our_correct,
        "our_accuracy": round(our_correct / n, 4) if n > 0 else 0,
        "our_brier": round(our_brier_sum / n, 4) if n > 0 else 0,
        "model_version": model_version,
    }

    if pear_available > 0:
        result["pear_games"] = pear_available
        result["pear_correct"] = pear_correct
        result["pear_accuracy"] = round(pear_correct / pear_available, 4)
        result["pear_brier"] = round(pear_brier_sum / pear_available, 4)
        result["edge_accuracy"] = round(result["our_accuracy"] - result["pear_accuracy"], 4)
        result["edge_brier"] = round(result["pear_brier"] - result["our_brier"], 4)

    return result


# ---------------------------------------------------------------------------
# Platt Scaling (Output Calibration)
# ---------------------------------------------------------------------------

# Global calibration parameters (fitted from backtest data)
_CALIBRATION: dict[str, float] = {"a": 1.0, "b": 0.0}
_DISK_LOADED: bool = False


def fit_calibration(conn: sqlite3.Connection) -> dict[str, float]:
    """Fit Platt scaling parameters from completed games.

    Finds a, b such that sigmoid(a * logit(raw_prob) + b) gives
    better-calibrated probabilities. Standard in prediction markets.

    Returns {"a": float, "b": float} and updates global _CALIBRATION.
    """
    global _CALIBRATION, _DISK_LOADED
    # Reset to identity so predict_matchup returns uncalibrated probabilities
    _CALIBRATION = {"a": 1.0, "b": 0.0}
    _DISK_LOADED = True  # prevent predict_matchup from reloading old params

    games = conn.execute("""
        SELECT h.name, a.name, g.home_runs, g.away_runs
        FROM games g
        JOIN teams h ON g.home_team_id = h.id
        JOIN teams a ON g.away_team_id = a.id
        WHERE g.status='final' AND g.home_runs IS NOT NULL
              AND h.games_played >= 10 AND a.games_played >= 10
              AND h.total_ra > 0 AND a.total_ra > 0
    """).fetchall()

    if len(games) < 200:
        return _CALIBRATION

    logits = []
    outcomes = []

    for g in games:
        pred = predict_matchup(conn, g[0], g[1])
        if not pred:
            continue
        raw = pred["home_win_prob"]
        raw = max(0.01, min(0.99, raw))
        logits.append(math.log(raw / (1 - raw)))
        outcomes.append(1.0 if g[2] > g[3] else 0.0)

    if len(logits) < 200:
        return _CALIBRATION

    # Simple grid search for a, b (avoid scipy dependency here)
    best_brier = float("inf")
    best_a, best_b = 1.0, 0.0

    for a_candidate in [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3]:
        for b_candidate in [-0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3]:
            brier = 0.0
            for logit, outcome in zip(logits, outcomes):
                z = a_candidate * logit + b_candidate
                p = 1.0 / (1.0 + math.exp(-max(-30, min(30, z))))
                brier += (p - outcome) ** 2
            brier /= len(logits)
            if brier < best_brier:
                best_brier = brier
                best_a, best_b = a_candidate, b_candidate

    _CALIBRATION = {"a": best_a, "b": best_b}
    # Also compute and persist HFA (with game count for cache validity)
    hfa = _estimate_hfa(conn)
    _CALIBRATION["hfa"] = hfa
    if _HFA_CACHE:
        _CALIBRATION["hfa_game_count"] = _HFA_CACHE[0]
    _save_calibration(_CALIBRATION)
    return _CALIBRATION


def _save_calibration(cal: dict[str, float]) -> None:
    """Persist calibration params + HFA to disk."""
    import json
    from pathlib import Path
    path = Path(__file__).parent.parent.parent / "data" / "calibration.json"
    with open(path, "w") as f:
        json.dump(cal, f)


def _load_calibration() -> None:
    """Load calibration params + HFA from disk if available."""
    import json
    from pathlib import Path
    global _CALIBRATION, _HFA_CACHE, _DISK_LOADED
    if _DISK_LOADED:
        return
    _DISK_LOADED = True
    path = Path(__file__).parent.parent.parent / "data" / "calibration.json"
    if path.exists():
        try:
            with open(path) as f:
                cal = json.load(f)
            if "a" in cal and "b" in cal:
                _CALIBRATION = {"a": cal["a"], "b": cal["b"]}
            if "hfa" in cal:
                hfa_gc = cal.get("hfa_game_count", 0)
                _HFA_CACHE = (hfa_gc, cal["hfa"])
        except (json.JSONDecodeError, KeyError):
            pass


def calibrate_probability(raw_prob: float, a: float = 1.0, b: float = 0.0) -> float:
    """Apply Platt scaling to a raw probability.

    Args:
        raw_prob: Uncalibrated probability in (0, 1)
        a: Scaling parameter (1.0 = no change)
        b: Shift parameter (0.0 = no change)

    Returns:
        Calibrated probability in (0, 1)
    """
    raw_prob = max(0.01, min(0.99, raw_prob))
    logit = math.log(raw_prob / (1 - raw_prob))
    z = a * logit + b
    return 1.0 / (1.0 + math.exp(-max(-30, min(30, z))))


def _get_team(conn: sqlite3.Connection, name: str) -> dict | None:
    """Look up team by name or alias."""
    row = conn.execute("""
        SELECT id, name, bt_rating, pythag_pct, total_rs, total_ra,
               games_played, wins, losses, sos, power_rating, elo,
               pear_power_rating, pear_elo
        FROM teams WHERE name = ?
    """, (name,)).fetchone()

    if row:
        return dict(row)

    # Try alias
    alias = conn.execute(
        "SELECT team_id FROM team_aliases WHERE alias = ?", (name,)
    ).fetchone()
    if alias:
        row = conn.execute("""
            SELECT id, name, bt_rating, pythag_pct, total_rs, total_ra,
                   games_played, wins, losses, sos, power_rating, elo,
                   pear_power_rating, pear_elo
            FROM teams WHERE id = ?
        """, (alias["team_id"],)).fetchone()
        if row:
            return dict(row)

    return None


_HFA_CACHE: tuple[int, float] | None = None


def _estimate_hfa(conn: sqlite3.Connection) -> float:
    """BT-derived HFA, cached until game count changes."""
    global _HFA_CACHE
    game_count = conn.execute(
        "SELECT COUNT(*) FROM games WHERE status='final'"
    ).fetchone()[0]
    if _HFA_CACHE and _HFA_CACHE[0] == game_count:
        return _HFA_CACHE[1]

    try:
        from fsbb.models.ratings import fit_dynamic_bt
        rows = conn.execute("""
            SELECT date, home_team_id, away_team_id, home_runs, away_runs
            FROM games WHERE status='final' AND home_runs IS NOT NULL
        """).fetchall()
        if len(rows) >= 200:
            teams = conn.execute("SELECT id FROM teams ORDER BY id").fetchall()
            team_id_map = {t[0]: idx for idx, t in enumerate(teams)}
            bt_games = []
            for r in rows:
                h_id, a_id = r[1], r[2]
                if h_id in team_id_map and a_id in team_id_map:
                    bt_games.append({
                        "home_idx": team_id_map[h_id],
                        "away_idx": team_id_map[a_id],
                        "home_won": r[3] > r[4],
                        "home_runs": r[3],
                        "away_runs": r[4],
                        "date": r[0],
                    })
            if len(bt_games) >= 200:
                _, hfa_log = fit_dynamic_bt(bt_games, len(teams), team_id_map, max_iter=50)
                _HFA_CACHE = (game_count, hfa_log)
                return hfa_log
    except Exception:
        pass

    row = conn.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN home_runs > away_runs THEN 1 ELSE 0 END) as home_wins
        FROM games
        WHERE status = 'final' AND home_runs IS NOT NULL AND neutral_site = 0
    """).fetchone()

    if row and row["total"] >= 50:
        home_pct = row["home_wins"] / row["total"]
        home_pct = max(0.45, min(0.65, home_pct))
        hfa = math.log(home_pct / (1 - home_pct))
        _HFA_CACHE = (game_count, hfa)
        return hfa

    _HFA_CACHE = (game_count, 0.16)
    return 0.16
