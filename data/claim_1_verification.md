# Claim #1: "College baseball lines are the most inefficient in American sports"

**Source:** v0v1_unified_specification.md:56 (Coach analysis)
**Date verified:** 2026-04-09

## Verdict: NOT YET VERIFIABLE

## Current State

- Games with odds data: 21 (need 500+ for statistical significance)
- odds_history table: 7 rows (CLV tracking enabled but sparse)
- No closing line value analysis possible yet

## Verification Plan

1. Run `fsbb odds` daily via cron/daily-update script
2. At 500+ games (~May 1 at 10-20 games/day), compute:
   - Average |model_prob - market_prob| (disagreement measure)
   - CLV: did closing lines move toward our predictions?
   - Compare college baseball vig (~7-10% est) vs MLB vig (~4-5%)
3. Inefficiency = model edge > 3% AND/OR vig > 5%

## Action Required

Ensure `fsbb odds` is in the daily pipeline. Check:
- .github/workflows/daily-update.yml includes odds step
- Local cron includes odds step

## Preliminary Evidence

College baseball odds are offered by fewer bookmakers (typically 2-4 vs 10+ for MLB),
wider spreads, and less sharp money — all indicators of market inefficiency.
But this is circumstantial, not quantitative.
