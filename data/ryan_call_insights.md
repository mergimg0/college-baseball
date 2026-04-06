# Ryan McCarthy Call — Deep Insights
**Date:** 2026-03-30 | **Duration:** 47 min | **Claims:** 510 | **Analyst:** Sentinel Insight Miner

---

## 1. Sentiment Trajectory & Emotional Arc

### Phase Map

| Phase | Time | Ryan's Mode | Energy | Key Signal |
|-------|------|-------------|--------|------------|
| **Onboarding** | 00:00–01:30 | Teaching/explaining | Medium-high | Explaining baseball structure to a non-American; warm, patient |
| **Context dump** | 01:30–05:30 | Educator | High | KenPom history, PEAR walkthrough, screen sharing — wants you to see what he sees |
| **Technical probe** | 05:30–10:00 | Evaluator | Steady | Deep into WOBA, run expectancy, data sources — testing your engagement |
| **Energy spike #1** | ~11:00 | Excited | **Peak** | When you mentioned 6-4-3 Charts API + Trackman data: "I've got to look into 643 charts. Is that free?" — genuine surprise, new information |
| **Recalibration** | 13:00–17:00 | Grounded realist | Lowered | Ryan says "baseball isn't a huge addressable market," "I'm a big fan of not sinking money" — PE risk discipline activating |
| **Energy spike #2** | ~26:00 | Inflection | **Peak** | Asks the V0 question: "What would you want to see as a V0 that can really convince you?" — this is the pivot from evaluating to investing |
| **Energy spike #3** | ~36:00 | Convinced enough | High | "Is the data there to make something happen?" followed by "It has fervent fans. The fervent fans would be sticky" — talking himself into it |
| **Closing** | 40:00–47:00 | Collaborative | Warm/aligned | "I think that's a great idea," next steps agreed, scrapers already running |

### Three Inflection Points (? INFERRED from claim density + tone markers)

1. **Inflection 1 (~11:00, chunk 2):** You introduce the 6-4-3 Charts API — something Ryan didn't know existed. His energy spikes ("I've got to look into 643 charts"). This is the moment he realizes you bring information asymmetry, not just technical execution. **The dynamic shifts from "Ryan teaches Mergim baseball" to "Mergim has done deep research Ryan hasn't."**

2. **Inflection 2 (~26:00, chunk 5):** Ryan asks the V0 question: "What would you want to see as a V0 that can really convince you that this has legs?" This is a PE deal-structuring question disguised as a product question. He's not asking about features — he's asking about your commitment threshold. **The dynamic shifts from "exploring feasibility" to "negotiating scope of engagement."**

3. **Inflection 3 (~36:00, chunk 7):** After you demonstrate the live scraper pulling PEAR data in real-time (308 teams, multiple rating systems, CSV/JSON output), Ryan says: "Is the data there to make something happen? Is the data there to place a bet that isn't hugely onerous?" Then self-answers: "It has fervent fans. The fervent fans would be sticky." **The dynamic shifts from "evaluating" to "rationalizing going forward."** Tim's interjection about ESPN+ growth and Connor as a resource seals it.

### Confidence Level: Medium-High
The timestamps are approximate (chunk-based, not exact), but the arc is clear in the claim sequence.

---

## 2. What Ryan DIDN'T Say

### Cross-Reference: Ryan's Brief vs Call Content

Ryan's brief had **3 structured questions**:

| Brief Question | Discussed? | Depth | What Was Missed |
|----------------|-----------|-------|-----------------|
| Q1: Difficulty of replicating PEAR? | **Partially** | Data pipeline discussed at length. You read Claude's bottleneck analysis aloud. But neither party defined "replicate" — is it PEAR's team ratings only, or PEAR + player metrics? | **No concrete timeline was committed to.** You said "about a week" but Ryan didn't push back or agree to a deadline. |
| Q2: Where are real bottlenecks? | **Yes, well covered** | Both agreed: data cleaning > modeling > scraping. Ryan's "the modeling is going to be the hardest part" got Ryan's enthusiastic agreement. | **Never discussed cost bottlenecks.** Who pays for server infra? Who pays for 6-4-3 Charts if it's institutional pricing? |
| Q3: Partner with PEAR vs build? | **Barely touched** | Brief explicitly asked this. On the call, PEAR was discussed as a data source to scrape from, never as a potential partner. Ryan never raised the partnership question. | **The build decision was assumed, never debated.** This is notable — it means Ryan already decided "build" before the call. |

### Topics Ryan Avoided (? INFERRED)

