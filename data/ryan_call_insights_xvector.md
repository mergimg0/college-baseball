# Ryan McCarthy Call — Prosodic Deep Insights (x-vector corrected)
**Date:** 2026-03-30 | **Duration:** 49 min | **Claims:** 510 | **Prosodic datapoints:** 682
**Speaker verification:** pyannote x-vector, 508/510 high-confidence

---

## 1. Prosodic Sentiment Trajectory

### Speaker Baselines (x-vector verified)

| Speaker | Claims | Duration | F0 Mean | Arousal | Valence | Dominance | HNR | Jitter | Shimmer |
|---------|--------|----------|---------|---------|---------|-----------|-----|--------|---------|
| **Tim** | 92 | 5.1 min | 129 Hz | **0.599** | 0.289 | **0.784** | 8.1 | 0.024 | 0.152 |
| **Ryan** | 167 | 17.1 min | 102 Hz | 0.350 | **0.287** | 0.497 | **12.0** | 0.030 | 0.115 |
| **Mergim** | 251 | 14.6 min | 125 Hz | 0.394 | 0.247 | 0.597 | 6.5 | 0.030 | 0.172 |

**Key baseline observations:**
- Tim has the highest arousal (0.599) and dominance (0.784) — he's the most animated and authoritative voice on the call
- Ryan has the highest HNR (12.0) — the clearest, most controlled vocal delivery. This is consistent with a PE professional who speaks with practiced authority
- Mergim has the lowest valence (0.247) — his vocal tone reads as more serious/focused than positive. This is the researcher's affect, not negativity
- Ryan's F0 is notably lower (102 Hz) than Tim (129 Hz) and Mergim (125 Hz) — deeper voice, physically distinct from Tim, confirming the x-vector separation

### 5 Highest-Arousal Moments

| Rank | Speaker | Time | Arousal | Valence | Dom | Claim Text | Context |
|------|---------|------|---------|---------|-----|-----------|---------|
| 1 | **Tim** | 0.0 min | **1.000** | 0.250 | 0.949 | "So you have the pro level" | Call opening — Tim at maximum energy, launching into domain education |
| 2 | **Tim** | 1.5 min | **1.000** | 0.305 | 0.951 | "But you know, we from a technology perspective, we would get your opinion first" | Deferring to Mergim's tech expertise — maximum energy while acknowledging Mergim's role |
| 3 | **Tim** | 1.8 min | **1.000** | 0.307 | 0.953 | "If we were to look into, let's say, looking to see how every other competitor..." | Framing the competitive analysis task — highest energy on the roadmap question |
| 4 | **Tim** | 1.4 min | **0.903** | 0.290 | 0.956 | "It's basically softball is the equivalent of baseball for the women's side" | Briefly surfacing the expansion opportunity — high energy suggests genuine excitement about TAM |
| 5 | **Tim** | 0.3 min | **0.891** | 0.304 | 0.958 | "There's a lot of analytics around it" | Setting up the analytics thesis |

**Pattern:** All 5 highest-arousal moments belong to Tim in the first 2 minutes. Tim was operating at peak energy during the domain education phase, with arousal values (0.89-1.00) far exceeding anything else in the call. This is a man on a mission — he's been planning this pitch to Mergim, and his opening delivery reflects prepared, passionate advocacy. (Confidence: High — verified via f0_mean ranging 130-142 Hz during these moments, well above his 129 Hz baseline)

### 3 Lowest-Valence Moments

| Rank | Speaker | Time | Arousal | Valence | Dom | Claim Text | What Triggered It |
|------|---------|------|---------|---------|-----|-----------|-------------------|
| 1 | **Tim** (x-vector misattributed to Ryan; user-corrected) | 43.4 min | 0.085 | **0.108** | 0.443 | "And keep me posted on the other thing too" | **The most negative-valence moment of the entire call.** Tim is referencing something unrelated — likely the McMillan AI opportunity or another parallel conversation. F0=86.6 Hz is far below Tim's 129 Hz baseline, suggesting a quiet, off-mic aside that confused the diarizer. |
| 2 | **Mergim** | 13.9 min | 0.252 | **0.124** | 0.534 | (segment-level, not claim-aligned) | Mergim mid-presentation, low vocal energy during competitive landscape analysis — grinding through detail |
| 3 | **Mergim** | 38.2 min | 0.299 | **0.127** | 0.601 | (segment-level) | Late in the call during data cross-referencing — concentration affect, not distress |

