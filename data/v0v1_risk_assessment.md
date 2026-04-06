# V0/V1 Risk Assessment & Failure Mode Analysis

**Date:** 2026-03-31 | **Analyst:** Sentinel Orange Team
**Sources:** Architecture spec, V0 ranking, existing OT analysis, full research doc, external research (Pythagorean accuracy, NCAA scraping, business model data)
**Classification:** Internal — pre-decisional

---

## Risk Register (Sorted by Risk Score)

| # | Risk | L | I | Score | Category |
|---|------|---|---|-------|----------|
| 1 | The "FSBB 58.2%" accuracy claim is fabricated — exceeds the theoretical ceiling for college baseball | 5 | 5 | **25** | Algorithm |
| 2 | The Pythagorean exponent 1.83 is wrong for college baseball — should be ~1.60-1.72 | 5 | 4 | **20** | Algorithm |
| 3 | NCAA ToS explicitly prohibits commercial scraping — legal exposure | 4 | 5 | **20** | Data/Legal |
| 4 | Pythagorean W% is near-useless after 10 games — model produces garbage for 18% of the season | 5 | 3 | **15** | Algorithm |
| 5 | RL/online learning won't converge within a 56-game season | 5 | 3 | **15** | Algorithm |
| 6 | D1 college baseball data is too thin for reliable win probability models (SABR published) | 4 | 4 | **16** | Algorithm |
| 7 | No validation baseline exists — zero published papers on D1 baseball prediction | 4 | 3 | **12** | Algorithm |
| 8 | The 12-18 hour V0 build estimate is unrealistic when Pythagorean exponent must be calibrated from scratch | 4 | 3 | **12** | Execution |
| 9 | NCAA site JS migration broke all existing scrapers — chromote dependency required | 4 | 3 | **12** | Data |
| 10 | V1 scope creep: V0 is 12-18h but V1 is 100+ hours — cliff between prototyping and production | 4 | 3 | **12** | Execution |
| 11 | 643 Charts API is enterprise-priced, not free — the "physics data layer" roadmap collapses | 4 | 3 | **12** | Data |
| 12 | Bayesian prior failure: new programs, massive roster turnover, transfers between talent tiers | 3 | 4 | **12** | Algorithm |
| 13 | KenPom took 9 years to go from free to paid — revenue timeline is decade-long | 3 | 4 | **12** | Market |
| 14 | College baseball betting handle is ~$150-450M (estimate) — too small for betting-as-revenue | 3 | 4 | **12** | Market |
| 15 | Missing data biases ratings toward strong teams (weak teams have worse data coverage) | 4 | 2 | **8** | Data |
| 16 | 64 Analytics expanding to "live rankings" — closing the gap from a 2-year head start | 3 | 3 | **9** | Competitive |
| 17 | PEAR still free, no signs of paywall — our "paid" product competes with free | 3 | 3 | **9** | Competitive |
| 18 | Ryan's 53 action items are 50%+ polite deferrals (from prosodic analysis) | 5 | 2 | **10** | Partnership |

---

## Top 10 Risks — Full Mitigation Plans

### RISK 1: The 58.2% Accuracy Claim Is Fabricated (Score: 25)

**What the spec says:**
> "Win prediction accuracy: FSBB 58.2% | PEAR ~53%*"
> "* estimated from PEAR's static probabilities"

**What the research says:**

The hard ceiling on game-by-game baseball prediction accuracy at ANY level is **57-59.5%**:
- Vegas betting markets (the best empirical benchmark): 58.2% accuracy (Cui, Wharton 2020)
- FiveThirtyEight Elo (2016-2018): 57.7%
- FanGraphs: 56.9%

These are **MLB** figures with:
- 162-game seasons (3x more data per team)
- 150+ years of historical data
- Statcast pitch-level tracking
- Billions of dollars of incentive to optimize

**College baseball ceiling is lower than MLB** due to:
- Greater game-to-game variance (wider talent spread)
- 56-game seasons (less data per team for calibration)
- Inconsistent data quality
- No pitch-tracking data in the model
- No published baseline to validate against

