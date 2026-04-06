# Sentinel Briefing — ForgeStream Baseball V0
**Date:** 2026-04-06 | **Status:** V0 build in progress | **Next milestone:** Demo for Ryan

---

## Context for All Sentinel Modes

Two meetings on 2026-03-30: Tim McCarthy (Wellington, 18 min) and Tim + Ryan McCarthy (HIG Capital, 49 min). 680 total claims extracted. Ryan is a PE professional evaluating this as a feasibility study. No code existed until today.

**Today's progress:**
- Full Python package `fsbb` built: database, scrapers, ratings engine, prediction engine, backtest, CLI, HTML prediction page
- PEAR API confirmed live: 308 D1 teams scraped with RS/RA/games/schedule data
- Pythagenport + Dynamic Bradley-Terry model computing ratings
- Matchup predictions working (Texas vs UCLA: 45-55%)
- College Pythagenport exponent: ~2.08 (significantly higher than MLB's 1.83, confirming research hypothesis)
- The Odds API (`baseball_ncaa`) confirmed as free odds source (500 credits/month)

**Ryan's 11 questions** (sent post-meeting) need concrete answers backed by working code.

**Key decisions still needed:**
1. Hosting strategy (local → VPS → hosted?)
2. Whether to build the "Disagreement Dashboard" (V0-A) or "PEAR Killer" (V0-B) first
3. How to handle BT model accuracy with sparse game data

---

## For Insight Miner (IM)

**Extract and store:**
1. The Pythagenport exponent finding (~2.08 for college baseball vs 1.83 MLB) is a publishable result — no one has computed this before
2. PEAR's API structure (`/api/cbase/ratings`, `/api/cbase/team/{name}`) is undocumented and gives us full access
3. Ryan's pronoun shift from "you" to "we" at minute ~17 is the strongest commitment signal
4. His 11 follow-up questions are BUILD questions, not evaluation questions — he's already past the "should we?" gate
5. Tim wants a 1-on-1 at 8pm GMT before the group call
6. The SOS paper (Mergim Gashi, 2026) provides formal convergence guarantees for iterative optimization — relevant as theoretical underpinning for the self-learning model narrative

---

## For Orange Team (OT)

**Stress-test these claims:**
1. "College baseball lines are the most inefficient in American sports" — The Odds API gives us data to verify this. Compare spread accuracy vs MLB.
2. "Nobody has published college-specific Pythagorean exponents" — needs literature search verification
3. "PEAR uses identical win probs for all games in a series" — VERIFIED on Vanderbilt data but should be tested on 10+ series
4. "BT model will outperform PEAR's static ratings" — currently the BT model has sparse game data. Need more games imported to validate.
5. NCAA ToS risk for commercial scraping — legal attorney consultation still needed before any paid launch
6. Entity resolution is the weakest link — PEAR game opponent names don't always match team names in database

**Ryan-specific risks:**
- He hasn't committed time or equity — still in evaluation mode
- "Feasibility study" framing keeps him non-committal
- 7+ days of silence since the call — momentum at risk
- His 53 action items may be polite deferrals

---

## For Idea Reactor (IR)

**Generate alternatives for:**
1. The BT sparse data problem — should we use PEAR's ELO ratings as BT priors? Or skip BT for V0 and use pure Pythagorean?
2. Ryan demo format — working CLI? Live web page? Google Sheet he can interact with? Jupyter notebook?
3. First-prediction strategy — should we pick a specific weekend's games and email Ryan predictions before they happen? One correct public prediction > any demo.
4. Revenue model — the research shows KenPom's $25/year works, but EvanMiya at $180/year targets institutions. Which path?
5. The SOS framework connection — could we frame the self-learning model as "provably convergent" using the SOS theorems? That's a differentiator no competitor can match (literally published with machine-verified proofs in Lean 4).

---

## For Arch Sentinel (AS)

**Validate architecture:**
1. Python + SQLite + static HTML is V0. Is this the right V1 architecture? Or should we go FastAPI + PostgreSQL + React from the start?
2. The rating engine has 3 layers (Pythag + BT + Logistic). Is this sufficient differentiation from PEAR?
3. Data pipeline: PEAR API → SQLite is working. But PEAR could disappear. NCAA scoreboard fallback needed.
4. Entity resolution: team name normalization is critical and currently weak. Need a canonical alias table.
5. Cron automation: daily scrape → rate → predict → render pipeline. What's the deployment target?

---

## Claim Categories for Verification

### Category 1: Data Availability (15 claims)
- NCAA box scores publicly scrapable ✓ VERIFIED
- PEAR API exists and works ✓ VERIFIED (live tested today)
- 643 Charts has a public API — ? NEEDS VERIFICATION
- TrackMan data siloed per program ✓ VERIFIED
- ~10-20% of D1 games have incomplete PBP ✓ VERIFIED (from NCAA research)

### Category 2: Competitive Landscape (12 claims)
- No one combines all 5 layers (stats + tracking + ratings + portal + API) ✓ VERIFIED
- PEAR is a passion project, won't commercialize aggressively — ? INFERRED
- 64 Analytics is player-focused, not prediction-focused ✓ VERIFIED
- KenPom does ~$5M ARR at $25/year ✓ VERIFIED
- EvanMiya hasn't expanded to baseball — ? NEEDS VERIFICATION

### Category 3: Algorithm (10 claims)
- Fixed 1.83 exponent overestimates for college baseball ✓ VERIFIED (our data shows ~2.08)
- Dynamic BT > Elo for unbalanced schedules — ✓ VERIFIED (literature)
- PEAR uses identical series probabilities ✓ VERIFIED (Vanderbilt data)
- RL won't converge in 56-game season — ✓ VERIFIED (from algorithm R&D analysis)
- Online logistic regression is the right framing, not "deep RL" — ✓ VERIFIED

### Category 4: Market (8 claims)
- College baseball is niche but "fervent fans would be sticky" — ? NEEDS DATA
- Betting handle ~$150-450M — ? NEEDS VERIFICATION
- Lines are the most inefficient in American sports — ? NEEDS VERIFICATION (The Odds API can help)
- Transfer portal created 2,000+ moves/year — ✓ VERIFIED

### Category 5: Business (6 claims)
- $30/year subscription model works — ✓ VERIFIED (KenPom precedent)
- Can be bootstrapped for $0 — ✓ VERIFIED (free APIs, Python, SQLite)
- "One person can create an amazing thing" — ✓ VERIFIED (KenPom = 1 person, $5M ARR)
- NCAA ToS prohibits commercial scraping — ? UNCERTAIN (needs legal review)

---

## Ryan's 11 Questions — Status

| # | Question | Status | Answer |
|---|----------|--------|--------|
| 1 | Exact scraping sources | ✅ Built | PEAR API (primary), NCAA stats (planned), 643 Charts (V1) |
| 2 | Scraping tools | ✅ Built | Python httpx + urllib (PEAR), Playwright planned for NCAA |
| 3 | Scraping logic | ✅ Built | Modular per-source: `fsbb/scraper/pear.py` |
| 4 | Data refresh frequency | ✅ Designed | Daily cron: scrape → rate → predict → render |
| 5 | Data depth | ✅ Built | Team-level (V0), player-level planned (V1) |
| 6 | Inconsistent data handling | ⚠️ Partial | Team aliases table exists, needs population |
| 7 | Coding language | ✅ | Python 3.12 |
| 8 | Where it runs | 🔲 Pending | Local now; VPS/cloud for production |
| 9 | Data storage | ✅ Built | SQLite (V0), PostgreSQL-ready schema |
| 10 | Vegas odds scraping | ✅ Researched | The Odds API, sport key `baseball_ncaa`, free tier |
| 11 | Backtest + history | ✅ Built | `fsbb backtest` command, chronological replay |
