# Ryan McCarthy Call — Coaching Analysis

**Date:** 2026-03-30, 10 PM BST / 5 PM ET
**Duration:** ~47 min (WAV: 88.9MB main + 4.5MB pre-recording)
**Participants:** Ryan (301 claims), Marjan (182 claims), Tim (27 claims)
**Talk ratio:** Ryan 59% | Marjan 36% | Tim 5%

---

## 1. Agenda Execution Scorecard

The pre-call analysis recommended 7 discussion items. Here's how each landed.

### 1.1 Validate Ryan's mental model — 7/10
**Covered.** Marjan affirmed Ryan's KenPom analogy (claim 245: "your intuition about Evan Maya is the right one"), agreed on data quality being the core challenge (claims 293-304), and correctly pointed out the small sample size issue (claim 293: "a pitcher with only 10 starts, often times it's even fewer"). Ryan felt heard.

**What was missed:** Marjan never explicitly said "KenPom is the floor, not the ceiling" — which was the key refinement from the research. The conversation stayed at Ryan's level of understanding rather than elevating it. Ryan walked away thinking "KenPom for baseball" is the plan, when the research showed baseball needs fundamentally different modeling. This was the single highest-value insight from the prep doc, and it wasn't delivered.

### 1.2 Share the research — 5/10
**Partially covered.** Marjan mentioned 6-4-3 Charts and its API (claims 116-123), showed the PEAR scraper running live (claims 405-410), and referenced 64 Analytics' methodology (claims 236-242). These were good moments — especially the live scraper demo.

**What was missed:** The 10-platform competitive landscape table was never shown. The "nobody combines all 5 layers" insight was never stated. The full research document (80+ sources, 10,000+ words) that Marjan had prepared remained largely unshared. Ryan is in PE — he reads deal memos. He would have devoured a structured competitive analysis. Instead, references came out piecemeal and conversationally. The research was done but not *deployed*.

### 1.3 Propose the build path — 4/10
**Weakly covered.** The conversation implicitly pointed toward building (not partnering with PEAR), but Marjan never made the explicit recommendation: "Build, don't partner. Here's why." The research doc had 5 crisp arguments against partnering. None were articulated. The decision was left floating.

Ryan himself landed on "build" organically (claim 379: "This is honestly more like a feasibility study at this point"), but Marjan should have driven this conclusion with authority rather than letting Ryan arrive there on his own. When you let the other party "discover" the conclusion you already have, you're giving away strategic credibility.

### 1.4 Introduce the equation angle — 6/10
**Covered but diluted.** Marjan's claims 40-48 are the strongest stretch of the call — describing the reinforcement learning agent, self-learning hedge fund tool, and competitive moat from data understanding. Ryan was clearly engaged (claim 52: "And I'm happy to take that").

However, Marjan framed it as "reinforcement learning" rather than the sharper pitch from the Tim call: "a mathematical equation that can deterministically prove an outcome." The Tim version was more compelling because it promised certainty. The Ryan version promised process. Ryan later echoed the stronger framing himself (claim 310: "if we can deterministically prove that the data..."), which means he'd heard it from Tim — the son is already primed for the stronger claim, but Marjan downgraded it.

### 1.5 Define MVP — 3/10
**This is where the call fell short.** Ryan asked the most important question directly (claim 289): "What would you want to see as a V0 that can really convince you that this has legs?" This was a buying signal wrapped in a question. Marjan's response (claims 291-304) was diffuse — agreed with Claude's analysis, discussed sample sizes, mentioned 64 Analytics' preseason approach, and concluded "this will always be somewhat more imperfect." That's analysis, not a plan.

**What Marjan should have said (see Section 5 for the full draft):** A concrete 3-step MVP with timeline. Instead, the V0 question — the most critical moment of the call — got a philosophical answer about data imperfection.

### 1.6 Discuss the gambling multiplier — 6/10
Marjan opened this well (claim 110: "the gambling aspect of this, I think that angle is where really that revenue multiplier lives"). Ryan was receptive (claim 314: "Any type of prediction can yield insane results"). But the conversation never got quantitative — no mention of the $10B+ US sports betting market, no mention of inefficient college baseball lines, no mention of the pricing differential ($50-100/month for bettors vs $25/year for fans). The opportunity was flagged but not sized.

### 1.7 Define roles — 2/10
**Barely touched.** Tim mentioned Connor as a coach who "knows his stuff" (claims 390-395). Marjan never proposed a role structure. Nobody said "Ryan does X, Marjan does Y, Connor does Z, Tim advises." The closest was Marjan saying "you guys are both super fans" (claim 112) and Ryan volunteering to do research (claims 421-424). But there's no clarity on who owns what. In a PE context, ambiguous ownership is a red flag.

