# Ryan McCarthy Feedback — Deep Analysis & Cross-Reference

**Date:** 2026-03-30 | **Zoom:** 5 PM ET / 10 PM BST

---

## Ryan's Frame of Reference

Ryan is thinking about this through a **proven playbook**: KenPom for college basketball. This is smart — KenPom is a one-person operation doing ~$5M/year revenue ($25 × 200K subscribers). The question is whether the same model works for college baseball.

**His reference models:**
- **KenPom.com** — tempo-adjusted efficiency, opponent-adjusted ratings, predictive modeling. $25/year, ~200K subscribers. Used by fans, bettors, teams.
- **EvanMiya.com** — player-level, lineup-based, Bayesian Performance Rating, transfer impact modeling. More modern/granular than KenPom.

**His assessment of existing players (accurate per our research):**
- **PEARatings** — passion project, not monetized, anonymous founder, small following. ✓ Confirmed.
- **64 Analytics** — more built out, player-level data, geared toward teams/recruiting, trickier for fans. ✓ Confirmed. We'd add: $13/month consumer, $2K-$5.5K institutional Portal Pass.

---

## Ryan's 3 Questions — Assessment

### Q1: "How difficult would it actually be to replicate PEARatings from a data + infra standpoint? And make it even better"

**Short answer: Medium difficulty for replication, hard for "even better."**

**Replicating PEAR's current functionality:**
- PEAR uses Python scraping of NCAA website + manual validation
- Core output: TSR (team quality) + RQI (resume quality) + SOS (schedule strength) = NET composite
- NCAA box score data IS publicly available via stats.ncaa.org
- Python libraries exist: `collegebaseball`, `baseballr` (R), custom scrapers
- The rating algorithm itself is not novel — similar to RPI with modern adjustments
- **Timeline to replicate:** 2-4 weeks for a skilled developer. The data pipeline is the real work, not the model.

**Making it "even better" — the hard parts:**
1. **Data quality** — Ryan correctly identifies this as the core challenge. NCAA reporting is inconsistent, games go missing, stats have errors. PEAR's manual validation step is labor-intensive but necessary.
2. **Player-level modeling** — PEAR doesn't do this. Moving from team-level to player-level requires individual game logs, which are harder to scrape consistently across all divisions.
3. **Starting pitcher analysis** — Requires knowing who started each game, which isn't always in box scores (especially DII/DIII). This is a real data gap.
4. **Cross-divisional normalization** — Comparing a DI team to a DII team requires strength-of-schedule adjustments that go deeper than PEAR's current model.

**Our recommendation:** Replicate + improve is the right call. PEAR is a passion project with no moat beyond "they did it first." The moat comes from better data infrastructure and better models, not from being first.

---

### Q2: "Where are the real bottlenecks - scraping, data cleaning, modeling, or all of the above?"

**Answer: Data cleaning is the biggest bottleneck. Then modeling. Scraping is solved.**

**Scraping (LOW bottleneck):**
- NCAA box scores can be scraped with existing tools
- Play-by-play is harder but 64 Analytics has solved this
- The scraping itself is a weekend project for a good developer
- Rate limiting and NCAA website changes are annoyances, not blockers

**Data cleaning (HIGH bottleneck — Ryan is right):**
- Missing games, duplicate entries, inconsistent formatting
- Team name variations (e.g., "UNC" vs "North Carolina" vs "North Carolina-Chapel Hill")
- Pitcher stats sometimes don't match team totals
- DII/DIII data quality is dramatically worse than DI
- **This is where PEAR spends most of their time** — manual validation
- **This is also where AI can provide a massive edge** — entity resolution, deduplication, anomaly detection

**Modeling (MEDIUM bottleneck):**
- Team-level ratings (KenPom-style) are well-understood mathematically
- Player-level models in baseball are harder than basketball because:
  - Baseball is pitcher-dependent (one player can swing a game outcome far more than in basketball)
  - Sample sizes are small (56 regular season games vs 30+ in basketball, but only 10-15 starts per pitcher)
  - Matchup effects (L/R splits, park factors) add complexity
  - Transfer impact is harder to model (pitcher changing conferences changes everything)
