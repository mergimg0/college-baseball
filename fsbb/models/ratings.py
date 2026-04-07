"""Rating engine: Pythagenport + Dynamic Bradley-Terry + SOS.

Three-layer architecture:
  Layer 1: Pythagorean Expected Win% (variable exponent for college baseball)
  Layer 2: Dynamic Bradley-Terry ratings via MM algorithm
  Layer 3: Strength of Schedule from BT ratings

References:
  - Pythagenport: Clay Davenport, adapts exponent to run environment
  - Pythagenpat: David Smyth, data-driven exponent
  - Bradley-Terry: Hunter 2004 MM algorithm
  - Dynamic BT: Firth & Kosmidis 2012, temporal decay
"""

from __future__ import annotations

import math
import sqlite3
from datetime import date, datetime

import numpy as np


# ---------------------------------------------------------------------------
# Layer 1: Pythagorean Expected Win Percentage
# ---------------------------------------------------------------------------

def pythagenport_exponent(runs_scored: int | float, runs_allowed: int | float, games: int | float) -> float:
    """Pythagenport (Davenport): exponent adapts to run environment.

    For college baseball, RPG varies 5.2–9.2 across conferences.
    Using fixed 1.83 (MLB) overestimates by 6–18%.
    Expected college exponent: ~1.60–1.72 for 2026 season.
    """
    rpg = (runs_scored + runs_allowed) / max(games, 1)
    return 1.50 * math.log10(max(rpg, 1.0)) + 0.45


def pythagenpat_exponent(runs_scored: int | float, runs_allowed: int | float, games: int | float) -> float:
    """Pythagenpat (Smyth): purely data-driven exponent."""
    rpg = (runs_scored + runs_allowed) / max(games, 1)
    return max(rpg, 1.0) ** 0.287


def pythagorean_wpct(rs: int | float, ra: int | float, games: int | float, method: str = "pythagenport") -> float:
    """Calculate Pythagorean expected win percentage.

    Args:
        rs: Total runs scored
        ra: Total runs allowed
        games: Games played
        method: "pythagenport" or "pythagenpat"

    Returns:
        Expected win percentage in [0, 1]
    """
    if rs + ra == 0 or games == 0:
        return 0.5

    if method == "pythagenpat":
        exp = pythagenpat_exponent(rs, ra, games)
    else:
        exp = pythagenport_exponent(rs, ra, games)

    return rs ** exp / (rs ** exp + ra ** exp)


# ---------------------------------------------------------------------------
# Layer 2: Dynamic Bradley-Terry via MM Algorithm
# ---------------------------------------------------------------------------

def fit_dynamic_bt(
    games: list[dict],
    n_teams: int,
    team_id_map: dict[int, int],
    lambda_decay: float = 0.020,
    max_iter: int = 200,
    tol: float = 1e-6,
    reference_date: date | None = None,
) -> tuple[np.ndarray, float]:
    """Fit Dynamic Bradley-Terry model via MM algorithm.

    Each game has temporal weight w_t = exp(-λ * days_ago).
    Home field advantage is estimated as a separate parameter.

    Args:
        games: List of dicts with keys: home_idx, away_idx, home_won, date
        n_teams: Number of teams
        team_id_map: Maps database team_id to 0-indexed array position
        lambda_decay: Temporal decay rate (half-life ≈ 35 days at 0.020)
        max_iter: Maximum MM iterations
        tol: Convergence tolerance
        reference_date: Date to compute recency from (default: today)

    Returns:
        (ratings, hfa) — log-scale team ratings and home field advantage
    """
    if not games:
        return np.zeros(n_teams), 0.0

    ref = reference_date or date.today()

    # Compute temporal weights
    weights = []
    home_idxs = []
    away_idxs = []
    home_wins = []

    for g in games:
        game_date = g["date"]
        if isinstance(game_date, str):
            game_date = datetime.fromisoformat(game_date).date()
        days_ago = (ref - game_date).days
        w = math.exp(-lambda_decay * max(days_ago, 0))
        weights.append(w)
        home_idxs.append(g["home_idx"])
        away_idxs.append(g["away_idx"])
        home_wins.append(1.0 if g["home_won"] else 0.0)

    weights = np.array(weights)
    home_idxs = np.array(home_idxs, dtype=int)
    away_idxs = np.array(away_idxs, dtype=int)
    home_wins_arr = np.array(home_wins)

    # Initialize ratings uniformly
    pi = np.ones(n_teams)
    hfa = 1.15  # Initial home field advantage multiplier (~54% home win rate)

    for iteration in range(max_iter):
        pi_old = pi.copy()
        hfa_old = hfa

        # E-step: compute expected outcomes
        home_strength = pi[home_idxs] * hfa
        away_strength = pi[away_idxs]
        p_home = home_strength / (home_strength + away_strength)

        # M-step: update ratings
        new_pi = np.ones(n_teams)
        for i in range(n_teams):
            home_mask = home_idxs == i
            away_mask = away_idxs == i

            # Weighted wins
            w_wins = (
                np.sum(weights[home_mask] * home_wins_arr[home_mask]) +
                np.sum(weights[away_mask] * (1 - home_wins_arr[away_mask]))
            )

            # Weighted expected denominator
            w_denom = (
                np.sum(weights[home_mask] / (home_strength[home_mask] + away_strength[home_mask])) +
                np.sum(weights[away_mask] / (home_strength[away_mask] + away_strength[away_mask]))
            )

            if w_denom > 0:
                new_pi[i] = w_wins / w_denom
            else:
                new_pi[i] = 1.0

        # Normalize (geometric mean = 1)
        log_mean = np.mean(np.log(np.maximum(new_pi, 1e-10)))
        pi = new_pi / math.exp(log_mean)

        # Update HFA
        hfa_num = np.sum(weights * home_wins_arr)
        hfa_den = np.sum(weights * pi[home_idxs] / (pi[home_idxs] * hfa + pi[away_idxs]))
        if hfa_den > 0:
            hfa = hfa_num / hfa_den
        hfa = max(0.8, min(hfa, 1.5))  # Clamp to reasonable range

        # Check convergence
        diff = np.max(np.abs(np.log(pi) - np.log(np.maximum(pi_old, 1e-10))))
        if diff < tol and abs(hfa - hfa_old) < tol:
            break

    # Convert to log-scale ratings
    ratings = np.log(np.maximum(pi, 1e-10))

    return ratings, math.log(max(hfa, 1e-10))