**Overall agenda score: 4.7/10** — The research was done. The insights were ready. But the delivery was conversational when it should have been structured.

---

## 2. Communication Effectiveness

### 2.1 Talk Ratio Analysis
Ryan 59% (301 claims) vs Marjan 36% (182 claims) vs Tim 5% (27 claims).

**Verdict: Too passive.** In a discovery call where you're learning the domain, 60/40 favoring the other party is fine. But this wasn't purely discovery — Marjan had a 17,000-word research brief and was supposed to be demonstrating technical capability. A 50/50 split would have been healthier. Marjan ceded too much floor time to Ryan explaining baseball basics (claims 150-167: what a single, double, triple is). That's 20+ claims of elementary explanation that could have been preempted with "Ryan, I did some research on the fundamentals — what I'd love to understand from you is the *nuances* that models miss."

### 2.2 Question-to-Statement Ratio
Marjan asked **9 questions** out of 182 claims = **4.9% question rate**. Of those 9:
- 3 were genuine discovery questions (good)
- 2 were hedged ("I'm not sure if this would be helpful," "Is this something we could stand up?")
- 2 were rhetorical
- 2 were about baseball basics ("When we say home run and double, are we talking, do you know what that is?")

Ryan asked **19 questions** — more than double Marjan's rate. Ryan was driving the conversation with questions. In a partnership pitch, the person with the technical edge should be asking *more* questions than the domain expert, not fewer. Marjan should have been interrogating Ryan's assumptions, probing for gaps, and revealing insights through Socratic questioning.

**High-value questions Marjan didn't ask:**
- "What's your model for how PEAR weights its NET composite? Have you reverse-engineered it?"
- "If you could only have one metric that PEAR doesn't offer, what would it be?"
- "How much would you pay for a tool that could predict game outcomes 5% better than the line?"
- "Who's your first 10 users — fans, bettors, or coaches?"
- "What does Connor see that no public data captures?"

### 2.3 Hedge Word Analysis
Marjan's top tone markers tell the story:

| Marker | Count | Signal |
|--------|-------|--------|
| "like" | 13 | Filler — reduces authority |
| hesitation | 10 | Uncertainty projection |
| "I think" | 9 | Hedging assertions |
| "probably" | 4 | Non-committal |
| "I don't know" | 2 | Explicit uncertainty |
| "I'm not sure" | implicit | Undermines credibility |

Compare to Ryan's markers: "definitely" (4x), "speculation" (5x), "I think" (6x). Ryan hedges at a similar rate, but his hedges are *speculative* (exploring possibilities) while Marjan's hedges are *defensive* (protecting against being wrong).

**The fix:** Replace "I think we could probably..." with "Here's what I'd do." Replace "I'm not sure if this is helpful" with "This is what the research shows." You had 80+ sources of research. Own it.

### 2.4 Confidence Map

**Marjan sounded most confident:**
- Claims 40-48: Describing reinforcement learning and the self-learning engine. This is home turf. Marjan's voice (per tone markers) shifts to "enthusiastic," "visionary," "confident."
- Claims 405-410: Showing live scraped PEAR data with exact numbers ("308 teams, four ratings"). Concrete data = confidence.

**Marjan sounded least confident:**
- Claims 181-189: Discussing whether this makes business sense ("I'm trying to wrap my arms around...could you do this with a reasonable amount of effort?"). This signaled uncertainty about the opportunity rather than excitement.
- Claims 345-350: "I'm trying to think through if this will ultimately make sense. I'm not a Python [scraper]." Admitting a capability gap mid-pitch.
- Claims 396-399: "I'm not sure if this would be helpful or not." Never preface a contribution with doubt.

### 2.5 Missed Opportunities

**Moment 1 — Claim 22:** Ryan says "what was eye opening to me was you actually don't need a big team." This is Marjan's opening to say: "Exactly — and I've already started. I built a scraper tonight that pulled all of PEAR's data in 15 minutes. Here's what it found." Instead, Marjan gave a general response about combining data sources.

**Moment 2 — Claim 191:** Ryan says "ChatGPT gives me the widest range ever." This was a chance to differentiate — "That's because ChatGPT doesn't have domain-specific training. What I build is different — it extracts expert knowledge and embeds it into the model. That's why Kazem felt like he had 10 analysts." Marjan let it pass.

**Moment 3 — Claim 289:** "What would you want to see as a V0?" (See Section 5.)

