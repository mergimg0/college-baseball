# Corrected V1 Roadmap (Post-OT Review)

## Honest Baseline
- **Production accuracy: 70.3%** on 4,070 games (Brier: 0.1923)
- **PEAR ELO baseline: 69.4%** — we are +0.9% ahead
- **V1 leaked backtest: 73.1%** — DISCREDITED (temporal data leakage, OT-019)
- **Realistic ceiling: 70-73%** with all improvements
- **Theoretical maximum: ~75%** (college baseball noise floor)

## Corrected Priority Order (OT-021)

| Priority | Feature | Expected Gain | Rationale |
|----------|---------|--------------|-----------|
| **P1** | **Starting pitcher adjustment** | +2-3% | THE MOAT. Only feature PEAR cannot replicate. Changes game-level predictions. |
| P2 | Walk-forward backtest | 0% (measurement) | Honest accuracy tracking. Required before claiming any improvement. |
| P3 | BABIP/LOB% regression flags | +0.5-1% | Identifies teams due for correction. Low effort, marginal gain. |
| P4 | Momentum (rolling 10-game) | +0.5% | Captures form shifts. Needs walk-forward implementation. |
| P5 | Betting edge calculator | Revenue, not accuracy | Turns predictions into value. Requires ODDS_API_KEY. |
| P6 | Conference z-scores | +0.3% | Marginal. May overlap with SOS already in model. |
| P7 | 308-team expansion | Risk: may hurt | Test first (OT-022). Weak teams add noise. |
| P8 | Travel/rest days | +0.3% | Easy but small. Fine at P8. |
| P9 | Weather (NOAA) | +0.3% | Engineering cost >> gain at this stage. |

## What We Tell Ryan
"70% accuracy on 4,000+ games. The next step is pitcher-specific predictions —
the one thing nobody else in college baseball does. We project 72-73% with that
addition. Under-promise, over-deliver."

## What We Do NOT Tell Ryan
- "73.1% accuracy" (leaked, discredited)
- "+7% accuracy available" (additive fallacy)
- "78-82% with all features" (fantasy)