**The damning finding:** The spec claims 58.2% accuracy for a model that hasn't been built, using data that hasn't been collected, for a sport where no published model exists — and that number happens to match the Vegas MLB benchmark exactly. This is not a coincidence. Someone (likely Claude during architecture generation) pulled the MLB ceiling and presented it as an achievable college baseball target.

**If Ryan asks "how did you get 58.2%?" we have no answer.** For a PE professional, presenting a fabricated number in a spec is a credibility-destroying event.

**PEAR's "~53%" is also fabricated.** PEAR doesn't publish prediction accuracy numbers. The asterisk says "estimated from static probabilities" but no estimation methodology is described. This makes our comparison ("we're 5% better!") doubly fictional.

**Mitigation:**
1. **Immediately remove 58.2% from all specs.** Replace with: "Target: measurably outperform PEAR's static rankings on game-outcome prediction. MLB ceiling is ~58%; college ceiling is unknown and likely lower. Our initial goal is >54% accuracy."
2. **Build the backtest first, then state the number.** Run the model on 2024-2025 data. Report the ACTUAL accuracy. If it's 53%, that's honest and still potentially better than PEAR.
3. **Add the disclaimer Ryan actually wants:** "This will always be somewhat more imperfect" (his own words). Honest framing builds PE trust. Fabricated precision destroys it.
4. **Never present Claude-generated numbers as empirical results.** The spec was generated from call analysis + Claude reasoning, not from running code against data. Label all unbuilt projections as "PROJECTED — NOT VALIDATED."

**Fallback:** If actual accuracy is 53-54% (plausible), that still demonstrates the concept but requires reframing. The differentiation story becomes "our model quantifies uncertainty (CIs) and is matchup-aware" rather than "our model is 5% more accurate."

---

### RISK 2: Pythagorean Exponent 1.83 Is Wrong (Score: 20)

**What the spec says:**
> "exp ≈ 1.83 for college" and "The exponent 1.83 is commonly cited for college baseball"

**What the research says:**

1.83 is the **MLB** exponent derived from 1901-2002 MLB data. It is NOT published as a college baseball exponent anywhere in the literature.

The correct framework is Davenport's Pythagenport formula:
```
Exponent = 1.50 × log10(RPG) + 0.45
```

Applied to college baseball scoring environments:

| D1 Era | Runs Per Game | Correct Exponent |
|--------|:---:|:---:|
| Pre-BBCOR peak (~1998) | 7.1 | ~1.72 |
| Post-BBCOR trough (2013) | 5.3 | ~1.54 |
| Post-flat-seam ball (2018+) | 6.5-7.0 | ~1.65-1.72 |

**Using 1.83 overestimates the exponent by 6-18%** depending on the scoring environment. This means:
- Win percentage estimates for extreme teams (very good or very bad) will be biased
- Teams with high run differentials will have inflated Pythagorean W%
- The model's "luck" metric (actual W% minus Pythagorean W%) will be systematically wrong
- Every metric that depends on the exponent (power rating, SOS-adjusted stats) inherits the error

**Why this matters for the V0:** The spec explicitly builds Layer 1 on Pythagorean W% with exponent 1.83. If the exponent is wrong, Layer 1 is wrong, which means Layers 2 and 3 (which build on Layer 1) are also wrong. The entire 3-layer architecture has a bad foundation.

**Mitigation:**
1. **Do NOT hardcode 1.83.** The spec already includes the exponent calibration code (scipy minimize_scalar) — this is correct. But the calibration MUST be run on actual college data before any ratings are produced.
2. **Calculate current-season RPG first** (easy: sum all runs from scraped games, divide by games). Use Davenport's formula for the initial estimate, then refine with least-squares optimization.
3. **Expect the exponent to be ~1.60-1.72** for the 2026 season. If the optimization returns 1.83, something is wrong with the data.
4. **Add exponent to the output JSON** so Ryan (and anyone else) can see what value the model is using. Transparency builds trust.

**Fallback:** Even with the wrong exponent, rankings will be approximately correct (the error affects extremes more than middle-of-the-pack teams). But "approximately correct" is not "better than PEAR" — it's "a different flavor of the same noise." The exponent calibration is a prerequisite for claiming any accuracy advantage.

---

