# V0/V1 Unified Specification — ForgeStream Baseball (FSBB)

**Synthesized:** 2026-03-31 | **Sources:** 5 Sentinel analyses (Market Intelligence, Algorithm R&D, Risk Assessment, Implementation Spec, GTM Strategy) + existing research (7 agents), x-vector verified call analysis (510 claims), PEAR scraped data (308 teams)

**This is the ONLY document needed to build. Everything is here. No cross-referencing.**

---

## Executive Summary

**What:** A college baseball prediction and ratings platform — "the KenPom for college baseball." A nightly prediction page that publishes game-by-game win probabilities for every D1 matchup, tracks accuracy in public, and differentiates from existing tools (PEAR, 64 Analytics) through algorithmic sophistication: variable-exponent Pythagorean estimation, Bayesian prior-posterior rating updates, and matchup-aware game predictions that account for starting pitcher, home/away, and recent form.

**For whom:** Three audiences in order of revenue potential: (1) serious sports bettors exploiting inefficient college baseball lines, (2) fans following tournament bubble scenarios, (3) college programs evaluating opponents and transfer portal additions. Ryan McCarthy (HIG Capital PE) is the business evaluator. Tim McCarthy (Wellington) is the domain expert. Connor McCarthy (player development, Appalachian State) is the practitioner lens.

**Why now:** College baseball is in a data availability inflection. The NCAA transfer portal moved 2,000+ players/year creating urgent evaluation demand. Legal sports betting is growing 20%+ annually. PEAR (free, passion project, anonymous founder in Arkansas) and 64 Analytics (2023, $13/month, player-focused) exist but nobody has built the prediction layer. EvanMiya proved the model in basketball ($180/year, 120+ D1 programs). Nobody has done the equivalent for baseball.

**The algorithmic thesis:** PEAR uses static team ratings where every game in a 3-game weekend series gets identical win probabilities regardless of who's pitching. [VERIFIED — Vanderbilt vs Tennessee Mar 27-29 shows identical 0.4914 home_win_prob for all three games.] Our model produces matchup-specific probabilities that adjust for game context. If this adjustment yields even a 3-5% accuracy improvement over PEAR's static approach, it validates the entire product thesis.

**V0 deliverable:** A static HTML "Nightly Prediction Page" — tonight's D1 games with predicted winner, win probability, and predicted run total. Yesterday's results filled in with accuracy tracking. PEAR comparison column. Automated daily via cron. Build time: 18-24 hours. No ML frameworks. Python + SQLite + Jinja2.

**V1 roadmap:** Player-level adjustments, transfer portal projections, Bayesian hierarchical model with conference-tier priors, historical backtest dashboard, betting edge calculator. 4-6 weeks beyond V0.

**Ryan needs to see:** A backtest showing our model outpredicts PEAR's static ratings on actual game outcomes. Promised by Wednesday evening. His framing: "feasibility study" — not a startup pitch, a research question with a quantitative answer.

---

## Part 1: Market Position

### Competitive Landscape

| Platform | What They Do | Price | Our Edge |
|----------|-------------|-------|----------|
| **PEAR** | Team ratings (TSR/RQI/SOS/NET/ELO), tournament projections. 308 D1 teams. Free. | Free | They use IDENTICAL win probs for all games in a series. No pitcher adjustment. No game-level context. [VERIFIED] |
| **64 Analytics** | Player-level stats (wRCE/wRAE/RE24), transfer portal tracking. 2023-founded. | $13/mo, $5.5K institutional | Player-focused, not prediction-focused. No public win probabilities. No accuracy tracking. Proprietary metrics unvalidated. [VERIFIED] |
| **6-4-3 Charts** | TrackMan + Synergy integration, 650+ D1 programs. API exists. | Enterprise (price unknown) | B2B only, not public-facing. Has the data but not the consumer product. Potential data licensing partner. [VERIFIED] |
| **KenPom** (basketball) | The reference model. $25/year, ~200K subs, ~$5M ARR. One person. 24 years. | $25/year | Proves the model works. Baseball version doesn't exist. [VERIFIED] |
| **EvanMiya** (basketball) | Bayesian BPR, 120+ D1 programs, $180/year. PhD-built. 2020-founded. | $180/year | Proves Bayesian player-level ratings sell. Baseball version doesn't exist. [VERIFIED] |

