# Architectural Analysis: Ryan_McCarthy_enriched_2026-03-30
**Date:** 2026-03-31

## Bottlenecks
- No claim processing gaps > 10s detected.

## Emotion-Quality Correlation
- No emotion data available for correlation analysis.

## Agent Performance
- No agent timeouts recorded.
- Claims per minute: 23206.7

## Config Suggestions
- No configuration changes suggested.

## Tuned Config (saved to data/config_overrides.json)
```json
{
  "spawn_cooldown_seconds": 61.91819897764695,
  "scaffold_timeout_minutes": 9.947362781350044,
  "max_concurrent_research": 3.0119750517245327,
  "max_concurrent_scaffold": 4.173413132433208,
  "emotion_stride_seconds": 1.0622251884105984,
  "emotion_window_seconds": 2.9803405675572923
}
```

## Evaluator Weight Sensitivity

Most impactful weight: **knowledge**

| Weight | Variance | Mean | Range |
|--------|----------|------|-------|
| knowledge | 0.004746 | 0.2707 | 0.2173 |
| uptake | 0.000824 | 0.2752 | 0.1024 |
| engagement | 0.000765 | 0.2696 | 0.0882 |
| verification | 0.000721 | 0.2784 | 0.0880 |
| scaffold | 0.000643 | 0.2745 | 0.1126 |