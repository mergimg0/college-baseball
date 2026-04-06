# Architectural Analysis: Tim_McCarthy_2026-03-30
**Date:** 2026-03-30

## Bottlenecks
- No claim processing gaps > 10s detected.

## Emotion-Quality Correlation
- No emotion data available for correlation analysis.

## Agent Performance
- No agent timeouts recorded.
- Claims per minute: 5056.8

## Config Suggestions
- No configuration changes suggested.

## Tuned Config (saved to data/config_overrides.json)
```json
{
  "spawn_cooldown_seconds": 58.17192822371643,
  "scaffold_timeout_minutes": 10.378388206555151,
  "max_concurrent_research": 2.9258939815734686,
  "max_concurrent_scaffold": 4.024283659827825,
  "emotion_stride_seconds": 1.0034062487487507,
  "emotion_window_seconds": 3.0775950675497414
}
```

## Evaluator Weight Sensitivity

Most impactful weight: **knowledge**

| Weight | Variance | Mean | Range |
|--------|----------|------|-------|
| knowledge | 0.004004 | 0.2925 | 0.2411 |
| uptake | 0.000894 | 0.3104 | 0.1208 |
| scaffold | 0.000638 | 0.3084 | 0.1025 |
| verification | 0.000598 | 0.2982 | 0.0803 |
| engagement | 0.000313 | 0.3060 | 0.0713 |