**Moment 4 — Claim 379:** Ryan calls this "a feasibility study." This was the moment to upgrade the framing: "I actually think we're past feasibility. I've already scraped the data, mapped the landscape, and identified the architectural gap. What we're doing is building." Instead, Marjan agreed with the "feasibility" framing, which keeps the project in evaluation mode rather than execution mode.

---

## 3. Ryan's Engagement Pattern

### 3.1 Engagement Arc

**Phase 1 (Claims 0-55): HIGH engagement — Ryan is selling.** Ryan opens with a 55-claim monologue explaining the opportunity, the landscape (PEAR, 64 Analytics, KenPom), and the vision. He's pitching *to* Marjan. This is significant — he came prepared and emotionally invested. He's not evaluating coldly; he's trying to get Marjan excited.

**Phase 2 (Claims 55-108): HIGH engagement — Ryan is teaching.** Detailed walkthrough of PEAR's limitations (same probabilities regardless of pitcher), 64 Analytics' player stats, how metrics roll up into models. Ryan is in his element. Claim density is highest here.

**Phase 3 (Claims 109-200): MEDIUM engagement — Shared exploration.** Both parties riffing on Evan Miya, data challenges, RL models. Energy is collaborative but unfocused. No clear direction emerging.

**Phase 4 (Claims 260-330): PEAK engagement — Ryan asks the hard questions.** Claims 287-289 are the climax: "Let me know what you think... where do you see us starting... what would you want to see as a V0?" This is Ryan in PE mode — structured, evaluative, wanting a concrete answer. He asks 6 requirements in rapid succession. This was the deal moment.

**Phase 5 (Claims 330-410): DECLINING — Agreement without conviction.** Both parties agree data comes first. Marjan shows scrapers. The energy is positive but diffuse. No decisions made.

**Phase 6 (Claims 420-509): CLOSING — Warm but noncommittal.** "Thursday maybe," "take your time," "informal catch-up." Ryan ends with "Really exciting, really can't wait" (claims 468-469) — genuine enthusiasm, but the next step is vague ("more research").

### 3.2 Language Shift Analysis

Ryan's language **never fully shifted** from evaluative to committed:

| Phase | Language Pattern | Mode |
|-------|-----------------|------|
| Early | "wouldn't it be cool," "is there a way" | Exploratory |
| Mid | "we should," "we have to" | Collaborative |
| Peak (289) | "What would you want to see as a V0" | Evaluative/buying |
| Late | "I'm gonna let these scrapers go," "see what comes back" | Autonomous/parallel |
| Close | "we can keep this informal," "proper catch-up" | Low-commitment |

He never said "let's do this," "I'm in," or "when do we start building?" The closest was "Really exciting, really can't wait" — which is emotional, not operational.

### 3.3 What Energized Ryan
- **Moneyball analogy** (claim 10) — his framing, his passion
- **PEAR's limitations** (claims 89-92) — he sees the gap viscerally
- **"Deterministically prove"** (claim 310) — the equation promise lit him up
- **Data mapping** (claims 327-328) — concrete next steps
- **"Already seeing connection points"** (claim 487) — he's doing his own research in real-time

### 3.4 What Made Ryan Cautious
- **Market size** (claims 384-386) — "not a huge addressable market, niche"
- **Effort vs reward** (claim 379) — "feasibility study" framing = not yet committed
- **When scheduling** (claims 441-444) — "I don't know when to say" = avoiding commitment velocity
- **Tim's "no pressure" interventions** (claims 470, 473) — Tim was managing Ryan's exposure to commitment

---

## 4. Relationship Trajectory

### Tim Call vs Ryan Call — Comparison

| Dimension | Tim Call | Ryan Call |
|-----------|---------|----------|
| Tone | Warm, mentoring, 10 compliments | Professional, evaluative, 0 compliments |
| Power dynamic | Tim pitching Marjan as talent | Ryan assessing whether to invest time |
| Commitment level | "I'll ping you, we'll get it done" | "Maybe Thursday, we'll see" |
| Information asymmetry | Marjan had Wellington research | Marjan had 80+ source research (under-deployed) |
| Decision made? | Yes — schedule Ryan call tonight | No — "more research" |

### Where Is Ryan Now?

**(b) Evaluating an investment** — with leanings toward (c).

Ryan is applying PE due diligence patterns: assess the market (claims 384-386), assess the team capability (claim 22), assess the competitive landscape (claims 76-107), ask for an MVP definition (claim 289). He's interested but hasn't crossed the commitment threshold.

**Evidence for investment mode:**
- "Feasibility study" language (claim 379)
- Market sizing concern (claims 384-386)
- MVP question as a gate (claim 289)
- Scheduling buffer ("maybe Thursday," not "tomorrow")