### RISK 3: NCAA ToS Prohibits Commercial Scraping (Score: 20)

**What the spec assumes:** NCAA box score data is freely scrapable at scale for a commercial product.

**What the research found:**

NCAA.org Terms of Service explicitly prohibit:
- "unauthorized robots, spiders, offline readers, or like devices, scraping, or harvesting of content or information"
- "distribute, reproduce, republish, display, modify... use any materials... for public or commercial purposes... without the written permission of the NCAA"

NCAA.com ToS adds: Prohibits "transfer or sale" or "using for commercial purposes" of NCAA content. Defines "Commercial Sites" broadly as any site regularly promoting a product/brand/service.

**No C&D letters have been publicly documented** against scrapers, likely because existing scrapers (PEAR, 64 Analytics, academic projects) have been small-scale or non-commercial. A visible commercial product that monetizes NCAA stats would face a meaningfully different risk profile.

**The specific threat:** If we launch a paid subscription product built entirely on scraped NCAA data, and the product gets enough visibility for the NCAA to notice (success is the trigger, not the scraping itself), we face:
1. Cease-and-desist letter requiring product shutdown
2. Potential damages claim for commercial use of copyrighted data
3. Permanent loss of the data source with no alternative

**Mitigation:**
1. **Consult a sports data IP attorney** before launching any paid product. 2-hour consultation costs ~$500 and could save the entire project.
2. **Research data licensing alternatives.** The NCAA sells official data through partners (e.g., NCAA Licensing, Sports Reference). What does a license cost? Is there a startup tier?
3. **Use the "facts not expression" defense** — in the US, factual data (scores, stats) is generally not copyrightable (per Feist Publications v. Rural Telephone). The NCAA's ToS is a contract restriction, not a copyright claim. This defense may hold but hasn't been tested for NCAA sports data specifically.
4. **Build the pipeline to work from multiple sources** so that if NCAA direct scraping is blocked, you can fall back to: (a) game scores from news sources (AP, ESPN), (b) box scores from team athletic websites (sidearm stats), (c) third-party aggregators.
5. **Keep V0 non-commercial.** A free research tool that scrapes NCAA data is in a much safer legal position than a paid subscription product. Go from free → paid only after legal review.

**Fallback:** If NCAA data is legally blocked for commercial use, the product must be either (a) free forever, (b) built on licensed data (cost unknown, likely $10K+/year), or (c) built on data sourced from non-NCAA origins (team websites, news APIs). Option (c) is possible but dramatically increases scraping complexity.

---

### RISK 4: Pythagorean W% Is Useless After 10 Games (Score: 15)

**What the spec implies:** The model produces useful predictions from the start of the season.

**What the research says:**
- Sabermetric research shows run differential doesn't reliably outperform raw W-L until ~45-50 games in MLB
- At 10 games (18% of a 56-game college season), Pythagorean W% is dominated by variance from individual series outcomes — it's "largely noise"
- Implied R-squared at 10 games: well below 0.20 against end-of-season record
- College seasons add MORE noise than MLB: heterogeneous opponent quality, weekend-series format, weather

**What this means for the V0:**
The "Nightly Prediction Page" launches at some point during the 2026 season (which is already underway — ~28 games played per team). Teams with 28 games already have reasonable Pythagorean estimates. But:
- At the START of any future season, the model will produce garbage for the first ~20 games
- Early-season predictions will be LESS accurate than simply picking the home team (home advantage is ~54% in college baseball)
- 64 Analytics explicitly acknowledged this: "we're not even going to do a preseason ranking because we just don't know"

**The V0-1 "holy shit" scenario is optimistic:**
> "The model went 18/25 (72%) on game winners."

72% is almost certainly impossible for baseball at any level. The MLB ceiling is 58-59%. Getting 18/25 correct in a single week is well within random variance for a 55% model — it happens about 8% of the time. Cherry-picking one good week would be dishonest. A bad week (12/25) is equally likely.

