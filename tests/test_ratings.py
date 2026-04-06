"""Tests for fsbb.models.ratings."""

import math
from fsbb.models.ratings import pythagenport_exponent, pythagorean_wpct


def test_pythagenport_exponent_equal_scoring():
    """Equal RS and RA should give exponent based on RPG."""
    exp = pythagenport_exponent(100, 100, 20)
    # RPG = 200/20 = 10, so exp = 1.50 * log10(10) + 0.45 = 1.50 + 0.45 = 1.95
    assert abs(exp - 1.95) < 0.01


def test_pythagenport_exponent_college_range():
    """College baseball RPG (~12-13) should give exponent ~2.0-2.1."""
    exp = pythagenport_exponent(180, 120, 25)
    # RPG = 300/25 = 12, exp = 1.50 * log10(12) + 0.45 ≈ 2.07
    assert 1.9 < exp < 2.2


def test_pythagenport_exponent_mlb_range():
    """MLB RPG (~8-9) should give exponent ~1.8-1.9."""
    exp = pythagenport_exponent(700, 650, 162)
    # RPG = 1350/162 ≈ 8.33, exp ≈ 1.83
    assert 1.7 < exp < 1.95


def test_pythagorean_wpct_equal():
    """Equal RS and RA should give 0.5."""
    assert pythagorean_wpct(100, 100, 20) == 0.5


def test_pythagorean_wpct_dominant():
    """Strong team should have win% > 0.8."""
    pct = pythagorean_wpct(265, 93, 28)  # UCLA 2026
    assert pct > 0.8


def test_pythagorean_wpct_zero_runs():
    """Zero total runs should return 0.5."""
    assert pythagorean_wpct(0, 0, 0) == 0.5


def test_pythagorean_wpct_zero_games():
    """Zero games should return 0.5."""
    assert pythagorean_wpct(100, 50, 0) == 0.5


def test_pythagorean_wpct_range():
    """Result should always be in [0, 1]."""
    for rs, ra, g in [(1, 1000, 50), (1000, 1, 50), (50, 50, 10)]:
        pct = pythagorean_wpct(rs, ra, g)
        assert 0.0 <= pct <= 1.0
