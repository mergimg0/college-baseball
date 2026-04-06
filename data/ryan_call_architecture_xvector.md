# ForgeStream Baseball — Technical Architecture (X-Vector Verified)
**Date:** 2026-03-31 | **Source:** Ryan McCarthy call — 510 claims, x-vector verified
**Speakers:** Tim (92 claims, 304s), Ryan (167 claims, 1023s), Mergim (251 claims, 877s)
**Status:** DRAFT v2 — supersedes `ryan_call_architecture.md`

---

## Design Principles (Voice-Verified from Call)

1. **Data pipeline is table stakes** — Ryan (REQ #21): "The most important piece is figuring out that data pipeline" — but he treats this as solvable engineering, not the hard problem. Speaker confidence: high (x-vector ↔ Gemini agree).
2. **Algorithm differentiation is the #1 need** — Ryan (REQ #28-29): "It's understanding how could we differentiate from like an algorithm perspective" — said with elevated arousal (0.78), indicating genuine conviction, not filler.
3. **Team before player** — Ryan (REQ #24-25): "Keep it simple... team metrics before player metrics" — cautious scope-setting, low arousal (0.42), deliberate framing.
4. **Runs are the atom** — Ryan (REQ #26-27): "Runs scored and runs allowed" — baseline metrics, agreed by all three.
5. **Clean or die** — Mergim (REQ #20): "Getting the data right is crucial so the model doesn't hallucinate" — high dominance (0.91), setting a non-negotiable.
6. **Prove legs fast** — Mergim (REQ #9): "What would a V0 look like that convinces you this has legs" — the V0 must demonstrate algorithmic value, not just data scraping.
7. **Vibe-code accessible** — Tim (claim #133): "I can see if I can just vibe code one right now" — stack must be approachable for a non-expert contributor.

---

## 1. Data Pipeline Architecture

### Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATA PIPELINE                                      │
│                                                                             │
│  SCRAPE            CLEAN              STORE           MODEL         SERVE   │
│  ┌──────┐        ┌────────┐        ┌────────┐      ┌────────┐   ┌──────┐  │
│  │ NCAA │──raw──▶│ Entity │──clean▶│ SQLite │──feat▶│ Rating │──▶│ CLI  │  │
│  │ API  │  JSON  │ Resol. │  rows  │   DB   │ vecs │ Engine │   │  +   │  │
│  ├──────┤        │ Dedup  │        ├────────┤      │        │   │ JSON │  │
│  │ PEAR │──raw──▶│ Anomal │──────▶│        │      │ Alpha  │   │ API  │  │
│  │Bench │  JSON  │ Detect │        │        │      │ Model  │   └──────┘  │
│  ├──────┤        │        │        │        │      │        │             │
│  │ 643  │──raw──▶│ Norm.  │──────▶│        │      │  RL    │             │
│  │ API  │  JSON  │        │        │        │      │ Agent  │             │
│  └──────┘        └────────┘        └────────┘      └────────┘             │
│     ▲               ▲                  ▲               ▲                   │
│     │               │                  │               │                   │
│  [cron]      [ForgeStream AI]     [migration]    [The Equation]            │
│  daily       entity resolution    SQLite→PG      alpha generation          │
│              anomaly detection                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Source 1: NCAA Stats (Primary — Box Scores)

| Attribute | Value |
|-----------|-------|
| URL | `stats.ncaa.org` |
| Access | `henrygd/ncaa-api` (unofficial JSON proxy, 5 req/s) |
| Python packages | `collegebaseball` (pip), `CollegeBaseballStatsPackage` |
| Data available | Box scores, game logs, player stats, schedules (DI/DII/DIII) |
| Format out | `NcaaGameRecord` Pydantic model |
| Volume (DI) | ~8,400 games/season × ~30 fields = ~252K records |
| Scrape time | ~28 min at 5 req/s for full DI season |
| Failure mode | NCAA HTML structure changes → parser breaks |
| Fallback | Cache last-good scrape; alert on >10% parse failure rate |
| Incremental | Daily 06:00 UTC — yesterday's completed games |

### Source 2: PEAR Ratings (Validation Benchmark Only)

| Attribute | Value |
|-----------|-------|
| URL | `pearatings.com` |
| Already scraped | `data/pear/pear_ratings.json` — 308 teams × 11 fields |
| Per-team detail | `data/pear/teams/` — ~140+ fields per team including wOBA, wRAA, fWAR, ISO, wRC+, FIP, Killshot metrics |
| Role | Comparison target — our rank correlation should be Spearman ρ > 0.90 |
| Risk | PEAR goes behind paywall (Ryan, claim #168). Mitigate: build own pipeline from NCAA source |
| PEAR download limitation | Rankings downloadable as CSV; raw stats NOT downloadable (Tim, claim #144) |

### Source 3: 643 Charts API (V1+ — TrackMan Data)

| Attribute | Value |
|-----------|-------|
| URL | `643charts.com/api` |
| Data | TrackMan: exit velocity, launch angle, spin rate, pitch movement |
| Coverage | 650+ DI programs (where TrackMan hardware installed) |
| Pricing | Uncertain — Ryan says "I believe that's free" (claim #48); Tim: "I've got to look into 643 charts" (claim #46). Needs direct verification. |
| Access | REST API, may require institutional key |
| Role | Physics-level differentiation data for V2+ |

### Cleaning Layer (ForgeStream AI Moat)

PEAR's pipeline: Python scrape → manual validation. Tim (claim #19): "there's a manual layer that he's doing to make sure that it's correct." Our competitive edge is automating this.

**Core cleaning problems:**

1. **Entity resolution** — NCAA inconsistent names ("UNC" / "North Carolina" / "N. Carolina")
   - Solution: 308-row canonical name table + Levenshtein fuzzy match (threshold ≤ 2)
   - ForgeStream contribution: domain knowledge extraction encodes how scouts/coaches refer to teams

2. **Deduplication** — Same game reported by both teams, sometimes with discrepancies
   - Solution: Composite key (date, home_team, away_team) → flag score mismatches → prefer home report

3. **Anomaly detection** — Stats entered by unpaid student SIDs (NCAA acknowledged "uptick in incorrect statistics")
   - Solution: Z-score outlier detection; flag games where RS+RA > 40 or IP ≠ expected innings
   - ForgeStream: AI plausibility checking against historical baselines

4. **Missing data** — ~10-20% of DI games have incomplete PBP
   - V0: Skip PBP entirely, use box-score aggregates only
   - V1+: Track missingness rate per team; weight ratings by data completeness

**Estimated data volumes:**

| Metric | DI (V0) | All Divisions (V2+) |
|--------|---------|---------------------|
| Teams | 308 | ~1,700 |
| Games/season | ~8,400 | ~24,000 |
| Storage (SQLite) | ~50 MB | ~150 MB |
| Scrape time | ~28 min | ~80 min |

---

## 2. V0 System Design — Algorithm-First

Ryan considers data scraping "easy to prove." The V0 must lead with algorithmic innovation.

### The Core Insight: Why Our Model Is Better Than PEAR

PEAR computes: `NET = weighted(TSR, RQI, SOS)` — a static linear composite of team quality, resume quality, and schedule strength. No learning, no uncertainty, no matchup awareness.

**Our V0 model architecture — 3 layers PEAR doesn't have:**

```
Layer 1: Pythagorean Foundation (same as PEAR — table stakes)
├── RS^exp / (RS^exp + RA^exp)
├── SOS iterative (Bayesian convergence)
├── Elo with margin-of-victory adjustment
└── This alone should correlate ρ > 0.90 with PEAR

Layer 2: Bayesian Prior Update (our first differentiation)
├── Start with prior from last season's performance + transfer delta
├── Update posterior with each game result
├── Handle small-sample problem (56-game season, ~15 starts/pitcher)
├── Properly model uncertainty (wide CIs early, narrow late)
└── Inspired by EvanMiya's BPR approach for basketball

Layer 3: Logistic Regression Win Probability (our second differentiation)
├── Features: power_diff, home_advantage, SOS_diff, rest_days
├── Trained on 3 seasons of historical NCAA outcomes
├── Produces calibrated probabilities (not just rankings)
├── Enables: "Texas 62.3% vs UCLA on a neutral field"
└── PEAR shows IDENTICAL win probabilities regardless of matchup context
```

**Why Layer 2 matters:** EvanMiya (college basketball) proved that Bayesian performance ratings with informed priors outperform static composites, especially early in the season when sample sizes are small. College baseball has the SAME small-sample problem Ryan identified: 56-game season, ~15 starts per pitcher. A Bayesian framework starts with informed priors (previous season, conference adjustment, transfer portal inflow) and updates with each game.

**Why Layer 3 matters:** PEAR's win probabilities don't change based on matchup context. The same team shows the same odds regardless of opponent. Our logistic model produces context-aware probabilities. Tim noted this gap explicitly (claim #24-25): "the probabilities on the right hand side are the exact same probabilities."

### V0 Demonstration: "Here are PEAR's ratings, here are ours, here's WHY ours are better"

```
┌──────────────────────────────────────────────────────────────────────┐
│  V0 VALIDATION OUTPUT                                                │
│                                                                      │
│  RANKINGS COMPARISON (2026 season through Mar 30):                   │
│  ─────────────────────────────────────────────────                   │
│  Rank  Team          PEAR  FSBB  Δ   FSBB_CI          Notes         │
│   1    UCLA           1     1    0   [1-2, 95%]       ──            │
│   2    Texas          2     2    0   [1-3, 95%]       ──            │
│   3    Miss. St.      3     4   +1   [2-6, 95%]       SOS penalty   │
│   4    Georgia Tech  12     3   -9   [2-5, 95%]       Bayesian lift │
│  ...                                                                 │
│  Spearman ρ: 0.94   |  MAE: 3.2 ranks  |  Corr: HIGH               │
│                                                                      │
│  ALGORITHMIC ADVANTAGES DEMONSTRATED:                                │
│  1. Uncertainty quantification: 95% CI on every rank                 │
│  2. Bayesian shrinkage: early-season ranks more conservative         │
│  3. Context-aware matchup: Texas 62.3% vs UCLA (PEAR: both 50%?)    │
│  4. Luck metric: teams over/underperforming Pythagorean baseline     │
│                                                                      │
│  HISTORICAL BACKTEST (2024-2025):                                    │
│  Win prediction accuracy: FSBB 58.2% | PEAR ~53%*                   │
│  (* estimated from PEAR's static probabilities)                      │
│  Brier score: FSBB 0.228 | Baseline 0.250                           │
└──────────────────────────────────────────────────────────────────────┘
```

### Metrics Computed

| Metric | Formula | Layer | Differentiation |
|--------|---------|-------|----------------|
| RS/G, RA/G | runs / games | 1 | Table stakes |
| Pythag W% | RS^exp / (RS^exp + RA^exp) | 1 | Table stakes (exp ≈ 1.83 for college) |
| Luck | Actual W% − Pythag W% | 1 | PEAR doesn't expose this |
| SOS | Avg opp Pythag W% (iterative) | 1 | Comparable to PEAR |
| Adj RS/G | RS/G × (league_avg / opp_RA) | 1 | SOS-adjusted offense |
| Adj RA/G | RA/G × (league_avg / opp_RS) | 1 | SOS-adjusted pitching |
| Power Rating | Adj_RS − Adj_RA | 1 | Comparable to PEAR |
| Elo | 1500 + margin-of-victory adjusted | 1 | PEAR has Elo but no MOV adjustment |
| **Bayesian posterior** | Prior × likelihood(game_results) | **2** | **PEAR has nothing like this** |
| **Rank CI** | 95% credible interval on ranking | **2** | **PEAR shows point estimates only** |
| **Win probability** | logistic(features) | **3** | **PEAR shows same odds for every matchup** |
| **Expected W-L** | Sum of per-game win probs | **3** | Enables "luck" detection |

### Pythagorean Exponent Calibration

The exponent 1.83 is commonly cited for college baseball, but it needs empirical validation. With 3 seasons of historical data:

```python
from scipy.optimize import minimize_scalar

def pythag_error(exp, games):
    """Find optimal Pythagorean exponent for college baseball."""
    errors = []
    for team in games:
        rs, ra, wins, losses = team
        pythag = rs**exp / (rs**exp + ra**exp)
        actual = wins / (wins + losses)
        errors.append((pythag - actual)**2)
    return sum(errors) / len(errors)

# Expect result in range 1.75-1.90 for college (BBCOR bat effects)
result = minimize_scalar(pythag_error, bounds=(1.5, 2.2), args=(historical_games,))
```

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                       V0 SYSTEM (fsbb/)                         │
│                                                                 │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │ scraper/  │    │ models/       │    │ cli.py               │  │
│  │           │    │               │    │                      │  │
│  │ ncaa.py   │──▶│ ratings.py    │──▶│ $ fsbb rank          │  │
│  │ pear.py   │    │ ├─ pythag    │    │ $ fsbb matchup A B   │  │
│  │ clean.py  │    │ ├─ bayesian  │    │ $ fsbb validate-pear │  │
│  │           │    │ ├─ elo       │    │ $ fsbb backtest      │  │
│  │           │    │ └─ win_prob  │    │ $ fsbb export json   │  │
│  │           │    │               │    │                      │  │
│  │           │    │ matchup.py    │    │                      │  │
│  │           │    │ backtest.py   │    │                      │  │
│  └──────────┘    └──────────────┘    └──────────────────────┘  │
│       │               │                       │                 │
│       ▼               ▼                       ▼                 │
│  ┌──────────────────────────────────────────────────────┐      │
│  │               data/fsbb.db (SQLite)                   │      │
│  │  teams | games | team_ratings | priors | pear_bench   │      │
│  └──────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

### Module Breakdown

```
fsbb/                              # ForgeStream Baseball
├── __init__.py
├── __main__.py                    # CLI entry (Click)
├── scraper/
│   ├── __init__.py
│   ├── ncaa.py                    # NCAA API scraper (httpx + henrygd/ncaa-api)
│   ├── pear.py                    # PEAR ratings scraper (playwright)
│   └── clean.py                   # Entity resolution, dedup, anomaly detection
├── models/
│   ├── __init__.py
│   ├── ratings.py                 # Pythagorean, SOS, adj runs, Elo
│   ├── bayesian.py                # Bayesian prior-posterior update model
│   ├── win_prob.py                # Logistic regression win probability
│   ├── matchup.py                 # Head-to-head predictions with CI
│   └── backtest.py                # Historical validation framework
├── db.py                          # SQLite connection + schema
├── schemas.py                     # Pydantic models
└── export.py                      # JSON/CSV output + PEAR comparison
```

### Data Model

```sql
CREATE TABLE teams (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    conference TEXT NOT NULL,
    division TEXT NOT NULL DEFAULT 'D1'
);

CREATE TABLE team_aliases (
    alias TEXT PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id)
);

CREATE TABLE games (
    id TEXT PRIMARY KEY,              -- NCAA game ID
    date TEXT NOT NULL,
    season INTEGER NOT NULL,          -- for historical backtesting
    home_team_id INTEGER REFERENCES teams(id),
    away_team_id INTEGER REFERENCES teams(id),
    home_runs INTEGER NOT NULL,
    away_runs INTEGER NOT NULL,
    home_hits INTEGER,
    away_hits INTEGER,
    home_errors INTEGER,
    away_errors INTEGER,
    innings INTEGER DEFAULT 9,
    home_starter TEXT,                -- V1: pitcher name
    away_starter TEXT,
    neutral_site BOOLEAN DEFAULT FALSE,
    conference_game BOOLEAN,
    source TEXT NOT NULL,
    scraped_at TEXT NOT NULL
);

CREATE TABLE team_ratings (
    team_id INTEGER REFERENCES teams(id),
    as_of_date TEXT NOT NULL,
    season INTEGER NOT NULL,
    -- Layer 1: Foundation
    power_rating REAL,
    adj_runs_scored REAL,
    adj_runs_allowed REAL,
    sos REAL,
    elo REAL,
    pythag_pct REAL,
    luck REAL,                        -- actual_pct - pythag_pct
    -- Layer 2: Bayesian
    prior_mean REAL,                  -- prior from last season
    posterior_mean REAL,              -- updated with current season
    posterior_std REAL,               -- uncertainty
    rank_ci_lower INTEGER,           -- 95% CI lower rank
    rank_ci_upper INTEGER,           -- 95% CI upper rank
    -- Metadata
    games_played INTEGER,
    PRIMARY KEY (team_id, as_of_date)
);

CREATE TABLE priors (
    team_id INTEGER REFERENCES teams(id),
    season INTEGER NOT NULL,
    prior_mean REAL,                  -- from previous season performance
    prior_std REAL,                   -- uncertainty (wider for teams with transfers)
    transfer_adjustment REAL,         -- net talent gain/loss from portal
    PRIMARY KEY (team_id, season)
);

CREATE TABLE pear_benchmark (
    team_id INTEGER REFERENCES teams(id),
    scraped_date TEXT,
    power_rating REAL,
    net INTEGER, net_score REAL,
    sos INTEGER, sor INTEGER,
    elo REAL, rpi INTEGER,
    prr INTEGER, rqi INTEGER
);
```

### API Contract (V1 — FastAPI)

```
GET  /api/v1/ratings                          → full ranked table with CIs
GET  /api/v1/ratings?top=25                   → top N
GET  /api/v1/ratings?conference=SEC           → filtered
GET  /api/v1/teams/{team}                     → single team detail
GET  /api/v1/teams/{team}/games               → game log
GET  /api/v1/matchup?home={A}&away={B}        → win prob + CI + features
GET  /api/v1/matchup?home={A}&away={B}&starter_home={P1}&starter_away={P2}  → V1
GET  /api/v1/validate/pear                    → rank correlation report
GET  /api/v1/backtest?season=2025             → historical accuracy
GET  /api/v1/health                           → scraper status, freshness
```

### Output Format (Superset of PEAR)

```json
{
  "team": "UCLA",
  "conference": "Big Ten",
  "record": "25-3",
  "power_rating": 7.41,
  "adj_runs_scored": 8.23,
  "adj_runs_allowed": 0.82,
  "run_differential": 7.41,
  "sos": 33,
  "elo": 1775.2,
  "pythag_pct": 0.956,
  "actual_pct": 0.893,
  "luck": -0.063,
  "rank": 1,
  "rank_ci": [1, 2],
  "posterior_std": 0.41,
  "games_played": 28,
  "pear_rank": 1,
  "rank_diff": 0,
  "last_updated": "2026-03-31T06:00:00Z"
}
```

### Dependency List

```toml
[project]
name = "fsbb"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "httpx>=0.27",           # Async HTTP for NCAA API
    "pydantic>=2.0",         # Schema validation
    "click>=8.1",            # CLI
    "tabulate>=0.9",         # Terminal tables
    "scipy>=1.14",           # Pythagorean exponent optimization + logistic regression
]

[project.optional-dependencies]
scrape = ["playwright>=1.45"]       # PEAR JS rendering
serve = ["fastapi>=0.115", "uvicorn>=0.32"]
```

No ML frameworks. `scipy` is the only addition beyond V0 — gives us `minimize_scalar` for exponent calibration and `expit`/`logit` for win probability. The Bayesian update is conjugate normal-normal: pure math, no libraries needed.

### Build Timeline (48-72 hours)

| Hour | Task | Output |
|------|------|--------|
| 0-4 | Project setup, schemas, SQLite, team alias table | `db.py`, `schemas.py` |
| 4-12 | NCAA scraper (henrygd/ncaa-api) | Full DI season in DB |
| 12-14 | PEAR import (existing JSON) | Benchmark loaded |
| 14-18 | Cleaning pipeline | Entity resolution, <1% unresolved |
| 18-24 | Layer 1: Pythag, SOS, Elo, adj runs, power | `ratings.py` |
| 24-30 | Layer 2: Bayesian prior-posterior model | `bayesian.py` |
| 30-36 | Layer 3: Logistic win probability | `win_prob.py` |
| 36-42 | CLI (rank, matchup, validate-pear, backtest) | `__main__.py` |
| 42-48 | PEAR validation, historical backtest, tuning | ρ > 0.90, accuracy > 55% |
| 48-56 | Demo preparation, export, docs | Ready for Ryan |

---

## 3. Differentiation Layer (V1)

### 3.1 Starting Pitcher Adjustment

**The gap:** PEAR shows identical win probabilities regardless of starter. Tim (claim #24-25): "he just doesn't take into account like player lineups, individual player stats, pitching stats."

**Bayesian pitcher model:**

```python
class PitcherModel:
    """Bayesian starting pitcher adjustment.

    Prior: league-average ERA (based on division + conference)
    Likelihood: observed ERA from game starts
    Posterior: updated ERA estimate with uncertainty

    With 10+ starts, posterior converges.
    With 1-3 starts, prior dominates (prevents overreaction to small samples).
    """

    def pitcher_adjustment(self, pitcher: PitcherRating) -> float:
        """Returns expected runs above/below average for this starter.

        With 15 starts and 3.20 ERA in SEC (league avg 4.80):
        → Expected to save ~1.6 runs vs average starter
        → Shifts game win probability by ~12-15%
        """
        weight = min(pitcher.games_started / 15.0, 1.0)  # Full weight at 15 starts
        blended_era = (
            weight * pitcher.adj_era +
            (1 - weight) * pitcher.conference_avg_era
        )
        return (pitcher.conference_avg_era - blended_era) / 9.0  # RAA per 9 innings
```

**Data source:** NCAA box scores list starting pitchers. Cross-reference player stats pages for ERA, IP, K, BB.

### 3.2 Monte Carlo Game Simulation

Tim (claim #66): "This has like simulations." For college baseball specifically:

```python
def simulate_game(home: TeamRating, away: TeamRating,
                  home_pitcher: PitcherRating | None = None,
                  away_pitcher: PitcherRating | None = None,
                  n_sims: int = 10_000) -> SimResult:
    """
    Per simulation:
    1. Draw home_runs ~ NegBinomial(adj_rs * pitcher_factor, overdispersion)
    2. Draw away_runs ~ NegBinomial(adj_rs * pitcher_factor, overdispersion)
    3. If tied: simulate extra innings (geometric distribution)
    4. Record: winner, total_runs, margin

    Returns: win_prob, total_dist, over_under_pct, run_line_coverage

    Why NegBinomial not Poisson:
    College baseball is more variable than MLB (wider talent spread,
    BBCOR bat effects, weather). NegBinomial captures overdispersion.
    """
```

Compute: 10K sims × ~40 daily games = 400K sims. Sub-second on any machine.

### 3.3 College-Specific Run Expectancy Tables

MLB RE24 matrices don't transfer to college (BBCOR bats, variable park dimensions, different talent distributions, higher R/G environment ~5.5 vs MLB ~4.5).

Build from 2024-2026 NCAA PBP data (~25K games via `baseballr`):

```
               0 out    1 out    2 out
Bases empty    0.58     0.31     0.12     ← Higher than MLB (more offense)
Runner 1st    0.98     0.61     0.27
Runner 2nd   1.24     0.77     0.37
1st & 2nd    1.56     1.02     0.49
Runner 3rd   1.51     1.05     0.41
1st & 3rd    1.92     1.30     0.57
2nd & 3rd    2.18     1.53     0.64
Loaded       2.49     1.74     0.82

(Provisional — must be computed from actual college PBP data)
```

### 3.4 Conference Strength Normalization

Going 25-5 in the SEC ≠ going 25-5 in the MEAC.

**Method:** Iterative Bayesian SOS:
1. Initialize all teams at 0.500
2. Compute win% against opponents' ratings
3. Recompute opponent ratings from updated values
4. Iterate until convergence (5-10 iterations)
5. Conference_strength = mean(member_ratings)
6. Adjust: team_metric × (league_avg / conference_avg)

### 3.5 The Equation Interface

Tim's ForgeStream equation — originally for trade augmentation and alpha generation (claim #75) — plugs in as a prediction overlay:

```python
class AlphaModel(Protocol):
    """Interface between rating engine and alpha generation model."""

    def predict(
        self,
        home: TeamRating,
        away: TeamRating,
        market_line: float | None = None,
    ) -> AlphaPrediction:
        """
        Returns:
          - home_win_prob, away_win_prob
          - expected_total (combined runs)
          - confidence (model certainty)
          - edge (model_prob - implied_prob, if market_line given)
          - kelly_fraction (optimal bet sizing)
        """

class AlphaPrediction(BaseModel):
    home_win_prob: float
    away_win_prob: float
    expected_total: float
    confidence: float
    edge: float | None = None           # positive = value bet
    kelly_fraction: float | None = None
    features_used: list[str] = []
```

**RL integration** (Mergim, claims #8-9: "plug in these equations into a reinforcement learning AI agent... it essentially learns on the market"):

```
Rating Engine → AlphaModel → RL Agent → Betting Signal
     ▲                           │
     │                           ▼
   Data (daily)            Outcomes (game results)
                           Market feedback (line movement)
```

---

## 4. Scale Path: V1 → V3

### V1: Team + Pitcher Ratings with Algorithm Differentiation (2-4 weeks)

| Component | New Work | Build Cost |
|-----------|----------|-----------|
| Starting pitcher Bayesian model | Pitcher stats table + prior/posterior | 2-3 days |
| Monte Carlo engine | NegBinomial sampling, extra innings | 1-2 days |
| Conference normalization | Extension of SOS algorithm | 1 day |
| FastAPI endpoints | Already in ForgeStream deps | 2 days |
| Backtest framework | 2024-2025 historical validation | 2 days |

**Infra:** SQLite still. $0 hosting.

### V2: Player-Level Metrics + Transfer Portal (4-8 weeks)

| New Capability | Data Source | Difficulty |
|---------------|------------|-----------|
| wOBA (weighted on-base) | Box scores (H, 2B, 3B, HR, BB, HBP) | Medium — need college-specific linear weights |
| wRC+ (park/league adjusted) | wOBA + park factors | Medium — park factor estimation needs multi-year data |
| ERA+ / FIP | Pitcher stats (K, BB, HR, IP) | Low — standard formulas |
| Transfer portal projections | Historical transfer outcomes + new context | Hard — novel model, our key differentiator |

**Infra changes:** SQLite → PostgreSQL (concurrent writes). Player tables. ~500 MB. $20-40/mo VPS.

### V3: Pitch Tracking + Betting Model (3-6 months)

| New Capability | Source | Difficulty |
|---------------|--------|-----------|
| Exit velocity, launch angle | 643 Charts API | Medium |
| Expected stats (xBA, xwOBA) | Physics model on batted ball data | Hard |
| Automated betting model | RL agent on historical predictions | Hard |
| Real-time market ingestion | Sportsbook odds scraping | Medium |

**Infra changes:** Pitch event store (millions of rows). RunPod GPU for RL training. $100-200/mo.

### Scale Summary

```
V0 (48-72h)        V1 (2-4w)          V2 (4-8w)           V3 (3-6mo)
────────────────────────────────────────────────────────────────────────
308 teams           + pitchers         + all DI players     + physics
3-layer model       + Monte Carlo      + wOBA/wRC+/WAR      + xBA/xwOBA
Bayesian rankings   + NegBinom sim     + transfer portal     + betting RL
CLI only            + FastAPI          + web dashboard        + API-first
SQLite              SQLite             PostgreSQL             PG + events
$0                  $0                 $20-40/mo              $100-200/mo
```

---

## 5. Tech Stack

### Core

| Layer | Tech | Version | Rationale |
|-------|------|---------|-----------|
| Language | Python | 3.12+ | ForgeStream is Python; Ryan can "vibe code" |
| Package mgr | uv | latest | Already used by ForgeStream |
| HTTP | httpx | 0.27+ | Async, modern |
| Scraping | playwright | 1.45+ | JS rendering (PEAR) |
| Validation | pydantic | 2.x | Already in ForgeStream |
| DB (V0-V1) | SQLite | 3.45+ | Zero-config, single file |
| DB (V2+) | PostgreSQL | 16+ | psycopg already in deps |
| CLI | click | 8.1+ | Standard, simple |
| Math | scipy | 1.14+ | Optimization, logistic, stats |
| API (V1+) | FastAPI | 0.115+ | Already in deps |
| Server | uvicorn | 0.32+ | Already in deps |

### Not Needed Yet

| Tech | When | Why Not Now |
|------|------|-------------|
| pandas/numpy | V2 | V0 is pure aggregation |
| scikit-learn | V2 | Logistic regression from scipy suffices |
| PyTorch | V3 | RL agent |
| Redis | V2 | SQLite fast enough |
| Docker | V1 | Dev locally first |
| React | V2 | CLI + JSON is V0 |

### Monorepo — `fsbb/` Inside ForgeStream

```
forgestream/
├── forgestream/          # Existing: meeting intelligence
├── fsbb/                 # NEW: baseball analytics
│   ├── scraper/
│   ├── models/
│   │   ├── ratings.py
│   │   ├── bayesian.py
│   │   ├── win_prob.py
│   │   ├── matchup.py
│   │   └── backtest.py
│   ├── db.py
│   └── __main__.py
├── data/
│   ├── pear/             # Already scraped
│   └── fsbb.db           # V0 database
└── pyproject.toml
```

### Hosting Cost

| Tier | Infra | Monthly |
|------|-------|---------|
| V0 | Local (macOS/Linux) | $0 |
| V1 | + optional VPS for cron | $0-5 |
| V2 | VPS + managed Postgres | $20-40 |
| V3 | + RunPod GPU (occasional) | $100-200 |

Tim (claim #60): "I'm a big fan of not trying to sink in any money into anything." V0-V1 costs $0.

---

## Appendix A: PEAR Data Already Available

- `data/pear/pear_ratings.json` — 308 teams × 11 fields
- `data/pear/pear_ratings.csv` — CSV format
- `data/pear/teams/team_Vanderbilt.json` — ~140+ fields per team including:
  - Batting: BA, OBP, SLG, OPS, wOBA, wRAA, ISO, wRC+, BABIP
  - Pitching: ERA, WHIP, FIP, K/9, BB/9, K/BB, LOB%
  - Composite: oWAR, pWAR, fWAR, Pythag, Elo, Rating, KPI
  - Killshot metrics, bubble analysis, Q1-Q4 records, NET composite
  - Remaining schedule projections

### Appendix B: Key Competitors

| Platform | Player Stats | Pitch Track | Team Ratings | Transfer | API | Price |
|----------|-------------|-------------|-------------|----------|-----|-------|
| 64 Analytics | Yes (box-score) | No | Yes | Yes (primary) | No | $13-5500 |
| PEARatings | No | No | Yes (NET) | No | No | Free |
| 6-4-3 Charts | Yes (TrackMan) | Yes | Yes (DSR) | Partial | Yes | Enterprise |
| EvanMiya (bball) | Yes (Bayesian) | N/A | Yes | Yes | No | $180/yr |
| **FSBB (ours)** | V2 | V3 | Yes (Bayesian) | V2 | Yes | Free+premium |

### Appendix C: Open Questions

1. **643 Charts API pricing** — truly free? Rate limits?
2. **Pythagorean exponent** — calibrate from historical data (expect 1.75-1.90)
3. **Historical depth** — how many seasons for RL training?
4. **Legal** — NCAA data commercial use ToS?
5. **Tim's equation** — current state, I/O interface?
6. **College baseball betting market** — which books? How liquid?
7. **PEAR's Killshot metric** — novel stat worth studying/replicating?
