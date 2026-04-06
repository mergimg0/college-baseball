# Meeting Analysis: Ryan McCarthy Call — 2026-03-30

**Re-generated with pyannote x-vector voice-verified speaker labels. 508/510 claims have high-confidence speaker assignment via vocal tract fingerprinting. 60% of Gemini's original speaker labels were incorrect.**

**Duration:** 49 minutes | **Platform:** Zoom (HIG Capital link)
**Claims:** 510 | **Pyannote segments:** 827 | **Prosodic datapoints:** 682

## Speaker Breakdown (x-vector verified)

| Speaker | Claims | Duration | F0 | Arousal | Valence | Role |
|---------|--------|----------|-----|---------|---------|------|
| **Mergim** | 251 (49%) | 14.6 min | 125 Hz | 0.39 | 0.25 | Technical architect, researcher, drove competitive analysis |
| **Ryan** | 167 (33%) | 17.1 min | 102 Hz | 0.35 | 0.29 | Business evaluator, PE framing, due diligence questions |
| **Tim** | 92 (18%) | 5.1 min | 129 Hz | 0.60 | 0.29 | Domain educator, baseball expert, network connector |

**CORRECTION NOTE:** Original Gemini diarization assigned 301 claims to Ryan, 182 to Mergim, 27 to Tim. X-vector analysis revealed Tim had 92 claims (not 27) — he did most of the domain education in the first 10 minutes. Mergim drove 49% of the conversation, not 36%.

---

## Executive Summary

A 49-minute Zoom call with Ryan McCarthy (HIG Capital), Tim McCarthy (Wellington Management), and Mergim Gashi to evaluate a college baseball analytics platform opportunity. **Tim opened with 10 minutes of domain education** (baseball structure, NCAA tournament, Moneyball context) — a critical correction from the original transcript which misattributed this to Ryan. Mergim then led the competitive landscape analysis and technical vision, while Ryan drove the business evaluation with PE rigor. The call produced a clear V0 scope (team-level ratings from runs scored/allowed), identified the data pipeline as the critical first milestone, and established that algorithmic differentiation — not data breadth — is the moat. Ryan committed to further research on algorithm differentiation while Mergim committed to building scrapers and researching the modeling approach. Tim anchored the conversation with domain expertise throughout and will connect the team with his other son Connor (player development at Appalachian State).

---

## Conversation Arc

### Phase 1: Tim's Domain Education (0-5 min) — 55 claims
**Tim: 43 claims | Ryan: 12 claims**

Tim led this entire phase — a major finding from x-vector correction. He explained baseball to Mergim using cricket analogies: MLB = Premier League, minor leagues = lower divisions. Covered NCAA tournament structure (64 teams, conference tournaments, the bubble). Referenced Moneyball as cultural touchpoint. Explained the pitcher/hitter dynamic and nine fielders.

**Key Tim claims:**
- "Baseball is truly one of the most mathematical things — there's just so many statistics"
- "Because it's kind of an uncovered space, there seems to be a few things popping up"
- "More as fans, we're just like, wouldn't it be cool to find different data sets"

**Emotion:** Tim's arousal was highest in the call (0.74) — genuinely passionate about this domain.

### Phase 2: Mergim's Competitive Analysis (5-10 min) — 53 claims
**Mergim: 53 claims (solo segment)**

Mergim took over entirely for 5 minutes, presenting the competitive landscape research. Discussed PEARatings (Python scraping, manual validation, passion project), 64 Analytics (paywall, player-focused, team-oriented), and the overall fragmentation.

**Key Mergim claim:**
- "There's people doing different things, but in terms of a platform where if you're a fan or even a bettor trying to understand the markets, no one has really forged them together"

### Phase 3: Collaborative Exploration (10-20 min) — 105 claims
**Mergim: 54 | Ryan: 35 | Tim: 16**

Three-way conversation exploring the opportunity space. Tim continued domain education (positions, scoring, tournament structure). Mergim introduced the reinforcement learning angle. Ryan began his PE evaluation framework.

**Key exchanges:**
- Mergim: "a tool that can continuously learn on itself but versioned for baseball"
- Tim (corrected from Ryan): "Three is a triple, four is a home run"
- Ryan: "wouldn't it be cool to understand who's going to be in this tournament?"

### Phase 4: Technical Deep Dive (20-30 min) — 98 claims
**Mergim: 49 | Ryan: 47 | Tim: 2**

Ryan and Mergim locked into technical discussion. Mergim introduced the hedge fund analogy: "kind of like a hedge fund tool... it's self-learning." Ryan focused on data pipeline challenges: "the ninjas that into our pipeline, we have to clean the data."

