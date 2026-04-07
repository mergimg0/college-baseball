"""Monte Carlo game simulation using negative binomial run distribution.

College baseball runs are overdispersed vs Poisson (variance ≈ 1.5 × mean).
Negative binomial models this naturally. Simulates score distributions,
spread probabilities, and over/under probabilities.
"""

from __future__ import annotations

import numpy as np


def negative_binomial_runs(
    rpg: float,
    opponent_quality: float = 1.0,
    n_sims: int = 10000,
) -> np.ndarray:
    """Sample runs from calibrated negative binomial distribution.

    Args:
        rpg: Expected runs per game (team average)
        opponent_quality: Multiplier for opponent strength (>1 = weaker opponent)
        n_sims: Number of simulations

    Returns array of simulated run counts.
    """
    mu = max(0.5, rpg * opponent_quality)
    # College baseball: variance ≈ 1.5 × mean (overdispersed)
    variance = 1.5 * mu
    # NB parameterization: r = mu^2 / (var - mu), p = mu / var
    if variance <= mu:
        variance = mu + 0.01
    r = mu ** 2 / (variance - mu)
    p = mu / variance
    return np.random.negative_binomial(max(r, 0.1), min(p, 0.999), size=n_sims)


def simulate_game(
    home_rpg: float,
    away_rpg: float,
    home_win_prob: float | None = None,
    n_sims: int = 10000,
) -> dict:
    """Simulate a complete game n_sims times.

    Args:
        home_rpg: Home team runs per game
        away_rpg: Away team runs per game
        home_win_prob: Optional calibration target (adjusts run distributions)
        n_sims: Number of simulations

    Returns dict with simulation results.
    """
    rng = np.random.default_rng()

    home_runs = negative_binomial_runs(home_rpg, n_sims=n_sims)
    away_runs = negative_binomial_runs(away_rpg, n_sims=n_sims)

    # Break ties (extra innings as coin flip weighted by win prob)
    ties = home_runs == away_runs
    n_ties = ties.sum()
    if n_ties > 0:
        wp = home_win_prob or 0.5
        home_wins_extra = rng.random(n_ties) < wp
        home_runs[ties] += home_wins_extra.astype(int)
        away_runs[ties] += (~home_wins_extra).astype(int)

    home_wins = (home_runs > away_runs).sum()
    totals = home_runs + away_runs
    spreads = home_runs.astype(int) - away_runs.astype(int)

    return {
        "n_sims": n_sims,
        "home_win_pct": round(float(home_wins / n_sims), 4),
        "avg_home_runs": round(float(home_runs.mean()), 2),
        "avg_away_runs": round(float(away_runs.mean()), 2),
        "avg_total_runs": round(float(totals.mean()), 2),
        "median_total": int(np.median(totals)),
        "spread_median": round(float(np.median(spreads)), 1),
        "spread_mean": round(float(spreads.mean()), 2),
        "total_std": round(float(totals.std()), 2),
        "home_runs_dist": _distribution_summary(home_runs),
        "away_runs_dist": _distribution_summary(away_runs),
        "total_dist": _distribution_summary(totals),
    }


def compute_over_under(
    sim_result: dict,
    line: float,
) -> dict:
    """Compute over/under probabilities against a total line."""
    # Reconstruct from averages (approximate)
    # For exact: would need the raw arrays, but summary stats suffice
    total_mean = sim_result["avg_total_runs"]
    total_std = sim_result["total_std"]

    if total_std <= 0:
        return {"over_pct": 0.5, "under_pct": 0.5, "push_est": 0.0}

    # Normal approximation
    from math import erf, sqrt
    z = (line - total_mean) / total_std
    over_pct = 0.5 * (1 - erf(z / sqrt(2)))
    under_pct = 1.0 - over_pct

    return {
        "line": line,
        "over_pct": round(over_pct, 4),
        "under_pct": round(under_pct, 4),
    }


def _distribution_summary(arr: np.ndarray) -> dict:
    """Summarize a distribution with percentiles."""
    return {
        "mean": round(float(arr.mean()), 2),
        "std": round(float(arr.std()), 2),
        "p10": int(np.percentile(arr, 10)),
        "p25": int(np.percentile(arr, 25)),
        "p50": int(np.percentile(arr, 50)),
        "p75": int(np.percentile(arr, 75)),
        "p90": int(np.percentile(arr, 90)),
    }
