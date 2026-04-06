# V0/V1 Algorithm R&D — ForgeStream Baseball

**Generated:** 2026-03-31 | **Sources:** 3 research agents (76 web searches), PEAR data analysis (308 teams), architecture spec, competitive research
**Purpose:** Determine exactly what makes our model different, whether the differentiation is real, and the concrete math for each component.

---

## CRITICAL FINDING: PEAR Is More Sophisticated Than We Thought

Before diving into R&D, a correction to the architecture spec. PEAR's per-team data (166 fields per team) already includes:

- **wOBA, wRAA, wRC+** (weighted offense metrics)
- **FIP** (fielding-independent pitching)
- **fWAR** (wins above replacement)
- **PYTHAG** (Pythagorean win expectation)
- **ELO with delta tracking**
- **Killshot metrics** (momentum/run scoring)
- **Bubble analysis** with projected records
- **Game-level win probabilities and spreads**

However, PEAR's game predictions have a critical weakness confirmed by data:

**PEAR uses IDENTICAL win probabilities for ALL games in a 3-game series.** Verified: Vanderbilt vs Tennessee (Mar 27-29, 2026) shows `home_win_prob: 0.4914` for all three games. The Texas A&M series (Apr 2-4) shows `0.6704` for all three. PEAR does NOT adjust for starting pitcher, game position within series, or any per-game context.

This narrows our differentiation: we're not competing against a naive model. We're competing against a model that has wOBA/FIP/fWAR but fails at game-level contextualization.

---

## 1. The Equation Translation: Financial Alpha → Baseball Prediction

### Research Finding: Sports Betting IS a Financial Market

Academic consensus (Kovalchik 2023, Hubacek et al. 2019): sports betting markets exhibit the same microstructure properties as financial markets — information asymmetry, price discovery, market efficiency with pockets of exploitable inefficiency. The translation is not metaphorical; it's structural.

**Key parallels:**

| Financial Concept | Baseball Equivalent |
|---|---|
| Asset price | Team rating / game line |
| Alpha (excess return) | Prediction accuracy above market (Vegas lines) |
| Signal | Game features (pitcher, weather, rest, SOS) |
| Noise | Baseball's inherent variance (~40% best team losing) |
| Portfolio | Betting slate / prediction set |
| Kelly criterion | Optimal bet sizing given edge and bankroll |
| Regime change | Seasonal evolution (early noise → late signal) |

**What transfers directly from Mergim's equation:**
1. **Probabilistic output** — distribution over outcomes, not point estimates
2. **Online learning** — the model updates beliefs with each observation (game result)
3. **Edge detection** — comparing model probability to market-implied probability
4. **Kelly-optimal sizing** — capital allocation per bet given edge and uncertainty
5. **Regime detection** — different model behavior for different market conditions (early vs late season)

**What does NOT transfer:**
- Financial markets have continuous prices; baseball has discrete events
- Trading frequency (thousands/day) vs game frequency (~15 per team per month)
- Financial data is noisy but abundant; baseball data is noisy AND scarce

**Key citation:** Tobias Moskowitz (Yale SOM), "Asset Pricing and Sports Betting," *Journal of Finance* (2021). Analyzed 100K+ sports betting contracts. Found: (1) momentum effect is real — bettors overprice winning streaks, causing systematic mispricing of ~1/5 equity momentum per unit risk; (2) value effect is weak but present; (3) neither factor survives transaction costs (bookmaker vig), but they ARE real probability mis-estimates. **Implication:** include a trailing 5-game momentum feature in our model.

**Honest assessment:** The equation framework transfers conceptually, but the parameter tuning is entirely different. A financial alpha model trained on tick data will not work on 56 games. The architecture transfers; the weights must be learned from scratch on baseball data.

**Moat rating: MODERATE.** The framework provides a structural advantage in thinking about the problem, but the actual model must be rebuilt for baseball. A quantitative sports bettor with financial background could replicate this approach.

### RL for Sports Prediction — State of the Art

**Research finding:** RL for game outcome prediction is mostly academic, not production-proven.

**What exists:**
- **In-game RL (production-proven):** Soccer analytics using offline RL for predicting offensive/defensive actions during play, achieving 87% accuracy (Springer Nature, 2024). This is RL for *within-game strategy*, not game outcome prediction.
- **Fantasy sports RL (proof-of-concept):** Deep RL for cricket team selection (2024 paper). Autonomous team construction using historical data. More about portfolio optimization than prediction.
- **NBA money line prediction (academic):** Stanford CS224R project applying Deep Q-Learning to NBA betting. Academic only, not production.
- **Bankroll management RL (production):** Using RL for Kelly criterion sizing — deciding how much to bet, not what to bet on. This is where RL is most naturally applicable.

**The right RL framing for our problem:**

