Ryan — treating this as the feasibility study you framed it as. Here's where I'm taking it.

I'm running a head-to-head backtest right now. I scraped PEAR's full dataset — all 308 D1 teams, current season ratings, schedules, and results. I'm building two models against the same data. Model A replicates what PEAR does: static team strength ratings where every game in a 3-game series gets the same win probability regardless of who's pitching. Model B adjusts for starting pitcher, home/away splits, and recent form — and recalibrates itself after each game result. I'm backtesting both against this season's actual outcomes to see if the adjustment layer produces a measurable predictive edge.

If Model B outpredicts PEAR's static approach by even 3-5% on game outcomes, that's not a stat page — that's a signal. And it directly answers your question about algorithmic differentiation: PEAR and 64 Analytics both work from the same public box score data. The data isn't the moat. The model is.

On market scale — you're right that the fan base alone is niche. But that's the floor, not the ceiling. College baseball lines are the most inefficient in American sports because oddsmakers have the least data to work with. A model with a demonstrable edge over the current tools doesn't need 200K subscribers to be valuable. It needs a few hundred serious users who'd pay for signal in a market where the lines are soft. Niche addressable market with premium pricing is a better business than mass market with commodity pricing — you know that better than I do.

I'll have the first backtest results by Wednesday evening. If the numbers show what I think they'll show, we can talk about what a proper V1 scope looks like with Tim and Connor's input on the domain side.

One question for you to chew on in the meantime: if the backtest shows a meaningful edge over PEAR's static ratings, what's the right way to structure a first version — free beta to build an audience and prove it publicly, or paid from day one to establish the value signal?

I'll send results as soon as they're ready.