1. **Equity/ownership structure.** Zero discussion. For a PE professional, this omission is deliberate. He's not ready to formalize roles — still in the "is this worth my time" phase. (Confidence: High)

2. **His own time commitment.** Ryan never said "I'll spend X hours/week on this." He offered domain knowledge and direction but no specific time pledge. (Confidence: High)

3. **Revenue projections or market sizing.** Despite being PE, he didn't run numbers on the call. No "if we get X subscribers at Y price..." — this suggests he hasn't modeled it yet, or he already has and doesn't want to anchor the conversation. (Confidence: Medium)

4. **Legal/compliance for gambling features.** You mentioned "the gambling aspect is where the revenue multiplier lives" — Ryan didn't respond to this specifically. A PE professional with gambling experience would normally flag state-by-state legality. (Confidence: Medium)

5. **His own failed attempts.** Ryan clearly has tried to use ChatGPT for this: "I've asked ChatGPT a bunch of times and they give me the widest range ever." He's been working on this problem alone for a while but never explicitly said how long or what he's tried. (Confidence: High)

6. **Women's softball expansion.** Ryan mentioned it in passing ("And then there is women's softball, we won't get into it") and immediately shut it down. This is a market-sizing instinct — he sees the opportunity but considers it scope creep for now. (Confidence: High)

---

## 3. Power Dynamics & Decision Signals

### Due Diligence Patterns

Ryan uses classic PE evaluation frameworks without naming them:

1. **TAM qualification** (chunk 7, ~35:00): "The reality is it's just not a huge addressable market. It's a niche addressable market." This is PE-speak for "I've mentally done the TAM calculation and it's small." He then qualifies it: "It has fervent fans. The fervent fans would be sticky." — testing whether niche + sticky = viable. (Confidence: High)

2. **Effort-to-reward ratio** (~16:00): "Could you do this with a reasonable amount of effort?" and "You're not sinking a ton of money into it." Ryan is sizing whether this is a $0 hobby, a $5K side project, or a $50K venture. His framing suggests he's targeting the $0-$5K range. (Confidence: High)

3. **Competitive moat assessment** (~18:00): "Being a first mover, people won't even know where to begin" — this is Ryan testing whether the difficulty = moat. He's assessing defensibility. (Confidence: High)

4. **Data availability as binary gate** (~36:00): "Is the data there to make something happen?" — not "can we build a great model?" but "is the data even there?" This is a go/no-go question, not a quality question. He's looking for permission to proceed. (Confidence: High)

### Conviction Signals

| Signal Type | Ryan's Words | What It Means |
|-------------|-------------|---------------|
| **Commitment language** | "I think we can push this quite far" (~17:00) | First-person plural. He's in, conditionally. |
| **Ownership language** | "We should stress test it together" (~31:00) | "Together" = he's planning to be involved, not just watching. |
| **Investment framing** | "I'm a big fan of not sinking money... until we really get to a block" (~17:00) | Classic PE staged investment mentality. Not "no money" — "not yet." |
| **Authority assertion** | "We can get you up to speed on this" (~13:00) | Asserting domain authority — he's the expert here, you're the builder. |
| **Deference on tech** | "One person can create an amazing thing with AI" (~01:00) | Complete deference on technical capabilities. No probing of your AI claims. |
| **Hedge language** | "I think it's going to be one of those where we just go out and see what sticks" (~28:00) | Low commitment framing — keeping optionality open. |

### Deference Patterns

- **Ryan defers to you on:** Technical implementation, AI/ML capabilities, scraping feasibility, UI/frontend. He never questions whether you can build it.
- **Ryan asserts on:** Baseball domain knowledge, market knowledge, business model intuition, what fans want, what data matters.
- **Ryan defers to Tim on:** Nothing specific — Tim's role is connector/supporter, not decision-maker.
- **Shift from evaluating to collaborating:** Happens at the V0 question (~26:00). Before that, Ryan is asking diagnostic questions. After, he's asking "what should WE do next?" (Confidence: High)

---

## 4. Hidden Requirements (Implicit, Not Stated)