**Key claims:**
- Mergim: "People won't be able to beat you if they don't understand the data you're scraping"
- Mergim: "People won't be able to beat you if they don't understand how you're ingesting it"
- Ryan: "That's probably going to be my next bit of research" (algorithm differentiation)

### Phase 5: EvanMiya Research + V0 Scoping (30-40 min) — 108 claims
**Mergim: 59 | Ryan: 40 | Tim: 9**

Mergim surfaced the EvanMiya research live — Bayesian prior updates, pitcher-dominated variants, park factor adjustments. Tim rejoined with domain context. Ryan began to scope the V0.

**Key claims:**
- Mergim: "This is just basically the answer to the equation"
- Mergim: "The key part is going to be the modeling. Modeling is what's going to distinguish this product"
- Ryan: "We should keep it simple by not even getting into player metrics right now"
- Ryan: "Simple things like runs scored and runs allowed should be considered"

### Phase 6: Action Items + Close (40-49 min) — 91 claims
**Mergim: 36 | Ryan: 33 | Tim: 22**

The most productive phase. All three speakers contributed heavily. Tim made his strongest contributions here — offering Connor's expertise, suggesting softball expansion, expressing belief in the predictive approach.

**Key claims:**
- Mergim: "I'd say for next steps, I'm gonna let these scrapers just keep ingesting"
- Ryan: "I need to think about differentiation from an algorithm perspective"
- Tim: "I have to believe there's a way to create something predictive that could be used in a bunch of different ways"
- Ryan: "This is honestly more like a feasibility study at this point"

---

## Ryan's Mental Model (x-vector corrected)

Ryan's actual contribution (167 claims, not 301) was more focused than the original transcript suggested. He operates through a **PE due diligence lens:**

1. **Feasibility first:** "This is honestly more like a feasibility study" — he wants proof the data pipeline works before committing
2. **Simple V0:** "Keep it at team metrics... runs scored and runs allowed" — minimum viable scope
3. **Algorithm as moat:** "I need to think about differentiation from an algorithm perspective" — not data, not UI, the model itself
4. **Risk awareness:** 9 concern claims (highest of any speaker) — he sees the challenges clearly
5. **Researcher mindset:** 54 action items — mostly about further research and understanding, not building

**What Ryan is NOT:** He's not the baseball domain expert. That's Tim. And he's not the technical builder. That's Mergim. Ryan is the evaluator — he's deciding whether this opportunity meets his investment criteria.

---

## Tim's Actual Role (corrected from 27 → 92 claims)

**This is the biggest finding from x-vector correction.** Tim wasn't a brief cameo — he was the domain anchor:

- **43 claims in the first 5 minutes** — he did ALL the baseball education
- **Domain educator:** MLB structure, NCAA tournament, Moneyball context, player positions, scoring rules
- **Network connector:** Connor at Appalachian State, ESPN+ watching, the "fun hobby project" framing
- **Emotional anchor:** Highest arousal (0.60) of any speaker — genuinely passionate
- **Validator:** "I have to believe there's a way to create something predictive"
- **Expander:** Suggested softball extension, prediction markets, multiple use cases

Tim's F0 (129 Hz) and energy (0.110) are both highest — he was the most animated speaker.

---

## Technical Discussion Summary

### V0 Scope (Agreed)
| Component | Status | Owner |
|-----------|--------|-------|
| Data pipeline (scraping NCAA stats) | **First priority** | Mergim |
| Team-level ratings (runs scored/allowed) | V0 scope | Mergim |
| Player-level metrics | **Deferred to V1** | — |
| Starting pitcher adjustments | Deferred | — |
| Algorithm differentiation | **Ryan researching** | Ryan |
| Monte Carlo simulation | Deferred | — |
| Transfer portal | Not discussed | — |
| Gambling integration | Revenue angle agreed, implementation deferred | — |