Game outcome prediction is NOT a sequential decision problem for the model. The model doesn't take actions that affect game outcomes. It's an **online learning problem** — the model observes features, makes a prediction, observes the outcome, and updates. This is a **contextual bandit**, not full RL.

```
State:  s_t = (team_A_features, team_B_features, context_features)
Action: a_t = probability prediction (continuous, [0,1])
Reward: r_t = -BrierScore(prediction, outcome)  [or log loss]
Policy: π(s_t) → a_t  (learned mapping from features to probabilities)
```

The "self-learning" claim is valid but should be framed as **online logistic regression with adaptive learning rate**, not as deep RL. This is more honest, more implementable, and actually performs better for this problem size.

**Cold-start problem:** 56 games per team per season is too few for deep RL to learn from scratch (Stanford DQN paper used 2,000+ NBA games — 36x more). Solutions:
1. **Pre-train on MLB data** via Retrosheet (free, back to 1871), fine-tune on college. The WSRL paper (arxiv 2412.07762) shows offline pre-training + small online rollout prevents Q-value divergence.
2. **Pre-train on previous college seasons** (3+ seasons = 25K+ games)
3. **Start with Bayesian priors** from last season, let online learning update
4. **Use hierarchical structure** — conference-level parameters pool data across 308 teams
5. **Glicko-2** (Mark Glickman, BU) — production-proven rating system that naturally handles cold-start through rating deviation (RD). RD starts high (uncertain) and shrinks as games are played. After 56 games, RD is appropriately narrow. Used in chess, video game matchmaking. Python: `glicko2` library.

**Research finding on Glicko-2 performance:** Glicko-2 outperformed both Elo and TrueSkill at predicting non-draw professional match outcomes (systematic gains in accuracy across training horizons). MOVDA showed 0.22%-1.54% lower Brier score over Glicko-2, suggesting Glicko-2 is a strong baseline that's hard to beat substantially.

**Moat rating: LOW for deep RL, MODERATE for online learning.** The "self-learning" concept is real but the implementation is standard online ML, not exotic RL. A grad student with scikit-learn can implement the same thing. The moat comes from domain knowledge in feature selection, prior design, and accumulated track record — not from the learning algorithm itself.

**Concrete recommendation (from RL agent):** Do NOT use model-free RL (DQN/PPO) as the core predictor. Use Glicko-2 or Dynamic Bradley-Terry as the online rating system, logistic regression as the game-level classifier with pre-season priors, and Kelly criterion as the evaluation metric. Reserve the RL framing for bankroll management (a separate module on top), not the prediction layer itself.

---

## 2. Bayesian Model Architecture — Concrete Specification

### The Conjugate Normal-Normal Update

For team strength rating θ:

**Prior:** θ ~ N(μ₀, σ₀²)
- μ₀ = last season's adjusted power rating (or conference average for new teams)
- σ₀ = prior uncertainty (wider for teams with high transfer portal activity)

**Likelihood:** For each game, observe margin y = RS - RA:
- y ~ N(θ_home - θ_away + HFA, σ²_game)
- σ²_game = game-level variance (estimated from historical data, ~4-5 runs²)
- HFA = home field advantage parameter

**Posterior after n games:**

```
τ₀ = 1/σ₀²              (prior precision)
τ = 1/σ²_game           (data precision per game)

After n games with observed margins y₁, ..., yₙ (adjusted for opponent):

τₙ = τ₀ + n·τ           (posterior precision)
σₙ² = 1/τₙ              (posterior variance)

μₙ = (τ₀·μ₀ + τ·Σyᵢ) / τₙ    (posterior mean = weighted average of prior and data)

Equivalently:
μₙ = w·ȳ + (1-w)·μ₀     where w = n·τ/(τ₀ + n·τ)
```

**Numerical example (college baseball):**
- σ₀ = 2.0 (prior std — moderate uncertainty about team strength)
- σ_game = 4.5 (game-level std — baseball is noisy)
- τ₀ = 1/4 = 0.25, τ = 1/20.25 ≈ 0.049

After 10 games: w = 10 × 0.049 / (0.25 + 0.49) = 0.49/0.74 = 0.66
→ **After 10 games, the model is 66% data, 34% prior.** This is the right balance for college baseball.

After 30 games: w = 1.47/1.72 = 0.85
→ **After 30 games, 85% data, 15% prior.** Prior is still non-trivial mid-season.

After 56 games: w = 2.74/2.99 = 0.92
→ **End of season, 92% data, 8% prior.** Prior still exerts slight shrinkage effect.

**Prior standard deviation for halving posterior variance:**
- σₙ² = σ₀²/2 when n = τ₀/τ = σ²_game/σ₀² = 20.25/4 ≈ 5 games
- **After just 5 games, the posterior uncertainty halves.** This means the model converges quickly, which is good for a 56-game season.

### Prior Distribution: Normal vs Student-t