| # | Implicit Requirement | Evidence | Confidence |
|---|---------------------|----------|------------|
| 1 | **Must see working scraped data before committing further** | V0 question (~26:00) + his immediate interest when you showed live scraper output. He needs tangible proof, not plans. | High |
| 2 | **Must be bootstrapped / zero upfront investment** | "I'm a big fan of not trying to sink money into anything" (~17:00). This isn't frugality — it's PE deal structure. He won't invest in speculative tech. | High |
| 3 | **Must be explainable to a non-technical person** | Repeatedly translates concepts using analogies (Premier League, cricket bowler). Needs to explain this to others (investors? wife? colleagues?). | Medium |
| 4 | **Must match or beat PEAR's current rankings as a baseline** | "Is there some level of authorship going into the ratings?" and comparing PEAR vs 64 Analytics rankings (~38:00). He uses ranking accuracy as a proxy for model quality. | High |
| 5 | **Must not require his coding involvement** | "I'm not a coder" (~12:00). He'll provide domain expertise, not PRs. If the project requires him to write code, he's out. | High |
| 6 | **Must have a path to being "set it and forget it"** | "The ongoing maintenance is not too crazy" (his words via chunk 3). He's imagining a product that runs itself, not a consulting engagement. | Medium |
| 7 | **Must demonstrate value within the current baseball season** | "We're like a handful of weeks into the college baseball season" (~28:00). He's feeling time pressure — if this isn't useful this season, the energy dies. | High |
| 8 | **Must validate against known outcomes (backtesting)** | "I wonder if there'd be a way to look back and say, what were the key drivers? You already know the outcome, right?" (~34:00). He wants backtesting, not just forward prediction. | High |
| 9 | **Must be visually comparable to KenPom/EvanMiya** | Extensive discussion of UI quality ("this is quite a good UI," "best in breed for college basketball"). The product must look professional, not like a data dump. | Medium |
| 10 | **Must integrate Tim and Connor's domain knowledge** | Tim suggests Connor as a resource; Ryan doesn't push back. The family involvement is both a feature and a requirement — they expect to be part of it. | Medium |
| 11 | **His conviction criteria is "data feasibility first, model second"** | "Starting at the data first seems like a good call for me" and "is the data there to make something happen?" — he'll only evaluate the model once data availability is proven. | High |
| 12 | **Must not over-promise on prediction accuracy** | "This will always be somewhat more imperfect" — Ryan agreed immediately ("Yeah, yeah, definitely"). He needs realistic framing, not hype. | High |

---

## 5. Information Asymmetry

### What Ryan Knows That We Don't

| Knowledge Area | Specific Intel | How It Helps |
|----------------|---------------|--------------|
| **KenPom's business model internals** | 15-year subscriber. Knows the UX evolution, pricing psychology, retention patterns firsthand. | Can validate whether our pricing and UX choices match proven patterns. |
| **64 Analytics subscription experience** | Paying customer. Knows what it does well and poorly from a user perspective. | Direct competitor intelligence we can't get from outside. |
| **PEAR founder's identity/background** | Knows he's ~20s, Arkansas-based, part-time, open-source oriented. | Competitive intelligence: PEAR likely won't scale or commercialize aggressively. |
| **PE deal structuring** | HIG Capital ($65B+ AUM). Knows how to structure investments, evaluate markets, negotiate partnerships. | If this becomes a real business, Ryan brings the business architecture. |
| **College baseball fan psychology** | "Fervent fans would be sticky." He knows WHAT fans want because he IS one. | Product-market fit intuition we can't easily replicate. |
| **Bill Petti / baseballr ecosystem** | Knows the R-based NCAA scraping community exists. | Data pipeline alternatives beyond Python. |
| **Sidearm Stats as a data source** | Mentioned it as a potential source for 64 Analytics' player data. | Alternative scraping target we hadn't identified. |
| **D1 Baseball (paid site) as competitor** | Tim flagged this; Ryan confirmed awareness. | Another competitor in the landscape. |
| **The "imperfect model" tolerance** | 64 Analytics refused to do preseason rankings due to uncertainty. Ryan understands and accepts model limitations. | We don't need perfection to deliver value. |

### What We Know That Ryan Doesn't

| Knowledge Area | Specific Intel | Strategic Value |
|----------------|---------------|-----------------|
| **6-4-3 Charts has a public API** | Documented at 643charts.com/api. Institutional pricing exists but API may be accessible. | Potential Trackman-derived data source nobody else is aggregating into a consumer product. |
| **MLB outlawed Trackman data exclusivity for amateur baseball** | Regulatory change creating a tailwind for data aggregation. | Moat opportunity: if showcase/college data can't be hoarded, first aggregator wins. |
| **Pixellot + TruMedia partnership (Oct 2024)** | Nearest forming competitor is B2B only, no consumer play. | Timing advantage: no consumer competitor is even close. |
| **Our equation (alpha generation background)** | Originally built for trade organization, proven in code generation, adaptable to baseball prediction. | Mathematical edge nobody in the space has — Tim told you this, not Ryan. |
| **ForgeStream's domain knowledge extraction architecture** | Extracts tacit knowledge from 2-3 domain experts. | Ryan IS the domain expert. His knowledge can be systematically extracted and encoded. |
| **EvanMiya's exact business model** | $180/year, 120+ D1 programs, NCAA-approved scouting service, Dropback partnership. | Proves institutional market exists at higher price points than KenPom's $25. |
| **NCAA data quality research** | ~10-20% incomplete PBP, student SID entry issues, NCAA acknowledged stats errors. | Realistic expectation-setting for Ryan on data challenges. |
| **Python scraping ecosystem** | `collegebaseball`, `CollegeBaseballStatsPackage`, `baseballr`, `henrygd/ncaa-api`. | Multiple proven tools exist — not building from scratch. |
| **The "Statcast gap" as long-term positioning** | Being the "Baseball Savant for college" is the endgame. | Long-term vision Ryan hasn't articulated but would resonate with PE thinking. |

