# College Baseball Analytics — Market Research

**Compiled:** 2026-03-30 | **Context:** Tim McCarthy + Ryan McCarthy collaboration opportunity

---

## The Core Opportunity

**"Baseball Savant for college baseball" doesn't exist.**

| Dimension | MLB (Baseball Savant) | College Baseball | Gap |
|-----------|----------------------|------------------|-----|
| Physics metrics (EV, LA, spin) | Every pitch, all 30 parks | Per-program siloed Rapsodo/Trackman | No cross-program database |
| Public player pages | Every MLB player | Nothing | Complete gap |
| Expected stats (xBA, xwOBA) | Full model since 2015 | Not available | Complete gap |
| API / bulk download | Free (pybaseball) | None public | Complete gap |
| Historical database | 2008-present | None | Complete gap |
| Transfer portal analytics | N/A | Fragmented | Major gap |
| Population size | ~750 active MLB players | ~40,000+ NCAA players | Data richness opportunity |

---

## Platform Landscape

### 1. PEARatings (pearatings.com)
**What:** Team-level ratings for NCAA tournament selection (D1/D2/D3/NAIA + softball + football)

**Methodology:** NET composite = TSR (team quality) + RQI (resume quality) + SOS (schedule strength)

**Model:** Free, no paywall. Appears to be a passion project.

**Strengths:**
- Multi-division coverage (D1 through NAIA)
- Multi-sport (baseball + softball + football)
- Tournament bracket projections
- Grassroots credibility (~6,750 Twitter followers)

**Gaps:**
- No player-level data at all
- No advanced metrics
- No recruiting/transfer data
- No API or data export

**Role in integrated platform:** Team-level ratings layer. Complementary to player analytics.

---

### 2. Baseball Savant (baseballsavant.mlb.com)
**What:** MLB's official Statcast data clearinghouse. The gold standard.

**Technology:** Hawk-Eye optical tracking (12 cameras per park), Google Cloud processing.

**Key metrics pioneered:** Exit velocity, launch angle, barrels, sprint speed, xBA/xwOBA/xSLG, bat speed (2023), attack angle (2025)

**Model:** Completely free, no login. Unofficial but stable API via pybaseball.

**College coverage:** Zero. MLB only.

**Why it matters:** Sets the benchmark for what a college platform should aspire to:
- Per-pitch granularity (90+ fields per pitch event)
- Expected stats layer (skill vs luck)
- Public player pages with percentile rankings
- Free access builds community → network effects