**Research finding (Bayesian agent):** Community consensus is: **Normal on latent team ratings, Student-t on the game outcome likelihood.** The upsets live in the observation noise, not the prior.

| Level | Distribution | Rationale |
|---|---|---|
| Team rating prior | Normal | CLT applies; hierarchical shrinkage regularizes |
| Sigma hyperparameters | HalfStudentT(ν=3) | Robust; Stan/PyMC default recommendation |
| Game outcome likelihood | Student-t(ν=5-7) | Fatter tails = upset probability modeled correctly |

**Recommendation:** Use Normal priors with Student-t(ν=5) likelihood. The update is no longer conjugate, but Laplace approximation (used by Glicko-2) provides a fast, accurate posterior.

### Critical Calibration: Pythagenpat Over Fixed Exponent

**Research finding (Pythag agent):** No published college-baseball-specific exponent exists. The default 1.83 is MLB-derived. But Pythagenpat (David Smyth) adapts the exponent to the run environment:

```
exp = ((RS + RA) / G) ^ 0.287
```

This matters enormously for college baseball because run environments vary wildly by conference:

| Context | RPG | Pythagenpat exp | Fixed 1.83 error |
|---|---|---|---|
| SEC (high offense) | 9.17 | 1.889 | -0.059 |
| Ivy League (low offense) | 5.18 | 1.603 | +0.227 |

Using a fixed 1.83 **systematically overestimates** win expectation in low-offense conferences and **underestimates** in high-offense ones. Pythagenpat eliminates this conference-level bias.

**BBCOR bat impact:** Post-2011 BBCOR implementation dropped home runs 44% in one year. The run environment shifted dramatically, meaning any historical exponent calibration must account for the BBCOR regime change.

### Key Finding: Bradley-Terry > Elo for College Baseball

**Research finding (Pythag agent):** Bradley-Terry (BT) is the **batch maximum likelihood version of Elo** — mathematically equivalent but BT solves the entire pairwise system simultaneously. The relationship:

```
π_i (BT strength) = 10^(r_i / 400)    where r_i = Elo rating
P(i beats j) = π_i / (π_i + π_j)
```

**Why BT is superior for college baseball:** A Sun Belt team and a Big Ten team may share zero direct opponents. BT propagates strength information through transitive connections across the full schedule graph. Elo cannot retroactively do this — it's sequential.

**Dynamic BT** (Firth & Kosmidis 2012) adds temporal decay: w_t = exp(-λt) with λ ≈ 0.017-0.023 (half-life 30-40 days). This handles both schedule-imbalance correction AND time-varying team strength.

**Fitting:** MM algorithm (Hunter 2004) converges in 50-200 iterations for NCAA-scale datasets. Trivially fast.

**Recommendation for V0:** Use Dynamic Bradley-Terry instead of Elo. Same probability model, better handling of college baseball's unbalanced schedules, and it can be retrained daily as batch computation (not sequential updates).

### Hierarchical Structure

```
National:    μ_national ~ N(0, σ_national²)       # Overall D1 average = 0
Conference:  μ_conf ~ N(μ_national, σ_conf²)       # Conference strength varies
Team:        θ_team ~ N(μ_conf, σ_team²)           # Team strength within conference
Game:        y_game ~ N(θ_home - θ_away + HFA, σ_game²)

σ_national ≈ 0      (fixed at 0 by definition)
σ_conf ≈ 3.0        (from PEAR data: SEC avg 4.76 vs SWAC avg -5.28)
σ_team ≈ 2.0        (within-conference variation)
σ_game ≈ 4.5        (game-level noise)
HFA ≈ 0.5-0.8       (home field advantage in runs — needs calibration)
```

This hierarchy means: a new, unrated team in the SEC starts with a prior mean of ~4.76 (SEC average), while a new team in the SWAC starts at ~-5.28. The data updates from there.

**PyMC Implementation (adapted from Rugby Analytics canonical model):**

```python
import pymc as pm

with pm.Model(coords={"team": team_names, "conference": conf_names}) as model:
    # National hyperpriors
    mu_att_national = pm.Normal("mu_att_national", mu=0, sigma=1)
    sigma_att = pm.HalfStudentT("sigma_att", nu=3, sigma=1)

    # Conference-level attack/defense
    mu_att_conf = pm.Normal("mu_att_conf", mu=mu_att_national,
                            sigma=sigma_att, dims="conference")
    sigma_att_conf = pm.HalfStudentT("sigma_att_conf", nu=3, sigma=0.5,
                                      dims="conference")

    # Team-level (drawn from conference)
    att = pm.Normal("att", mu=mu_att_conf[conf_idx],
                    sigma=sigma_att_conf[conf_idx], dims="team")
    def_ = pm.Normal("def_", mu=0,
                     sigma=sigma_att_conf[conf_idx], dims="team")

    # Home advantage
    home = pm.Normal("home", mu=0.6, sigma=0.3)

    # Game noise
    sigma_game = pm.HalfStudentT("sigma_game", nu=5, sigma=3.0)

    # Likelihood: observed run margin
    mu_margin = home + att[home_idx] - def_[away_idx] \
                - att[away_idx] + def_[home_idx]
    pm.StudentT("margin_obs", nu=5, mu=mu_margin,
                sigma=sigma_game, observed=observed_margins)

    # Inference
    trace = pm.sample(2000, tune=1000, target_accept=0.9)
```