**Evidence for partnership leanings:**
- "We" language throughout (not "you")
- "Really exciting, really can't wait" (claims 468-469)
- Volunteering to do research himself (claims 421-424)
- "Already seeing connection points" (claim 487)
- Staying an extra ~20 min beyond the expected call length

### What Would Move It to (c) Building With a Partner?

Three things:

1. **A working demo.** Not wireframes. Not research. A page with real data that Ryan can interact with. PE people believe what they can touch.

2. **Marjan taking the lead without being asked.** Ryan is used to managing investments. If Marjan sends him a V0 before Thursday *without being asked*, that flips the dynamic from "evaluating Marjan" to "Marjan is already building."

3. **Revenue math.** Ryan said "niche market" (claim 385). Counter with: "200K subscribers at $30 = $6M ARR, and that's just fans. Betting premium at $100/month with 5K subscribers = $6M more. That's a $12M annual opportunity with near-zero marginal cost." PE people move when the math works.

---

## 5. The V0 Question — Coaching on the Response

### What Ryan Asked (Claim 289)
> "What would you want to see as a V0 that can really convince you that this has legs and you know exactly how to push this forward?"

### How Marjan Responded
Claims 291-304: Agreed with Claude's analysis on small samples. Mentioned 64 Analytics not doing preseason rankings. Discussed how the model would evolve over the season. Concluded with "I think that also kind of makes it fun."

**Problem:** This answered "why is this hard?" not "what is the V0?" Ryan asked for a concrete deliverable and got a philosophical observation about data imperfection. The word "fun" in a PE conversation is particularly dangerous — it signals hobby, not business.

### What Marjan Should Have Said

> "Here's what I'd build as V0 — three things, in order.
>
> First: a data pipeline. We scrape NCAA box scores for all D1 teams — runs, hits, errors, pitcher stats, game-by-game. I've already started this tonight — I built a scraper that pulled all 308 teams' ratings from PEAR in under 15 minutes. The NCAA source data is next.
>
> Second: a team rating engine. KenPom-style adjusted efficiency, but calibrated for baseball. Opponent-adjusted run differential, home/away splits, strength of schedule. I layer in a starting pitcher adjustment — which is the gap PEAR has. If I know who's pitching, the model should show different win probabilities for each game in a series.
>
> Third: a single page. One URL. You type in two teams, pick the starters, and it gives you a win probability with confidence intervals. No login, no paywall. That's the thing nobody has. If that page is more accurate than PEAR's static probabilities, we have a product.
>
> I can have that in two weeks. Then we test it against real games and see if the model has edge."

**60 seconds. Concrete. Testable. Time-bound.** This would have moved Ryan from evaluation to anticipation.

### Follow-Up Action
Send Ryan a message within 48 hours containing: (1) the V0 plan above, and (2) one screenshot of real scraped data — the PEAR ratings comparison showing Mississippi State ranked differently across platforms. Visual proof that you're already executing.

---

## 6. Next Interaction Plan

### 6.1 Follow-Up Message (Send by Tuesday EOD)

**Tone:** Professional but energized. Not a wall of text. PE-calibrated.

**Length:** 8-10 sentences max. Link to the data/research for depth.

**Structure:**

> Ryan — great talking through this tonight. Three things from my side:
>
> 1. **Data is live.** I've already scraped all 308 D1 teams from PEAR's API (ratings, schedules, head-to-head) and have the NCAA source data pipeline running. CSV and JSON, clean, ready to model against.
>
> 2. **V0 plan:** I want to build a single-page tool: pick two teams, pick starters, get a win probability that adjusts for pitcher quality — the one thing PEAR doesn't do. Two weeks to have something testable.
>
> 3. **Research doc attached.** Full competitive landscape (10 platforms mapped), the "5-layer gap" nobody fills, and the revenue math for the betting angle. Worth a 10-minute read.
>
> Happy to stress-test the data together Thursday or whenever works. In the meantime I'll keep building.