### Key Technical Decisions
1. **Start with team metrics, not player** (Ryan's scope preference)
2. **Data pipeline is the critical path** (Ryan: "the most important piece")
3. **Modeling is the moat** (Mergim: "what distinguishes this product")
4. **Self-learning RL model** is the technical differentiator (Mergim)
5. **Feasibility study framing** (Ryan: not committed to full build yet)

---

## Emotion Analysis (x-vector + prosodic)

### Per-Speaker Emotion Profile
| Speaker | Avg Arousal | Avg Valence | F0 Mean | Energy | Pattern |
|---------|-------------|-------------|---------|--------|---------|
| Tim | 0.60 | 0.29 | 129 Hz | 0.110 | Most animated, passionate about domain |
| Mergim | 0.39 | 0.25 | 125 Hz | 0.059 | Steady engagement, focused technical delivery |
| Ryan | 0.35 | 0.29 | 102 Hz | 0.033 | Calm evaluator, analytical tone |

### Emotion Arc Over Time
| Phase | Tim | Mergim | Ryan |
|-------|-----|--------|------|
| 0-5 min | **0.74** (passionate domain education) | 0.51 (listening, engaged) | 0.33 (observing) |
| 5-10 min | (silent) | 0.40 (presenting research) | (silent) |
| 10-15 min | 0.41 (supporting) | 0.42 (driving discussion) | 0.30 (evaluating) |
| 20-25 min | 0.60 (re-engaged) | 0.40 (technical depth) | 0.29 (processing) |
| 40-45 min | 0.41 (closing support) | 0.39 (committing) | 0.34 (highest — deciding) |

**Key emotion signal:** Ryan's arousal peaked in the final 5 minutes (0.34) when action items crystallized. This is the "decision energy" spike — he was deciding whether to commit. Tim's arousal started highest (0.74) and stabilized (0.41) — classic enthusiasm → grounded pattern.

---

## Competitive Positioning (per speaker)

| Platform | Who Discussed It | View |
|----------|-----------------|------|
| PEARatings | Tim (introduced), Mergim (analyzed) | Passion project, manual data pipeline, team-only, free |
| 64 Analytics | Ryan (subscriber), Mergim (analyzed) | Player-focused, paywalled, geared toward recruiting |
| 6-4-3 Charts | Mergim (discovered), Ryan (asked about pricing) | Has API, 650+ programs, institutional |
| KenPom | Mergim (researched) | $25/year, 200K subs, one person, the reference model |
| EvanMiya | Mergim (deep research), Ryan (knows it) | Bayesian BPR, 120+ programs, $180/year |
| Bill Petti/baseballr | Ryan (mentioned) | Open-source scraping tools |

---

## Key Quote from Each Speaker

**Ryan:** "The most important piece is figuring out that data pipeline. If that is somewhat easily stood up, then it's understanding how could we differentiate from an algorithm perspective."

**Mergim:** "Imagine having something that is continuously learning. It's not fresh at the moment of coding it, but as it goes along, it's scraping. Kind of like a hedge fund tool."

**Tim:** "I have to believe there's a way to create something that in any way if it's predictive could be used in a bunch of different ways and then maybe we could do softball or whatever."

---

## Action Items (x-vector corrected ownership)

### Mergim — 30 action items
Key commitments:
- Let scrapers keep ingesting data
- Research the modeling approach (EvanMiya/Bayesian)
- Understand baseball terminology deeper
- Create landscape analysis for next call
- Build V0 data pipeline
- Stress test findings together with Ryan

### Ryan — 53 action items
Key commitments:
- Research algorithm differentiation
- Cross-reference data sources
- Think about what a V0 should look like
- Schedule follow-up call (Thursday proposed)
- Continue research on competitive landscape

### Tim — 5 action items
Key commitments:
- Connect team with Connor (player development)
- Keep watching games / staying informed
- "Keep me posted on the other thing too"

---

## GRPO Scoring: Call Effectiveness

| Agenda Item | Score | Evidence |
|-------------|-------|---------|
| Validate "KenPom for baseball" model | 0.9 | Discussed extensively, refined with RL angle |
| Share landscape research | 0.8 | PEAR, 64, 643, EvanMiya presented during call |
| Propose build > partner | 0.6 | Direction implicit but not explicitly framed |
| Introduce the equation | 0.5 | Mentioned briefly at 35min, not elaborated |
| Define MVP together | 0.9 | Clear V0: team metrics, runs/allowed, pipeline first |
| Discuss gambling multiplier | 0.7 | Mergim: "revenue multiplier" — Ryan agreed |
| Clarify roles | 0.4 | Implicit (Ryan=evaluator, Mergim=builder, Tim=domain) but not formalized |
| Surface transfer portal as killer feature | 0.0 | Not raised |

**Overall call effectiveness: 0.61 / 1.00**

**What went well:** V0 definition, EvanMiya research resonating, data pipeline as first priority, Tim's domain education
**What was missed:** Formal role definition, transfer portal feature, deep equation discussion, explicit build-vs-partner, McMillan AI angle
**Corrected from original:** Effectiveness dropped from 0.79 to 0.61 because several "wins" were misattributed — things we thought Ryan embraced were actually Tim's contributions