**Why nobody has built this yet:**
1. College baseball data quality is significantly worse than basketball (NCAA stat entry by unpaid student SIDs) [VERIFIED — NCAA acknowledged "uptick in incorrect statistics"]
2. Baseball is pitcher-dominated with small samples (56-game season, ~15 starts per pitcher) making prediction harder [VERIFIED]
3. The addressable market is smaller than basketball or football [VERIFIED — Ryan flagged this: "it's a niche addressable market"]
4. Advanced data (exit velocity, spin rate) is siloed per-program with no public aggregation [VERIFIED]

### Market Size

| Segment | TAM | SAM | SOM (Year 1) | Source |
|---------|-----|-----|-------------|--------|
| College baseball fans (US) | ~15M | ~2M (engaged enough to use analytics) | 5,000-10,000 | Insight Miner research |
| College baseball bettors | ~$150-450M handle | Unknown active bettors | 500-2,000 | Orange Team estimate |
| D1 college programs | 302 programs | ~150 with analytics budget | 10-20 | EvanMiya basketball comp: 120+ |
| Betting edge subscribers | Unknown | Unknown | 100-500 at $50-100/mo | Speculative |

**Honest assessment [from Orange Team]:** The fan TAM is niche. KenPom's $5M ARR took 9 years of free → paywall. The betting edge is the revenue multiplier but the college baseball handle is small (~$150-450M vs $10B+ total US sports betting). The path to meaningful revenue is measured in years, not months. Ryan knows this — his "feasibility study" framing is appropriate.

**Counter [from Coach]:** A niche market with premium pricing beats a mass market with commodity pricing. College baseball lines are the most inefficient in American sports because oddsmakers have the least data. Even a small edge = significant value per user.

### Why Now

1. **Transfer portal demand** — 2,000+ transfers/year. Coaches need cross-conference player evaluation tools. [VERIFIED]
2. **Betting market growth** — legal sports betting expanding 20%+ annually. College baseball is underserved. [VERIFIED]
3. **Data availability inflection** — henrygd/ncaa-api provides scoreboard data (scores, schedules). PEAR API provides team ratings. NCAA box scores scrapable. [VERIFIED via live testing]
4. **No published prediction model** — zero published accuracy metrics from any college baseball model. First to publish = first-mover authority. [VERIFIED — Insight Miner found no published accuracy from PEAR, 64, Warren Nolan, or Massey]

---

## Part 2: Algorithm Specification

### V0 Model: 3-Layer Architecture

**CRITICAL CORRECTION [Orange Team]:** The original spec claimed "58.2% accuracy" for an unbuilt model. This number is fabricated — it matches the MLB Vegas ceiling exactly. **All accuracy claims are PROJECTED until backtested.** The honest target is: "measurably outperform PEAR's static ratings. MLB ceiling is ~58%; college ceiling is unknown and likely 55-60%."

#### Layer 1: Pythagorean Expected Win Percentage

**Formula:** `ExpW% = RS^exp / (RS^exp + RA^exp)`

**CRITICAL: Use Pythagenport variable exponent, NOT fixed 1.83.**

```python
# Pythagenport (Davenport): adapts to run environment
exp = 1.50 * math.log10((total_rs + total_ra) / games) + 0.45

# Alternative: Pythagenpat (Smyth): data-driven
exp = ((total_rs + total_ra) / games) ** 0.287
```

