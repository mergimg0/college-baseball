# Message to Ryan (iMessage group)

---

Ryan — built the engine. Here's the live site:

**https://mergimg0.github.io/college-baseball-predictions/**

Tomorrow's D1 games are up with win probabilities. 65.9% accuracy on 4,159 games backtested this season — all tracked transparently on the page. Rankings, tonight's picks, yesterday's results with checkmarks.

Your 11 questions are answered in the About section. Quick version:
- Data: NCAA scoreboard API + PEAR Ratings API, Python, refreshes daily
- Storage: SQLite, runs locally, deployable anywhere
- Odds: The Odds API — sport key "baseball_ncaa", free 500 credits/month, moneyline + run line + totals from 40+ books
- Backtest: Full chronological replay, no future data leakage. 0.2125 Brier score.

One finding nobody has published: the college baseball Pythagorean exponent is 2.13, not the MLB-derived 1.83. The high-scoring college environment (13 RPG vs MLB's 8.5) means all existing models using 1.83 are systematically wrong. That's our first algorithmic edge.

I'll keep it running daily and tracking accuracy. Happy to stress-test together whenever works.

---

# Message to Tim (separate)

---

Tim — built a working prediction engine for college baseball. Rankings match what you'd expect — UCLA, Texas, Mississippi State at the top. Live at:

**https://mergimg0.github.io/college-baseball-predictions/**

65.9% accuracy across 4,000+ games. Updating daily. Free tonight if you want to compare notes before the group call.

---