**Mitigation:**
1. **Start the V0 NOW, mid-season, where there's enough data.** 28 games per team is just above the noise threshold. This is actually an advantage — we have enough 2026 data to produce meaningful ratings immediately.
2. **Do NOT launch at the start of the 2027 season without clear warnings.** Preseason predictions should be labeled "LOW CONFIDENCE — based on prior-season data and transfer portal adjustments, not current-season results."
3. **Rewrite the "holy shit" scenario honestly:** "After one week: the model correctly predicted the winner in 15/25 games (60%). PEAR's static rankings implied the same result in 13/25 games (52%). Our model shows a 8-percentage-point edge, consistent with MLB benchmarks." This is honest and still compelling.
4. **Use the Bayesian framework (Layer 2) to properly express uncertainty.** Wide confidence intervals early, narrow ones late. This is actually a selling point: "We tell you how confident we are, PEAR doesn't."

**Fallback:** If early-season predictions are demonstrably bad, frame the product as a "mid-season and tournament predictor" rather than a full-season tool. Tournament prediction (the 64-team bracket) is where accuracy matters most for fans and bettors, and by tournament time (late May) there's enough data.

---

### RISK 5: RL Won't Converge Within a 56-Game Season (Score: 15)

**What the spec claims:**
> "We can go even further with a self-learning model" (V1 differentiation)
> The RL Agent appears in the architecture diagram as a V1+ component

**What the research says:**
- FiveThirtyEight's Elo (effectively an online algorithm) requires ~10+ seasons before team ratings stabilize
- Baseball ML models show learning curves that plateau after 3-5 seasons of training data (Cui, Wharton 2020)
- RL convergence bounds "are expected to be rather loose" and don't translate to game counts
- A single 56-game college season is "almost certainly insufficient for any online algorithm to converge"
- Pre-training on multi-season historical data is essential, and the algorithm will be in high-uncertainty state for the first 20-30 games of any new season

**The specific failure mode:**
The architecture spec shows: `Rating Engine → AlphaModel → RL Agent → Betting Signal` with the RL Agent learning from game results and market feedback. In a 56-game season with ~300 teams:
- The RL agent sees each team ~56 times
- Each unique matchup occurs 3-4 times at most (weekend series)
- There are ~46,000 unique team-pair combinations but only ~8,400 games
- The reward signal (game outcome) is binary and noisy
- The agent would need to generalize from 8,400 data points to 46,000 matchup predictions

This is a fundamentally under-determined problem for within-season RL. The agent will either:
1. Overfit to early-season results (and get worse as the season progresses)
2. Learn nothing useful within the season (converging only on trivially obvious patterns like "the #1 team beats the #300 team")
3. Require so much pre-training that the "self-learning" framing is misleading — it's really "pre-trained model with minor within-season updates"

**Mitigation:**
1. **Drop "self-learning" from the V0-V1 pitch.** It's a V3+ feature that requires multi-season data to be meaningful.
2. **Use Bayesian updating instead of RL for within-season learning.** Bayesian updating IS a form of "learning from data" but it's well-understood, converges faster with small samples, and doesn't require the ML hype.
3. **Pre-train on 3+ seasons of historical data** (2023-2025). The "learning" happens in the pre-training; within-season updates are incremental Bayesian adjustments, not RL episodes.
4. **If Ryan asks about RL:** "We started with Bayesian updating because it handles small samples better. RL is the V3 play when we have 3+ seasons of our own prediction data to train on."

**Fallback:** The Bayesian approach (Layer 2) is the actual technical differentiator. RL is aspirational. Reframe all architecture docs to lead with Bayesian and mention RL only as a long-term research direction.

---

### RISK 6: D1 Data Too Thin for Win Probability (Score: 16)

**What the spec claims:** Layer 3 produces "calibrated probabilities" like "Texas 62.3% vs UCLA."

**What published research says:**

SABR's analysis of D1 college baseball data (Adam Maloof) found:
- D1 baseball produces approximately **100 instances per base-out-inning-run-differential game state** vs. **3,800-4,600 instances** in the full 1903-2024 MLB Retrosheet data — a **40x gap**
- The run distribution may be bimodal (not normal), complicating standard probability models
- Standard deviation of runs is 7.7 in college (higher than MLB)
- Conclusion: "D1 baseball datasets are currently too thin for statistically reliable win probability or run expectancy models"