### 6.2 Timing
- **Message:** Tuesday (2 days). Too soon = eager. Too late = lost momentum. Tuesday is "I've been working on this since we hung up."
- **Next call:** Thursday-Friday (per Ryan's suggestion, claim 443). Don't push earlier.
- **Follow-up cadence after that:** Weekly until V0 is ready.

### 6.3 Deliverable for Next Call
**The V0 itself — or a working prototype of it.** If Marjan shows up Thursday with a live URL where Ryan can type "Texas vs Mississippi State" and see a win probability, the conversation shifts from research to product. That's worth more than any amount of further analysis.

Minimum viable demo for Thursday:
- Static page pulling from scraped PEAR data
- Two-team matchup view showing: each team's PEAR ratings, recent results, and a naive win probability
- Even if the model is basic (just using Elo ratings), the *interface* existing is the proof of concept

### 6.4 What to Ask Ryan to Do Before Thursday
> "Before we talk again, could you send me your top 5 matchups this week that you care about? I want to run them through the model and see if the outputs match your intuition. That'll tell us immediately if the ratings are capturing what matters."

This does three things: (1) gets Ryan invested by contributing domain input, (2) gives Marjan a validation test, (3) moves from abstract to concrete.

### 6.5 The One Thing That Would Most Accelerate Ryan's Commitment
**A correct prediction.** If Marjan's model predicts Game X's outcome and it happens, Ryan will go from "feasibility study" to "we're building this." The gambling angle isn't abstract for Ryan — he wants to see edge. One publicly verifiable prediction is worth a thousand research documents.

---

## 7. Tim Management

### "The Other Thing"
Tim's claim 502: "And keep me posted on the other thing too."

Cross-referencing the Tim call (meeting_analysis), "the other thing" is **McMillan AI / the enterprise advisory opportunity.** In the Tim meeting, three opportunities were discussed: (1) baseball platform with Ryan, (2) McMillan AI collaboration, (3) SMB engine pitches (law firms Wednesday). Tim is asking about #2 and/or #3.

Specifically, Tim positioned two plays around McMillan:
- Help McMillan "behind the scenes to make a few bucks"
- Study McMillan's model and replicate for mid-small businesses

Tim's strategic insight (claim 100 from his call): "I actually think the opportunity is going to be in these mid-small businesses." He sees the baseball project as one thread and the enterprise AI advisory as another — and he wants to know both are progressing.

### How to Keep Tim in the Loop
Tim is not a detail person ("I'm not good with the chat stuff" — claim 478). He wants signal, not noise.

**Pattern:** One text message per week, max 3 sentences.

> "Tim — good call with Ryan tonight. I've already built scrapers pulling all the baseball data. Working on a V0 for him this week. Also looked into McMillan's setup — will share thoughts soon."

That's it. Tim is a connector, not a project manager. He wants to know the connections he made are producing results so he feels good about facilitating. Don't send him data, don't send him links. One text. He'll respond with encouragement and more connections.

### Tim's Ideal Role Going Forward
**Advisory board member / door opener.** Tim brings:
- Network (McMillan, other Wellington contacts, baseball community)
- Credibility (30+ years at $1T AUM firm)
- Domain enthusiasm (self-described "big college baseball guy")

He does NOT want:
- Operational responsibility
- Regular meetings
- Technical details
- To be CC'd on everything

Keep him warm with periodic wins. Loop him in when there's something to show, not when there's work to discuss.

---

## 8. Overall Session Grade

| Dimension | Grade | Note |
|-----------|-------|------|
| Preparation | A | 17K-word research brief, meeting prep, competitive analysis |
| Research deployment | C+ | Had the goods, didn't deliver them structurally |
| Technical credibility | B+ | RL explanation strong, live scraper demo strong |
| Business acumen | C | Never sized the opportunity, no revenue math shared |
| Listening | B+ | Correctly identified Ryan's concerns and interests |
| Driving to conclusion | D | No decisions made, no commitments secured, V0 unanswered |
| Confidence projection | C | 10 hesitation markers, 9 "I think" hedges in 182 claims |
| Relationship advancement | B | Warm close, next call scheduled, but still in evaluation mode |

**Summary:** Marjan did A-grade preparation and C-grade delivery. The gap between what was known and what was communicated is the coaching opportunity. Ryan left interested but uncommitted. The V0 question was the critical moment and it was missed. The next 48 hours — sending a structured follow-up with concrete plan and live data — can recover what the call left on the table.

---

## 9. Three Things to Do Differently Next Call

1. **Lead with deliverables, not analysis.** Open with "Here's what I built since we last talked" and show a screen. Ryan's engagement peaked when Marjan showed live data (PEAR scraper). Do more of that. Less talking about what could be done, more showing what's been done.

2. **Kill the hedge words.** Before the call, write down three assertions you want to make and practice saying them without "I think," "probably," "I'm not sure." Example: not "I think we could probably build this" but "I'll build this. Here's the plan."

3. **Ask Ryan to commit to something specific.** "Can you send me 5 matchups?" or "Can you write a one-pager on what metrics matter most to you as a fan?" Give him homework. People who do homework are invested. People who say "let's catch up sometime" are being polite.

---

*This analysis is for Marjan's eyes only. Written by Sentinel Coach, 2026-03-30.*
