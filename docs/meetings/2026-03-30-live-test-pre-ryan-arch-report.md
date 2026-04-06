# Architectural Analysis: live-test-pre-ryan
**Date:** 2026-03-30

## Bottlenecks
- No claim processing gaps > 10s detected.

## Emotion-Quality Correlation
- Engagement-claim density: r=0.00 (weak negative)
- Low-engagement claims: 82% confidence avg

## Agent Performance
- No agent timeouts recorded.
- Claims per minute: 2.3

## Config Suggestions
- No configuration changes suggested.

## Tuned Config (saved to data/config_overrides.json)
```json
{
  "spawn_cooldown_seconds": 58.52647216650895,
  "scaffold_timeout_minutes": 10.332544463273159,
  "max_concurrent_research": 3.080254743118607,
  "max_concurrent_scaffold": 3.831134274616197,
  "emotion_stride_seconds": 0.996039759219123,
  "emotion_window_seconds": 2.967474443787542
}
```

## Evaluator Weight Sensitivity

Most impactful weight: **knowledge**

| Weight | Variance | Mean | Range |
|--------|----------|------|-------|
| knowledge | 0.002656 | 0.2322 | 0.1760 |
| verification | 0.000859 | 0.2463 | 0.0985 |
| uptake | 0.000693 | 0.2388 | 0.0975 |
| engagement | 0.000471 | 0.2351 | 0.0744 |
| scaffold | 0.000312 | 0.2308 | 0.0700 |