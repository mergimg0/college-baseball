# ForgeStream Baseball — Technical Architecture
**Date:** 2026-03-30 | **Source:** Ryan McCarthy call (510 claims) + market research
**Author:** Mergim (Architecture) + Ryan (Domain) | **Status:** DRAFT v1

---

## Design Principles (Derived from Call)

1. **Data-first** — "Starting at the data first seems like a good call" (Ryan, REQ #18)
2. **Team before player** — "Keep it simple... team metrics before player metrics" (Mergim, REQ #24-25)
3. **Runs are the unit** — "Runs scored and runs allowed" as atoms (Mergim, REQ #26-27)
4. **Clean or die** — "Getting the data right is crucial so the model doesn't hallucinate" (Ryan, REQ #20)
5. **Pipeline is the moat** — "Figuring out that data pipeline is the most important piece" (Mergim, REQ #21)
6. **Vibe-code accessible** — "I can see if I can just vibe code one right now" (Ryan, REQ #30)
7. **Prove legs first** — "What would a V0 look like that convinces Ryan this has legs" (Ryan, REQ #9)

---

## 1. Data Pipeline Architecture

### Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        DATA PIPELINE                                 │
│                                                                      │
│  SCRAPE           CLEAN            STORE          MODEL      SERVE   │
│  ┌─────┐        ┌──────┐        ┌──────┐       ┌──────┐   ┌──────┐ │
│  │NCAA │──raw──▶│Entity│──clean▶│SQLite│──feat▶│Rating│──▶│ CLI  │ │
│  │ API │  JSON  │Resol.│  CSV   │  DB  │ vecs  │Engine│   │  +   │ │
│  ├─────┤        │Dedup │        ├──────┤       │      │   │ JSON │ │
│  │PEAR │──raw──▶│Anomal│──────▶│      │       │      │   │ API  │ │
│  │Scrpr│  JSON  │Detect│        │      │       │      │   └──────┘ │
│  ├─────┤        │      │        │      │       │      │            │
│  │643  │──raw──▶│Norm. │──────▶│      │       │      │            │
│  │ API │  JSON  │      │        │      │       │      │            │
│  └─────┘        └──────┘        └──────┘       └──────┘            │
│     ▲               ▲                              ▲                │
│     │               │                              │                │
│  [cron]      [ForgeStream AI]              [The Equation]           │
│  daily         entity resol.               alpha generation         │
└──────────────────────────────────────────────────────────────────────┘
```

### Stage 1: Scraping

#### Source: NCAA Stats (Primary)

| Attribute | Value |
|-----------|-------|
| **URL** | `stats.ncaa.org` |
| **Access method** | `henrygd/ncaa-api` (unofficial JSON proxy) |
| **Rate limit** | 5 req/s (documented) |
| **Data available** | Box scores, game logs, player stats, schedules (DI/DII/DIII) |
| **Format in** | JSON (from API proxy) |
| **Format out** | `NcaaGameRecord` (Pydantic model, see schema below) |
| **Python packages** | `collegebaseball` (pip), `CollegeBaseballStatsPackage` |
| **Volume** | ~8,400 DI games/season × ~30 fields = ~252K records |
| **Scrape time** | ~28 min at 5 req/s for full DI season |
| **Failure mode** | NCAA website changes HTML structure → parser breaks |
| **Fallback** | Cache last-good scrape; alert on >10% parse failure rate |

#### Source: PEAR Ratings (Benchmark)

| Attribute | Value |
|-----------|-------|
| **URL** | `pearatings.com` |
| **Access method** | Playwright headless browser (dynamic JS rendering) |
| **Data available** | 308 DI teams: power_rating, NET, net_score, SOS, SOR, ELO, RPI, PRR, RQI |
| **Volume** | 308 rows × 11 fields (already scraped: `data/pear/pear_ratings.json`) |
| **Role** | Validation benchmark only — compare our output to theirs |
| **Risk** | "If PEAR goes behind a paywall tomorrow" (Mergim, claim #168) |
| **Mitigation** | Build own pipeline from NCAA source; PEAR is comparison only |

#### Source: 643 Charts API (V1+)

| Attribute | Value |
|-----------|-------|
| **URL** | `643charts.com/api` |
| **Access method** | REST API (documented, requires API key) |
| **Data available** | TrackMan data: exit velocity, launch angle, spin rate, pitch movement |
| **Coverage** | 650+ DI programs (where TrackMan is installed) |
| **Pricing** | Unknown — "I believe that's free" (Mergim, claim #48), needs verification |
| **Format** | JSON |
| **Role** | Physics-level data for V2+ differentiation |
| **Risk** | May require institutional agreement; "I don't think a lot of people are using that" (Mergim, claim #42) |

#### Scraper Implementation

**Technology:** Python 3.12 + `httpx` (async) + `playwright` (for JS-rendered pages)

```python
# Core scraper interface
from pydantic import BaseModel
from datetime import date

class NcaaGameRecord(BaseModel):
    game_id: str                # NCAA game identifier
    date: date
    home_team: str              # Normalized team name
    away_team: str
    home_runs: int
    away_runs: int
    home_hits: int
    away_hits: int
    home_errors: int
    away_errors: int
    innings: int                # 9 default, extras tracked
    home_starter: str | None    # V1: starting pitcher name
    away_starter: str | None
    attendance: int | None
    neutral_site: bool
    conference_game: bool
    division: str               # "D1", "D2", "D3"
    source: str                 # "ncaa", "pear", "643"

class TeamSeason(BaseModel):
    team_name: str              # Canonical name
    aliases: list[str]          # ["UNC", "North Carolina", "N. Carolina"]
    conference: str
    division: str
    games: list[NcaaGameRecord]
    runs_scored: int            # Aggregate
    runs_allowed: int           # Aggregate
    wins: int
    losses: int
```

**Schedule:**
- Full scrape: Once at season start (~28 min for DI)
- Incremental: Daily at 06:00 UTC (picks up yesterday's games)
- PEAR comparison: Weekly Sunday scrape

**What we automate vs manual validation:**

| Task | Automated | Manual |
|------|-----------|--------|
| Scraping NCAA box scores | ✅ | |
| Entity resolution (team names) | ✅ (fuzzy match + alias table) | First-pass audit |
| Detecting missing games | ✅ (schedule vs results diff) | |
| Cross-referencing sources | ✅ (NCAA ↔ PEAR team counts) | |
| Handling edge cases (suspended games, forfeits) | | ✅ |
| Validating new team name mappings | | ✅ |
| Approving anomaly flags (15-0 blowouts, errors) | | ✅ (spot check) |

### Stage 2: Cleaning

**This is where ForgeStream's AI stack fits in.** The cleaning layer is the competitive moat.

**Core cleaning problems (from research):**

1. **Entity resolution** — NCAA uses inconsistent team names:
   - "UNC" / "North Carolina" / "North Carolina-Chapel Hill" / "N. Carolina"
   - Solution: Canonical name table (308 DI teams) + fuzzy matching (Levenshtein ≤ 2)
   - ForgeStream contribution: Domain knowledge extraction encodes how scouts/coaches refer to teams

2. **Deduplication** — Same game reported by both teams, sometimes with discrepancies:
   - Solution: Match on (date, home_team, away_team) → flag score mismatches
   - Threshold: If runs differ by >0, log warning, prefer home team's report

3. **Anomaly detection** — Stats entered by unpaid student SIDs:
   - NCAA acknowledged "uptick in incorrect statistics being reported"
   - Solution: Z-score outlier detection on per-game stats; flag games where RS+RA > 40 or IP ≠ innings
   - ForgeStream contribution: AI-powered plausibility checking against historical baselines

4. **Missing data** — ~10-20% of DI games have incomplete play-by-play:
   - V0 approach: Skip PBP entirely, use box-score aggregates only
   - V1+: Track missingness rate per team; weight ratings by data completeness

**Technology:** Python, custom cleaning pipeline with Pydantic validators

```python
class CleaningReport(BaseModel):
    total_games_scraped: int
    games_after_dedup: int
    entity_resolutions: int      # Name mismatches corrected
    anomalies_flagged: int       # Requires human spot-check
    missing_data_rate: float     # % games with incomplete fields
    source_agreement_rate: float # % where NCAA ↔ PEAR agree
```

**Estimated volumes:**

| Metric | DI Only (V0) | All Divisions (V2+) |
|--------|-------------|---------------------|
| Teams | 308 | ~1,700 |
| Games/season | ~8,400 | ~24,000 |
| Records (games × fields) | ~252K | ~720K |
| Storage (SQLite) | ~50 MB | ~150 MB |
| Scrape time | ~28 min | ~80 min |
| Clean time | ~5 min | ~15 min |

### Stage 3: Storage

**V0 storage: SQLite.** Single file, zero ops, portable, queryable.

**Rationale:** Ryan said "I can see if I can just vibe code one right now" — SQLite works with every language, needs no server, deploys as a single file. At 308 teams × 56 games, we're well within SQLite's comfort zone (~50 MB). PostgreSQL is overkill until we hit V2 scale.

**Schema:**

```sql
-- Core tables
CREATE TABLE teams (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,        -- Canonical name ("North Carolina")
    conference TEXT NOT NULL,
    division TEXT NOT NULL DEFAULT 'D1'
);

CREATE TABLE team_aliases (
    alias TEXT PRIMARY KEY,           -- "UNC", "N. Carolina", etc.
    team_id INTEGER REFERENCES teams(id)
);

CREATE TABLE games (
    id TEXT PRIMARY KEY,              -- NCAA game ID
    date TEXT NOT NULL,               -- ISO 8601
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
    source TEXT NOT NULL,             -- "ncaa", "manual"
    scraped_at TEXT NOT NULL          -- ISO 8601 timestamp
);

-- Computed / model output
CREATE TABLE team_ratings (
    team_id INTEGER REFERENCES teams(id),
    as_of_date TEXT NOT NULL,         -- Rating valid for this date
    power_rating REAL,                -- Our computed power rating
    adj_runs_scored REAL,             -- SOS-adjusted RS/game
    adj_runs_allowed REAL,            -- SOS-adjusted RA/game
    sos REAL,                         -- Strength of schedule
    elo REAL,                         -- Elo rating
    win_pct REAL,                     -- Actual win %
    pythag_pct REAL,                  -- Pythagorean win %
    PRIMARY KEY (team_id, as_of_date)
);

-- PEAR benchmark (for validation)
CREATE TABLE pear_ratings (
    team_id INTEGER REFERENCES teams(id),
    scraped_date TEXT,
    power_rating REAL,
    net INTEGER,
    net_score REAL,
    sos INTEGER,
    sor INTEGER,
    elo REAL,
    rpi INTEGER,
    prr INTEGER,
    rqi INTEGER
);
```

**Migration path:** When we outgrow SQLite (V2: player-level data, concurrent writes, API serving):
- Export SQLite → PostgreSQL via `pgloader`
- ForgeStream already depends on `psycopg` — the connection code is ready
- Timeline: When write concurrency becomes an issue (multiple scrapers + API serving)

### Stage 4: Modeling (see Section 2 for V0, Section 3 for V1+)

### Stage 5: Serving

**V0:** CLI output + JSON file
**V1:** FastAPI endpoint (ForgeStream already has `fastapi` + `uvicorn` in deps)
**V2:** Web dashboard (React or plain HTML/JS — keep it simple)

---

## 2. V0 System Design — "Prove It Has Legs"

**Goal:** The simplest system that produces team ratings from scraped data, buildable in 48-72 hours.

### What V0 Computes

| Metric | Formula | What It Tells You |
|--------|---------|-------------------|
| **RS/G** | runs_scored / games | Raw offensive output |
| **RA/G** | runs_allowed / games | Raw pitching/defense |
| **Pythagorean Win%** | RS^1.83 / (RS^1.83 + RA^1.83) | Expected win rate from run differential |
| **Luck Factor** | Actual W% − Pythag W% | Over/underperformance |
| **SOS** | Avg opponent Pythag W% | Schedule difficulty |
| **Adj RS/G** | RS/G × (league_avg_RS / avg_opp_RA) | Opponent-adjusted offense |
| **Adj RA/G** | RA/G × (league_avg_RA / avg_opp_RS) | Opponent-adjusted pitching |
| **Power Rating** | Adj RS/G − Adj RA/G | Net run differential, adjusted |
| **Win Probability** | logistic(power_diff × k) | Head-to-head prediction |

Note: Exponent 1.83 is the empirically-derived Pythagorean exponent for college baseball (differs from MLB's 1.83 — needs validation against historical data, may be closer to 1.80-1.85 for college).

### Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    V0 SYSTEM                             │
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────┐  │
│  │ scraper/ │    │ models/  │    │    cli.py         │  │
│  │          │    │          │    │                    │  │
│  │ ncaa.py  │──▶│ratings.py│──▶│  $ python -m fsbb  │  │
│  │ pear.py  │    │          │    │    rank            │  │
│  │ clean.py │    │ matchup  │    │    matchup TEX UNC │  │
│  │          │    │   .py    │    │    validate-pear   │  │
│  └──────────┘    └──────────┘    └──────────────────┘  │
│       │               │               │                 │
│       ▼               ▼               ▼                 │
│  ┌──────────────────────────────────────────┐           │
│  │          data/fsbb.db (SQLite)           │           │
│  │  teams | games | team_ratings | pear     │           │
│  └──────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────┘
```

### Module Breakdown

```
fsbb/                           # ForgeStream Baseball (the V0 package)
├── __init__.py
├── __main__.py                 # CLI entry point
├── scraper/
│   ├── __init__.py
│   ├── ncaa.py                 # NCAA stats scraper (httpx + henrygd/ncaa-api)
│   ├── pear.py                 # PEAR ratings scraper (playwright)
│   └── clean.py                # Entity resolution, dedup, anomaly detection
├── models/
│   ├── __init__.py
│   ├── ratings.py              # Pythagorean, SOS, adjusted runs, power rating
│   └── matchup.py              # Head-to-head win probability
├── db.py                       # SQLite connection + schema migration
├── schemas.py                  # Pydantic models (NcaaGameRecord, TeamSeason, etc.)
└── export.py                   # JSON/CSV output, PEAR comparison report
```

### CLI Interface

```bash
# Scrape today's games
$ python -m fsbb scrape --date 2026-03-30

# Full season scrape (takes ~30 min)
$ python -m fsbb scrape --full --season 2026

# Compute/update ratings
$ python -m fsbb rate

# Show ranked table (top 25)
$ python -m fsbb rank --top 25

# Output (matches PEAR's format for comparison):
#  Rank  Team              PwrRat   AdjRS   AdjRA   SOS   W-L     Pythag   Luck
#  1     UCLA               7.41    8.23    0.82    33   25-3     .956    -.024
#  2     Texas              6.58    7.89    1.31     8   24-4     .937    -.017
#  3     Mississippi St.    6.55    7.11    0.56    66   23-5     .959    -.032
#  ...

# Head-to-head matchup
$ python -m fsbb matchup "Texas" "UCLA"
# Texas vs UCLA: UCLA 58.3% | Texas 41.7%
# Power diff: 0.83 (UCLA advantage)
# Note: Does not account for starting pitchers (V1 feature)

# Validate against PEAR
$ python -m fsbb validate-pear
# Rank correlation (Spearman): 0.94
# Mean absolute rank diff: 3.2 positions
# Largest disagreement: Georgia Tech (us: #8, PEAR: #12)
# Verdict: WITHIN REASONABLE RANGE ✓

# Export
$ python -m fsbb export --format json --output ratings.json
$ python -m fsbb export --format csv --output ratings.csv
```

### API Contract (V1 — FastAPI, after CLI is proven)

```
GET  /api/v1/teams                    → list of all teams with current ratings
GET  /api/v1/teams/{team}             → single team detail
GET  /api/v1/teams/{team}/games       → game log with per-game stats
GET  /api/v1/ratings                  → full ranked table (JSON)
GET  /api/v1/ratings?top=25           → top N
GET  /api/v1/matchup?home={A}&away={B} → win probability
GET  /api/v1/health                   → scraper status, last update, data freshness
```

### Data Model

PEAR's output format (our validation target — 308 teams, 11 fields each):
```json
{
  "Team": "UCLA",
  "power_rating": 7.36,
  "NET": 1,
  "net_score": 0.997,
  "SOS": 33,
  "SOR": 1,
  "Conference": "Big Ten",
  "ELO": 1772.65,
  "RPI": 3,
  "PRR": 1,
  "RQI": 1
}
```

Our V0 output format (superset — we compute everything PEAR does plus more):
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
  "pear_rank": 1,
  "rank_diff": 0,
  "last_updated": "2026-03-30T06:00:00Z"
}
```

### Dependency List (V0)

```toml
[project]
name = "fsbb"
version = "0.1.0"
description = "ForgeStream Baseball — NCAA team ratings engine"
requires-python = ">=3.12"
dependencies = [
    "httpx>=0.27",          # Async HTTP for NCAA API
    "pydantic>=2.0",        # Data validation/schemas
    "click>=8.1",           # CLI framework
    "tabulate>=0.9",        # Terminal table formatting
]

[project.optional-dependencies]
scrape = [
    "playwright>=1.45",     # JS-rendered page scraping (PEAR)
]
serve = [
    "fastapi>=0.115",       # API layer (V1)
    "uvicorn>=0.32",        # ASGI server
]
```

**No ML frameworks needed for V0.** Pure math (Pythagorean, Elo, log regression).

### Build Timeline (48-72 hours)

| Hour | Task | Output |
|------|------|--------|
| 0-4 | Set up project, schemas, SQLite, team alias table | `fsbb/db.py`, `fsbb/schemas.py` |
| 4-12 | NCAA scraper (using henrygd/ncaa-api) | `fsbb/scraper/ncaa.py` — full DI season in DB |
| 12-16 | PEAR scraper + import existing `pear_ratings.json` | `fsbb/scraper/pear.py` — benchmark loaded |
| 16-20 | Cleaning pipeline (entity resolution, dedup) | `fsbb/scraper/clean.py` — <1% unresolved |
| 20-28 | Rating model (Pythag, SOS, adj runs, Elo, power) | `fsbb/models/ratings.py` |
| 28-32 | Matchup model (logistic win probability) | `fsbb/models/matchup.py` |
| 32-40 | CLI (rank, matchup, validate-pear, export) | `fsbb/__main__.py` |
| 40-48 | PEAR validation, tuning, edge cases | Spearman ρ > 0.90 target |
| 48-56 | JSON export, basic docs, demo prep | `ratings.json`, README |

---

## 3. The Differentiation Layer (V1)

"If that is easily somewhat easily stood up, then it's understanding how could we differentiate from like an algorithm perspective?" — Mergim, REQ #28-29

### 3.1 Starting Pitcher Adjustment

**The gap:** PEAR shows the same win probability regardless of who pitches. A team's odds in a midweek game with their #4 starter should differ dramatically from a Friday night game with their ace.

**Implementation:**

```python
class PitcherAdjustment(BaseModel):
    pitcher_name: str
    team: str
    games_started: int
    innings_pitched: float
    era: float
    whip: float
    k_per_9: float
    bb_per_9: float
    # Derived
    adj_era: float            # SOS-adjusted ERA
    runs_above_avg: float     # RAA vs league average starter

def adjust_matchup(base_win_prob: float,
                   home_pitcher: PitcherAdjustment,
                   away_pitcher: PitcherAdjustment) -> float:
    """Shift base win probability by pitcher quality differential."""
    pitcher_diff = away_pitcher.adj_era - home_pitcher.adj_era
    # Each 1.0 ERA difference shifts win prob by ~8-10%
    shift = pitcher_diff * 0.09
    return clamp(base_win_prob + shift, 0.05, 0.95)
```

**Data source:** NCAA box scores list starting pitchers. Cross-reference with player stats pages for ERA, IP, K, BB.

### 3.2 Monte Carlo Game Simulation Engine

**Purpose:** Generate probability distributions, not point estimates. "This has like simulations" (Ryan, claim #66).

```python
def simulate_game(home: TeamRating, away: TeamRating,
                  home_pitcher: PitcherAdjustment | None,
                  away_pitcher: PitcherAdjustment | None,
                  n_sims: int = 10_000) -> SimulationResult:
    """
    For each simulation:
    1. Sample home runs from Poisson(adj_runs_scored × pitcher_factor)
    2. Sample away runs from Poisson(adj_runs_scored × pitcher_factor)
    3. If tied after 9, simulate extra innings
    4. Record winner + total runs

    Returns: win probabilities, expected total runs,
             over/under distribution, run line coverage
    """
```

**Why Poisson:** Baseball runs per game are well-modeled by Poisson distributions. Simple, fast, interpretable. College baseball may need a slightly overdispersed Poisson (negative binomial) due to higher variance — validate empirically.

**Compute cost:** 10K simulations per matchup × ~40 daily games = 400K sims. <1 second on any modern machine.

### 3.3 College-Specific Run Expectancy Tables

**The problem:** MLB run expectancy tables (based on millions of plate appearances with pro-level wood bats) don't apply to college because:
- BBCOR aluminum bats produce different batted ball profiles
- College parks vary wildly in dimensions
- Talent distribution is much wider (SEC ace vs. MEAC #3 starter)
- Run environments differ (college averages ~5.5 R/G vs MLB ~4.5 R/G)

**The solution:** Build our own RE24 matrices from NCAA play-by-play data.

```
24 base-out states (8 base states × 3 out states):
                 0 out    1 out    2 out
Bases empty      0.52     0.28     0.11
Runner on 1st    0.91     0.55     0.24
Runner on 2nd   1.17     0.70     0.33
1st & 2nd       1.47     0.94     0.45
Runner on 3rd   1.43     0.98     0.37
1st & 3rd       1.80     1.21     0.52
2nd & 3rd       2.05     1.44     0.58
Bases loaded    2.35     1.63     0.75

(Values above are MLB placeholders — college values will be
higher due to BBCOR offense and must be computed from data)
```

**Data needed:** Play-by-play from NCAA (available via `baseballr` in R for 2022+). V1 can start with 2024-2026 PBP data (~25K games worth).

### 3.4 Conference Strength Normalization

Going 25-5 in the SEC means something very different from 25-5 in the MEAC.

**Method:** Iterative Bayesian SOS calculation:
1. Initialize all teams at 0.500
2. For each team, compute win% against opponents' ratings
3. Recompute opponent ratings using updated values
4. Iterate until convergence (typically 5-10 iterations)
5. Normalize across conferences: conference_strength = avg(member_ratings)

**Conference adjustment factor:** Multiply team metrics by (league_avg / conference_avg) to normalize.

### 3.5 The Equation Interface

Ryan's ForgeStream "equation" — originally built for trade augmentation and alpha generation — plugs in here:

```python
class AlphaModel(Protocol):
    """Interface for the equation/alpha generation model."""

    def predict(self,
                home: TeamRating,
                away: TeamRating,
                market_line: float | None = None,
                context: dict | None = None) -> AlphaPrediction:
        """
        Given team ratings and optional market line,
        return a prediction with confidence interval.

        If market_line is provided, also return:
        - edge: model_prob - implied_prob (positive = value bet)
        - kelly_fraction: optimal bet size
        """
        ...

class AlphaPrediction(BaseModel):
    home_win_prob: float        # 0-1
    away_win_prob: float        # 0-1
    expected_total: float       # Expected combined runs
    confidence: float           # Model confidence (0-1)
    edge: float | None          # vs market line
    kelly_fraction: float | None
    features_used: list[str]    # Transparency
```

**Integration point:** The equation receives `TeamRating` objects (from our pipeline) and optionally market lines (scraped from sportsbooks). It returns predictions with edge estimates. The pipeline feeds the equation; the equation generates alpha.

**Where reinforcement learning fits:** "It's really interesting to plug in these equations into a reinforcement learning AI agent... it essentially learns on the market as you go along" (Mergim, claim #8-9). The RL layer sits between the equation and the betting decision, learning from outcomes which prediction signals are most reliable.

```
Pipeline → TeamRatings → AlphaModel → RL Agent → Betting Signal
                ▲                         │
                │                         ▼
              Data                    Outcomes
            (daily)               (game results)
```

---

## 4. Scale Path: V1 → V2 → V3

### V1: Team Ratings + Starting Pitcher Adjustment

**Timeline:** 2-4 weeks after V0 validation
**Data needed:** NCAA box scores + starting pitcher game logs (already scrapable)

| Component | New Infrastructure | Incremental Build Cost |
|-----------|-------------------|----------------------|
| Starting pitcher model | Pitcher stats table in SQLite | 2-3 days |
| Monte Carlo engine | Pure Python, no new deps | 1-2 days |
| Conference normalization | Extension of SOS algorithm | 1 day |
| Matchup UI (CLI) | Enhanced CLI output | 1 day |
| FastAPI endpoints | Already in ForgeStream deps | 2 days |

**Deliverable:** "That will be a good version one for us to sort of point to" (Ryan, claim #68). A ranked table + matchup tool that adjusts for starting pitchers and runs simulations. Comparable to KenPom's basketball output.

### V2: Player-Level Metrics

**Timeline:** 4-8 weeks after V1
**Data needed:** Individual player game logs, per-PA data where available

| New Metrics | Source | Difficulty |
|-------------|--------|-----------|
| wOBA (weighted on-base average) | Box scores (H, 2B, 3B, HR, BB, HBP) | Medium — need college-specific linear weights |
| wRC+ (weighted runs created, park/league adjusted) | wOBA + park factors | Medium — park factor estimation requires multi-year data |
| ERA+ / FIP (fielding independent pitching) | Pitcher stats (K, BB, HR, IP) | Low — standard formulas |
| WAR (wins above replacement) | Composite of batting + pitching + fielding | Hard — replacement level undefined for college |
| Transfer portal projections | Historical transfer outcomes + new team context | Hard — novel model, our differentiator |

**Infrastructure changes:**
- SQLite → PostgreSQL (concurrent reads/writes from scraper + API)
- Player table, at-bat table (if PBP available)
- Player identity resolution across transfers (player_id system)
- Storage: ~500 MB for DI player-level season data

**Build cost:** 4-8 weeks for one developer. The player entity resolution across seasons/transfers is the hard part.

### V3: Pitch Tracking + Predictive Betting

**Timeline:** 3-6 months after V2
**Data needed:** TrackMan/Rapsodo data from 643 Charts or direct program partnerships

| New Capabilities | Source | Difficulty |
|-----------------|--------|-----------|
| Exit velocity, launch angle | 643 Charts API (if accessible) | Medium — API integration |
| Spin rate, pitch movement | 643 Charts or Rapsodo CSV exports | Medium-Hard — data format varies by hardware |
| Expected stats (xBA, xwOBA) | Physics model on batted ball data | Hard — requires large dataset for college calibration |
| Automated betting model | RL agent on historical predictions vs outcomes | Hard — needs 1+ seasons of prediction data |
| Draft projection model | Player stats + physical measurables | Very hard — requires scouting data |

**Infrastructure changes:**
- Dedicated pitch event store (millions of rows)
- GPU for RL training (ForgeStream's RunPod setup)
- Real-time market data ingestion (sportsbook odds scraping)
- Monitoring/alerting on model drift

**Build cost:** 3-6 months. The physics data acquisition is the bottleneck — not engineering.

### Scale Summary

```
V0 (48-72h)     V1 (2-4w)        V2 (4-8w)          V3 (3-6mo)
─────────────────────────────────────────────────────────────────
308 teams        + pitchers       + all DI players    + physics data
Team ratings     + Monte Carlo    + wOBA/wRC+/WAR     + xBA/xwOBA
CLI only         + FastAPI        + Web dashboard      + Betting model
SQLite           SQLite           PostgreSQL           PG + event store
$0 hosting       $0 (local)       $20/mo (VPS)        $100-200/mo
1 developer      1 developer      1-2 developers       2-3 developers
```

---

## 5. Tech Stack Recommendation

### Core Stack

| Layer | Technology | Version | Rationale |
|-------|-----------|---------|-----------|
| **Language** | Python | 3.12+ | ForgeStream is Python; Ryan can "vibe code" in Python; all NCAA scraping packages are Python |
| **Package manager** | uv | latest | ForgeStream already uses uv; fastest Python package manager |
| **HTTP client** | httpx | 0.27+ | Async, modern, replaces requests |
| **Browser scraping** | Playwright | 1.45+ | For JS-rendered pages (PEAR); headless Chromium |
| **Data validation** | Pydantic | 2.x | ForgeStream already uses Pydantic; type-safe schemas |
| **Database (V0-V1)** | SQLite | 3.45+ | Zero-config, single file, comes with Python |
| **Database (V2+)** | PostgreSQL | 16+ | ForgeStream already has `psycopg`; concurrent access |
| **CLI** | Click | 8.1+ | Standard Python CLI framework; simple, well-documented |
| **Table formatting** | tabulate | 0.9+ | Terminal output for rankings |
| **API (V1+)** | FastAPI | 0.115+ | Already in ForgeStream deps; auto-docs, async |
| **API server** | Uvicorn | 0.32+ | Already in ForgeStream deps |
| **Task scheduler** | cron (system) | — | V0: system cron for daily scrape. V2: consider APScheduler |

### What We Don't Need Yet

| Technology | When to Add | Why Not Now |
|-----------|------------|-------------|
| pandas/numpy | V2 (player metrics) | V0 is pure aggregation — no dataframes needed |
| scikit-learn | V2 (player models) | V0 models are closed-form formulas |
| PyTorch | V3 (RL agent) | ForgeStream has this for RunPod already |
| Redis | V2 (caching) | SQLite is fast enough at V0 scale |
| Docker | V1 (API deployment) | Dev locally first, containerize when deploying |
| React/Next.js | V2 (dashboard) | CLI + JSON is the V0 deliverable |

### Monorepo vs Separate Services

**Recommendation: Monorepo.** Specifically, `fsbb/` as a new package within the ForgeStream project.

**Rationale:**
1. ForgeStream already has the Python infrastructure (`uv`, Pydantic, FastAPI, psycopg)
2. The equation / alpha model lives in ForgeStream — tightly coupled
3. At V0-V1 scale, this is one process, not a distributed system
4. Ryan needs to see the code in one place to evaluate ("vibe code")
5. Separate when there's a reason to — not before

```
forgestream/
├── forgestream/          # Existing: meeting intelligence engine
├── fsbb/                 # NEW: baseball analytics package
│   ├── scraper/
│   ├── models/
│   ├── db.py
│   └── __main__.py
├── data/
│   ├── pear/             # Already scraped PEAR data
│   └── fsbb.db           # V0 SQLite database
├── pyproject.toml        # Add fsbb as workspace package
└── tests/
    └── fsbb/             # fsbb-specific tests
```

### Hosting Cost per Tier

| Tier | Infrastructure | Monthly Cost |
|------|---------------|-------------|
| **V0** | Local development (macOS/Linux) | $0 |
| **V1** | Same + optional VPS for cron scraping | $0-5 (free tier VPS) |
| **V2** | VPS (4 CPU, 8GB RAM) + managed Postgres | $20-40 |
| **V3** | VPS + Postgres + RunPod GPU (occasional) | $100-200 |
| **V3+** (scale) | AWS/GCP with load balancer | $300-500 |

"I'm a big fan of not trying to sink in any money into anything and just push as far as we can" — Ryan, claim #60. V0-V1 costs $0.

### ForgeStream Stack Alignment

| ForgeStream Component | Baseball Application |
|----------------------|---------------------|
| Domain knowledge extraction | Encode scout/coach knowledge into feature weights |
| SOS framework | Quality/governance for data pipeline outputs |
| GRPO / reinforcement learning | Model calibration across seasons; market-learning agent |
| Emotion pipeline | Fan engagement analysis (future — V3+) |
| Bespoke engine model | White-label analytics for programs |
| Gemini integration | Natural language queries over ratings ("who's the best team in the SEC?") |
| Dashboard (FastAPI + Textual TUI) | Ratings display, matchup tool |

---

## Appendix A: PEAR Data Already Captured

We have scraped and stored:
- `data/pear/pear_ratings.json` — 308 teams, 11 fields each
- `data/pear/pear_ratings.csv` — Same data, CSV format
- `data/pear/teams/team_Vanderbilt.json` — Detailed per-team data including:
  - Full batting/pitching stats (BA, ERA, WHIP, OPS, etc.)
  - Advanced metrics (wOBA, wRAA, oWAR, pWAR, fWAR, ISO, wRC+, FIP, BABIP)
  - Elo ratings + deltas
  - Killshot metrics (novel PEAR-specific stat)
  - Projected RPI, WAB (wins above bubble), NET composite
  - Remaining schedule analysis
  - Q1/Q2/Q3/Q4 record breakdown

This is considerably richer than what PEAR's public website shows. The per-team files contain ~140+ fields. This data serves as both validation benchmark and feature inspiration.

## Appendix B: Key Competitors' Data Sources

| Competitor | Data Source | Method | Accessible? |
|-----------|------------|--------|-------------|
| PEAR | NCAA website | Python scraper + manual validation | Yes (NCAA is public) |
| 64 Analytics | NCAA + SidearmStats | Unknown (likely scraping) | Behind paywall |
| 6-4-3 Charts | TrackMan direct feeds | API partnerships with programs | API exists, pricing unclear |
| EvanMiya (basketball) | NCAA + PBP | Proprietary scraping | No — closed |
| KenPom (basketball) | NCAA | Proprietary | No — closed |
| Bill Petti (baseballr) | NCAA bulk data | R package, open source | Yes — MIT license |

## Appendix C: Open Questions for Next Call

1. **643 Charts API** — Is it truly free? What data fields are exposed? What's the rate limit?
2. **Pythagorean exponent** — Is 1.83 right for college baseball, or should we calibrate from historical data?
3. **Historical data depth** — PEAR has data back to 2006. How much historical data do we need for the RL model?
4. **Legal** — Is scraping NCAA for a commercial product legally clear? (NCAA data is public but ToS may restrict commercial use)
5. **Ryan's "equation"** — What's the current state? What inputs does it expect? What does it output?
6. **Division scope** — V0 is DI only. When do DII/DIII matter? (Data quality drops dramatically)
7. **Market data** — Which sportsbooks have college baseball lines? How liquid are the markets?