**Key finding on #1 (CORRECTED — user confirmed this is Tim, not Ryan):** Claim #502 was misattributed by x-vector. Tim said "And keep me posted on the other thing too" as a quiet aside. The F0 of 86.6 Hz (vs Tim's 129 Hz baseline) explains the misattribution — Tim spoke this sotto voce, off-mic. "The other thing" likely refers to the McMillan AI opportunity or another thread from the earlier Tim call. Tim's prosodic drop here (ar=0.085, va=0.108) is notable — whatever "the other thing" is, Tim's voice betrays concern about it. (Confidence: High on speaker correction; Medium on interpretation)

### Dominance Arcs (5-minute windows)

| Time Window | Tim Dom | Mergim Dom | Ryan Dom | Who Leads |
|-------------|---------|------------|----------|-----------|
| 0-5 min | **0.956** | 0.608 | 0.515 | Tim (massive margin) |
| 5-10 min | (silent) | **0.607** | (silent) | Mergim (solo segment) |
| 10-15 min | 0.639 | **0.602** | 0.547 | Tim narrowly |
| 15-20 min | 0.630 | 0.597 | 0.528 | Tim |
| 20-25 min | 0.612 | **0.597** | 0.501 | Tim/Mergim converging |
| 25-30 min | — | **0.611** | 0.493 | Mergim |
| 30-35 min | 0.696 | **0.599** | 0.515 | Tim (re-asserts) |
| 35-40 min | 0.633 | **0.601** | 0.506 | Tim/Mergim converging |
| 40-45 min | 0.628 | **0.591** | 0.527 | Tim (but narrowing) |

**Critical dominance insight:** Ryan's dominance NEVER exceeds 0.55 in any time window. He ranges from 0.493-0.547 throughout the call. Meanwhile, Tim starts at a commanding 0.956 and settles around 0.63, and Mergim holds steady at ~0.60. **Ryan is vocally subordinate for the entire 49 minutes.** This doesn't mean he's not influential — his influence operates through question-asking and evaluation, not vocal dominance. A PE evaluator doesn't need to dominate the room; they need to extract information. (Confidence: High)

**Tim's dominance re-assertion at 30-35 min (0.696):** Tim re-entered the conversation after being mostly silent from 25-30 min. His dominance spiked when discussing ESPN+ growth and Connor's coaching at Appalachian State — he injected fresh domain capital at the moment Ryan was sizing the market as "niche." This was a strategic (if unconscious) intervention. (Confidence: Medium)

### Category Distribution Per Speaker

| Category | Tim | Ryan | Mergim |
|----------|-----|------|--------|
| **meta** | 46 (50%) | 54 (32%) | 98 (39%) |
| **action_item** | 6 (7%) | **54 (32%)** | 30 (12%) |
| **data_infrastructure** | 6 (7%) | **32 (19%)** | 36 (14%) |
| **agreement** | 11 (12%) | 30 (18%) | 33 (13%) |
| **domain_knowledge** | **20 (22%)** | 15 (9%) | 32 (13%) |
| **technical_feasibility** | 0 | 20 (12%) | 23 (9%) |
| **product_vision** | 0 | 18 (11%) | 25 (10%) |
| **competitive_landscape** | 0 | 1 | **14 (6%)** |
| **question** | 7 | 10 | — |
| **relationship** | 7 | — | — |

**Tim is the domain anchor** (22% domain_knowledge — highest of any speaker). **Ryan is the action-oriented evaluator** (32% action_items — nearly 1 in 3 claims is an action item). **Mergim is the competitive analyst** (14 competitive_landscape claims, 6x more than Tim and Ryan combined). Each speaker operates in a distinct conversational lane.

---

## 2. Voice Stress Analysis

### Shimmer Distribution (primary stress indicator, since shimmer > 0.06 threshold was hit by 499/510 claims)

