# V0/V1 Go-to-Market Strategy & Execution Plan

**Date:** 2026-03-31 | **Author:** Sentinel Coach
**Status:** COMPLETE — external research integrated (2 oracle agents, 43K + 53K tokens)
**Purpose:** Day-by-day execution plan for Mergim. Not strategy deck. Action document.

---

## Context Summary

**What Ryan actually wants (x-vector verified, speaker-corrected):**
- Ryan is a flat-affect PE evaluator (~83 verified claims, arousal range 0.28-0.59)
- His #1 concern: algorithm differentiation (not data pipeline — he considers that table stakes)
- His peak engagement: "You can predict the outcome... then that's really big. You wouldn't even need to go that far."
- His framing: "feasibility study" — not a startup, not a product. A test.
- His highest valence (V=0.32): "Getting the data right is crucial so the model doesn't hallucinate"
- His ask: "What would a V0 look like that convinces you this has legs?"

**The V0 (from ideas ranking):** The Nightly Prediction Page. Tonight's 10 biggest D1 games, predicted winner + confidence %, results filled in next morning. Build time: 12-18 hours. Composite score: 10/10.

**The follow-up message:** Already drafted (data/ryan_followup_message.md). Frames it as a backtest — Model A (PEAR static) vs Model B (ours with pitcher adjustment + recalibration). Promises results by Wednesday evening.

**The architecture:** 3-layer model (Pythagorean foundation → Bayesian prior-posterior → Logistic win probability). SQLite, Python, CLI-first, no ML frameworks. 48-72 hour build.

---

## 1. Sprint Execution Plan

### Day 0 — Monday (Today): Foundations

**ALREADY DONE:**
- [x] PEAR data scraped (308 teams, full ratings, JSON + CSV)
- [x] PEAR scraper built (`scripts/scrape_pear.py`)
- [x] Architecture spec written
- [x] Follow-up message to Ryan drafted

**TODAY (4-6 hours):**

| Hour | Task | Output | Ship-ugly version |
|------|------|--------|-------------------|
| 0-1 | Project scaffold: `fsbb/` directory, `pyproject.toml`, SQLite schema, Pydantic models | `db.py`, `schemas.py` | Skip Pydantic, raw dicts |
| 1-3 | NCAA scraper: connect to `henrygd/ncaa-api`, pull full D1 2026 season box scores | All ~8,400 games in SQLite | Scrape top 25 teams only (~600 games) |
| 3-4 | PEAR import: load existing `pear_ratings.json` into `pear_benchmark` table | Benchmark loaded | Direct JSON read, skip DB |
| 4-5 | Cleaning: team alias table (308 canonical names), dedup games | <1% unresolved names | Manual alias map for top 50 teams |
| 5-6 | Layer 1: Pythagorean W%, SOS (iterative), Elo with MOV adjustment | `ratings.py` producing rankings | Pythagorean + simple SOS only |

**Stretch:** Layer 2 Bayesian model started.

**End-of-day checkpoint:** Can you run `fsbb rank` and see a ranked list of D1 teams? If yes, Day 0 succeeded.

---

### Day 1 — Tuesday: The Model

**SEND RYAN FOLLOW-UP MESSAGE (morning, before starting build)**

| Hour | Task | Output | Ship-ugly version |
|------|------|--------|-------------------|
| 0-2 | Layer 2: Bayesian prior-posterior model. Prior = last season's Pythag. Update with each 2026 game. | `bayesian.py` | Skip priors, use current season only |
| 2-4 | Layer 3: Logistic regression win probability. Features: power_diff, home_adv, SOS_diff, rest_days | `win_prob.py` | Simple Elo-based win prob (no logistic) |
| 4-6 | Matchup engine: `fsbb matchup "Texas" "UCLA"` → win prob + CI | `matchup.py` | Print raw numbers, no formatting |
| 6-8 | PEAR validation: compute Spearman ρ between our rankings and PEAR's. Target: ρ > 0.90 | `validate_pear` CLI command | Eyeball correlation, don't compute |

**Stretch:** Historical backtest started (2024-2025 data).

**End-of-day checkpoint:** Can you type `fsbb matchup "Texas" "Mississippi State"` and get a win probability? If yes, Day 1 succeeded.

---

### Day 2 — Wednesday: The Backtest