**Note:** This full Bayesian model is V1+ (requires PyMC/Stan). V0 uses the conjugate normal-normal approximation for speed. The hierarchical model here is the rigorous version that properly handles conference effects, which we approximate in V0 by manually setting conference-level priors.

### Transfer Portal Delta

**Research finding (from EvanMiya basketball):** EvanMiya estimates an "Expected Transfer Improvement" per program using Bayesian regression with shrinkage. Programs with few transfers are regressed toward the national average; programs with many transfers get data-driven estimates.

**For baseball (no player-level metrics in V0):** Approximate transfer delta as:
```
transfer_delta = Σ(departure_contribution) - Σ(arrival_contribution)

Where contribution is estimated from:
- Departure: player's share of team's fWAR (available in PEAR data)
- Arrival: prior from previous team's conference strength × minutes/starts

Prior adjustment:
σ₀_transfer = σ₀ × (1 + 0.5 × |net_transfers| / roster_size)
```

**Honest assessment:** V0 cannot compute transfer delta accurately without player-level tracking. The best we can do is widen the prior standard deviation for teams with high roster turnover. V1 (with player stats) enables proper transfer modeling.

### Home Field Advantage

**Research findings (multiple sources, 81,063 games analyzed):**

| Context | Home Win % | Source |
|---|---|---|
| MLB regular season | 54% | Historical |
| College baseball regular season | **57-59%** | Gettysburg study; Core.ac.uk |
| NCAA Regional host (individual games) | **~75%** | NCAA.com |
| NCAA Regional host advancement | **~70%** | NCAA.com |
| NCAA Super Regional host | **60.6%** | NCAA.com |
| Florida State specific | 74.5% home / 48.3% road | Program data |

**Model parameter derivation:**
```python
from scipy.stats import norm
# P(home win) = 0.58, sigma_game = 3.0 runs
home_adv_runs = 3.0 * norm.ppf(0.58)  # ≈ 0.60 runs
# Prior: home_adv ~ Normal(0.6, 0.3)
```

**Altitude:** No college-specific study found. MLB Coors Field proxy: +0.5-1.0 runs/game at >5,000 ft. Air Force (6,600 ft) and Wyoming (7,220 ft) are the highest college venues. Include altitude as a V2 feature.

---

## 3. Feature Engineering — What Actually Predicts College Baseball Outcomes

### Research Findings on Feature Importance

From logistic regression and XGBoost models applied to baseball prediction:

**Highest importance features (validated):**
1. **Pitching quality differential** (starter ERA/FIP difference) — consistently the #1 predictor
2. **wRC+ differential** (team offensive quality adjusted for league and park) — #2 predictor
3. **WHIP differential** (baserunners allowed) — top 5
4. **On-base percentage differential** — top 5
5. **Rest days** — significant for bullpen fatigue
6. **Home/away** — ~0.6 runs advantage

**Features specific to college that MLB models don't need:**
- Conference strength adjustment (SEC game ≠ SWAC game)
- Series position (game 1 vs game 3 of a weekend series — bullpen fatigue compounds)
- Mid-week vs weekend (starting pitcher quality differs dramatically)
- Non-conference vs conference games (motivational/competitive differences)
- Neutral site indicator (tournament games)

### V0 Feature Set (Minimal Viable)

| Feature | Source | Availability | Expected Importance |
|---|---|---|---|
| `power_diff` | PEAR data / computed | Now | High |
| `home_advantage` | Game location | Now | High |
| `sos_diff` | PEAR data / computed | Now | Medium |
| `elo_diff` | PEAR data / computed | Now | High |
| `conference_game` | Schedule data | Now | Low-Medium |
| `rest_days` | Inferred from schedule | Now | Medium |

### V1 Feature Set (Add Starting Pitcher)

| Feature | Source | Availability | Expected Importance |
|---|---|---|---|
| All V0 features | — | — | — |
| `starter_era_diff` | Box scores | Week 2+ | **Very High** |
| `starter_fip_diff` | Box scores + formula | Week 2+ | Very High |
| `starter_ip_season` | Box scores | Week 2+ | Medium (fatigue proxy) |
| `series_game_num` | Schedule | Week 1 | Medium (bullpen fatigue) |
| `mid_week` | Schedule | Week 1 | Low-Medium |
| `conference_strength` | Hierarchical model | Week 1 | Medium |