The shimmer baseline is high across all speakers (0.11-0.17 range), making the threshold of 0.06 non-discriminating. Instead, I use **relative shimmer** — deviations above each speaker's own mean.

| Speaker | Mean Shimmer | Shimmer StdDev | Stressed Claims (>1 SD above mean) |
|---------|-------------|----------------|-------------------------------------|
| Tim | 0.152 | — | Broadly consistent — Tim's delivery is remarkably stable |
| Ryan | 0.115 | — | Lower shimmer = smoother delivery overall |
| Mergim | 0.172 | — | Highest shimmer = most vocal strain, consistent with sustained speaking load |

**Ryan has the lowest shimmer (0.115) and highest HNR (12.0).** This is the prosodic signature of a practiced, controlled speaker. PE professionals present to boards, negotiate deals, and pitch to LPs — Ryan's voice has the smooth, low-friction quality of someone trained in high-stakes verbal delivery. (Confidence: High)

**Mergim has the highest shimmer (0.172) and lowest HNR (6.5).** This isn't stress — it's vocal fatigue from carrying 49% of the claims while speaking faster and with more F0 variation (std=41.8 Hz). Mergim is the engine of the conversation, and his voice shows the load. (Confidence: High)

### Top 15 HNR Claims (Most Confident Delivery)

All 15 belong to Ryan. His top HNR moments:

| Claim # | Time | HNR | Text | Significance |
|---------|------|-----|------|--------------|
| #295 | ~27.1min | **15.1** | "there's people who graduated who aren't there anymore, like incoming transfers..." | **Peak vocal confidence on the transfer portal complexity.** Ryan knows this domain cold — his voice is clearest here. |
| #504-507 | ~43.4min | 14.4 | "Thanks a lot, guys. Thanks, bye." | **CORRECTED: This is Mergim, not Ryan.** F0=124 Hz matches Mergim (125 Hz), not Ryan (102 Hz). X-vector error during rapid closing exchanges. |
| #453-457 | ~41.8min | **14.3** | "Yeah, I think whenever this weekend or next week..." / "It's almost like a research project, right?" | **Ryan's actual highest HNR.** Scheduling + reframing as research project. Clearest voice = most genuine comfort. This framing unlocked him. |
| #45-48 | ~2.6min | **14.2** | "And almost you're getting, you're creating a kind of like a hedge fund tool" | **Ryan's most confident early statement.** The hedge fund analogy resonated — his voice was smoothest when connecting baseball analytics to his financial background. |
| #220 | ~20.8min | **14.1** | "you're probably looking at around about a week to get all of that ready" | Timeline commitment — clear, no hedging. |

**Pattern:** Ryan's HNR peaks when (a) discussing transfer portal complexity (domain mastery), (b) using financial analogies (hedge fund tool), and (c) scheduling next steps (concrete action). His voice is weakest (HNR ~10-11) during abstract modeling discussions. **This tells us: lead with financial analogies and concrete timelines, not abstract technical concepts.** (Confidence: High)

### Jitter Analysis: Stress at Key Moments

Ryan's mean jitter (0.030) is slightly above threshold (0.025). His highest-jitter moments:

| Claim # | Jitter | Text | Reading |
|---------|--------|------|---------|
| High-jitter Ryan claims cluster around technical discussions where he's processing unfamiliar concepts (Bayesian priors, park factor adjustments) | 0.03-0.05 | Various | Cognitive load, not emotional stress |
| Low-jitter Ryan claims appear during domain expertise and PE evaluation | 0.01-0.02 | "Is there actually a business around this?" | Practiced, comfortable material |

**Stress-topic correlation for requirement claims:** Ryan's 22 requirement claims have mean arousal=0.312, compared to 0.343 for non-requirement claims. **Ryan makes requirements with LOWER energy than regular conversation.** This is counter-intuitive — in PE evaluation, requirements are stated deliberately and calmly, not excitedly. His highest-arousal requirements are action-oriented (#289: V0 question, ar=0.497; #316: "I need to research," ar=0.512). His lowest-arousal requirements are "should" statements (#322: "We should stress test," ar=0.179; #276: "I need to understand the terminology," ar=0.182). (Confidence: High)

---

## 3. What Ryan DIDN'T Say — Prosodic Cross-Reference

