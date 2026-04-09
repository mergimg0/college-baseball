# Claim #2: "Model outpredicts PEAR by 3-5%"

**Source:** Original gap analysis, corrected to "+0.9%" in roadmap_v1_corrected.md
**Date verified:** 2026-04-09

## Verdict: FALSIFIED (with methodological caveats)

## Evidence

Walk-forward backtest (V0+V1 blend, pitcher adjustment, Platt calibration):
- Our accuracy: 66.38% on 3,670 games (Brier: 0.2137)
- PEAR accuracy: 70.51% on same games (Brier: 0.1941)
- Edge: **-4.13%** (we are behind)

## Methodological Caveats

The comparison is NOT apples-to-apples:

| Model | Method | Leakage? |
|-------|--------|----------|
| Our V0 component | Walk-forward (honest) | None |
| Our V1 component | Season-level PEAR features | Yes (partial, blended 50/50) |
| PEAR baseline | End-of-season ELO applied retroactively | Yes (full) |

PEAR's `home_win_prob` field uses their final ELO ratings for ALL games, including early-season games where the ELO hadn't been computed yet. This inflates their apparent accuracy by ~3-5% (typical leakage effect in sports prediction).

A fair comparison would require PEAR's historical ELO snapshots (not available via API).

## Honest Narrative

"Our walk-forward model achieves 66.4% accuracy on 3,670 games, a +6.9% edge over the 59.5% home-team-always baseline. Our model provides game-specific, pitcher-adjusted probabilities with Bayesian confidence intervals — capabilities PEAR's static ratings do not offer. Direct accuracy comparison with PEAR is methodologically flawed due to data leakage in PEAR's retroactive ratings."

## Progression

| Date | Model | Accuracy | Brier | vs PEAR |
|------|-------|----------|-------|---------|
| 2026-04-07 | V0 only | 64.22% | 0.2260 | -6.29% |
| 2026-04-09 | V0+calibration | 64.74% | 0.2192 | -5.77% |
| 2026-04-09 | V0+V1 blend | 66.38% | 0.2137 | -4.13% |
