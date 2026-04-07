"""Kelly criterion bet sizing for college baseball predictions.

Full Kelly: f* = (p*b - q) / b
where p = model probability, q = 1-p, b = decimal_odds - 1

Default: quarter-Kelly (reduces variance 75%, same growth direction).
"""

from __future__ import annotations

import sqlite3
from datetime import date


def kelly_fraction(model_prob: float, market_prob: float) -> float:
    """Compute full Kelly fraction.

    Returns fraction of bankroll to bet (can be negative = don't bet).
    """
    if market_prob <= 0 or market_prob >= 1 or model_prob <= 0 or model_prob >= 1:
        return 0.0
    b = (1.0 / market_prob) - 1.0  # decimal odds - 1
    if b <= 0:
        return 0.0
    p = model_prob
    q = 1.0 - p
    return (p * b - q) / b


def compute_edge(model_prob: float, market_prob: float) -> float:
    """Edge in percentage points (model - market)."""
    return model_prob - market_prob


def recommend_bets(
    conn: sqlite3.Connection,
    target_date: date | None = None,
    bankroll: float = 1000.0,
    min_edge: float = 0.05,
    kelly_multiplier: float = 0.25,
    max_bet_pct: float = 0.05,
) -> list[dict]:
    """Generate bet recommendations for games with sufficient edge.

    Args:
        target_date: Date to analyze (default: today)
        bankroll: Total bankroll in dollars
        min_edge: Minimum edge to recommend (default 5%)
        kelly_multiplier: Fraction of Kelly to use (default 0.25 = quarter-Kelly)
        max_bet_pct: Max single bet as fraction of bankroll (default 5%)

    Returns sorted list of recommendations by edge size.
    """
    if target_date is None:
        target_date = date.today()

    games = conn.execute("""
        SELECT g.id, h.name as home, a.name as away,
               g.our_home_win_prob, g.odds_implied_home_prob,
               g.odds_home_ml, g.odds_away_ml, g.odds_bookmaker
        FROM games g
        JOIN teams h ON g.home_team_id = h.id
        JOIN teams a ON g.away_team_id = a.id
        WHERE g.date = ? AND g.our_home_win_prob IS NOT NULL
              AND g.odds_implied_home_prob IS NOT NULL
    """, (target_date.isoformat(),)).fetchall()

    recs = []
    for g in games:
        model_home = g["our_home_win_prob"]
        market_home = g["odds_implied_home_prob"]

        # Check both sides (home and away)
        for side, model_p, market_p, ml in [
            ("home", model_home, market_home, g["odds_home_ml"]),
            ("away", 1 - model_home, 1 - market_home, g["odds_away_ml"]),
        ]:
            edge = compute_edge(model_p, market_p)
            if edge < min_edge:
                continue

            fk = kelly_fraction(model_p, market_p)
            if fk <= 0:
                continue

            adjusted = fk * kelly_multiplier
            capped = min(adjusted, max_bet_pct)
            bet_amount = round(bankroll * capped, 2)

            if kelly_multiplier >= 0.9:
                confidence = "full_kelly"
            elif kelly_multiplier >= 0.45:
                confidence = "half_kelly"
            else:
                confidence = "quarter_kelly"

            team = g["home"] if side == "home" else g["away"]
            recs.append({
                "game_id": g["id"],
                "team": team,
                "side": side,
                "home": g["home"],
                "away": g["away"],
                "model_prob": round(model_p, 4),
                "market_prob": round(market_p, 4),
                "edge": round(edge, 4),
                "kelly_full": round(fk, 4),
                "kelly_adjusted": round(capped, 4),
                "recommended_bet": bet_amount,
                "moneyline": ml,
                "bookmaker": g["odds_bookmaker"] or "",
                "confidence": confidence,
            })

    recs.sort(key=lambda r: r["edge"], reverse=True)
    return recs
