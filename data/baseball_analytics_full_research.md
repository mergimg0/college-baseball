# College Baseball Analytics — Complete Market Research

**Compiled:** 2026-03-30 | **Sources:** 4 research agents, 80+ sources | **Context:** Tim McCarthy + Ryan McCarthy opportunity

---

## Executive Summary

**"Baseball Savant for college baseball" doesn't exist.** This is not an incremental gap — it's structural. 40,000+ NCAA players across 1,700+ programs have zero centralized physics-level analytics. The tools that do exist are fragmented, siloed, and incomplete. The transfer portal (2,000+ players/year) has created urgent demand for better evaluation tools. Tim and Ryan's instinct is correct — there's a real product here.

---

## The Four Platforms Researched

### 1. McMillan AI (mcmillanai.com)

**What it is:** Boutique C-suite AI advisory firm. NOT a technology company.

**Founder:** Jeff McMillan — West Point grad, 15 years at Morgan Stanley, served as the firm's first-ever Head of Firmwide AI. Built the AI @ Morgan Stanley Assistant (OpenAI-powered, 16,000 financial advisers), AskResearchGPT, and AI Debrief for automated meeting notes. Left Morgan Stanley late 2024/early 2025.

**Services:** AI literacy for boards, strategic roadmaps, governance frameworks, implementation advisory, investor due diligence on AI capabilities, keynotes/workshops.

**Business model:** Principal-led advisory. High-value, low-volume. No disclosed pricing. Solo practice or team of 1-3. No proprietary software.

**Key insight from Tim (claim 100):** "I actually think the opportunity is going to be in these mid-small businesses." McMillan targets the enterprise. You target SMBs. Non-competing, potentially complementary.

**Collaboration angle:**
- He has the brand (Morgan Stanley pedigree) but no product
- You have the product (ForgeStream) but need the brand
- He may need help delivering at scale — currently capacity-constrained
- **Outreach style:** Direct, specific, no-fluff. Lead with concrete value, not broad partnership framing.
- **Timing favorable:** Early in his independent practice, still building pipeline

---

### 2. 64 Analytics (64analytics.com)

**What it is:** The leading consumer-facing college baseball analytics platform. Subscription SaaS founded 2023 from a Google Doc ranking portal players. 80+ college programs contacted them before they had a product.

**Metrics:** wRCE (hitting), wRAE (pitching), RE24 — all adapted for college's unique characteristics (opponent quality, series type, divisional averages). Built entirely on play-by-play box score data.

**Coverage:** All NCAA divisions (DI/DII/DIII) + softball (added 2025)

**Pricing:**
| Tier | Price | Audience |
|------|-------|----------|
| Standard | $12.99/month | Fans, players, families |
| Portal Pass (1 season) | $2,000 | Coaching staff |
| Portal Pass (2 seasons) | $3,750 | Coaching staff |
| Portal Pass (3 seasons) | $5,500 | Coaching staff |

**Strengths:** Cross-divisional coverage, transfer portal as killer feature (first mover), college-specific metrics, real-time PBP ingestion, softball expansion

**Critical gaps:**
- **Zero pitch-tracking data** (no exit velocity, spin rate, pitch movement)
- **No video integration**
- **No public API or data export** (completely closed)
- **Only 2 years of historical data**
- **Metrics unvalidated externally** (proprietary, no peer review)

**What 64 Analytics proves:** There IS product-market fit. 80+ programs reaching out unprompted validates the demand. But they're solving only part of the problem — the box-score layer.

---

### 3. PEARatings (pearatings.com)

**What it is:** Free team-level ratings platform for NCAA tournament selection (D1/D2/D3/NAIA + softball + football).

**Methodology:** NET composite = TSR (team quality) + RQI (resume quality) + SOS (schedule strength)

**Model:** Completely free, no paywall. Appears to be a passion project/embedded in broader org.

**Strengths:** Multi-division, multi-sport, tournament projections, grassroots credibility

**Gaps:** No player data, no advanced metrics, no API, no recruiting/transfer data

**Role:** Team-level layer in an integrated platform. Complementary to 64 Analytics' player focus.

---

### 4. Baseball Savant (baseballsavant.mlb.com)

**What it is:** MLB's official Statcast data clearinghouse. The gold standard for what's possible.

**Technology:** Hawk-Eye optical tracking (12 cameras per park), Google Cloud, 90+ fields per pitch event.

**Model:** Completely free, no login. De facto API via pybaseball.

**College coverage:** Zero. MLB only.

**Key metrics pioneered:** Exit velocity, launch angle, barrels, sprint speed, xBA/xwOBA/xSLG, bat speed (2023), attack angle (2025)

