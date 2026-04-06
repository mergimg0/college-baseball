# Architectural Analysis: Ryan_McCarthy_xvector_2026-03-30
**Date:** 2026-03-31

## Bottlenecks
- No claim processing gaps > 10s detected.

## Emotion-Quality Correlation
- No emotion data available for correlation analysis.

## Agent Performance
- No agent timeouts recorded.
- Claims per minute: 3298.6

## Config Suggestions
- No configuration changes suggested.

## Tuned Config (saved to data/config_overrides.json)
```json
{
  "spawn_cooldown_seconds": 59.24758464040703,
  "scaffold_timeout_minutes": 10.159545841622279,
  "max_concurrent_research": 3.0710330241391866,
  "max_concurrent_scaffold": 3.9520202733747882,
  "emotion_stride_seconds": 0.9687255981553194,
  "emotion_window_seconds": 3.0493139007032584
}
```

## Evaluator Weight Sensitivity

Most impactful weight: **knowledge**

| Weight | Variance | Mean | Range |
|--------|----------|------|-------|
| knowledge | 0.004815 | 0.2497 | 0.2382 |
| verification | 0.000879 | 0.2548 | 0.1046 |
| uptake | 0.000791 | 0.2515 | 0.0949 |
| engagement | 0.000447 | 0.2568 | 0.0774 |
| scaffold | 0.000427 | 0.2520 | 0.0886 |