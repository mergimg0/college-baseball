# Architectural Analysis: Ryan_McCarthy_2026-03-30
**Date:** 2026-03-30

## Bottlenecks
- No claim processing gaps > 10s detected.

## Emotion-Quality Correlation
- No emotion data available for correlation analysis.

## Agent Performance
- No agent timeouts recorded.
- Claims per minute: 3736.8

## Config Suggestions
- No configuration changes suggested.

## Tuned Config (saved to data/config_overrides.json)
```json
{
  "spawn_cooldown_seconds": 61.13789688198555,
  "scaffold_timeout_minutes": 10.87014480869312,
  "max_concurrent_research": 3.0657745637540206,
  "max_concurrent_scaffold": 4.0176786990670195,
  "emotion_stride_seconds": 0.9774586065456342,
  "emotion_window_seconds": 2.9771445782427217
}
```

## Evaluator Weight Sensitivity

Most impactful weight: **knowledge**

| Weight | Variance | Mean | Range |
|--------|----------|------|-------|
| knowledge | 0.005513 | 0.2797 | 0.2631 |
| uptake | 0.000403 | 0.2596 | 0.0788 |
| verification | 0.000319 | 0.2539 | 0.0796 |
| engagement | 0.000275 | 0.2689 | 0.0728 |
| scaffold | 0.000214 | 0.2637 | 0.0573 |