---

## 6. The "Convinced" Threshold — Reverse-Engineered

### What Ryan Actually Needs to Flip from "Evaluating" to "Committed"

Based on everything he said, Ryan's conviction criteria is a **three-gate sequence**:

#### Gate 1: Data Feasibility (STATUS: Nearly Passed)
**Evidence:** "Is the data there to make something happen?" + his reaction to the live scraper output.
**What satisfies it:** Show him a dataset with:
- 308 D1 teams with basic ratings (already scraped from PEAR)
- Historical data back to ~2006 (PEAR has this)
- Real-time updates (scraper is running)
- Cross-referenced with 64 Analytics rankings (you showed this live)

**He's 80% through this gate.** The remaining 20% is seeing clean, structured data in a format he can read (spreadsheet/CSV he can open and gut-check).

#### Gate 2: Model Differentiation (~0% Started)
**Evidence:** "What would differentiate this from an algorithm perspective?" + "I need to think about differentiation from an algorithm perspective a little bit more."
**What satisfies it:**
- A concrete explanation of WHY your model would be different from PEAR's
- Backtesting results: "in the 2025 season, our model would have predicted X correctly that PEAR got wrong"
- The "deterministic proof" he referenced — show the equation working on historical data

**He hasn't seen any model output yet.** This is the real proving ground. Data availability was necessary but not sufficient.

#### Gate 3: Low-Effort Maintenance (~10% Addressed)
**Evidence:** "I'm a big fan of not sinking money" + "reasonable amount of costs, ongoing maintenance not too crazy."
**What satisfies it:**
- Show that once built, the system auto-updates daily
- Cloud hosting costs are <$50/month
- No need for a team — one person (you) maintains it
- Revenue covers costs quickly (even 100 subscribers × $25 = $2,500/year)

**He needs to believe this won't become a money pit or a time sink.**

### The Actual Conviction Statement He's Looking For

Ryan wants to be able to say to himself (and possibly Tim):

> "We can build something that pulls NCAA data automatically, runs it through a model that's better than PEAR, displays it on a clean site, and do it all for basically nothing. If 200 people pay $25, we're profitable. If not, we lose nothing."

That's the sentence. Build toward making that sentence true and demonstrable. (Confidence: High)

---

## 7. Meta-Insights (Non-Obvious Patterns)

### 7.1 Ryan Is Doing Due Diligence on YOU, Not Just the Project

The call structure is classic PE "founder evaluation." Ryan is:
- Testing domain knowledge (can you follow baseball concepts?)
- Testing preparation (did you research before the call?)
- Testing initiative (are you already building, or waiting to be told?)
- Testing judgment (do you overpromise or stay grounded?)

When you mentioned 6-4-3 Charts and showed live scraper output, you passed 2 of 4 tests (preparation and initiative). When you said "The actual baseball slang, no" honestly, you passed the judgment test. The domain knowledge gap is expected and not a dealbreaker — he explicitly offered to fill it ("We can get you up to speed"). (Confidence: High)

### 7.2 The ChatGPT Admission Is More Revealing Than It Seems

Ryan said: "I've asked ChatGPT a bunch of times and they give me the widest range ever, so I don't know." And then you (who use Claude) started reading Claude's research output aloud. Ryan's reaction: "I agree with what Claude said."

The subtext: **Ryan has been trying to build this himself with ChatGPT and failing.** He's not just evaluating an opportunity — he's been stuck at the feasibility stage for weeks/months and is looking for someone who can actually execute. Your Claude-powered research output was qualitatively better than anything ChatGPT gave him. This is a conversion signal. (Confidence: Medium-High)

### 7.3 The "Feasibility Study" Reframe Is Protective

At ~36:00, you reframed the project: "This is honestly more like a feasibility study at this point. The study is about doing this without overbuilding anything." Ryan immediately agreed.

