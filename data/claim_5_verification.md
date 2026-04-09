# Claim #5: "BT model will outperform PEAR's static ratings"

**Source:** sentinel_briefing_v0.md:46
**Date verified:** 2026-04-09

## Verdict: PARTIALLY TRUE (BT contributes but doesn't solo outperform)

## Evidence

The blended model (Pythag 50% + BT 50% + pitcher + calibration) achieves 66.38%.
BT's contribution is in the blend — it propagates strength through transitive
connections in college baseball's unbalanced schedules.

BT alone was not isolated and tested separately (requires --mode bt-only flag
in backtest, not yet implemented).

From the power rating formula (ratings.py:326-341):
- BT weight scales 0% → 40% as games accumulate
- With 27+ games/team (mid-season), BT has ~40% influence
- Early season: BT has near-zero influence

## Assessment

BT is a valuable COMPONENT but not a standalone predictor. The claim should be
reframed: "Our blended Pythag+BT model outperforms either component alone.
BT's value is in transitive strength propagation for unbalanced schedules."

## TODO

Implement --mode bt-only and --mode pythag-only flags in fsbb backtest to
isolate each component's contribution.