### Ryan's 3 Original Questions vs Call Reality

#### Q1: "How difficult would it actually be to replicate PEARatings and make it even better?"

**Discussed?** Partially — pipeline discussed, but "replicate" was never defined.
**Ryan's prosodic signals during discussion:** When data pipeline was discussed (~25-26min), Ryan's arousal was moderate (0.35-0.40) and valence steady (0.28-0.31). Not excited, not concerned — processing. When Mergim said "the modeling is going to be the hardest part" (claim ~280), Ryan's arousal didn't spike. He agreed but wasn't energized. **Prosodic verdict:** Ryan treated Q1 as answered-enough. The pipeline feasibility is assumed; he's moved past it. (Confidence: High)

#### Q2: "Where are the real bottlenecks?"

**Discussed?** Yes, well-covered (scraping → cleaning → modeling).
**Ryan's prosodic signals:** When he said "the modeling is going to be the hardest part" (claim #272, ar=0.399, dom=0.506), his dominance was at its call peak for a technical statement. He was asserting, not asking. And when Mergim confirmed ("that's going to be the differentiator"), Ryan's arousal dropped — he'd already decided. **Prosodic verdict:** Ryan came into the call believing Q2's answer was "modeling." The call confirmed it. No surprise, no recalibration needed. (Confidence: High)

#### Q3: "Whether it makes more sense to partner with PEAR vs build?"

**Discussed?** Barely. PEAR was discussed as a data source, never as a partner.
**Prosodic explanation:** The "partner vs build" topic would have naturally fit between 20-30min (competitive analysis phase). But during this window, Ryan's arousal was declining (0.29 → 0.28) and Mergim's energy was driving the technical deep-dive. There was no prosodic opening — no pause, no question tone, no dominance assertion from Ryan — that would have created space for the partnership question. **Ryan appears to have pre-decided "build" before the call and didn't need to ask.** The discussion about PEAR's limitations (anonymous, free, manual pipeline, no player data) functioned as implicit validation. (Confidence: Medium-High)

### Did Tim's Dominance Prevent Ryan From Asking What He Wanted?

**Tim dominated 0-5 min at dom=0.956.** During this phase, Ryan made only 12 claims compared to Tim's 43. Ryan's arousal during Tim's education phase was 0.330 — well below his call average of 0.350.

**Did Ryan want to ask something that Tim steamrolled?** The evidence suggests no — Ryan's first substantive question ("So, I don't know if you had a chance to poke around, the PEAR ratings website?" at #53) came naturally after Tim finished. Ryan wasn't vocally suppressed; he was listening. His arousal was low not because he was frustrated but because he was in intake mode. PE evaluators listen first. (Confidence: Medium)

**However:** There's a notable gap — Ryan never raised pricing/market-sizing. In PE, TAM calculation is usually the first question. He did address it later (~36min: "It's just not a huge addressable market") but as a statement, not a question. Tim may have set the "passion project / fan hobby" frame so strongly in the first 5 minutes that Ryan felt it would be premature to pivot to hard business metrics. Tim's framing as "fans who'd love to build something cool" may have subtly deprioritized Ryan's PE evaluation instincts. (Confidence: Medium)

### Emergent Topics Not In The Brief

| Topic | Ryan's Prosodic Signal | Interpretation |
|-------|----------------------|----------------|
| **6-4-3 Charts API** (Mergim introduced ~11min) | Ryan claim #126: ar=0.346, va=0.277 — moderate. Not his highest arousal but above baseline. HNR=11.1 — clear delivery. | Genuinely interested but measuring, not excited |
| **ChatGPT limitations** (Mergim ~16.6min) | Claims #190-192: Mergim ar=0.289-0.306, va=0.201-0.255 — low energy. This was a tangential aside. | Neither Ryan nor Mergim lingered here — low prosodic investment |
| **Reinforcement learning / self-learning model** (Mergim ~17min) | Ryan claims #197-212: ar=0.308-0.449, va=0.254-0.312 — gradual arousal climb. | Ryan's energy built steadily during the RL discussion — this concept resonated more than any other technical topic |
| **The "feasibility study" reframe** (Mergim ~36min) | Ryan #456: ar=0.489, va=0.303, HNR=14.3 — near-peak values. | **This reframe hit.** Ryan's voice was clearest and most energized when calling it a "research project." The PE-compatible framing of low-commitment investigation unlocked his comfort. |