This reframe served two purposes:
1. **Reduced perceived commitment** — nobody's "starting a company," just "studying feasibility"
2. **Gave Ryan an exit ramp** — if the data isn't there, the study concludes and nobody lost

This is the correct framing for someone in PE who evaluates 100 opportunities for every 1 they invest in. Let him stay in "studying" mode until the data proves itself. Pushing for commitment too early would activate his PE skepticism. (Confidence: High)

### 7.4 Tim's Role Is More Strategic Than Either Party Acknowledges

Tim spoke only 27 claims (5.3% of the call) but his interventions were surgically timed:
- **ESPN+ growth comment** (~36:30): Injected at the exact moment Ryan was sizing the market as "niche." Tim countered with a growth narrative. Market timing defense.
- **Connor as a resource** (~36:45): Offered another family member with direct coaching expertise. Network deepening.
- **"It's growing in popularity"** — the only forward-looking market claim in the conversation. Ryan and you were both grounded in current state; Tim injected optimism at the right moment.

Tim is playing the role of "deal catalyst" — he brought you together, and he's now making sure the deal doesn't die in the diligence phase. (Confidence: High)

### 7.5 Ryan's Language Shifted from "You" to "We" at Minute ~17

Early call: "Is there a way for us to create something?" (inclusive but vague)
Mid-call: "What would you want to see as a V0?" (asking you)
Late-call: "We should stress test it together" / "We should map out the data" / "Let me let these scrapers keep ingesting"

The pronoun shift from "you" to "we" happened after he saw the live scraper output and the Claude research. He started owning the project linguistically. This is a stronger commitment signal than any explicit statement. (Confidence: High)

### 7.6 The Softball Mention Is a Hidden Market Signal

Ryan mentioned women's softball and immediately shut it down: "We won't get into it." But he brought it up unprompted. This means:
1. He's already thinking about expansion markets
2. Softball uses the same NCAA infrastructure (same scraping targets)
3. He's disciplining himself to focus (good PE instinct)
4. **It's a natural Phase 2 if Phase 1 works**

File this for later. When the baseball V0 proves feasible, softball is the obvious expansion pitch. Same data pipeline, same model architecture, different sport. (Confidence: High)

---

## 8. Risk Signals (What Could Go Wrong)

| Risk | Signal | Severity |
|------|--------|----------|
| **Ryan treats this as a hobby, not a venture** | "More as fans, we're just like, wouldn't it be cool" (~00:47) | Medium — he may lose interest after the novelty wears off |
| **Scope creep from Tim** | Tim sees multiple opportunities (McMillan, baseball, advisory). May dilute focus. | Low — Ryan is more disciplined than Tim |
| **The "feasibility study" stays a study forever** | Ryan's PE instinct is to evaluate, not build. May never cross the build threshold. | Medium — needs a forcing function (season ending, competitor launching) |
| **You're doing all the work for free** | No discussion of compensation, equity, or cost sharing. You're building scrapers, doing research, and building the V0 on spec. | High — needs to be addressed before significant further investment |
| **PEAR commercializes first** | PEAR is iterating fast ("every other week there's something new"). If PEAR adds player data and a paywall before you launch, the window narrows. | Medium — but PEAR is a passion project, unlikely to monetize aggressively |

---

## 9. Recommended Next Actions (Derived from Insights)

1. **Send Ryan the scraped data in a Google Sheet within 48 hours** — This passes Gate 1 definitively. Let him gut-check the rankings against his 15 years of KenPom intuition.

2. **Build a simple backtesting proof** — Take 2025 NCAA tournament results. Show which model (PEAR, 64 Analytics, yours) would have predicted the bracket most accurately. This is Ryan's "what were the key drivers?" question answered concretely.

3. **Don't discuss equity or roles yet** — Ryan is still in "feasibility study" mode. Premature structuring will activate PE negotiation instincts. Let the data do the convincing first.

4. **Introduce the equation gently** — Tim told you about the equation, but Ryan hasn't seen it. Don't lead with "deterministic proof" — lead with "here's a backtesting result, and here's the method that produced it."

5. **Set a 2-week checkpoint** — "In two weeks, I'll have scraped data from NCAA + PEAR + 64 Analytics, a basic team rating model, and a backtesting comparison. Let's review then." This gives Ryan a concrete thing to evaluate and a deadline to maintain momentum.

6. **Surface the softball expansion as a throwaway** — In the next call, casually mention "by the way, this same pipeline works for softball too." Don't push it — just plant the seed. Ryan already thought of it; confirming it's technically trivial makes the opportunity feel bigger.