- **Monte Carlo simulation** is computationally straightforward but requires good input distributions
- **Run expectancy tables** exist for MLB but need to be rebuilt for college (different run environments: BBCOR bats, variable parks)

**Our unique edge on data cleaning:** ForgeStream's domain knowledge extraction + AI pipeline could automate what PEAR does manually. Entity resolution, anomaly detection, cross-referencing multiple sources — this is exactly what your AI stack does.

### Deep Technical Answers (from NCAA data research)

**Data sources that exist:**
- `stats.ncaa.org` — box scores, game logs, player stats, PBP text (all divisions)
- Python: `collegebaseball` package (pip installable, D1/D2/D3 aggregate stats)
- Python: `CollegeBaseballStatsPackage` (team stats 2002-2025, player stats 2021-2025)
- R: `baseballr` — bulk PBP loading for 2022+, most capable NCAA scraper
- Unofficial NCAA JSON API: `henrygd/ncaa-api` (live scores, schedules, 5 req/s)
- **6-4-3 Charts has a documented API** at 643charts.com/api — institutional pricing

**What's NOT publicly available:** Trackman pitch data, exit velocity, spin rate, pitch sequencing, biomechanics, catcher framing. No public platform has broken through this wall.

**Data quality reality:**
- Stats entered by student SIDs (often unpaid) using PrestoStats/StatCrew
- NCAA itself acknowledged "uptick in incorrect statistics being reported"
- D1 Power conference = best quality. D2/D3 = significantly worse.
- ~10-20% of D1 games have incomplete PBP
- Player identity ambiguity across seasons/transfers

**Build timeline estimate:**
- Phase 1 MVP (aggregate stats): 4-6 weeks with existing Python packages
- Phase 2 (game-level D1 box scores + PBP): 8-12 weeks with Playwright headless scraper
- Phase 3 (quality layer): ongoing — automated validation is the moat
- D2/D3 PBP: skip in v1, quality too low
- Full D1+D2+D3 season: ~24,000 games, scrapable in 6-13 hours at polite rate

**The key insight:** The data infra challenge is solvable engineering, not fundamental data unavailability — EXCEPT for pitch-tracking data. The differentiation is in the quality layer and analytical models, not raw data access.

---

### Q3: "Whether it makes more sense to partner with PEAR vs build"

**Answer: Build. Here's why.**

**Arguments for partnering with PEAR:**
- They have 12-18 months of scraped+cleaned data
- They've identified the audience (tournament bubble followers)
- Small but real following (~6,750 Twitter followers)
- Could accelerate launch by months

**Arguments against (stronger):**
1. **PEAR is a passion project with no commercial ambition** — anonymous founder, no monetization, no pricing. Partnership requires a partner who wants to be partnered with.
2. **PEAR's data pipeline is manual and doesn't scale** — Python scraping + manual validation. You'd be inheriting tech debt, not tech advantage.
3. **PEAR has no player-level data** — Ryan's vision requires player modeling, which means building that data layer from scratch regardless.
4. **PEAR's methodology is a black box** — no published weights or peer review. Building your own model means you understand every assumption.
5. **PEAR's multi-sport coverage is irrelevant** — if you're building for baseball, football/softball ratings don't help.
6. **The real moat is data infrastructure, not the ratings** — anyone can build team ratings. The hard part (and the moat) is the automated data pipeline. Build that right, and the ratings are a product feature, not the product.

**Recommendation:** Build, but study PEAR closely. Their rating output is a validation benchmark (your model should produce similar-ish rankings if the methodology is sound). Their scraped data could be useful for bootstrapping historical baselines. But don't partner — build a better pipeline from the ground up.

**64 Analytics is the more interesting potential partner** — they have play-by-play data across all divisions, real revenue, institutional clients. But they have no API and may not want to share their data moat. Worth a conversation, but approach as a potential acquirer or data partner, not a collaborator.

---

## Ryan's Strategy Assessment: "The concept would look most like..."

