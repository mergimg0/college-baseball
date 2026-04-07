"""Bayesian confidence intervals for game predictions.

Uses conjugate normal-normal updates in log-odds space to provide
credible intervals around win probability predictions.

Prior: Normal(0, 1) for log-odds of team strength differential.
Posterior updates: After each observed game, tighten the variance.
CI: posterior_mean +/- z * sqrt(posterior_var), then sigmoid transform.
"""

from __future__ import annotations

import math
import sqlite3


class BayesianPredictor:
    """Bayesian predictor with conjugate normal updates in log-odds space."""

    def __init__(self, prior_mean: float = 0.0, prior_var: float = 1.0):
        self.mean = prior_mean
        self.var = prior_var

    def update(self, observation: float, obs_var: float = 0.25) -> None:
        """Update posterior with a new observation (in log-odds space).

        observation: observed log-odds (e.g., from game outcome)
        obs_var: observation variance (lower = more informative)
        """
        precision_prior = 1.0 / self.var
        precision_obs = 1.0 / obs_var
        precision_post = precision_prior + precision_obs
        self.mean = (precision_prior * self.mean + precision_obs * observation) / precision_post
        self.var = 1.0 / precision_post

    def predict(self, log_odds_diff: float) -> tuple[float, float]:
        """Predict win probability with uncertainty.

        Returns (prob, variance_in_prob_space).
        """
        total_mean = log_odds_diff + self.mean
        total_var = self.var
        prob = _sigmoid(total_mean)
        return prob, total_var

    def credible_interval(
        self, log_odds_diff: float, alpha: float = 0.10
    ) -> tuple[float, float, float]:
        """Compute credible interval for win probability.

        Args:
            log_odds_diff: log-odds from the prediction model
            alpha: significance level (0.10 = 90% CI)

        Returns (mean_prob, ci_lower, ci_upper).
        """
        z = _z_score(1 - alpha / 2)
        total_mean = log_odds_diff + self.mean
        total_std = math.sqrt(self.var)

        lo_lower = total_mean - z * total_std
        lo_upper = total_mean + z * total_std

        return (
            _sigmoid(total_mean),
            _sigmoid(lo_lower),
            _sigmoid(lo_upper),
        )


def compute_team_posteriors(conn: sqlite3.Connection) -> dict[int, BayesianPredictor]:
    """Build Bayesian posteriors for all teams from game history.

    Processes games chronologically, updating both teams' posteriors
    after each game. Returns dict mapping team_id -> BayesianPredictor.
    """
    games = conn.execute("""
        SELECT home_team_id, away_team_id, home_runs, away_runs
        FROM games
        WHERE status = 'final' AND home_runs IS NOT NULL
        ORDER BY date
    """).fetchall()

    posteriors: dict[int, BayesianPredictor] = {}

    for home_id, away_id, h_runs, a_runs in games:
        if home_id not in posteriors:
            posteriors[home_id] = BayesianPredictor()
        if away_id not in posteriors:
            posteriors[away_id] = BayesianPredictor()

        # Outcome in log-odds: win=+1, loss=-1 (scaled)
        margin = (h_runs - a_runs) if h_runs is not None and a_runs is not None else 0
        outcome = 0.5 * max(-3, min(3, margin))  # cap at 3 runs

        # Update both teams (home perspective)
        posteriors[home_id].update(outcome, obs_var=0.5)
        posteriors[away_id].update(-outcome, obs_var=0.5)

    return posteriors


def predict_with_ci(
    conn: sqlite3.Connection,
    home_team: str,
    away_team: str,
    alpha: float = 0.10,
) -> dict | None:
    """Predict matchup with Bayesian credible intervals.

    Returns dict with home_win_prob, ci_lower, ci_upper, ci_width.
    """
    home = conn.execute("SELECT id FROM teams WHERE name=?", (home_team,)).fetchone()
    away = conn.execute("SELECT id FROM teams WHERE name=?", (away_team,)).fetchone()
    if not home or not away:
        return None

    posteriors = compute_team_posteriors(conn)
    h_post = posteriors.get(home[0], BayesianPredictor())
    a_post = posteriors.get(away[0], BayesianPredictor())

    # Combined log-odds: difference of posterior means + HFA
    hfa = 0.16  # ~54% baseline
    log_odds_diff = h_post.mean - a_post.mean + hfa
    combined_var = h_post.var + a_post.var

    # Build combined predictor for CI
    combined = BayesianPredictor(prior_mean=0.0, prior_var=combined_var)
    prob, ci_lower, ci_upper = combined.credible_interval(log_odds_diff, alpha)

    return {
        "home_team": home_team,
        "away_team": away_team,
        "home_win_prob": round(prob, 4),
        "ci_lower": round(ci_lower, 4),
        "ci_upper": round(ci_upper, 4),
        "ci_width": round(ci_upper - ci_lower, 4),
        "alpha": alpha,
        "home_posterior_var": round(h_post.var, 4),
        "away_posterior_var": round(a_post.var, 4),
    }


def _sigmoid(x: float) -> float:
    x = max(-30, min(30, x))
    return 1.0 / (1.0 + math.exp(-x))


def _z_score(p: float) -> float:
    """Approximate inverse normal CDF for common quantiles."""
    # Rational approximation (Abramowitz & Stegun 26.2.23)
    if p <= 0.5:
        return -_z_score(1 - p)
    t = math.sqrt(-2 * math.log(1 - p))
    c0, c1, c2 = 2.515517, 0.802853, 0.010328
    d1, d2, d3 = 1.432788, 0.189269, 0.001308
    return t - (c0 + c1 * t + c2 * t * t) / (1 + d1 * t + d2 * t * t + d3 * t * t * t)