| Hour | Task | Output | Ship-ugly version |
|------|------|--------|-------------------|
| 0-3 | Historical backtest: scrape 2024-2025 NCAA results. Run model on historical data. | 2 seasons in DB | 2025 only, top 50 teams |
| 3-5 | Accuracy calculation: our model vs PEAR's implied probabilities on historical outcomes | Accuracy %, Brier score | Simple win/loss accuracy only |
| 5-6 | Generate comparison output: "Our model: 58.2% accuracy. PEAR implied: ~53%." | Backtest report | Print to terminal |
| 6-7 | Tonight's predictions: pick 10 D1 games scheduled for Wednesday night. Generate predictions. | First prediction page | Text file with predictions |
| 7-8 | **Send Ryan the backtest results** (Wednesday evening as promised) | Message with numbers | |

**CRITICAL:** The backtest results MUST show a measurable edge. If the model doesn't beat PEAR by at least 2-3%, diagnose why before sending. Common issues:
- Pythagorean exponent not calibrated for college (should be ~1.83, not 2.0)
- SOS not converged (needs 3+ iterations)
- Home advantage coefficient wrong (college is ~55-57%, not MLB's 54%)

**End-of-day checkpoint:** Do you have a single number — "X% accuracy vs PEAR's Y%" — that you can send to Ryan? If yes, Day 2 succeeded.

---

### Day 3 — Thursday: Ryan Demo

**Demo call with Ryan (scheduled "maybe Thursday")**

| Hour | Task | Output |
|------|------|--------|
| 0-2 | Fill in Wednesday night's prediction results. Calculate hit rate. | "Went X/10 last night" |
| 2-4 | Build simple HTML page: today's predictions, yesterday's results, running accuracy | `index.html` (static) |
| 4-5 | Prepare demo talking points (see Section 2 below) | Notes |
| 5-6 | **Demo call with Ryan** | |

**If demo is pushed to Friday:** Use the extra day to accumulate 2 nights of predictions. More data = more credibility.

---

### Days 4-7 (Fri-Mon): Accumulate

| Day | Task |
|-----|------|
| Friday | Run daily predictions. Post results. Calculate running accuracy. Fix any model bugs. |
| Saturday | Full day of NCAA games = more data. 40+ games on a Saturday. |
| Sunday | Same. By Sunday evening: 3+ days of predictions, 80+ games predicted. |
| Monday | Weekly accuracy report. If accuracy holds: start planning V1. If not: diagnose and recalibrate. |

**Success criteria for Week 1:**
- 80+ games predicted
- Running accuracy > 55% on game winners (PEAR baseline: ~52-53%)
- At least one "headline prediction" — a game where our model strongly disagreed with PEAR and was right

---

### Week 2: What Constitutes "Enough Data"

**Minimum:** 150 games predicted (achievable in 1 week if running daily)
**Ideal:** 300 games (2 weeks). At this volume:
- Accuracy differences of 3%+ are statistically significant (p < 0.05 with n=300)
- Brier score comparison is meaningful
- Can slice by: conference games vs non-conference, home vs away, ranked vs unranked

**Share threshold:** Share results when you have 150+ games AND a headline number ("our model beat PEAR by X%"). Don't wait for perfection. Ryan's V0 framing is "feasibility study" — he wants signal, not polish.

---

## 2. Ryan Demo Script (Thursday Call)

### Pre-Call Setup
- Screen share ready with the prediction page open
- Terminal ready with `fsbb matchup` command
- Backtest results printed out
- **Tim NOT on the call** (or if Tim joins, Mergim leads every topic)

### The Script

**OPENING (2 min) — Show results first, not code:**

> "Ryan, I've been running the model since we talked. Let me show you the results."

Share screen → prediction page. Point to:
1. Yesterday's predictions vs actual results
2. Running accuracy number (top of page)
3. "PEAR would have predicted..." column

**Do NOT explain the architecture.** Do NOT mention Python, SQLite, or APIs. Just results.

---

**THE "HOLY SHIT" MOMENT (3 min):**

> "See these three games? PEAR's static rating would have predicted Team A to win all three. Our model predicted Team B in two of them. Team B won both. That's the pitcher adjustment working — PEAR ignores who's on the mound."

Pick the 2-3 most dramatic disagreements where your model was right and PEAR was wrong. Ryan cares about this because it's the same pattern as alpha generation — information asymmetry.

If you don't have dramatic disagreements yet:
> "The overall accuracy is X% vs PEAR's Y%. It's early data, but the gap is consistent."

---

**THE QUESTION (2 min):**

> "I want your read on this. If you were evaluating this as an investment — not the product, just the predictive edge — what would you need to see to be convinced?"

This uses Ryan's PE framework. It gives him evaluator agency. It makes him define his own success criteria. And it positions the backtest as a track record — language he understands from fund evaluation.

---

**THE CLOSE (2 min):**

> "I'll keep running daily predictions for the next two weeks. By [date], we'll have 300+ games of data. If the edge holds, we have a product. If it doesn't, we know before investing real time. I want your input on two things: which matchups matter most to you as a fan, and whether you think the free beta → paywall path or paid-from-day-one is the right launch strategy."

This does three things:
1. Gives Ryan homework (matchup preferences + pricing opinion)
2. Frames next steps as evidence-gathering, not commitment
3. Keeps the "feasibility study" language Ryan chose

---

**FALLBACK: If Backtest Isn't Ready**

Minimum viable demo: open a terminal, run `fsbb matchup "Texas" "Mississippi State"`, show the win probability. Then:

> "The model is running but I don't have enough predictions yet to share a meaningful accuracy comparison. Let me run it for a few more days and send you the results. But here's what a matchup looks like..."

Then type in 3-4 matchups Ryan cares about (ask him which teams to test). The interactive nature — him picking teams, seeing instant probabilities — is engaging even without backtest data.

---

## 3. Launch Strategy Research

### How Comparable Platforms Launched (Verified)

**KenPom.com (Ken Pomeroy):**
- **Data begins 2002** (kenpom.com/index.php?y=2002 exists). Free rankings of all ~330 D1 teams.
- **Day job:** Meteorologist at the **National Weather Service for 12 years** before going full-time.
- **Paywall added 2011** at $20/year. Front-page rankings stayed free; deeper team pages went behind paywall.
- **Demand was immediate:** "Within weeks, he knew he was very wrong" about there being few takers.
- **Quit NWS 2012-2013** — roughly one year after paywalling. Profitability was essentially instant.
- **Current pricing: $24.95/year** (verified on registration page).
- **"200K subscribers"** widely cited but **never confirmed** by Pomeroy. At $24.95, 200K = ~$5M ARR. Plausible but speculative. Similarweb ranks site ~22,000 globally.
- **Key pattern:** 9 years free (2002-2011) → audience → paywall → quit day job within 1 year. The NCAA tournament was the growth driver.

**EvanMiya.com (Evan Miyakawa):**
- **Background:** PhD Statistics, Baylor University (2022). BA Mathematics, Taylor University (2017). Day job: data scientist at **Zelus Analytics** serving multiple NBA teams.
- **Pricing: $29.99/month or $179.99/year** (verified).
- **100+ D1 programs subscribe** (confirmed). NCAA-approved for coaching staff use under NCAA bylaws.
- Partnership with **Dropback** for GM/NIL roster management tools. Featured in ESPN, CBS Sports, The Athletic, FiveThirtyEight.
- **Key pattern:** Launched with differentiation (player-level BPR, not just team-level). Faster path to institutional revenue because market already existed. Substack blog as free acquisition funnel.

**Bart Torvik (T-Rank):**
- **Day job:** Personal injury and food safety **attorney** in Evanston, IL. U of Minnesota Law grad (top of class). Former federal law clerk.
- **Started building 2014** as a hobby. Data goes back to 2008. Gained real traction ~2015.
- **Pricing: Permanently free.** No paywall, no subscription. Runs on his own Amazon server.
- **Differentiation:** Recency weighting (games lose 1% emphasis/day after 40 days), women's basketball, flexible date/venue splits.
- **NCAA adoption (2025):** Officially used as one of four advanced metrics in March Madness selection/seeding. An attorney's hobby project became an NCAA selection tool.

**Nate Silver / PECOTA / FiveThirtyEight:**
- Built **PECOTA** at KPMG (while employed as a consultant) in **2002-2003**. Sold to Baseball Prospectus for a partnership stake. Quit KPMG April 2004.
- **FiveThirtyEight** launched March 7, 2008 (political). Licensed to NYT August 2010. ESPN acquired July 2013. Traffic: 3.6M → 11.5M uniques March 2015-2016.
- **Never a paid sports product.** Monetized by selling the brand to media companies. Site shut down March 5, 2025.
- **Key pattern:** Build credibility through public predictions → media acquisition. The opposite of the subscription model.

**Common patterns across all four:**
1. All started as side projects while employed full-time (meteorologist, NBA data scientist, attorney, KPMG consultant)
2. Free first → prove accuracy → then monetize (paywall, institutional sales, or media acquisition)
3. The NCAA tournament / postseason drives most traffic for basketball; CWS is the equivalent for baseball
4. Institutional sales (to programs) are higher margin than consumer subs
5. Each found a differentiation niche: KenPom (tempo-free efficiency), EvanMiya (player-level BPR), Torvik (recency weighting), Silver (probabilistic forecasting)

### Implications for ForgeStream Baseball

**Don't paywall V0.** KenPom ran free for 9 years. Torvik is still free. You don't need 9 years, but you need at least 1 season of public accuracy data. The college baseball analytics audience is ~1/10th of basketball — adoption must precede revenue.

**Target the College World Series as launch milestone.** The CWS runs June 12-22, 2026 at Charles Schwab Field, Omaha. Conference tournaments all begin May 19. NCAA Selection Show is May 25 (noon ET, ESPN2). Regionals: May 29-June 1. Super Regionals: June 5-8. If the model is running and accurate by conference tournaments (May 19), you can ride the postseason attention wave. ESPN is broadcasting 4,000+ games in 2026 — expanded coverage means expanded audience.

**The institutional path is faster.** EvanMiya has 100+ D1 programs paying. NCAA approved his product for coaching staff use. 64 Analytics charges programs $2K-5.5K/year. If ForgeStream can offer better predictions at V1 (player-level), coaching staff will pay. But this requires V1, not V0.

**The Torvik precedent is most relevant.** An attorney built a college basketball analytics site as a hobby in 2014. It's now one of four metrics the NCAA officially uses for March Madness selection. He never charged a dollar. Your equation + domain knowledge is a stronger starting position than any of these founders had.

---

## 4. Tim & Connor Engagement Plan

### Tim's Role: Domain Knowledge Input (Not Meeting Participant)

**Why separate Tim from Ryan calls:** Tim's vocal dominance (0.784) suppresses Ryan's evaluative process. Tim's value is as a domain expert, not a meeting participant.

**Structured extraction format:**

*Weekly 15-20 min call or async voice notes with Tim:*

| Session | Topic | Output |
|---------|-------|--------|
| Week 1 | "Walk me through how you evaluate a team. What do you look at first?" | Bayesian prior calibration |
| Week 2 | "What makes a pitcher dominant in college vs MLB? What metrics matter?" | Pitcher model parameters |
| Week 3 | "How do you evaluate transfers? What predicts success at a new program?" | Transfer portal adjustment |
| Week 4 | "What non-statistical factors matter? Weather, altitude, fatigue, scheduling?" | Park/environment factors |

**Each session produces a structured "domain expert interview" document** that feeds directly into model parameters. Tim becomes the most important input to the product without attending every meeting.

### Connor's Role: Product Validator

Connor coaches at Appalachian State. His perspective:
- What tools does his coaching staff actually use?
- What data do they wish they had but don't?
- Would they subscribe to a better analytics platform? At what price?
- Can he beta-test the product with his program?

**Engagement:** After V0 is running, Tim introduces Mergim to Connor for a 20-min call. Connor evaluates the product as a potential customer, not a co-founder.

### Equity / Compensation Structure

**For a side-project at feasibility stage, don't formalize equity yet.** Here's the standard progression:

| Stage | Action | Typical Structure |
|-------|--------|-------------------|
| Feasibility (NOW) | No formal entity. Everyone contributes informally. | Handshake. Track hours loosely. |
| V0 proves edge | Form LLC or Inc. Assign founding equity. | Tech founder: 40-60%. Domain founder: 20-40%. Advisor: 5-10%. |
| V1 generates revenue | Formalize operating agreement. Vesting. | 4-year vesting, 1-year cliff. Standard. |

**Verified market data on splits (Carta 2024):**
- Median 2-founder split narrowed from 60-40 (2019) to **51-49 by 2024**
- For domain + technical co-founders where tech founder does bulk of building: **55-65% technical / 35-45% domain** is common
- YC guidance: equal splits are fine if contributions are genuinely equal; don't default to 50/50 out of politeness

**Recommended split (if it gets there):**
- Mergim (technical architect, sole builder): 55%
- Ryan (PE structuring, business strategy): 25%
- Tim (domain expert, network, advisory): 10%
- Connor (product validation, coaching perspective): 5%
- Reserve (future hires/partners): 5%

**Don't discuss this with Ryan yet.** He's in "feasibility study" mode. Bringing up equity before proving the model works signals premature commitment. Wait until Ryan says "let's build V1." Every comparable founder (KenPom, EvanMiya, Torvik, Silver) built solo first and formalized later.

**Precedent:** All four comparable platforms were built by solo founders with day jobs. None started with co-founders or equity structures. The product proved itself first; the business followed.

---

## 5. Content & Distribution Strategy

### Where College Baseball Fans Are (Verified)

| Platform | Audience | Strategy |
|----------|----------|----------|
| **Twitter/X** | Core community. @d1baseball is dominant voice. @EvanMiya has 54K followers. Key hashtags: #RoadToOmaha, #CWS, #NCAABaseball | Create @ForgeStreamBB. Post daily predictions. Quote-tweet results. Tag @d1baseball, @ncaa_base_stat |
| **Reddit r/collegebaseball** | 38K+ confirmed subscribers (likely 80-150K current). Highly seasonal — spikes Feb-June, especially CWS week | Post weekly prediction accuracy reports. Don't spam. Add genuine value. |
| **D1Baseball.com** | Full paywall: $15.99/mo or $139.99/yr. Has "D1 Extra" tier at $189.99/yr. Expert-only chats with conference insiders. | Not a launch channel. Long-term potential competitor or partner. |
| **Baseball America** | Insider Club: $9.99/mo or $74.99/yr. Draft/prospect-heavy. | Not a priority for V0. |
| **Podcasts** | **11Point7** is self-described #1. **D1Baseball Podcast** (Kendall Rogers, Aaron Fitt). **College Baseball Show.** **BA College Podcast.** | Offer to be a guest once accuracy is proven over 2+ weeks. |
| **Discord** | No dominant college baseball Discord exists — gap in market. Betting-oriented channels dominate (BettorEdge, Outlier Insights). | Consider launching a ForgeStream Discord for analytics community — low-hanging fruit. |

### Minimum Viable Content Schedule

| Day | Content | Platform | Time |
|-----|---------|----------|------|
| Daily | Tonight's top 10 predictions | Twitter/X | 10 AM ET (before games) |
| Daily | Yesterday's results + running accuracy | Twitter/X | 8 AM ET |
| Weekly | "This week in FSBB" — headline predictions, accuracy, biggest misses | Reddit + Twitter | Monday |
| Weekly | PEAR vs FSBB accuracy comparison | Twitter | Friday |

**Total time: ~30 min/day.** The predictions are automated; the content is just formatting and posting. This can be further automated with a Twitter bot.

**Key principle:** Post predictions BEFORE games. Accountability builds credibility. Anyone can claim accuracy after the fact. Posting predictions in advance is proof.

### Launch Timing

| Date | Event | Action |
|------|-------|--------|
| **Now (March 31)** | Mid-season. ~7 weeks of regular season remain. | Build model, start predictions |
| **April 1-30** | Regular season continues. Tuesday = national rankings reshuffles. | Accumulate accuracy data, build audience |
| **May 1-18** | Conference regular season stretch run. Bubble teams fighting for at-large bids. | Higher-stakes predictions, more traffic |
| **May 19-24** | Conference tournaments (SEC @ Hoover AL, ACC @ Charlotte, Big 12 @ Surprise AZ). Highest-engagement week outside Omaha. | Tournament bracket predictions |
| **May 25** | NCAA Selection Show (noon ET, ESPN2). Bracket reveal = huge social traffic. | 64-team field predictions, bracket projections |
| **May 29-June 1** | Regionals (64 teams, 16 sites) | Regional winner predictions |
| **June 5-8** | Super Regionals (16 teams, 8 sites) | Head-to-head matchup predictions |
| **June 12-22** | College World Series, Charles Schwab Field, Omaha. Championship Series June 20-22. | Peak attention. If model is accurate, this is the breakout moment |

**The window is NOW.** There are ~8-10 weeks left in the 2026 season. Starting today gives enough runway to prove accuracy before the postseason attention spike.

---

## 6. Pricing & Monetization

### Competitive Pricing Landscape

| Platform | Consumer Price | Institutional | Notes |
|----------|---------------|---------------|-------|
| KenPom | ~$19.99/year | None disclosed | 100-200K subs (est.). Pure destination site, no social strategy. |
| EvanMiya | $29.99/month or **$179.99/year** | 120+ D1 programs (NCAA-approved scouting service) | 54K X followers. Substack blog as free acquisition funnel. |
| D1Baseball | $15.99/month or $139.99/year. Extra: $22.99/mo or $189.99/yr | Expert chats with insiders | Full paywall. The ESPN Insider of college baseball. |
| 64 Analytics | $12.99/month ($156/year) | $2K-5.5K/year Portal Pass | Player-level, portal focus |
| PEAR | Free | None | Passion project |
| Bart Torvik | Free | None | Ad-supported or none |

### Recommended Pricing (V0 → V1 → V2)

| Phase | Price | Rationale |
|-------|-------|-----------|
| **V0 (free beta)** | $0 | Build audience, prove accuracy, get feedback. Nobody pays for unproven predictions. |
| **V1 (proven edge)** | $29.99/year consumer | Match KenPom's willingness-to-pay proof point + slight premium for baseball niche |
| **V1 premium** | $9.99/month ($120/year) | For bettors: daily predictions, API access, alerts |
| **V2 institutional** | $2,000-3,000/year | For coaching staff: player-level data, transfer portal analytics |
| **API access** | $49/month | For developers, data scientists, betting models |

### College Baseball Betting Market (Verified)

- **Total US sports betting: ~$14B handle in 2024.** College baseball is a small, unquantified fraction.
- **Platforms offering it:** DraftKings, FanDuel, BetMGM, Caesars, BetUS, MyBookie, Bally Bet — all offer college baseball lines.
- **Line efficiency:** No peer-reviewed study on college baseball specifically. Adjacent research shows college basketball markets reject efficiency hypotheses in 13/24 bins. **Low-volume markets are structurally LESS efficient** because fewer sharp bettors correct prices.
- **Existing prediction models for college baseball betting: NONE FOUND.** This is a genuine white space.
- **Implication:** A model with even modest predictive edge would be operating in one of the least efficient betting markets in American sports. The opportunity isn't volume — it's margin per bet.

**Ryan's pricing signal:** "There's fervent fans, they would be sticky" + "niche addressable market" → he's thinking about unit economics, not volume. Position as premium niche, not mass market.

**The gambling question Ryan should answer:** "Free beta to build audience, or paid from day one?" (Already in the follow-up message.) His PE background will give a structured answer. Let him own the pricing decision — it increases his investment in the project.

---

## 7. Legal & Compliance Quick Check

### NCAA Data Scraping (Verified Legal Position)
- **NCAA TOS explicitly prohibits:** Commercial use, derivative works, and transfer/sale of NCAA content. This is a contractual restriction, not a copyright one.
- **hiQ v. LinkedIn (9th Cir. 2022):** Scraping publicly accessible data does NOT violate the CFAA (Computer Fraud and Abuse Act). But ToS violations remain a contract law risk.
- **Enforcement reality: ZERO documented cases** of NCAA pursuing analytics companies for scraping stats. KenPom (since 2002), Torvik (since 2014), EvanMiya, PEAR, 64 Analytics — all operate without challenge.
- **EvanMiya's NCAA approval** for coaching staff subscriptions strongly suggests NCAA is not adversarial to commercial analytics tools.
- **Risk mitigation:** Sell analytical outputs and derived metrics, not raw box score data. Standard industry practice.
- **Facts/statistics are not copyrightable:** Feist v. Rural Telephone (1991) — you cannot copyright factual data. The arrangement may be protected, but the facts themselves are not.
- **Rate limiting:** Be polite. 5 req/s max. Include identifying User-Agent ("ForgeStream/1.0").

### Team Names & Logos
- **Team names:** Generally usable in editorial/analytical context. KenPom, EvanMiya, cfbstats.com, 64 Analytics, PEAR all use team names as plain text data labels — considered descriptive fair use.
- **Logos:** Do NOT use. Logos are trademarked by universities, licensed through the Collegiate Licensing Company (CLC).
- **NCAA® trademark:** Do not use "NCAA" as part of your product name. Say "college baseball" instead. NCAA has 70+ federally registered event marks.
- **AVOID these trademarked terms:** "College World Series," "Road to Omaha," "Final Four," "March Madness," "The Big Dance." NCAA successfully enjoined a developer for "April Madness" and sent C&D to a Virginia urology practice over "Vasectomy Madness." They're aggressive on event trademark names.
- **No known C&D actions** against pure statistics/analytics sites that use only team names as data labels and avoid logos.

### Betting/Gambling Disclaimers
- **Required:** "For entertainment purposes only. Not gambling advice."
- **Standard in industry:** KenPom, EvanMiya, and 64 Analytics all avoid explicit gambling framing while clearly serving bettors.
- **State-specific:** Some states regulate prediction services. A simple disclaimer is sufficient at V0 scale.

### Recommended Disclaimer (following cfbstats.com / College Board format)
> "ForgeStream Baseball provides statistical analysis of college baseball games. Predictions are probabilistic estimates based on historical data and are not guaranteed. This product is for informational and entertainment purposes only. NCAA® is a trademark registered by the National Collegiate Athletic Association, which is not affiliated with, and does not endorse, this product."

---

## 8. Success Metrics

### V0: Feasibility Study (Weeks 1-2)

| KPI | Target | How to Measure |
|-----|--------|----------------|
| Ryan says "build V1" | Binary yes/no | Demo call outcome |
| Win prediction accuracy | >55% (PEAR baseline ~52-53%) | Games predicted correctly / total games |
| Brier score | <0.240 (baseline 0.250) | Mean squared error of probabilities |
| PEAR rank correlation | Spearman ρ > 0.90 | Our rankings vs PEAR's |
| Headline predictions | ≥3 "disagreed with PEAR and was right" | Manual tracking |

### V0 Running 1 Week (Days 7-14)

| KPI | Target | How to Measure |
|-----|--------|----------------|
| Games predicted | >150 | Count |
| Accuracy sustained | >55% at n=150+ | Rolling accuracy |
| Twitter followers | 100+ (low bar, but tracking) | @ForgeStreamBB |
| Ryan engagement | Responds to backtest data | Message/call frequency |

### V1: First Paying Subscriber (Months 1-3)

| KPI | Target | How to Measure |
|-----|--------|----------------|
| Unique visitors/week | 500+ | Analytics |
| Free tier users | 200+ (email captured) | Signup count |
| First paying subscriber | 1 | Payment received |
| Accuracy through season | >56% on 500+ games | Running stats |

### V1 Running 1 Month (Month 2-4)

| KPI | Target | How to Measure |
|-----|--------|----------------|
| Paying subscribers | 50+ at $29.99/year | Revenue |
| Monthly revenue | $500+ (covers hosting) | Stripe |
| Institutional interest | 1 program inquiry | Inbound |
| Media mention | 1 (blog, podcast, tweet from established account) | Monitoring |
| Model accuracy | >57% across 1000+ games | Season data |

### Track from Day 1

- **Prediction accuracy** (daily, cumulative)
- **PEAR comparison** (weekly)
- **Response rate** from Ryan (engagement proxy)
- **Time spent building vs time spent marketing** (optimize over time)
- **Model calibration** — are 60% confidence predictions winning 60% of the time? (Brier decomposition)

---

## 9. The One-Page Summary (Print This)

**WHAT:** Nightly prediction page for D1 college baseball. Our model vs PEAR. Results posted publicly.

**WHY NOW:** 8-10 weeks left in 2026 season. Conference tournaments + CWS in May-June. Window to prove accuracy before postseason attention spike.

**BUILD ORDER:**
1. Monday: Scraper + data + Layer 1 ratings
2. Tuesday: Layers 2-3 + matchup engine. **SEND RYAN MESSAGE.**
3. Wednesday: Backtest + first predictions. **SEND RYAN RESULTS.**
4. Thursday: **DEMO CALL WITH RYAN.**
5. Fri-Mon: Accumulate daily predictions.
6. Week 2: 300+ game accuracy report.

**DEMO SCRIPT:** Results first. "Holy shit" disagreement examples. Ask "what would convince you?" Close with homework for Ryan.

**PRICING:** Free beta now. $29.99/year at V1. $2K+/year institutional at V2.

**TIM:** Weekly domain extraction calls. NOT on Ryan demos.

**RYAN:** Send backtest, ask him to evaluate. Let him define success criteria. Don't push commitment — he'll commit when the numbers convince him.

**THE ONE NUMBER THAT MATTERS:** Model accuracy vs PEAR. If it's higher, everything else follows. If it's not, nothing else matters. Build the model. Run the predictions. Let the numbers talk.

---

*Written by Sentinel Coach. For Mergim's execution. 2026-03-31.*