# ---------------------------------------------------------------------------
# Layer 3: Strength of Schedule
# ---------------------------------------------------------------------------

def compute_sos(
    games: list[dict],
    ratings: np.ndarray,
    n_teams: int,
) -> np.ndarray:
    """Compute strength of schedule as average opponent BT rating.

    Args:
        games: List of game dicts with home_idx, away_idx
        ratings: BT ratings array
        n_teams: Number of teams

    Returns:
        SOS array indexed by team position
    """
    opp_sum = np.zeros(n_teams)
    opp_count = np.zeros(n_teams)

    for g in games:
        h, a = g["home_idx"], g["away_idx"]
        opp_sum[h] += ratings[a]
        opp_count[h] += 1
        opp_sum[a] += ratings[h]
        opp_count[a] += 1

    sos = np.where(opp_count > 0, opp_sum / opp_count, 0.0)
    return sos


# ---------------------------------------------------------------------------
# Orchestrator: compute all ratings from database
# ---------------------------------------------------------------------------

def compute_all_ratings(conn: sqlite3.Connection) -> dict:
    """Compute Pythagorean W%, BT ratings, SOS for all teams.

    Steps:
      1. Load all final games
      2. Build team index
      3. Compute aggregate RS/RA per team
      4. Calculate Pythagenport exponent + Pythagorean W%
      5. Fit Dynamic BT
      6. Compute SOS
      7. Compute composite power rating
      8. Write all back to teams table

    Returns summary stats.
    """
    # Load teams with PEAR-imported stats
    teams = conn.execute("""
        SELECT id, name, total_rs, total_ra, games_played, wins, losses
        FROM teams ORDER BY id
    """).fetchall()
    if not teams:
        return {"error": "No teams in database"}

    team_id_map = {}  # db_id -> array_index
    team_names = {}   # array_index -> name
    for idx, row in enumerate(teams):
        team_id_map[row["id"]] = idx
        team_names[idx] = row["name"]

    n_teams = len(teams)

    # Use PEAR-imported team-level RS/RA for Pythagorean (more complete than game-level)
    rs_map = np.zeros(n_teams)
    ra_map = np.zeros(n_teams)
    gp_map = np.zeros(n_teams)
    wins_map = np.zeros(n_teams)

    for idx, row in enumerate(teams):
        rs_map[idx] = row["total_rs"] or 0
        ra_map[idx] = row["total_ra"] or 0
        gp_map[idx] = row["games_played"] or 0
        wins_map[idx] = row["wins"] or 0

    # Load completed games for BT model
    rows = conn.execute("""
        SELECT date, home_team_id, away_team_id, home_runs, away_runs, actual_winner_id
        FROM games WHERE status='final' AND home_runs IS NOT NULL
    """).fetchall()

    if not rows:
        # Even without games, compute from PEAR-imported RS/RA
        _compute_pythag_from_pear(conn, teams)
        return {"teams": n_teams, "games": 0, "note": "No games found, used PEAR stats"}

    # Build game list for BT
    bt_games = []

    for r in rows:
        h_id, a_id = r["home_team_id"], r["away_team_id"]
        if h_id not in team_id_map or a_id not in team_id_map:
            continue

        h_idx = team_id_map[h_id]
        a_idx = team_id_map[a_id]
        h_runs = r["home_runs"]
        a_runs = r["away_runs"]
        home_won = h_runs > a_runs

        bt_games.append({
            "home_idx": h_idx,
            "away_idx": a_idx,
            "home_won": home_won,
            "date": r["date"],
        })

    # Layer 1: Pythagorean W%
    pythag = np.full(n_teams, 0.5)
    pythag_exp = np.full(n_teams, 1.83)
    for i in range(n_teams):
        if gp_map[i] >= 5 and rs_map[i] > 0 and ra_map[i] > 0:
            p = pythagorean_wpct(int(rs_map[i]), int(ra_map[i]), int(gp_map[i]))
            pythag[i] = p
            pythag_exp[i] = pythagenport_exponent(int(rs_map[i]), int(ra_map[i]), int(gp_map[i]))

    # Layer 2: Dynamic BT
    ratings, hfa = fit_dynamic_bt(bt_games, n_teams, team_id_map)

    # Layer 3: SOS
    sos = compute_sos(bt_games, ratings, n_teams)

    # Composite power rating: Pythag-dominant blend
    # BT is noisy with sparse game data, so weight Pythag heavily
    if ratings.std() > 0:
        bt_norm = (ratings - ratings.min()) / (ratings.max() - ratings.min())
    else:
        bt_norm = np.full(n_teams, 0.5)

    sos_norm = (sos - sos.min()) / (sos.max() - sos.min() + 1e-10)

    # Count games per team in BT data for confidence weighting
    bt_game_count = np.zeros(n_teams)
    for g in bt_games:
        bt_game_count[g["home_idx"]] += 1
        bt_game_count[g["away_idx"]] += 1

    # Dynamic power rating weights based on actual data coverage
    avg_games_per_team = float(np.mean(bt_game_count[bt_game_count > 0])) if np.any(bt_game_count > 0) else 0
    # BT weight scales with data: 0% at 0 games/team → 40% at 20+ games/team
    global_bt_weight = min(avg_games_per_team / 20.0, 1.0) * 0.4

    pear_sos_vals = np.array([
        conn.execute("SELECT pear_sos FROM teams WHERE id=?", (teams[i]["id"],)).fetchone()[0] or 150
        for i in range(n_teams)
    ], dtype=float)
    sos_strength = 1.0 - (pear_sos_vals / (pear_sos_vals.max() + 1))

    # Per-team BT confidence: teams with more games get more BT weight
    team_bt_weight = np.minimum(bt_game_count / 15.0, 1.0) * global_bt_weight

    # Power = (1 - team_bt_weight - 0.1) * Pythag + team_bt_weight * BT_norm + 0.1 * SOS
    pythag_weight = np.maximum(0.9 - team_bt_weight, 0.5)
    power = pythag_weight * pythag + team_bt_weight * bt_norm + 0.1 * sos_strength

    # Derive ELO from BT ratings: ELO = 1500 + bt_rating * (400 / ln(10))
    # This maps BT log-scale to the standard ELO scale where 400 points ≈ 10:1 odds
    bt_to_elo_scale = 400.0 / math.log(10)  # ≈ 173.72
    elo = 1500.0 + ratings * bt_to_elo_scale

    # Write computed ratings back to database (keep PEAR RS/RA intact)
    for i in range(n_teams):
        db_id = teams[i]["id"]
        conn.execute("""
            UPDATE teams SET
                pythag_exp=?, pythag_pct=?, bt_rating=?, sos=?, power_rating=?, elo=?
            WHERE id=?
        """, (
            float(pythag_exp[i]), float(pythag[i]),
            float(ratings[i]), float(sos[i]), float(power[i]), float(elo[i]),
            db_id,
        ))

    conn.commit()

    # Calibration info
    global_rpg = (rs_map.sum() + ra_map.sum()) / max(gp_map.sum(), 1)
    global_exp = pythagenport_exponent(int(rs_map.sum()), int(ra_map.sum()), int(gp_map.sum()))

    return {
        "teams": n_teams,
        "games": len(bt_games),
        "global_rpg": float(global_rpg),
        "global_pythagenport_exp": float(global_exp),
        "hfa_log": float(hfa),
        "hfa_pct": float(1 / (1 + math.exp(-hfa))),  # Convert to win probability
        "bt_iterations": "converged",
        "mean_bt_rating": float(ratings.mean()),
        "std_bt_rating": float(ratings.std()),
    }


def _compute_pythag_from_pear(conn: sqlite3.Connection, teams: list) -> None:
    """Fallback: compute Pythagorean from PEAR-imported RS/RA."""
    for row in teams:
        t = conn.execute(
            "SELECT total_rs, total_ra, games_played FROM teams WHERE id=?",
            (row["id"],)
        ).fetchone()
        if t and t["games_played"] > 0:
            p = pythagorean_wpct(t["total_rs"], t["total_ra"], t["games_played"])
            exp = pythagenport_exponent(t["total_rs"], t["total_ra"], t["games_played"])
            conn.execute(
                "UPDATE teams SET pythag_pct=?, pythag_exp=? WHERE id=?",
                (p, exp, row["id"])
            )
    conn.commit()