### V2+ Feature Set (Player-Level + Physics)

| Feature | Source | Availability | Expected Importance |
|---|---|---|---|
| `team_wrc_plus_diff` | PEAR data / computed | V2 | Very High |
| `team_fip_diff` | PEAR data / computed | V2 | Very High |
| `bullpen_era` | Box scores | V2 | High |
| `travel_distance` | Venue geocoding | V2 | Low |
| `temperature` | NOAA API | V2 | Low |
| `altitude` | Venue data | V2 | Low |
| `exit_velocity_avg` | 643 Charts | V3 | Medium |

---

## 4. What Makes This Non-Replicable? — Honest Assessment

### Layer-by-Layer Moat Analysis

| Component | Can a Grad Student Replicate? | Time to Replicate | Moat Rating |
|---|---|---|---|
| Pythagorean + SOS | Yes, with a spreadsheet | 2 hours | **NONE** |
| Elo with MOV adjustment | Yes, FiveThirtyEight formula is public | 4 hours | **NONE** |
| Logistic regression win prob | Yes, standard sklearn | 1 day | **WEAK** |
| Bayesian updating (conjugate) | Yes, the math is in any textbook | 2 days | **WEAK** |
| Hierarchical conference model | Harder — needs domain knowledge for priors | 1 week | **MODERATE** |
| Starting pitcher adjustment | 64 Analytics claims to have this | Unknown | **MODERATE** |
| Online learning / daily updates | Standard ML, but requires infrastructure | 2 weeks | **MODERATE** |
| Data quality pipeline (entity resolution, anomaly detection) | Engineering effort, not algorithmic novelty | 1-2 months | **MODERATE-STRONG** |
| Domain expert priors (Tim/Connor) | Requires equivalent domain experts | Not replicable | **STRONG** |
| Track record (accumulated predictions) | Requires same time period running | Not replicable | **STRONG** |
| Full RL/equation integration | Requires Mergim's equation + domain transfer | Months | **STRONG** |

### The Real Moat Stack

The moat is NOT any single component. It's the **stack**:

```
WEAK:   Pythagorean + Elo + logistic regression
        (anyone can build this in a weekend)
                    │
MODERATE: + Bayesian updating + hierarchical model + pitcher adjustment
          (requires ML knowledge + 2 weeks work)
                    │
STRONG:  + Domain expert priors + data quality pipeline + daily online learning
         (requires team composition + infrastructure + time)
                    │
VERY STRONG: + 6+ months of accumulated prediction track record
             (literally cannot be replicated without running for 6 months)
```

A competitor can replicate the bottom layers in days. They cannot replicate the top layers without equivalent domain experts AND equivalent running time. **The moat is temporal, not algorithmic.**

### Comparison with 64 Analytics

64 Analytics' model uses wRCE (weighted Run Created Efficiency) and wRAE (pitching equivalent) — college-specific adaptations of MLB's wRC+ and WAR. They claim play-by-play ingestion across all divisions.

**What 64 Analytics DOES have that we don't (V0):**
- Player-level metrics (wRCE, wRAE)
- Play-by-play data integration
- Transfer portal as primary feature
- 2+ years of historical data