**The college gap it reveals:**
1. No centralized physics-level data across programs
2. No cross-program comparability (each school's Trackman data is siloed)
3. No population-level expected stats (need large dataset to model)
4. No standardized pitch classification
5. No transfer portal analytics layer
6. Cost inequality: Trackman ($30K+) vs Rapsodo ($4K) creates haves/have-nots

---

### 3. 64 Analytics (64analytics.com)
*(Research in progress — agent still running)*

**Known from PEARatings comparison:**
- Player rankings with advanced metrics (wRCE/wRAE/RE24)
- Transfer portal coverage (daily alerts)
- "Field of 64" team ratings
- Subscription: $9.99-$12.99/month
- Closest consumer competitor to what Ryan envisions

---

### 4. McMillan AI (mcmillanai.com)
*(Research in progress — agent still running)*

**Known from meeting claims:**
- Founded by Jeff McMillan, ex-Morgan Stanley (they didn't want to lose him)
- C-suite direction, executive training, AI
- Tim sees it as "enterprise version" of what you do locally for SMBs
- Potential collaboration or competitive intelligence

---

## Other Players in the Space

| Platform | Focus | Model | Coverage |
|----------|-------|-------|----------|
| **6-4-3 Charts** | Synergy + Trackman visualization | B2B institutional | 650+ D1 programs |
| **TruMedia** | In-game tagging | Paywalled, SEC-heavy | 200+ D1 teams |
| **GoRout Connect** | Play-signaling + analytics | B2B operational | Growing |
| **Prep Baseball Report** | Regional scouting | Recruiting focus | National |
| **D1Baseball** | News + traditional stats | Free/premium | D1 only |
| **College Baseball Insights** | Program-level analytics | Subscription | D1 |
| **Pixellot + TruMedia** | Video + analytics (Oct 2024 partnership) | B2B paywalled | Forming |

**Key regulatory context:** MLB outlawed Trackman data exclusivity in amateur baseball — meaning no single entity can hoard showcase data. This helps a platform play.

---

## Strategic Analysis

### Why This Opportunity Is Real

1. **40,000+ players, zero centralized analytics** — The demand side is enormous
2. **Transfer portal creates urgency** — 1,000+ transfers/year need evaluation tools
3. **Fragmented supply** — Team ratings (PEAR), player stats (64), scouting (6-4-3), video (TruMedia) all separate
4. **Cost democratization** — D2/D3/NAIA programs have zero analytics. Camera-based solutions (vs radar) can level the field
5. **Regulatory tailwind** — MLB banned data hoarding for amateur baseball
6. **Community network effects** — Baseball Savant proved free access builds massive engaged community

### Platform Architecture (proposed)

```
┌──────────────────────────────────────────────────────┐
│           College Baseball Analytics Platform          │
├──────────────────────────────────────────────────────┤
│                                                        │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Team Ratings │  │ Player Stats │  │ Transfer     │ │
│  │ (PEAR-style) │  │ (64-style)   │  │ Portal       │ │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                │                  │          │
│  ┌──────┴────────────────┴──────────────────┴───────┐ │
│  │              Unified Data Layer                    │ │
│  │     (normalized cross-program, all divisions)     │ │
│  └──────────────────────┬───────────────────────────┘ │
│                         │                              │
│  ┌──────────────────────┴───────────────────────────┐ │
│  │              AI/Analytics Engine                   │ │
│  │  - Expected stats (college xBA, xwOBA)            │ │
│  │  - Prediction markets integration                 │ │
│  │  - Recruiting grade models                        │ │
│  │  - Your equation (deterministic proof)            │ │
│  └──────────────────────┬───────────────────────────┘ │
│                         │                              │
│  ┌──────────┐  ┌───────┴──────┐  ┌─────────────────┐ │
│  │ Public   │  │ Program     │  │ Prediction      │ │
│  │ Player   │  │ Dashboard   │  │ Market          │ │
│  │ Pages    │  │ (B2B paid)  │  │ Analytics       │ │
│  └──────────┘  └──────────────┘  └─────────────────┘ │
│                                                        │
│  Free tier (fans/recruits) + Institutional ($$/year)  │
└──────────────────────────────────────────────────────┘
```

### Revenue Model Options

| Tier | Audience | Price | Features |
|------|----------|-------|----------|
| Free | Fans, recruits, analysts | $0 | Player pages, basic stats, team ratings |
| Premium | Serious fans, bettors | $30/year (Tim's suggestion) | Advanced metrics, predictions, alerts |
| Institutional | College programs | $500-5000/year | Dashboard, recruiting tools, data export |
| Engine License | Other analytics companies | Per-seat | White-label analytics engine |

### Your Unique Advantages

1. **ForgeStream architecture** — Domain knowledge extraction system already built
2. **The equation** — Deterministic proof methodology from alpha generation, applicable to prediction markets
3. **AI/RL experience** — 12-hour training runs, architectural thinking, self-learning reinforcement
4. **Tim's network** — Wellington relationships, college baseball domain expertise
5. **Ryan's domain depth** — Deep dive into prediction markets, PE background
6. **Connor's player development lens** — Uses data daily, understands the practitioner perspective

---

## Next Steps

1. **Complete research** on 64 Analytics and McMillan AI (agents finishing)
2. **Call with Ryan** — tonight 10 PM BST / 5 PM ET
3. **Evaluate equation applicability** — what parameters map to baseball prediction?
4. **Prototype data ingestion** — pybaseball for MLB baseline, NCAA scraper for box scores
5. **Define MVP scope** — probably: player pages + team ratings + transfer portal alerts
