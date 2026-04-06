# Gap Analysis: V0 → World-Class Product

## What We Have (V0): 2 features → 65.9% accuracy
- Runs Scored, Runs Allowed → Pythagorean Win% → Log5 matchup

## What PEAR Provides (166 metrics per team): We use 2 of 166

### Tier 1: Opponent-Quality Metrics (CRITICAL — closes 2-3%)
- **SOS** (Strength of Schedule) — who you've played
- **SOR** (Strength of Record) — quality of wins adjusted for opponent
- **RQI** (Resume Quality Index) — composite resume metric
- **NET_Score** — normalized NET composite (0-1 scale)
- **Q1/Q2/Q3/Q4 records** — record split by opponent quality quadrant
- **expected_wins** — wins above what a random team would get against their schedule
- **WAB** (Wins Above Bubble) — tournament selection metric
- **NCSOS** — non-conference strength of schedule
- **RemSOS** — remaining schedule difficulty

### Tier 2: Advanced Batting (IMPORTANT — adds 1-2%)
- **wOBA** (weighted on-base average) — single best measure of offensive production
- **wRAA** (weighted runs above average) — runs created above average
- **wRC+** (weighted runs created plus) — park/league-adjusted, 100 = average
- **ISO** (isolated power) — raw power metric (SLG - BA)
- **BABIP** — batting average on balls in play (luck indicator)
- **BB%** — walk rate (plate discipline)
- **OPS** — on-base + slugging (composite offense)

### Tier 3: Advanced Pitching (IMPORTANT — adds 1-2%)
- **FIP** (fielding independent pitching) — what pitchers actually control
- **ERA** — traditional earned run average
- **WHIP** — walks + hits per inning pitched
- **KP9** — strikeouts per 9 innings
- **WP9** — walks per 9 innings  
- **K/BB** — strikeout-to-walk ratio (control + stuff)
- **LOB%** — left on base percentage (strand rate, regression indicator)
- **RA9** — runs allowed per 9 innings

### Tier 4: WAR Components (VALUABLE — adds 0.5-1%)
- **oWAR_z** — offensive wins above replacement (z-scored)
- **pWAR_z** — pitching wins above replacement (z-scored)
- **fWAR** — total franchise WAR (batting + pitching combined)

### Tier 5: PEAR's Proprietary Metrics (UNIQUE)
- **KPI** (Killshot Performance Index) — PEAR's proprietary clutch metric
- **Killshots** — games won by 1-2 runs
- **KillshotOffEff / KillshotDefEff** — close-game execution
- **KSHOT_Ratio** — killshots given vs received
- **KillshotWinPercent** — win rate in close games
- **KillshotRunPct** — % of scoring in close-game situations

### Tier 6: Percentile Rankings (CONTEXT)
- **pBA, pOPS, pERA, pFIP, pWHIP, pwOBA, etc.** — percentile ranks across D1
- These let us compare any team to the D1 average instantly

### Tier 7: Projections (FORWARD-LOOKING)
- **Projected_Wins / Projected_Losses** — PEAR's season projection
- **Projected_NET** — projected final NET ranking
- **Projected_Record** — "32-24" type projection
- **Games_Remaining** — schedule context
- **Remaining_Wins / Remaining_Losses** — projected remaining record

### Tier 8: ELO System (THEIR CORE)
- **ELO** — current ELO rating
- **ELO Delta** — recent ELO change (momentum)
- **ELO_Rank** — ELO-based ranking

### What PEAR Does NOT Have (Our Edge)
1. **Game-specific predictions** — PEAR shows identical probabilities per series
2. **Starting pitcher adjustments** — pitcher identity changes everything
3. **Published accuracy tracking** — nobody publishes Brier scores
4. **Weather/park factor adjustments** — temperature affects run scoring
5. **Betting line comparison** — model vs market edge detection
6. **The correct Pythagenport exponent** — 2.13, not 1.83
7. **Formal convergence guarantees** — SOS framework (our published research)

---

## The World-Class Product Roadmap

### Phase 1: Multi-Feature Model (IMMEDIATE — closes 3.5% gap)
Use ALL 166 PEAR metrics in a proper statistical model:
- Feature selection: top 20-30 predictive features
- Regularized logistic regression or gradient boosted trees
- Cross-validated to prevent overfitting
- SOS-adjusted run differential as foundation
- Killshot metrics as clutch performance indicator

### Phase 2: Starting Pitcher Layer (DIFFERENTIATOR)
- Scrape individual pitcher stats from NCAA box scores
- Pitcher Impact Score: how much does each starter shift team win probability?
- This is what makes Game 1 of a series different from Game 3
- PEAR explicitly cannot do this

### Phase 3: Betting Edge Calculator (REVENUE)
- Integrate The Odds API for live lines
- Compare model probability vs implied odds probability
- Flag value bets where edge > threshold
- Kelly criterion for optimal bet sizing
- Track P&L transparently

### Phase 4: Real-Time Pipeline (SCALE)
- NCAA scoreboard for live game updates
- Intra-day rating updates as games finish
- Push notifications for high-edge opportunities
- API for programmatic access

### Phase 5: Historical Depth (PROOF)
- Backtest on 2024, 2023, 2022 seasons
- Demonstrate persistent edge across years
- Publish academic-quality accuracy analysis