Ryan describes: PEARatings-style but with:
1. Player-level modeling (not just team)
2. Starting pitching analysis (game-by-game, not series-level)
3. Monte Carlo simulation engine
4. Run expectancy tables + advanced stats
5. Data infrastructure edge (scraping)
6. Productized for fans, teams, gambling

### Assessment: This is 80% right. Here's the 20% to refine.

**What Ryan gets right:**
- ✅ PEARatings as the starting point (team ratings are table stakes)
- ✅ Player-level modeling as the upgrade (this is where 64 Analytics is and PEAR isn't)
- ✅ Starting pitcher analysis (a genuine gap — PEAR shows same win probability regardless of starter)
- ✅ Monte Carlo simulation (computationally simple, powerful for predictions/gambling)
- ✅ Data infrastructure as competitive moat
- ✅ Multiple monetization angles (fans, teams, gambling)

**What to refine/add:**

1. **The KenPom model is the FLOOR, not the ceiling.** KenPom works for basketball because 5 players drive most outcomes. Baseball is more stochastic — pitcher-hitter matchups, park factors, weather, bullpen depth. The model needs to be fundamentally different, not just "KenPom for baseball."

2. **Run expectancy tables need to be college-specific.** MLB run expectancy matrices don't transfer to college because of BBCOR bats (metal, less pop), different park dimensions, and dramatically different talent distributions. Building college-specific RE tables from NCAA play-by-play data is a real innovation.

3. **Transfer portal is the killer feature Ryan didn't mention.** 2,000+ players transfer per year. A model that can project how a transfer will perform at their new program (different conference, different opponents, different park) is enormously valuable to coaches AND bettors. This is where your equation could shine — predicting outcomes in new contexts.

4. **The gambling angle is the revenue multiplier.** KenPom's $25/year × 200K = $5M is good. But the sports betting market is $10B+ in the US. A product that gives bettors an edge on college baseball lines (which are inefficient because oddsmakers have less data) could command $50-100/month from serious bettors. That's a different revenue tier.

5. **API-first architecture matters.** Neither KenPom nor PEAR nor 64 Analytics has a public API. Being API-first means:
   - Developers build tools on top of your data (network effects)
   - Other platforms integrate your ratings (distribution)
   - Bettors can build automated models (premium pricing)
   - This is what made Baseball Savant the gold standard for MLB

6. **The "Statcast gap" is the long-term play.** Ryan's short-term plan (box-score analytics) is the right MVP. But the long-term moat is physics-level data (exit velocity, spin rate, pitch movement). If/when you can aggregate this from programs with Trackman/Rapsodo, you own the "Baseball Savant for college" position. Nobody else is close.

---

## Cross-Reference: Our Research vs Ryan's Assessment

| Topic | Ryan's View | Our Research Says | Alignment |
|-------|------------|-------------------|-----------|
| PEAR is a passion project | ✅ "not monetized, anonymous founder" | ✅ Free, no paywall, ~6,750 followers | Full alignment |
| 64 Analytics is player-focused | ✅ "geared towards teams/recruiting" | ✅ $13/mo consumer, $5.5K institutional, portal-focused | Full alignment |
| Data quality is the core challenge | ✅ "inconsistent NCAA reporting, missing games" | ✅ Confirmed — this is where AI can provide massive edge | Full alignment |
| Baseball is harder than basketball | ✅ "more dependent on individual matchups" | ✅ Pitcher-dominated, small samples, matchup effects | Full alignment |
| Advanced data not publicly available | ✅ "exit velocity, bat speed not public" | ✅ Trackman/Rapsodo data siloed per program, $4K-$30K hardware | Full alignment |
| KenPom is the reference model | ✅ Good starting analogy | ⚠️ KenPom is the floor — baseball needs fundamentally different modeling | Partial — needs refinement |
| PEAR vs build | ? Asks the question | 🔨 Build. PEAR's data pipeline is manual, no player data, no commercial ambition | We have a clear recommendation |

---

## What Ryan Doesn't Know Yet (Bring to the Call)

1. **Your equation** — originally built for alpha generation / trade organization, proven in coding. Could be adapted for game outcome prediction and player valuation. This is a mathematical edge nobody else in this space has.

2. **ForgeStream's architecture** — domain knowledge extraction from experts (Tim, Connor, coaches) is exactly what this product needs. Encoding what a scout "feels" when evaluating a pitcher.

3. **6-4-3 Charts has a public API** — potential data source for TrackMan-derived metrics from 650+ DI programs. Nobody in this conversation has mentioned this yet.

4. **MLB outlawed Trackman data exclusivity for amateur baseball** — meaning showcase data can't be hoarded. This creates a regulatory tailwind for data aggregation platforms.

5. **Pixellot + TruMedia partnership** (Oct 2024) — the nearest forming competitor is B2B only. No consumer-facing play.

6. **The AI automation angle for data cleaning** — what PEAR does manually (Python scraping + validation), your AI stack can automate and scale. This is the actual infrastructure moat.

---

## Recommended Discussion Agenda for the Call

1. **Validate Ryan's mental model** — "KenPom for baseball" is the right starting analogy, but refine: baseball needs pitcher-centric modeling, college-specific run expectancy, and transfer portal projection
2. **Share the research** — show him we've already mapped the full landscape (PEAR, 64 Analytics, 6-4-3 Charts, TruMedia, Baseball Savant gap analysis)
3. **Propose the build path** — build > partner with PEAR. The moat is automated data infrastructure + superior modeling.
4. **Introduce the equation angle** — your math background applied to prediction markets = concrete technical edge
5. **Define MVP** — team ratings + player-level stats + starting pitcher adjustment + Monte Carlo game simulator. Free tier for fans, premium for bettors ($30/year = Tim's suggestion, or $50/year matching KenPom's willingness-to-pay proof point)
6. **Discuss the gambling multiplier** — college baseball lines are inefficient. A model that's even slightly predictive is enormously valuable.
7. **Roles** — Ryan (domain knowledge, PE business structuring, user), Tim (network, baseball expertise), Connor (player development data), You (AI/architecture/modeling), ForgeStream (the engine)

---

## EvanMiya — The Methodological Blueprint

EvanMiya (college basketball) is the EXACT template for what to build in baseball. Key findings:

**Bayesian Performance Rating (BPR):** 3-model ensemble:
1. RAPM (play-by-play lineup data) — who's on court matters
2. Box BPR (box-score derived) — stable in small samples
3. Bayesian prior (preseason projection) — solves cold-start problem

**Why this matters for baseball:**
- College baseball has the SAME small-sample problem Ryan flagged (56-game season, ~15 starts per pitcher)
- A Bayesian framework starts with informed priors (previous season, conference adjustment) and updates as games are played
- **Transfer-specific model** — EvanMiya built a SEPARATE model for transfers vs returners. Same logic applies to baseball transfers.
- **Lineup simulation** — predict outcomes for unseen lineups. In baseball: predict game outcomes for untested pitcher-lineup matchups.

**Business model proof:**
- $180/year consumer, 120+ D1 programs subscribe
- NCAA-approved scouting service (programs can expense it)
- Partnership with Dropback for NIL/revenue-sharing roster management
- Substack + podcast for distribution

**The lesson:** Player-level Bayesian ratings are the wedge. Team ratings (what PEAR does) are table stakes. The "EvanMiya for baseball" position is still open.

**Kill Shot metric analog for baseball:** EvanMiya tracks 10-0 scoring runs. A baseball equivalent could be: "shutdown innings after opponent scores" or "run differential in high-leverage situations." Novel, intuitive, media-friendly.

---

## Zoom Link

https://higcapital.zoom.us/j/92250687511?pwd=qpnwEqtfjus9lIPMR5u6UrlaR8v9MJ.1

**HIG Capital** — confirms Ryan works at HIG Capital (private equity). This is a tier-1 middle-market PE firm ($65B+ AUM). Ryan's PE lens explains his structured approach to opportunity assessment.