**What 64 Analytics does NOT have:**
- Bayesian uncertainty quantification (they show point estimates only)
- Per-game starter adjustment (unconfirmed — their model may do this internally but it's not exposed)
- Online learning / model self-improvement (their metrics appear static within a season)
- Published prediction track record (they explicitly refused to do preseason rankings)
- API for external developers

**Honest differentiation summary:** At V0, our model is *simpler* than 64 Analytics on the player level but *more sophisticated* on the team level (Bayesian updating, uncertainty quantification, contextual win probabilities). Our real differentiation emerges at V1+ when the RL pipeline and pitcher adjustment layer go live.

---

## 5. V0 → V1 Algorithm Progression

### V0: Pythagorean + Bayesian + Logistic (12-18 hours)

**Model specification:**

```
Step 1: Pythagorean Win Expectation
  W%_pythag = RS^exp / (RS^exp + RA^exp)

  Calibrate exp from 2024-2025 data:
  exp* = argmin Σ(W%_actual - RS^e/(RS^e + RA^e))²
  Expected result: exp ≈ 1.80-1.88 for college baseball

  Alternative (Pythagenpat): exp = ((RS+RA)/G)^0.287
  → Use Pythagenpat for teams with extreme run environments

Step 2: Iterative SOS (10 iterations)
  Initialize all teams at θ=0
  For each iteration:
    For each team:
      θ_team = mean(game_margins adjusted for opponent θ values)
  SOS_team = mean(θ_opponents)

Step 3: Elo with Margin-of-Victory Adjustment
  FiveThirtyEight MLB formula (adapted):

  K = 20 × (MOV + 3)^0.8 / (7.5 + 0.006 × |elo_diff|)

  Expected score: E_A = 1 / (1 + 10^((R_B - R_A)/400))
  Update: R_A_new = R_A + K × (S_A - E_A)

  Where S_A = 1 (win), 0 (loss), 0.5 (tie/suspended)

  Season regression: R_preseason = 0.67 × R_end + 0.33 × 1500

Step 4: Bayesian Prior-Posterior Rating
  Prior: θ ~ N(power_rating_2025, σ₀²)
  σ₀ = 2.5 for returner-heavy teams, 3.5 for high-transfer teams

  Update with each game:
  μ_new = (τ₀μ₀ + τΣy) / (τ₀ + nτ)
  σ_new = 1/√(τ₀ + nτ)

Step 5: Logistic Win Probability
  P(home_wins) = σ(β₀ + β₁·power_diff + β₂·home + β₃·sos_diff + β₄·elo_diff)

  Where σ(x) = 1/(1+e^(-x))

  Train on 2023-2025 NCAA game outcomes (~25,000 games)
  Regularization: L2 with λ = 0.01
```

**Expected accuracy:** 57-60% on held-out game predictions (above ~53% naive baseline).
**Expected Brier score:** 0.235-0.242 (vs 0.250 baseline).

### V0.5: Add Starting Pitcher + Series Context (Week 1-2 of predictions)

```
New features:
  starter_adj = (league_avg_ERA - blended_starter_ERA) / 9.0
  blended_starter_ERA = w × observed_ERA + (1-w) × conference_avg_ERA
  w = min(starts / 15, 1.0)   # Full weight at 15 starts

  series_game = {1, 2, 3}     # Position within weekend series
  bullpen_fatigue = IP_last_3_days / 9.0  # Simple fatigue proxy

Updated logistic:
  P(home_wins) = σ(β₀ + β₁·power_diff + β₂·home + β₃·sos_diff
                   + β₄·elo_diff + β₅·starter_adj_diff
                   + β₆·series_game + β₇·bullpen_fatigue)
```

**Expected accuracy improvement:** +2-4% from starting pitcher alone (the single largest feature addition).

### V1: Full Model with Online Learning + Conference Hierarchy (Month 1-2)

```
New components:
  1. Hierarchical conference model (Stan/PyMC)
  2. Online learning: after each day's results, update weights via SGD:
     β_new = β_old - η × ∇L(β_old; today's games)
     η = adaptive learning rate (Adam optimizer)
  3. Temporal feature weighting: feature importance changes through season
  4. Calibration layer: Platt scaling on validation set
```

**Expected accuracy improvement:** +1-2% from online learning, +1% from hierarchy.

### V1.5: Monte Carlo Game Simulation (Month 2-3)

```
For each matchup:
  For i in 1..10000:
    home_runs ~ NegBinomial(adj_RS × pitcher_factor, overdispersion)
    away_runs ~ NegBinomial(adj_RS × pitcher_factor, overdispersion)
    if tied: extra_innings ~ Geometric(p_score_per_inning)

  Returns: win_prob, run_total_dist, spread_coverage, over/under %
```

### V2: Player-Level + Transfer Portal (Month 3-6)

Player wRC+, FIP, individual WAR contributions. Transfer projection model using Bayesian regression with conference adjustment.

### Expected Accuracy by Stage

| Stage | Accuracy vs Baseline | Brier Score | Key Addition |
|---|---|---|---|
| Baseline (home team wins) | 53% | 0.250 | — |
| V0 (Pythag + logistic) | 57-60% | 0.235-0.242 | Bayesian uncertainty |
| V0.5 (+ pitcher) | 60-63% | 0.225-0.232 | **Largest single jump** |
| V1 (+ online + hierarchy) | 62-65% | 0.218-0.225 | Online adaptation |
| V1.5 (+ Monte Carlo) | Same accuracy, better calibration | 0.215-0.222 | Distribution outputs |
| V2 (+ player-level) | 64-67% | 0.210-0.220 | Player WAR features |

---

## 6. Concrete Mathematical Specification (V0)

### Pythagorean Win Expectation

```
W%_pythag(RS, RA, exp) = RS^exp / (RS^exp + RA^exp)

For Pythagenpat (recommended for college — adapts to run environment):
exp(RS, RA, G) = ((RS + RA) / G)^0.287

Log-likelihood for exponent calibration:
ℓ(exp) = Σᵢ [wᵢ log(W%_pythag(RSᵢ, RAᵢ, exp)) + (1-wᵢ) log(1 - W%_pythag(RSᵢ, RAᵢ, exp))]

Where wᵢ = wins_i / (wins_i + losses_i)
Maximize via scipy.optimize.minimize_scalar(bounds=(1.5, 2.2))
```

### Elo Rating System (FiveThirtyEight Exact Formula)

```
Initial rating: R₀ = 1500 (all teams start equal)
Seasonal regression: R_pre = R_end + (1500 - R_end) / 3
  Example: Team finishes at 1560 → preseason = 1540

Home field adjustment: +24 Elo points to home team pre-game
  (FiveThirtyEight used 9.6 during COVID no-fans era)

Expected outcome:
E_A = 1 / (1 + 10^((R_B - R_A) / 400))

Margin-of-Victory Multiplier (exact reverse-engineered formula):
MoVM = LN(|run_diff| + 1) × (2.2 / ((Elo_winner - Elo_loser) × 0.001 + 2.2))

The second factor is the autocorrelation adjustment:
- Shrinks MoVM when the favorite wins big (prevents inflation)
- Keeps it large when the underdog wins big (rewards upsets)

Numerical examples:
  1-run win, teams equal:  LN(2) × 1.0 = 0.693
  5-run win, teams equal:  LN(6) × 1.0 = 1.792
  10-run win, equal:       LN(11) × 1.0 = 2.398
  10-run win, +200 Elo:    LN(11) × (2.2/2.4) = 2.198 (dampened)

Update:
ΔElo = K × MoVM × (S_A - E_A)
R_A_new = R_A + ΔElo
R_B_new = R_B - ΔElo  [zero-sum]

FiveThirtyEight MLB K ≈ 4 (regular) / 6 (postseason)
For college (more variance): K ≈ 8-12 (needs calibration)

Simpler alternative (Andrew321): MoVM = run_diff^(1/3)
  1-run = 1.0, 5-run = 1.71, 10-run = 2.15
```

### UPGRADE: Dynamic Bradley-Terry (V0.5+)

The research strongly suggests replacing Elo with Dynamic BT for college baseball:
```
P(i beats j) = π_i / (π_i + π_j)

Fit by maximizing weighted log-likelihood:
  ℓ(π) = Σ w_t × [y_t log(π_home/(π_home+π_away)) + (1-y_t) log(π_away/(π_home+π_away))]

Where w_t = exp(-λ(T-t)), λ ≈ 0.02 (half-life ~35 days)

MM algorithm update (Hunter 2004):
  π_i^(new) = W_i / Σ_{j≠i} (n_ij / (π_i^(old) + π_j^(old)))

Converges in 50-200 iterations. Retrain daily as batch.
```

BT > Elo for college because it solves the full schedule graph simultaneously, propagating transitive strength through indirect opponents.

### Bayesian Prior-Posterior Update

```
Notation:
θ = true team strength (latent, in run-differential units)
μ₀ = prior mean (from last season or conference average)
σ₀ = prior standard deviation
y = observed game margin (RS - RA, adjusted for opponent)
σ_y = observation noise (~4.5 runs for college baseball)

Prior:      θ ~ N(μ₀, σ₀²)
Likelihood: y | θ ~ N(θ, σ_y²)

Posterior after observing n game margins y₁, ..., yₙ:

Precision form:
  τ_post = 1/σ₀² + n/σ_y²
  μ_post = (μ₀/σ₀² + Σyᵢ/σ_y²) / τ_post
  σ_post = 1/√τ_post

Weighted average form:
  w = (n/σ_y²) / (1/σ₀² + n/σ_y²)
  μ_post = w × ȳ + (1-w) × μ₀

  After 5 games:  w ≈ 0.38  (38% data, 62% prior)
  After 15 games: w ≈ 0.60  (60% data, 40% prior)
  After 30 games: w ≈ 0.75  (75% data, 25% prior)
  After 56 games: w ≈ 0.86  (86% data, 14% prior)

95% credible interval for rating:
  [μ_post - 1.96σ_post, μ_post + 1.96σ_post]
```

### Logistic Regression Win Probability

```
P(home_wins | x) = σ(x^T β)

Where σ(z) = 1 / (1 + exp(-z))

Feature vector x:
  x₁ = power_diff (home - away adjusted power rating)
  x₂ = 1 (home indicator; 0 for neutral site)
  x₃ = sos_diff (SOS differential)
  x₄ = elo_diff / 400 (normalized Elo gap)
  x₅ = rest_diff (home rest days - away rest days)

Loss function (negative log-likelihood):
  L(β) = -Σᵢ [yᵢ log σ(xᵢ^T β) + (1-yᵢ) log(1 - σ(xᵢ^T β))] + λ||β||₂²

Solve: β* = argmin L(β)   [via scipy.optimize.minimize or sklearn]

Training data: 2023-2025 NCAA D1 results (~25,000 games)
Validation: 5-fold cross-validation, stratified by season
```

### Matchup Prediction (Combining All Layers)

```
For game: Home team A vs Away team B

1. Compute feature vector x from current ratings
2. Base probability: p_base = σ(x^T β)  [logistic model]
3. Bayesian adjustment:
   p_bayesian = Φ((μ_A - μ_B + HFA) / √(σ_A² + σ_B² + σ_game²))
   Where Φ is the standard normal CDF
4. Final probability: p_final = 0.5 × p_base + 0.5 × p_bayesian
   [equal blend; tune weights on validation data]
5. Uncertainty:
   σ_pred = √(σ_A² + σ_B²)
   CI_95 for p_final: bootstrap or delta method
```

---

## 7. Backtest Design

### Data Split

```
Training:   2023-2024 NCAA D1 seasons (~16,800 games)
Validation: First half of 2025 season (~4,200 games)
Test:       Second half of 2025 + 2026 season-to-date
```

### Walk-Forward Protocol

```
For each game day d in test period:
  1. Model has seen all games before day d
  2. Predict outcomes for day d's games
  3. Record predictions
  4. After day d completes, update model with actual results
  5. Move to day d+1

This prevents look-ahead bias and simulates real-time operation.
```

### Metrics

| Metric | Formula | Baseline | Target |
|---|---|---|---|
| **Accuracy** | correct / total | 53% (home team) | >57% |
| **Brier Score** | (1/n) Σ(p_i - o_i)² | 0.250 (coin flip) | <0.240 |
| **Log Loss** | -(1/n) Σ[o_i log(p_i) + (1-o_i) log(1-p_i)] | 0.693 (coin flip) | <0.670 |
| **Calibration** | Plot predicted vs observed in decile bins | — | Calibration slope ≈ 1.0 |
| **PEAR comparison** | Rank correlation with PEAR | — | Spearman ρ > 0.90 |

### Statistical Significance

For a 5% accuracy improvement (53% → 58%) to be significant at p<0.05 using McNemar's test:

```
Required sample size ≈ (z_α/2)² × p(1-p) / δ²
                     ≈ (1.96)² × 0.55 × 0.45 / (0.05)²
                     ≈ 380 games

With ~4,200 games per half-season, we have >10x the required sample.
5% improvement is detectable with high power (>0.99).
Even 2% improvement (53% → 55%) requires ~2,400 games — still feasible.
```

### Baseline Comparisons

| Baseline | Method | Expected Accuracy |
|---|---|---|
| Random | 50% | 50% |
| Home team always wins | — | ~58% |
| Higher PEAR ranking wins | PEAR NET rank | ~55-58% |
| Simple Elo | FiveThirtyEight formula | ~56-59% |
| Our V0 | Bayesian + logistic + Elo | 57-60% |
| Our V0.5 | + starting pitcher | 60-63% |

---

## Summary: Is the Differentiation Real or Hand-Waving?

| Claim | Verdict | Evidence |
|---|---|---|
| "Our model is Bayesian" | **REAL but not unique** | Conjugate updates are standard. But PEAR/64 don't use them. |
| "We quantify uncertainty" | **REAL and differentiated** | Nobody in college baseball shows credible intervals on rankings. |
| "We adjust per game, not per series" | **REAL and immediately demonstrable** | PEAR confirmed to use identical probs for all games in a series. |
| "We have RL self-learning" | **OVERSTATED** | Better described as "online logistic regression with adaptive weights." Real but not exotic. |
| "Our equation from finance transfers" | **PARTIALLY REAL** | Framework transfers (probabilistic, online, Kelly). Weights don't transfer — must be learned from baseball data. |
| "Nobody can replicate our model" | **FALSE as stated** | Any ML engineer can replicate the algorithm. The moat is domain knowledge + track record + time, not the algorithm itself. |
| "Starting pitcher adjustment is unique" | **REAL for now** | PEAR doesn't do it (confirmed). 64 Analytics may do it internally (unconfirmed). Building it first in a transparent model is differentiation. |
| "Data quality pipeline is the moat" | **STRONGEST TRUE CLAIM** | Entity resolution + anomaly detection + daily automation is genuine engineering moat. 1-2 months to replicate. |
| "Prediction track record is the moat" | **STRONGEST LONG-TERM CLAIM** | 6 months of verifiable daily predictions cannot be replicated without 6 months of operation. |

### The Honest Pitch to Ryan

"Our V0 model uses standard statistical methods — Pythagorean expectation, Elo ratings, Bayesian updating, logistic regression — assembled in a way that nobody in college baseball has done. The methods aren't novel; the assembly is. Our real differentiation comes in three layers:

1. **Per-game prediction where competitors give per-series** (confirmed PEAR weakness)
2. **Uncertainty quantification where competitors give point estimates** (our Bayesian layer)
3. **A verifiable prediction track record that competitors can't replicate without time** (our temporal moat)

The algorithm isn't a magic black box. It's a disciplined combination of proven methods applied to a domain where nobody else has bothered. That's exactly how KenPom won — not with novel math, but with rigorous execution in an uncontested space."