**What it reveals about the college gap:**
1. No centralized physics-level data across programs
2. No cross-program comparability (each school's Trackman siloed)
3. No public player pages (MLB has one for every player)
4. No population-level expected stats (xBA requires large dataset)
5. No standardized pitch classification
6. No transfer portal analytics layer
7. Cost inequality: Trackman ($30K+) creates haves/have-nots
8. No historical database of physics-level data from any year

---

## The Complete Competitive Landscape

| Platform | Player Stats | Pitch Tracking | Team Ratings | Transfer Portal | Video | API | Price | Divisions |
|----------|-------------|---------------|-------------|----------------|-------|-----|-------|-----------|
| **64 Analytics** | Yes (box-score derived) | No | Yes | Yes (primary) | No | No | $13-$5500 | DI/DII/DIII |
| **PEARatings** | No | No | Yes (NET composite) | No | No | No | Free | DI-NAIA |
| **6-4-3 Charts** | Yes (TrackMan) | Yes (where available) | Yes (DSR) | Partial | Yes (Synergy) | Yes | Enterprise | DI |
| **TruMedia** | Yes (advanced) | Yes (where available) | No | No | Yes | No | Enterprise | 200+ DI |
| **D1Baseball** | Basic | No | Yes (DSR collab) | Basic tracker | No | No | Free/premium | DI only |
| **GoRout Connect** | Some | No | No | No | No | No | Enterprise | Growing |
| **Baseball Reference** | Historical | No | No | No | No | Partial | Free/paid | DI/DII/DIII |
| **The Baseball Cube** | Historical | No | No | No | No | Partial | Free/paid | All levels |
| **NCAA.com** | Box score only | No | No | No | No | No | Free | DI |
| **Prep Baseball Report** | Recruiting focus | Some (showcases) | No | No | Video | No | Subscription | HS + college |

**The white space:** Nobody combines all five layers: (1) player stats + (2) pitch/batted ball tracking + (3) team ratings + (4) transfer portal + (5) API/data export. The closest is 6-4-3 Charts, but they're B2B only and not public-facing.

---

## The Opportunity Architecture

### What Would Win

**A platform that is to college baseball what Baseball Savant is to MLB:**
- Public player pages for every NCAA player (the flagship feature)
- Physics-level data where available (partner with Rapsodo/Trackman programs)
- College-specific expected stats (xBA, xwOBA calibrated to BBCOR bats, college parks)
- Transfer portal analytics with performance context
- Cross-program normalized comparisons (a Vanderbilt pitcher vs a mid-major pitcher)
- API-first architecture (build the developer/research community)
- Free tier for fans → institutional tier for programs

### Why Your Stack Maps Perfectly

| Your Asset | Maps To |
|------------|---------|
| ForgeStream (domain knowledge extraction) | Extract tacit knowledge from coaches, scouts — encode what they "feel" when evaluating talent |
| The equation (deterministic proof, alpha gen) | Prediction markets for college baseball outcomes; player valuation models |
| GRPO / reinforcement learning | Model calibration across seasons; self-improving evaluation weights |
| SOS framework | Quality/governance layer for analytics outputs |
| Emotion pipeline | Fan engagement analysis; broadcast sentiment |
| Bespoke engine model | White-label analytics engine for programs |

### Revenue Model

| Tier | Audience | Price | Features |
|------|----------|-------|----------|
| Free | Fans, recruits, researchers | $0 | Player pages, basic stats, team ratings, API (rate-limited) |
| Premium | Serious fans, bettors, families | $30/year (Tim's suggestion) | Advanced metrics, predictions, portal alerts |
| Coach | Individual coaching staff | $150/month | Full portal analytics, player comparison, data export |
| Program | Athletic departments | $2,000-5,000/year | Dashboard, recruiting tools, unlimited API, historical data |
| Engine License | Other analytics companies | Custom | White-label analytics engine |

### Build Sequence (MVP → Full)

**Phase 1 (MVP — weeks):** NCAA box score scraper + college-adapted expected stats + public player pages. This alone would be novel — nobody has public player pages with advanced metrics.

**Phase 2 (Transfer Portal):** Portal tracker with performance context. Compete directly with 64 Analytics' Portal Pass on data depth.

**Phase 3 (Physics Data):** Partner with programs that have Trackman/Rapsodo for pilot data. Even 10 programs' data would be unprecedented in a public platform.

**Phase 4 (Prediction Markets):** Your equation applied to game outcomes, player projections, draft modeling. This is where Ryan's domain knowledge meets your math.

---

## Key Regulatory/Data Notes

- MLB outlawed Trackman data exclusivity in amateur baseball — cannot hoard showcase data
- NCAA stats (box score level) are publicly available via stats.ncaa.org
- pybaseball + baseballr packages exist for scraping NCAA traditional stats
- 6-4-3 Charts has a public API — potential data source
- Data ownership question: does the conference own Trackman data, the school, or Trackman?
- Pixellot + TruMedia partnership (Oct 2024) is the nearest forming competitor — B2B/paywalled only

---

## Action Items for Call with Ryan

1. **Understand his prediction market thesis** — which markets, what parameters, what data does he use?
2. **Discuss the "Statcast gap"** — does he see the physics data layer as the real prize?
3. **Explore partnership models** — build from scratch vs aggregate existing tools vs engine license?
4. **Clarify roles** — Tim = domain/network, Ryan = prediction markets/business, Connor = player dev perspective, You = tech/AI/architecture
5. **Ask about Jeff McMillan** — what's the connection, what does Tim envision there?
6. **Define MVP scope together** — what would Ryan build first if he could wave a magic wand?