**What this means for the V0:**
- The logistic regression win probability model (Layer 3) is trained on 3 seasons of NCAA data = ~25,200 games
- But many features (SOS, conference strength, Elo differences) are correlated, reducing effective sample size
- The model will produce numbers ("62.3%") but the confidence intervals on those numbers will be wide
- Calibration (does 62% confidence = 62% actual win rate?) requires large samples per probability bucket — we may not have enough games per bucket to verify calibration

**Mitigation:**
1. **Always show confidence intervals on win probabilities.** "Texas 55-69% vs UCLA" is honest. "Texas 62.3%" implies false precision.
2. **Start with a simpler model.** Logistic regression with 3-4 features (power difference, home advantage, SOS difference) rather than the 10+ features in the spec. More features need more data to avoid overfitting.
3. **Validate calibration explicitly.** After running backtests, group predictions into deciles (50-55%, 55-60%, etc.) and check: do teams predicted to win 55% actually win 55% of the time? If the calibration plot is noisy, the model is overfit.
4. **Use the SABR finding as a selling point:** "Nobody else has even tried to build a calibrated win probability model for college baseball. The data is thin, which is why we use Bayesian methods to properly express uncertainty. PEAR doesn't even attempt this."

**Fallback:** If win probabilities are poorly calibrated, drop Layer 3 from the V0 and lead with Layer 1 + 2 (rankings with uncertainty). Rankings don't require calibrated probabilities — they only need to order teams correctly.

---

### RISK 7: No Validation Baseline Exists (Score: 12)

**What the spec assumes:** We can compare "FSBB 58.2% | PEAR ~53%"

**What the research found:** Zero peer-reviewed papers on D1 college baseball game prediction were published 2024-2026. The arXiv literature is entirely NCAA basketball and MLB. No published model provides a baseline accuracy to compare against.

**This means:**
- We can't say "our model is X% better than the state of the art" because there is no published state of the art
- PEAR doesn't publish accuracy metrics. 64 Analytics doesn't publish accuracy metrics. There is no benchmark.
- Any accuracy claim we make is unverifiable by external parties
- An investor or partner asking "how does this compare to published research?" gets the answer "there is no published research" — which sounds like an excuse

**Mitigation:**
1. **Create our own benchmark:** Scrape PEAR's current rankings, derive naive predictions (higher-ranked team wins), and track accuracy. This becomes the "PEAR baseline" we compare against.
2. **Create a Vegas benchmark:** DraftKings, FanDuel, and BetMGM all offer college baseball lines. Scrape closing lines, derive implied probabilities, track accuracy. This is the gold standard.
3. **Publish our methodology and accuracy openly.** If nobody else is doing this, being the first to publish creates the benchmark. That's a competitive advantage (credibility moat), not a weakness.
4. **Frame the absence of research as opportunity:** "College baseball prediction is a white space in the literature. We're building the first rigorous, published model."

---

### RISK 8: The 12-18 Hour Build Estimate Is Unrealistic (Score: 12)

**What the spec says:** V0-1 "Nightly Prediction Page" build time: 12-18 hours.

**Hour-by-hour breakdown and reality check:**

| Spec Estimate | Task | Actual Risk |
|:---:|-----------|-------------|
| 0-4h | Project setup, schemas, SQLite, alias table | **Realistic.** Boilerplate. |
| 4-12h | NCAA scraper via henrygd/ncaa-api | **HIGH RISK.** The NCAA site migrated to JS rendering. The unofficial API may not return box scores. baseballr's scraper was deprecated because of this. Need to verify the API actually returns what we need BEFORE counting this as 8 hours. If it doesn't, add 16-24h for playwright-based scraping. |
| 12-14h | PEAR import | **Realistic.** JSON already scraped. |
| 14-18h | Cleaning pipeline | **MODERATE RISK.** Entity resolution for 308 team names is straightforward. But anomaly detection and deduplication require understanding the data format, which depends on the scraper working (Risk 8.1). |
| 18-24h | Layer 1: Pythagorean, SOS, Elo | **HIGH RISK.** The Pythagorean exponent must be calibrated from historical data (Risk 2). This requires HAVING 3 seasons of historical data — which hasn't been scraped yet. If historical scraping is needed, add 4-8 hours. SOS requires iterative convergence (5-10 iterations) — straightforward in code but requires testing. |
| 24-30h | Layer 2: Bayesian prior-posterior | **MODERATE RISK.** Conjugate normal-normal is mathematically simple. But setting priors requires last season's data (again, historical scraping dependency). Transfer delta estimation is hand-waved in the spec ("net talent gain/loss from portal") — how exactly? |
| 30-36h | Layer 3: Logistic win probability | **MODERATE RISK.** Logistic regression is simple. But training requires labeled data (historical game outcomes + features) which depends on having the historical pipeline working. |
| 36-42h | CLI | **Realistic.** Click CLI is boilerplate. |
| 42-48h | PEAR validation, backtest, tuning | **HIGH RISK.** This is where you discover the exponent is wrong, the SOS isn't converging, the win probabilities aren't calibrated. "Tuning" is an open-ended task that can absorb unlimited hours. |