**Why variable matters [VERIFIED — Insight Miner]:**
- Fixed 1.83 is MLB-derived. No published college-specific exponent exists.
- College baseball RPG varies 5.2-9.2 across conferences.
- Using 1.83 overestimates by 6-18% depending on conference. [Orange Team Risk #2, Score: 20]
- Expected college exponent: ~1.60-1.72 for 2026. If calibration returns 1.83, the data is wrong.

**Implementation:**

```python
def pythagenport_exponent(runs_scored: int, runs_allowed: int, games: int) -> float:
    rpg = (runs_scored + runs_allowed) / max(games, 1)
    return 1.50 * math.log10(max(rpg, 1.0)) + 0.45

def pythagorean_wpct(rs: int, ra: int, games: int) -> float:
    exp = pythagenport_exponent(rs, ra, games)
    if rs + ra == 0:
        return 0.5
    return rs**exp / (rs**exp + ra**exp)
```

**Risk [Orange Team, Score: 15]:** Pythagorean W% is near-useless after <10 games. Mitigation: we're launching mid-season (~28 games played per team), which is above the noise threshold. Early-season future launches need Bayesian priors.

#### Layer 2: Dynamic Bradley-Terry Ratings

**Why BT over Elo [VERIFIED — Algorithm R&D]:** Bradley-Terry is the batch maximum likelihood version of Elo — mathematically equivalent but solves the entire pairwise system simultaneously. Critical for college baseball where a Sun Belt team and Big Ten team may share zero direct opponents. BT propagates strength through transitive connections.

**Formula:**
```
P(i beats j) = π_i / (π_i + π_j)
where π_i = exp(θ_i) and θ_i is team i's latent strength
```

**Dynamic BT (Firth & Kosmidis 2012):** Adds temporal decay `w_t = exp(-λt)` with `λ ≈ 0.020` (half-life ~35 days). Recent games matter more.

**Home field advantage:** Separate parameter `HFA ≈ 0.15-0.20` (translates to ~54-57% home win probability). [VERIFIED — college baseball HFA is slightly higher than MLB's 54%]

**Fitting:** MM algorithm (Hunter 2004). Converges in 50-200 iterations. Trivially fast for 308 teams.

**Implementation:**

```python
def fit_dynamic_bt(
    games: list[dict],  # {home_id, away_id, home_won, date, home_runs, away_runs}
    n_teams: int,
    lambda_decay: float = 0.020,
    max_iter: int = 200,
    tol: float = 1e-6,
) -> tuple[np.ndarray, float]:  # (ratings, hfa)
    """Fit Dynamic Bradley-Terry model via MM algorithm.
    Returns team strength ratings (log-scale) and home field advantage.
    """
    ...
```

#### Layer 3: Game-Level Win Probability

**Logistic regression** combining BT ratings with game-specific features:

```
logit(P(home wins)) = β₀ + β₁·(θ_home - θ_away) + β₂·HFA + β₃·rest_days_diff
```

For V0, features are limited to what's available from scoreboard data:
- `θ_home - θ_away`: BT rating difference
- `HFA`: home field indicator
- `rest_days_diff`: days since last game (schedule density)

**V1 additions:** Starting pitcher adjustment, conference vs non-conference, weather, travel distance.

**Output:** Calibrated win probability in [0, 1] with confidence interval via bootstrap.

**Calibration metric:** Brier score. Nobody else publishes this. [VERIFIED — Insight Miner: "No college baseball model publishes accuracy metrics. Not one."]

### Differentiation Assessment (Honest)

| Claim | Status | Moat Rating |
|-------|--------|-------------|
| "Variable-exponent Pythagorean for college baseball" | REAL — no one has published the college-specific exponent | **HIGH** (first-mover research) |
| "Dynamic BT > Elo for unbalanced schedules" | REAL — mathematically superior for college baseball | **MODERATE** (a grad student could replicate) |
| "Game-level contextualization (vs PEAR's static)" | REAL — PEAR confirmed to use identical series probabilities | **HIGH** (the core product thesis) |
| "Self-learning RL model" | OVERSTATED — should be framed as online logistic regression with adaptive learning rate | **LOW** (standard ML, not exotic) |
| "The equation from alpha generation" | PARTIALLY REAL — the framework transfers (probabilistic output, online learning, edge detection) but weights must be learned from scratch | **MODERATE** (thinking advantage, not code advantage) |
| "Bayesian priors solve small-sample problem" | REAL — conjugate normal-normal gives 66% data weight after 10 games | **MODERATE** (well-known technique, novel application) |

**Backtest design:**
- Training data: 2024-2025 NCAA D1 season results (~8,400 games/season)
- Test data: 2026 season games (already ~4,200 played)
- Metrics: Accuracy % (straight-up winner prediction), Brier score (probability calibration), Spearman ρ (ranking correlation vs PEAR)
- Statistical significance: n=300+ games needed for 3% accuracy difference to be significant at p<0.05
- Baseline: PEAR's implied win probabilities (from their static ratings)

---

## Part 3: Implementation Plan

### Hour-by-Hour V0 Build Plan (18-24 hours)

#### Hour 0-2: Project Scaffold + Data Foundation

```bash
mkdir -p fsbb/{scraper,models,templates}
```

**Files to create:**

| File | Purpose | Lines (est.) |
|------|---------|-------------|
| `fsbb/db.py` | SQLite schema: teams, team_aliases, games, predictions | ~120 |
| `fsbb/schemas.py` | Pydantic models: Team, Game, Prediction | ~80 |
| `fsbb/scraper/pear.py` | Import from existing PEAR scraper (already built) | ~50 |
| `fsbb/scraper/ncaa.py` | Scoreboard scraper via henrygd/ncaa-api | ~100 |
| `fsbb/scraper/clean.py` | Team name normalization + alias table | ~80 |

**SQLite schema (from Arch Sentinel):**

```sql
CREATE TABLE teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    conference TEXT NOT NULL,
    division TEXT NOT NULL DEFAULT 'D1',
    pear_power_rating REAL,
    pear_net INTEGER,
    pear_elo REAL,
    total_rs INTEGER DEFAULT 0,
    total_ra INTEGER DEFAULT 0,
    games_played INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    pythag_pct REAL,
    power_rating REAL,
    elo REAL DEFAULT 1500.0
);

CREATE TABLE games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    home_team_id INTEGER NOT NULL REFERENCES teams(id),
    away_team_id INTEGER NOT NULL REFERENCES teams(id),
    home_runs INTEGER,
    away_runs INTEGER,
    status TEXT NOT NULL DEFAULT 'scheduled',
    our_home_win_prob REAL,
    our_predicted_winner_id INTEGER,
    pear_home_win_prob REAL,
    actual_winner_id INTEGER
);

CREATE TABLE predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL REFERENCES games(id),
    model_version TEXT NOT NULL,
    home_win_prob REAL NOT NULL,
    predicted_total_runs REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

**Risk [Orange Team, Score: 12]:** NCAA site JS migration broke existing scrapers. Mitigation: use henrygd/ncaa-api for scores (confirmed working via live test), not direct NCAA scraping. For box scores, use PEAR API as primary source.

**Risk [Orange Team, Score: 20]:** NCAA ToS prohibits commercial scraping. Mitigation: keep V0 non-commercial (free research tool). Consult sports data IP attorney before any paid launch. Use "facts not expression" defense (Feist v. Rural Telephone). Build pipeline to work from multiple sources.

#### Hour 2-4: NCAA Data Ingestion

```python
# fsbb/scraper/ncaa.py
async def scrape_season_scores(
    season: int = 2026,
    division: str = "d1",
) -> list[dict]:
    """Pull all game scores for a season via henrygd/ncaa-api.

    Returns: [{"date": "2026-03-31", "home": "Texas", "away": "UCLA",
               "home_runs": 5, "away_runs": 3, "status": "final"}, ...]

    Rate limit: 5 req/s. Full D1 season (~8,400 games): ~28 min.
    """
```

**Data cleaning [critical path]:**
- Team name normalization: "UNC" → "North Carolina", "N. Carolina" → "North Carolina"
- Build alias table for all 308 D1 teams
- Cross-reference PEAR team names with NCAA team names (different naming conventions)
- Handle postponed/cancelled games
- Validate: home_runs + away_runs should match reasonable ranges (0-30)

#### Hour 4-6: Rating Engine (Layer 1 + Layer 2)

```python
# fsbb/models/ratings.py
def compute_all_ratings(db: sqlite3.Connection) -> None:
    """Compute Pythagorean W%, BT ratings, SOS for all teams.

    1. Load all final games
    2. Calculate Pythagenport exponent from overall RPG
    3. Compute Pythagorean W% per team
    4. Fit Dynamic BT (MM algorithm, 200 iterations max)
    5. Compute SOS (iterative, 3 passes)
    6. Write ratings back to teams table
    """
```

#### Hour 6-8: Win Probability Model (Layer 3)

```python
# fsbb/models/predict.py
def predict_game(
    home_team: Team,
    away_team: Team,
    model_params: dict,
) -> dict:
    """Predict game outcome.

    Returns: {
        "home_win_prob": 0.623,
        "away_win_prob": 0.377,
        "predicted_total_runs": 8.4,
        "confidence": "medium",  # based on sample size
        "model_version": "v0.1",
    }
    """
```

#### Hour 8-10: PEAR Comparison + Backtest

```python
# fsbb/models/backtest.py
def run_backtest(
    db: sqlite3.Connection,
    start_date: str = "2026-02-14",
    end_date: str = "2026-03-30",
) -> dict:
    """Backtest our model vs PEAR on historical outcomes.

    For each completed game:
    1. Compute our win probability (using only data available BEFORE the game)
    2. Get PEAR's implied probability (from their static ratings)
    3. Compare both against actual outcome

    Returns: {
        "our_accuracy": 0.572,
        "pear_accuracy": 0.531,
        "our_brier": 0.238,
        "pear_brier": 0.251,
        "n_games": 4200,
        "edge": 0.041,  # our - pear
        "p_value": 0.003,  # statistical significance
    }
    """
```

**Risk [Orange Team, Score: 25]:** The 58.2% accuracy claim is fabricated. Mitigation: **NEVER present projected numbers as empirical results.** Run the backtest first, report the ACTUAL number. If it's 54%, that's honest and still potentially meaningful. The story becomes "probability calibration" not "accuracy percentage."

#### Hour 10-12: Nightly Prediction Page

```python
# fsbb/templates/predictions.html (Jinja2)
# Static HTML page with:
# - Tonight's games table (home, away, our prob, PEAR prob, predicted total)
# - Yesterday's results (✓/✗ on our pick, ✓/✗ on PEAR pick)
# - Running accuracy (our % vs PEAR %)
# - Brier score comparison
# - Last updated timestamp
```

```python
# fsbb/__main__.py CLI commands
@cli.command()
def predict():
    """Generate tonight's predictions."""

@cli.command()
def results():
    """Fill in yesterday's results."""

@cli.command()
def render():
    """Render the prediction page to HTML."""

@cli.command()
def rank():
    """Print team rankings."""

@cli.command()
def matchup(home: str, away: str):
    """Predict a specific matchup."""
```

#### Hour 12-14: Automation + First Night

- Cron job: `0 16 * * * cd /path/to/fsbb && fsbb predict && fsbb render`
- Morning job: `0 10 * * * cd /path/to/fsbb && fsbb results && fsbb render`
- First real prediction night

#### Hour 14-18: Buffer for Debugging, Calibration, Edge Cases

- Pythagorean exponent calibration against actual college data
- BT convergence verification
- Win probability calibration check (do predicted 60% games win ~60% of the time?)
- Edge case handling: postponed games, tournaments, neutral sites

### Dependencies

```toml
[project]
requires-python = ">=3.12"
dependencies = [
    "httpx>=0.27",
    "pydantic>=2.0",
    "click>=8.1",
    "tabulate>=0.9",
    "jinja2>=3.1",
    "numpy>=1.26",
    "scipy>=1.12",
]
```

No ML frameworks. No torch. No scikit-learn. Pure math + standard library.

---

## Part 4: V1 Roadmap

| Component | Description | Build Est. | Dependencies | Data Needed |
|-----------|-------------|-----------|-------------|-------------|
| **V1.1: Bayesian Prior-Posterior** | Normal-normal conjugate update. Prior = last season's Pythag. Posterior updates with each game. | 8-12 hours | V0 ratings working | 2024-2025 historical data |
| **V1.2: Starting Pitcher Adjustment** | Modify win probability based on who's starting. Requires pitcher ERA/FIP from box scores. | 12-16 hours | NCAA box score scraper | Individual pitcher game logs |
| **V1.3: Transfer Portal Projections** | Separate model for transfers (different feature weights than returners). | 16-20 hours | V1.1 + portal data | 64 Analytics or manual tracking |
| **V1.4: Historical Backtest Dashboard** | Interactive web page showing model performance over time. | 8-12 hours | V0 + 2 weeks of predictions | Accumulated prediction data |
| **V1.5: Betting Edge Calculator** | Kelly criterion overlay: given model probability and market odds, compute optimal bet size. | 4-6 hours | V0 predictions + odds feed | Live odds API (free: Odds API) |

**RL self-learning component [honest assessment from Algorithm R&D + Orange Team]:**
- Game outcome prediction is NOT a sequential decision problem. It's an online learning problem — contextual bandit, not full RL.
- The right framing: online logistic regression with adaptive learning rate. Not deep RL.
- Cold-start problem: 56 games/team/season is too few for deep RL to converge. Pre-training on multi-season data is essential.
- **Recommendation:** Use Dynamic BT + logistic regression for V0-V1. Reserve "RL" framing for bankroll management (a separate module on top of predictions), not the prediction layer itself.
- **Risk [Orange Team, Score: 15]:** RL won't converge within a 56-game season. Mitigation: don't use model-free RL for predictions. Use it for portfolio/bankroll optimization where the action space is simpler.
- **Moat rating: LOW for deep RL, MODERATE for online learning.** The "self-learning" concept is real but the implementation is standard online ML.

---

## Part 5: Go-to-Market

### Day-by-Day Sprint Plan

| Day | Focus | Deliverable | Send to Ryan? |
|-----|-------|-------------|---------------|
| **Day 0 (Mon)** | Scaffold + data ingestion + Layer 1 ratings | `fsbb rank` works | No |
| **Day 1 (Tue)** | Layer 2 (BT) + Layer 3 (win prob) + matchup engine | `fsbb matchup "Texas" "UCLA"` works. **Send follow-up message.** | Follow-up message |
| **Day 2 (Wed)** | Backtest + first night predictions | Accuracy % vs PEAR. **Send results.** | **Backtest results** |
| **Day 3 (Thu)** | Fill results + render HTML + demo prep | Prediction page live. **Demo call (if scheduled).** | Demo |
| **Day 4-7** | Accumulate daily predictions. 80+ games. Fix bugs. | Running accuracy report. | Weekly summary |

### Ryan Demo Script (Thursday)

**Opening:** Show results first, not code. Screen share the prediction page. Point to: yesterday's predictions vs actual, running accuracy, PEAR comparison column.

**The moment:** Pick 2-3 games where our model disagreed with PEAR and was right. "PEAR's static rating would have picked Team A in all three. Our model picked Team B in two. Team B won both."

**The question:** "If you were evaluating this as an investment — not the product, just the predictive edge — what would you need to see to be convinced?"

**The close:** "I'll keep running daily predictions. By [date] we'll have 300+ games. If the edge holds, we have a product."

### Pricing Strategy

| Phase | Price | Audience | Duration | Rationale |
|-------|-------|----------|----------|-----------|
| Beta | Free | Early adopters, fans, bettors | 1-3 months | Build audience, accumulate track record, prove accuracy publicly |
| V1 launch | $25/year | Fans + casual bettors | Ongoing | KenPom-proven price point. Impulse buy, no budget approval needed. |
| Institutional | $2,000-5,000/year | College programs | Ongoing | 64 Analytics Portal Pass comp. NCAA-approved scouting service. |
| Premium (V2) | $50-100/month | Serious bettors | Ongoing | Betting edge calculator. Kelly criterion. Model confidence signals. |

**KenPom lesson [VERIFIED]:** $25/year is a moat, not a revenue lever. It's cheaper than almost any paywall. The value is obvious. The subscription is an impulse buy. 200K subscribers × $25 = $5M ARR for one person. The price keeps competitors from undercutting without going free.

### Legal Checklist

- [ ] Consult sports data IP attorney ($500, 2 hours) — BEFORE any paid launch
- [ ] Research NCAA data licensing alternatives and costs
- [ ] Review "facts not expression" defense (Feist v. Rural Telephone) applicability
- [ ] Keep V0 non-commercial (free research tool)
- [ ] Build data pipeline to work from multiple sources (NCAA, ESPN, PEAR, team sites)

---

## Part 6: Risk Register (Top 10)

| # | Risk | L×I | Mitigation | Owner | Deadline |
|---|------|-----|-----------|-------|----------|
| 1 | **Accuracy claims are fabricated** (58.2% is MLB ceiling, not built) | 25 | Remove ALL projected accuracy. Run backtest. Report ACTUAL numbers only. | Mergim | Before sending to Ryan |
| 2 | **Pythagorean exponent 1.83 is wrong** for college | 20 | Use Pythagenport variable formula. Calibrate on actual college data. Expect ~1.60-1.72. | Mergim | Hour 4-6 of build |
| 3 | **NCAA ToS prohibits commercial scraping** | 20 | Keep V0 free. Consult attorney. Use "facts not expression" defense. Build multi-source pipeline. | Mergim + legal | Before paid launch |
| 4 | **Pythagorean useless after <10 games** | 15 | Launch mid-season (28+ games available). Add Bayesian priors for future season starts. | Mergim | V1.1 |
| 5 | **RL won't converge in 56-game season** | 15 | Don't use model-free RL for predictions. Use Dynamic BT + logistic regression. RL for bankroll only. | Mergim | V1 design |
| 6 | **D1 data too thin for reliable win probabilities** | 16 | Publish confidence intervals. Use Brier score not just accuracy. Bayesian uncertainty quantification. | Mergim | V0 |
| 7 | **No validation baseline exists** | 12 | BE the baseline. Publish accuracy first. First-mover defines the benchmark. | Mergim | Week 1 |
| 8 | **V0 build estimate unrealistic** (18h but exponent must be calibrated) | 12 | Budget 24h not 18h. Exponent calibration is prerequisite, not optional. | Mergim | Day 0 |
| 9 | **643 Charts API is enterprise-priced** | 12 | Don't depend on it for V0. Use NCAA scoreboard + PEAR only. Explore licensing later. | Mergim | V1+ |
| 10 | **Ryan's 53 action items are polite deferrals** | 10 | Show results, not promises. The backtest IS the conviction engine. Don't ask for validation — provide evidence. | Mergim | Wednesday |

---

## Part 7: Decision Log

| Decision | Rationale | Source |
|----------|-----------|--------|
| **V0 = Nightly Prediction Page** | Highest impact/effort ratio. Demonstrates the core thesis (matchup-aware predictions > static ratings). Can be built in 18-24h. | Idea Reactor V0 ranking: 10/10 composite |
| **Algorithm = Pythagenport + Dynamic BT + Logistic** | Pythagenport handles variable run environments. BT handles unbalanced schedules. Logistic provides calibrated probabilities. Each component is verified in literature. | Algorithm R&D + Insight Miner verification |
| **NOT neural net or XGBoost for V0** | Overfitting risk with 8,400 games. No interpretability for Ryan. No feature engineering budget in 18h. Simple models are harder to beat than complex ones in low-data regimes. | Orange Team Risk #1 + Algorithm R&D |
| **Data = NCAA scoreboard + PEAR for V0** | Scoreboard API confirmed working (scores, schedules). PEAR API confirmed working (308 teams, ratings). No box scores needed for V0 (runs scored/allowed is sufficient). | Insight Miner live API testing |
| **NOT play-by-play for V0** | PBP scraping requires headless browser, 10-20% incompleteness, and hours of engineering. V0 only needs game scores. | Insight Miner + Orange Team |
| **Pricing = free during beta** | NCAA ToS risk. Need track record before charging. KenPom was free for 9 years. Build audience first. | Coach GTM research + Orange Team legal risk |
| **Stack = Python + SQLite + static HTML** | No deployment complexity. No server costs. No framework lock-in. SQLite handles 308 teams × 8,400 games trivially. Jinja2 for HTML. Click for CLI. | Arch Sentinel implementation spec |
| **Build > partner with PEAR** | PEAR has no commercial ambition, manual data pipeline, no player data, no API. The moat is automated infrastructure + superior modeling. | Ryan feedback analysis + full research |
| **Dynamic BT > Elo** | BT solves the full pairwise system simultaneously. Elo is sequential and can't propagate strength through transitive connections. Critical for college baseball's unbalanced schedules. | Algorithm R&D verified finding |
| **Pythagenport > fixed exponent** | Fixed 1.83 overestimates by 6-18% for college. Pythagenport self-calibrates to scoring environment. College-specific exponent is itself a publishable finding. | Insight Miner + Orange Team Risk #2 |
| **Brier score as primary metric** | Nobody publishes calibration metrics. Calibrated probabilities are more valuable to bettors than raw accuracy. Being first to publish Brier score = authority. | Insight Miner finding on calibration vs accuracy |
