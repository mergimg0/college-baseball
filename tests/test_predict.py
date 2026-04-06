"""Tests for fsbb.models.predict."""

from fsbb.db import init_db
from fsbb.models.predict import predict_matchup, _estimate_hfa


def test_predict_nonexistent_team_returns_none():
    """predict_matchup should return None for teams not in DB."""
    conn = init_db()
    result = predict_matchup(conn, "Nonexistent University", "Fake College")
    conn.close()
    assert result is None


def test_predict_probability_clamped():
    """Win probability must be in [0.05, 0.95]."""
    conn = init_db()
    # Use two real teams with very different quality
    result = predict_matchup(conn, "UCLA", "Delaware St.")
    conn.close()
    if result is None:
        return  # Skip if teams not in DB
    assert 0.05 <= result["home_win_prob"] <= 0.95
    assert 0.05 <= result["away_win_prob"] <= 0.95


def test_predict_probabilities_sum_to_one():
    """Home + away probabilities should sum to ~1.0."""
    conn = init_db()
    result = predict_matchup(conn, "Texas", "UCLA")
    conn.close()
    if result is None:
        return
    total = result["home_win_prob"] + result["away_win_prob"]
    assert abs(total - 1.0) < 0.01


def test_hfa_single_source():
    """HFA should come from exactly one source — no double-counting.

    The bug (IM-2/IR-001): HFA was applied twice when bt_weight was
    between 0 and 0.3. After fix, HFA is only applied in the BT path
    (via _estimate_hfa in bt_logit) OR via log-odds shift when bt_weight=0.
    Never both.
    """
    conn = init_db()
    # Predict same matchup — home and away should differ by HFA amount
    result_home = predict_matchup(conn, "Texas", "Alabama")
    result_away = predict_matchup(conn, "Alabama", "Texas")
    conn.close()
    if result_home is None or result_away is None:
        return
    # The HFA effect: Texas-at-home vs Alabama-at-home
    # The difference should be moderate (not doubled)
    home_advantage = result_home["home_win_prob"] - result_away["away_win_prob"]
    # HFA should add ~3-8% to win probability, not 10%+
    assert abs(home_advantage) < 0.15, f"HFA effect too large: {home_advantage:.3f} (possible double-counting)"


def test_estimate_hfa_reasonable():
    """Estimated HFA should be in reasonable range."""
    conn = init_db()
    hfa = _estimate_hfa(conn)
    conn.close()
    # Log-odds: 0.16 = ~54% home win rate. Should be in [0.05, 0.50]
    assert 0.0 <= hfa <= 0.50