**Critical path dependency:** Everything from hour 18 onward depends on the NCAA scraper working AND historical data being available. If the scraper breaks on the JS-rendered site, the entire timeline collapses.

**Realistic estimate:** 30-50 hours for V0-1, not 12-18. The 12-18 hour estimate assumes:
- The NCAA API works as documented (untested)
- Historical data is available without additional scraping (unverified)
- The Pythagorean exponent is known (it's not)
- Win probability calibration takes zero iteration (it won't)

**Mitigation:**
1. **Test the NCAA API in hour 1, not hour 4.** Before setting up project infrastructure, run a single API call: `GET /games?team=UCLA&season=2026`. If it returns box scores with runs/hits/errors, proceed. If it doesn't, stop and assess alternatives before investing further.
2. **Separate historical scraping from current-season scraping.** Historical data (2023-2025) is a one-time batch job that can run overnight. Current-season data is incremental. Don't block V0 on historical data — use PEAR's existing ratings as the Layer 1 proxy and build Layer 2-3 on top.
3. **Build V0-1 in phases, not sequentially:**
   - Phase A (4h): Scrape current PEAR + today's schedule + today's results. Output: a page with predictions for tomorrow's games using PEAR power ratings + home advantage.
   - Phase B (8h): Add Pythagorean from this season's box scores. Output: FSBB power rating alongside PEAR.
   - Phase C (8h): Add Bayesian uncertainty + logistic win probability. Output: the full V0-1.
   - This way, Phase A is demoable after 4 hours even if Phase B/C slip.

---

### RISK 9: NCAA Site JS Migration Broke Existing Scrapers (Score: 12)

**What the spec assumes:** `henrygd/ncaa-api` provides reliable JSON proxy at 5 req/s.

**What the research found:** stats.ncaa.org migrated to dynamic JavaScript rendering. All existing rvest, BeautifulSoup, and requests-based scrapers broke. The fix requires headless Chrome (chromote). baseballr's `ncaa_scrape()` was deprecated and replaced with a function requiring chromote (a full browser runtime).

**What this means:**
- `henrygd/ncaa-api` may or may not have been updated for the JS migration. Its last commit date is unknown from our research.
- If it hasn't been updated, the API will return empty or malformed data
- The fallback (chromote/playwright) works but adds:
  - A full Chrome browser as a runtime dependency
  - 10-50x slower scraping (browser rendering vs HTTP requests)
  - Higher failure rate (browser crashes, timeouts, memory leaks)
  - The "28 minutes for full DI season" estimate becomes 4-8 hours

**Mitigation:**
1. **Test henrygd/ncaa-api immediately.** One curl command: does it return game data for the 2026 season? If yes, proceed. If no, switch to playwright.
2. **Build the scraper abstraction layer** so the model code doesn't care whether data comes from the API, playwright, or a CSV import. This is already in the spec but should be the FIRST thing built, not an afterthought.
3. **Cache aggressively.** Once a game result is scraped, it never changes. Store it in SQLite immediately. Only scrape yesterday's games daily, not the full season.

---

### RISK 10: V0 to V1 Scope Cliff (Score: 12)

**What the spec says:**
- V0: 12-18 hours (our estimate: 30-50)
- V1: adds pitcher model + Monte Carlo + conference normalization + FastAPI = 2-4 weeks

**The cliff:**
- V0 is a CLI tool with basic ratings. Ryan can look at it.
- V1 requires: pitcher identification from box scores (cross-referencing player pages), pitcher ERA with Bayesian priors, NegBinomial Monte Carlo simulation, FastAPI web service, and a proper backtest framework
- The gap between "I have a CLI that ranks teams" and "I have a web service that predicts games with pitcher adjustments" is ~100 hours of engineering
- And that's ONE PERSON doing it nights/weekends while running ForgeStream, pitching law firms, and managing Sentinel

**The risk:** V0 works and Ryan says "great, now add pitchers." Mergim says "2-4 weeks." Four weeks later, it's not done because the pitcher data is messier than expected, the Monte Carlo distribution parameters need tuning, and the web service needs authentication. Ryan's PE attention cycle has moved on.

**Mitigation:**
1. **Don't promise V1 until V0 is validated.** "Let's see how V0 performs for two weeks before scoping V1."
2. **If V1 is greenlit, the pitcher model is the highest-value/lowest-cost addition.** Skip Monte Carlo simulation (it's computationally cool but adds minimal accuracy over logistic regression). Skip FastAPI (a static HTML page with daily updates is fine).
3. **The minimum viable V1 is: V0 + starting pitcher adjustment.** That's the feature PEAR lacks and Ryan's brief specifically called out. Everything else is V2+.

---

## Additional Risks (Not in Top 10 but Noteworthy)

### 643 Charts API Is Enterprise-Priced (Risk 11, Score: 12)

The spec says: "Ryan says 'I believe that's free' (claim #48)." Research found: 643 Charts operates on institutional subscription packages with no public pricing. Contact is sales-only (derek@643charts.com). Enterprise pricing means $5K-$50K/year, not free. The "physics data layer" (V3) depends entirely on either 643 Charts or direct program relationships. Neither is validated.

### Bayesian Prior Failure Modes (Risk 12, Score: 12)

The spec says: "Prior = last season + transfer delta." Specific failure modes:
1. **New DI programs** (e.g., a team moving up from DII): no DI prior exists. The model has no basis for an initial rating.
2. **Massive roster turnover:** If 8 of 9 position players transferred out, last season's team-level data is meaningless. The "transfer delta" would need to capture this, but the spec describes it as a single REAL column, not a comprehensive roster reconstruction.
3. **Transfers between talent tiers:** A player hitting .350 at a MEAC school transfers to an SEC school. His .350 was against dramatically weaker pitching. The prior must be adjusted for conference strength — but this requires player-level data (a V2 feature) to implement properly. Using it at the team level (V0) means the transfer delta is a rough approximation at best.
4. **Coaching changes:** A new coaching staff changes everything about a team's approach. The prior based on last year's data is for a different team, functionally.

### KenPom Revenue Timeline (Risk 13, Score: 12)

KenPom launched around 2002, went paid in October 2011 (9 years later), and the founder didn't quit his day job until 2013 (Year 2 of paywall, Year 11 of the site). If our baseball analytics follows a similar trajectory:
- Year 0-2: Free, building audience, zero revenue
- Year 3-5: Small paywall, $20-50K/year (if college baseball audience is 5x smaller than basketball)
- Year 5-10: Maybe $200K-$500K/year at maturity

This is a decade-long project for hobby-level returns. Ryan's PE lens evaluates opportunities on 3-5 year return horizons. A 10-year timeline to modest returns is not investable by PE standards.

### College Baseball Betting Handle (Risk 14, Score: 12)

No published figure breaks out college baseball betting specifically. Total US sports betting handle was $165B in 2025. College baseball's share is estimated at 0.1-0.3% = **$150M-$450M**. For comparison, college basketball's handle is estimated at $15B+ (100x larger).

If college baseball betting handle is $300M and our model captures 0.1% of that as revenue (via subscriptions to bettors): $300K/year. That's a side project, not a business.

---

## The Build-Time Reality Check

| Task | Spec Estimate | Realistic Estimate | Blocker |
|------|:---:|:---:|---------|
| Verify NCAA API works | Not in spec | 1-2 hours | **Must be first.** If it fails, everything shifts. |
| Scrape current season (DI box scores) | 8 hours | 8-24 hours | Depends on API vs playwright |
| Scrape historical data (2023-2025) | Not in spec | 4-12 hours | Required for exponent calibration and backtesting |
| Pythagorean exponent calibration | Not in spec (assumed 1.83) | 2-4 hours | Requires historical data |
| Build Layer 1 (Pythag, SOS, Elo, Power) | 6 hours | 6-10 hours | SOS iterative convergence needs testing |
| Build Layer 2 (Bayesian) | 6 hours | 6-10 hours | Prior construction from historical + transfer data |
| Build Layer 3 (Win probability) | 6 hours | 6-10 hours | Calibration testing is open-ended |
| CLI + output | 6 hours | 4-6 hours | Straightforward |
| PEAR validation + backtest | 6 hours | 8-16 hours | This is where you discover everything that's wrong |
| **Total V0** | **12-18 hours** | **45-90 hours** | |
| **V1 additions** | **2-4 weeks** | **4-8 weeks** | Pitcher data is messier than expected |

The 12-18 hour estimate is for the happy path where everything works the first time. The 45-90 hour estimate includes: API verification, historical scraping, exponent calibration, iterative debugging, and honest validation. Reality is closer to the latter.

---

## Summary Verdicts

| Spec Claim | Verdict | Action |
|-----------|---------|--------|
| "FSBB 58.2% accuracy" | **FABRICATED.** No model exists to produce this number. MLB ceiling is 58%; college ceiling is lower. | Remove immediately. Replace with honest target. |
| "exp ≈ 1.83 for college" | **WRONG.** Should be ~1.60-1.72. | Calibrate from data, never hardcode. |
| "Scrape time ~28 min" | **UNTESTED.** NCAA JS migration may have broken the API. | Test API before committing to timeline. |
| "12-18 hour V0 build" | **OPTIMISTIC 2-4x.** Realistic: 45-90 hours. | Set expectations with Ryan accordingly. |
| "RL self-learning model" | **WON'T CONVERGE** in a 56-game season. | Drop from V0/V1. Use Bayesian instead. |
| "643 Charts API — free" | **ENTERPRISE-PRICED.** No free tier found. | Remove from V0-V1 architecture. V3+ only, budget $10K+. |
| "Layer 3: calibrated probabilities" | **UNCERTAIN.** SABR says D1 data too thin for reliable win probability. | Always show CIs. May need to drop Layer 3 from V0. |
| "PEAR ~53% estimated" | **FABRICATED.** PEAR publishes no accuracy data. | Create our own PEAR baseline by tracking their rankings vs outcomes. |
| "NCAA data freely scrapable" | **LEGALLY RISKY.** ToS explicitly prohibits commercial scraping. | Legal consultation before any paid launch. |

---

## Recommended Immediate Actions

1. **Hour 0: Test the NCAA API.** One curl command. Pass/fail. Everything depends on this.
2. **Hour 1: Scrape 2026 season box scores** (however the API works). Get data in hand.
3. **Hour 2: Calculate current-season RPG and derive correct Pythagorean exponent.** Do NOT use 1.83.
4. **Hour 3: Remove all fabricated numbers from specs** (58.2%, PEAR ~53%, 12-18h timeline). Replace with "TBD — will measure from actual model output."
5. **Hours 4-20: Build the honest V0** — rankings with uncertainty, using the correct exponent, with PEAR as a comparison benchmark.
6. **Before showing Ryan anything:** Run the backtest. Report the ACTUAL accuracy. If it's 54%, say 54%.

**The credibility test for this entire project is whether we report honest numbers or fabricated ones.** Ryan is a PE professional trained to detect bullshit. Present him with a 58.2% claim from a model that doesn't exist, and the relationship is over. Present him with a 54% accuracy from a real model with proper uncertainty quantification, and he has something to evaluate.

---

*[SENTINEL:ORANGE_TEAM] V0/V1 risk assessment complete. Multiple critical spec claims are fabricated or incorrect. Recommended: spec revision before any code is written.*