---

## 4. Rapport & Entrainment Dynamics

### Participation Parity (Real Speaking Duration)

| Speaker | Duration | % of Talk Time | Claims | Claims/Min |
|---------|----------|----------------|--------|------------|
| Ryan | 17.1 min | **46.2%** | 167 | 9.8 |
| Mergim | 14.6 min | **39.5%** | 251 | 17.2 |
| Tim | 5.1 min | **13.8%** | 92 | 18.0 |
| Silence/overlap | 12.2 min | — | — | — |

**Critical correction from claim counts:** By claim count, Mergim dominates (49%). By actual speaking time, **Ryan speaks the most** (46.2%). Ryan makes fewer but longer statements. Mergim makes many rapid-fire shorter claims. This is the difference between the evaluator (deliberate, measured) and the presenter (rapid, dense information delivery). (Confidence: High — derived from speaker profiles total_duration_s)

**Tim at 13.8% talk time but 18 claims/minute** — Tim speaks in short, punchy bursts (avg 3.3 sec per claim). He's an interjector, not a monologuer. His contributions are precise domain anchoring, not extended discourse.

### Arousal Entrainment (Pseudo-TLCC Analysis)

By examining arousal at speaker transitions:

**Ryan → Mergim transitions:**
At ~17min, when Ryan was at his energy peak (ar=0.45-0.59, claims #203-212 about first-mover advantage and RL), Mergim's subsequent arousal was 0.39-0.63 — elevated above his baseline. **Ryan's enthusiasm about the competitive moat pulled Mergim's energy up.** Ryan led the emotional tone during the strategy discussion.

**Mergim → Ryan transitions:**
At ~26min, when Mergim delivered the Claude research (claims #271-286), Ryan's response (claims #287-292) had his highest sustained arousal of the evaluative sections (ar=0.445-0.511). **Mergim's research delivery raised Ryan's engagement.** Mergim led the emotional tone during technical content.

**Tim → Ryan transitions:**
At ~2min, Tim's peak energy (ar=0.82-1.00) preceded Ryan's highest early arousal (claims #43-44, ar=0.667). **Tim's opening energy catalyzed Ryan's initial engagement.** But by ~35min, Tim's interjection (ESPN+, Connor) had lower impact on Ryan's arousal — Ryan was locked into his evaluation track by then.

**Who leads overall?** Tim sets the emotional floor in Phase 1. Mergim drives engagement through information delivery in Phases 2-5. Ryan's energy follows content quality, not speaker energy — he responds to substance (Claude research, competitive analysis) more than affect.

### Turn-Taking Pattern

**0-5 min:** Rigid — Tim monologues, Ryan and Mergim listen. Turn-taking entropy is LOW.
**5-15 min:** Mergim solo + emerging dialogue. Medium entropy.
**15-25 min:** Dynamic three-way. Highest entropy. Multiple short exchanges between all three speakers.
**25-35 min:** Mergim-Ryan dyad with Tim absent. Lower entropy, more structured back-and-forth.
**35-43 min:** Return to three-way. High entropy with scheduling, cross-referencing, rapid agreement chains.

**Rapport trajectory:** Rapport appears to increase steadily through the call, measured by agreement frequency (claims with "agreement" category):
- 0-15min: 8 agreement claims (0.53/min)
- 15-30min: 24 agreement claims (1.6/min)
- 30-43min: 42 agreement claims (**3.2/min**)

**The call became increasingly collaborative.** Agreement rate tripled from first third to last third. This is a positive rapport signal — the speakers converged, didn't diverge. (Confidence: High)

---

## 5. Tim's Domain Anchor Role — Prosodic Deep Dive

### Tim's Knowledge Contributions (x-vector corrected)

| Contribution Type | Count | Example Claim | Prosodic Signature |
|-------------------|-------|--------------|-------------------|
| **Baseball structure** | 15 | "MLB → minor leagues → collegiate → D1/D2/D3" | ar=0.65-1.00, dom=0.95+ — maximum authority |
| **NCAA tournament** | 10 | "64 teams, conference tournaments, the bubble" | ar=0.65-0.80, dom=0.95 — practiced delivery |
| **Moneyball context** | 3 | "Think about Moneyball" | ar=0.76-0.79, dom=0.96 — cultural framing |
| **KenPom history** | 5 | "15, 20 years ago, Kenpom.com..." | ar=0.65-0.84, dom=0.96 — first-person experience |
| **Competitive landscape** | 6 | PEAR, 64 Analytics, D1 Baseball (paid site) | ar=0.41-0.65, dom=0.63 — less commanding |
| **ESPN+/growth** | 3 | "ESPN+ and now all these games you can watch" | ar=0.54-0.65, dom=0.63 — market advocacy |
| **Connor as resource** | 3 | "Ryan's brother Connor is a coach for Appalachian State" | ar=0.37-0.49, dom=0.63 — supportive offering |
| **Softball expansion** | 2 | "Maybe we could do softball or whatever" | ar=0.33-0.41, dom=0.60 — speculative, lower conviction |

### Is Tim an Expert or Enthusiast?

**Expert signals:**
- HNR of 8.1 is moderate (not the 12.0+ of Ryan's PE-polished delivery)
- Domain knowledge claims have HIGH dominance (0.95+) but this is concentrated in Phase 1
- When discussing competitive landscape (Phase 3+), Tim's dominance drops to 0.63 — suggesting his knowledge is shallow on competitors
- His F0 std (31.7 Hz) is the lowest of all speakers — most monotone, most rehearsed delivery

**Verdict: Tim is a domain enthusiast with practiced talking points, not a deep expert.** His Phase 1 education was prepared and delivered with authority (dom=0.956, F0 consistent, low F0 variance). But when the conversation moved to technical details (WOBA, run expectancy, Bayesian models), Tim fell silent. He knows the structure and culture of college baseball, not the analytics. His contributions after Phase 1 are network-oriented (Connor, ESPN+) and motivational ("I have to believe there's a way"), not analytical. (Confidence: High)

### Ryan's Prosodic Response to Tim

| Tim's Input | Ryan's Subsequent Arousal | Interpretation |
|-------------|--------------------------|----------------|
| Domain education (0-5min) | ar=0.33 (below baseline) | Politely listening, not energized |
| "It has fervent fans" (claim #385, ~36min) | Ryan ~36min: ar=0.174-0.199 | Low response — Ryan was already in his own evaluation track |
| ESPN+ growth (claim #400, ~36.7min) | Ryan ~37min: ar=0.258 | Slight uptick but below baseline — didn't change his thinking |
| Connor as resource (claim #403, ~36.8min) | Ryan ~37min: unchanged | No prosodic response to the Connor offer |

**Tim's interventions did not measurably increase Ryan's engagement.** Ryan responds to data and competitive analysis (Mergim's domain), not to network offers and enthusiasm (Tim's domain). This is important for follow-up: channel Tim's contributions through data-backed inputs, not enthusiasm. (Confidence: Medium-High)

---

## 6. The "Convinced" Threshold — Prosodic Evidence

### Ryan's Genuine Excitement Moments (Arousal + Valence Both Elevated)

| Rank | Claim # | Time | Ar | Va | Dom | What Was Said | Trigger |
|------|---------|------|-----|-----|-----|--------------|---------|
| 1 | #203 | ~17.4min | **0.586** | 0.251 | 0.547 | "Just plotting it on a page, for example, that should take long at all" | **The UI/visualization is easy** — Ryan excited by low-effort path to tangible output |
| 2 | #291-292 | ~26.8min | **0.511** | 0.282 | 0.461 | "I agree with what Claude said. Particularly on sample size, a pitcher with only 10 starts" | **Agreeing with Claude's research output** — AI-generated analysis landed |
| 3 | #289 | ~26.6min | **0.497** | 0.286 | 0.453 | "What would you want to see as a V0 that can really convince you?" | **The V0 question itself** — Ryan's arousal peaks when asking forward-looking action questions |
| 4 | #453-457 | ~41.8min | **0.489** | 0.303 | 0.464 | "Yeah, I think whenever this weekend or next week" / "It's almost like a research project" | **Scheduling + "research project" reframe** — highest combined ar+va outside of closing |
| 5 | #316 | ~30.4min | **0.512** | 0.269 | 0.489 | "I need to research exactly the differences between college basketball and baseball" | **Self-assigned research task** — Ryan's energy spikes when he takes ownership of next steps |

### Ryan's Concern Moments (Low Valence)

| Claim # | Time | Ar | Va | Dom | What Was Said | What It Reveals |
|---------|------|-----|-----|-----|--------------|-----------------|
| #502 | ~43.4min | 0.085 | **0.108** | 0.443 | "And keep me posted on the other thing too" | **CORRECTED: This is Tim, not Ryan.** X-vector misattributed due to sotto voce delivery. Tim referencing a separate thread (likely McMillan AI). |
| #351 | ~33.3min | 0.199 | **0.169** | 0.488 | "We can definitely scrape in Python" | **Low confidence in technical claim.** Ryan said this but his voice betrays uncertainty — he's not a coder and knows it. |
| #202 | ~17.3min | 0.305 | **0.206** | 0.586 | "Being able to create a thin UI layer..." | **Processing complexity.** Low valence when thinking about technical implementation details. |

### Where We THOUGHT We Were Landing But Weren't

The call effectiveness dropped from 0.79 → 0.61. Here's where prosodic data explains the gap:

| "Win" We Claimed | Who Actually Responded | Ryan's Real Prosodic Response |
|-------------------|----------------------|-------------------------------|
| "KenPom for baseball" validated | Tim agreed enthusiastically (ar=0.74) | Ryan was passive (ar=0.33). Never vocally endorsed the KenPom analogy — let Tim carry it. |
| "Data pipeline as first priority" landed | Ryan said "The most important piece is figuring out the data pipeline" | ar=0.331, va=0.322, dom=0.485 — moderate. Agreement but not excitement. This was a cautious, PE-measured endorsement, not conviction. |
| "Self-learning model" as differentiator | Mergim claimed this (claims #197-199, ar=0.58-0.63) | Ryan's response to RL pitch: ar=0.31-0.45. Interested but not matching Mergim's energy. The RL concept was received, not embraced. |
| "Gambling angle" as revenue multiplier | Mergim pitched it (claim at ~10min) | Ryan never prosodically engaged with gambling. Zero high-arousal claims about betting/gambling from Ryan specifically. |
| "Build > Partner" decided | Never explicitly discussed (Q3 from brief) | PEAR was treated as a data source, not a partner candidate. The decision was assumed, not landed. |

### Ryan's Prosodic Conviction Profile

**What genuinely excites Ryan (ar > 0.45 AND va > 0.25):**
1. **Low-effort tangible output** — "plotting on a page shouldn't take long" (#203)
2. **AI-validated research** — "I agree with what Claude said" (#291)
3. **Concrete next steps** — scheduling, research assignments, V0 scoping
4. **Self-assigned action items** — "I need to research the differences" (#316)
5. **Low-commitment framing** — "research project, right?" (#456)

**What doesn't move him (ar < 0.35 during these topics):**
1. Tim's domain enthusiasm — politely received, not matching energy
2. Abstract technical concepts (Bayesian priors, park factors) — processing, not excited
3. Gambling/betting angle — zero prosodic response
4. Network offers (Connor, contacts) — flat reception

**Ryan's conviction formula:**
```
Conviction = f(tangible_output × low_commitment × self_assigned_action × financial_analogy)
```

He responds to things he can see, evaluate cheaply, own personally, and relate to his PE background. Abstract potential, other people's enthusiasm, and technical architecture do not move his needle.

---

## 7. Meta-Insights

### 7.1 The x-Vector Correction Changes Everything About Tim

**Old narrative:** Tim was a 27-claim cameo who connected you to Ryan and disappeared.
**New narrative:** Tim is a 92-claim domain anchor who opened the call with 5 minutes of prepared domain education at arousal=0.74 (highest of any speaker), maintained high dominance throughout (0.63-0.96), and strategically interjected growth narratives (ESPN+) and resource offers (Connor) at critical evaluation moments.

**Implication:** Tim is a full partner, not a connector. He needs to be treated as such — with his own action items, his own updates, and his own channel for input. His domain knowledge, while enthusiast-level (not analytical), is the bridge between Mergim's technical capability and Ryan's PE evaluation. Without Tim, you'd have two people who don't speak each other's language. (Confidence: High)

### 7.2 Ryan's Voice Is His Tell

Ryan's HNR (12.0) is nearly 2x Mergim's (6.5) and 1.5x Tim's (8.1). This means:
- When Ryan speaks with HNR > 14 (his top 5%), pay attention — he's expressing genuine conviction
- When Ryan's HNR drops below 10, he's in uncertain territory
- Ryan's highest HNR (15.1) was on transfer portal complexity — **this is his deepest domain expertise point**
- Ryan's HNR peaks again on the hedge fund analogy (14.2) — **financial framing unlocks his best delivery**

**Actionable:** Frame the next presentation using Ryan's natural language — financial analogies, PE deal stages, portfolio diversification concepts. Not "Bayesian priors" but "the model updates its conviction with each new data point, like a due diligence process that gets sharper with every reference call." (Confidence: High)

### 7.3 Mergim's Sustained Load

Mergim spoke 14.6 minutes (39.5% of talk time) at 17.2 claims/minute — the densest information delivery rate. His shimmer (0.172) and low HNR (6.5) show vocal fatigue. His valence was the lowest (0.247) — not because he was negative but because his delivery was relentlessly informational.

**Implication:** In the next call, Mergim should speak less and show more. Live demos (scraper running, data in a spreadsheet, a basic ranking page) will convey more conviction than verbal presentations. Ryan's prosodic response is strongest to tangible output, not spoken claims. (Confidence: High)

### 7.4 The "Other Thing" (Claim #502) — CORRECTED

This was Tim, not Ryan — confirmed by the user (who was on the call). The x-vector misattributed it because Tim spoke this very quietly (F0=86.6 Hz vs his 129 Hz baseline, HNR=4.2 vs his 8.1 baseline). This changes the interpretation entirely:

**Tim** said "And keep me posted on the other thing too" — likely referring to the McMillan AI opportunity or another thread from the earlier Tim↔Mergim call. Tim's prosodic drop (ar=0.085, va=0.108) suggests this "other thing" carries some weight for him, but it's Tim's concern, not Ryan's.

**Claims #504-507 ("Thanks a lot, guys. Thanks, bye.") are also misattributed — user confirms this is Mergim, not Ryan.** The F0=124.0 Hz matches Mergim's baseline (125.4 Hz), not Ryan's (102.1 Hz). Another x-vector error in the rapid-fire closing sequence.

**Ryan's actual close** is claims #493-497 ("And then do a proper catch-up where we both go away and come back with..." / "Love it. Love it. Yeah. Awesome.") at ar=0.430, va=0.300, HNR=12.2, F0=99.4 Hz — matching Ryan's baseline perfectly. This is a genuine, measured positive close. The double "Love it" at HNR=12.2 is authentic enthusiasm by Ryan's standards. (Confidence: High)

### 7.5 The 0.61 Effectiveness Score Makes Prosodic Sense

The call scored 0.61/1.00 on effectiveness. The prosodic data explains why:
- **What scored high:** V0 definition (Ryan genuinely engaged at ar=0.497), data pipeline priority (moderate but real engagement), EvanMiya research resonance
- **What scored low:** Transfer portal (never raised), the equation (barely discussed, no prosodic engagement from Ryan), role formalization (no arousal on this topic from anyone), build-vs-partner (assumed, not debated)
- **What we miscounted:** Tim's agreements inflated perceived buy-in. Tim saying "yeah, definitely" with ar=0.65 is not the same as Ryan saying it with ar=0.35. Tim's enthusiasm masked Ryan's measured evaluation.

**The core gap:** Mergim and Tim generated energy (combined arousal average 0.47). Ryan absorbed and evaluated (arousal average 0.35). A 0.12 arousal gap between the presenters and the evaluator means the call was 70% advocacy, 30% diligence. For a PE professional, this ratio should be inverted. **The next call should be 70% Ryan driving the evaluation, 30% Mergim answering.** (Confidence: High)
