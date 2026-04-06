"""The Odds API integration for college baseball betting lines.

Sport key: baseball_ncaa
Markets: h2h (moneyline), spreads (run line), totals (over/under)
Free tier: 500 credits/month (~166 calls at 3 markets × 1 region)

Answers Ryan's question #10: "Can we scrape in Vegas odds easily?"
Answer: Yes. Clean JSON REST API, free tier sufficient for daily polling.

Setup:
    1. Get free API key at https://the-odds-api.com
    2. Set environment variable: export ODDS_API_KEY=your_key_here
    3. Run: fsbb odds

Documentation: https://the-odds-api.com/liveapi/guides/v4/
"""

from __future__ import annotations

import json
import os
import urllib.request


SPORT = "baseball_ncaa"
BASE_URL = "https://api.the-odds-api.com/v4"


def get_api_key() -> str | None:
    """Get The Odds API key from environment."""
    return os.environ.get("ODDS_API_KEY")


def fetch_odds(
    api_key: str | None = None,
    markets: str = "h2h,spreads,totals",
    regions: str = "us",
) -> list[dict] | None:
    """Fetch current college baseball odds.

    Args:
        api_key: The Odds API key (or from env ODDS_API_KEY)
        markets: Comma-separated markets (h2h, spreads, totals)
        regions: Comma-separated regions (us, us2, uk, eu, au)

    Returns:
        List of game odds dicts, or None on error.
    """
    key = api_key or get_api_key()
    if not key:
        return None

    url = (
        f"{BASE_URL}/sports/{SPORT}/odds/"
        f"?apiKey={key}"
        f"&regions={regions}"
        f"&markets={markets}"
        f"&oddsFormat=american"
    )

    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read().decode())
        return data if isinstance(data, list) else None
    except Exception:
        return None


def fetch_scores(
    api_key: str | None = None,
    days_from: int = 1,
) -> list[dict] | None:
    """Fetch recent game scores from The Odds API.

    Args:
        api_key: API key
        days_from: Number of days back to fetch (1-3)

    Returns:
        List of score dicts
    """
    key = api_key or get_api_key()
    if not key:
        return None

    url = (
        f"{BASE_URL}/sports/{SPORT}/scores/"
        f"?apiKey={key}"
        f"&daysFrom={days_from}"
    )

    try:
        resp = urllib.request.urlopen(urllib.request.Request(url), timeout=30)
        data = json.loads(resp.read().decode())
        return data if isinstance(data, list) else None
    except Exception:
        return None


def parse_odds(games: list[dict]) -> list[dict]:
    """Parse raw odds API response into clean format.

    Returns list of dicts with:
        home_team, away_team, commence_time,
        home_ml, away_ml, spread, total,
        bookmaker
    """
    parsed = []
    for game in games:
        home = game.get("home_team", "")
        away = game.get("away_team", "")
        start = game.get("commence_time", "")

        for bm in game.get("bookmakers", []):
            book_name = bm.get("key", "unknown")
            entry = {
                "home_team": home,
                "away_team": away,
                "commence_time": start,
                "bookmaker": book_name,
                "home_ml": None,
                "away_ml": None,
                "spread": None,
                "spread_price": None,
                "total": None,
                "over_price": None,
            }

            for market in bm.get("markets", []):
                mkey = market.get("key", "")
                outcomes = market.get("outcomes", [])

                if mkey == "h2h" and len(outcomes) >= 2:
                    for o in outcomes:
                        if o.get("name") == home:
                            entry["home_ml"] = o.get("price")
                        elif o.get("name") == away:
                            entry["away_ml"] = o.get("price")

                elif mkey == "spreads" and len(outcomes) >= 1:
                    for o in outcomes:
                        if o.get("name") == home:
                            entry["spread"] = o.get("point")
                            entry["spread_price"] = o.get("price")

                elif mkey == "totals" and len(outcomes) >= 1:
                    for o in outcomes:
                        if o.get("name") == "Over":
                            entry["total"] = o.get("point")
                            entry["over_price"] = o.get("price")

            parsed.append(entry)

    return parsed


def odds_to_probability(american_odds: int | float) -> float:
    """Convert American odds to implied probability."""
    if american_odds > 0:
        return 100 / (american_odds + 100)
    else:
        return abs(american_odds) / (abs(american_odds) + 100)


def display_odds(parsed: list[dict]) -> None:
    """Pretty-print odds for terminal display."""
    if not parsed:
        print("No odds available")
        return

    # Group by game
    games: dict[str, list[dict]] = {}
    for p in parsed:
        key = f"{p['home_team']} vs {p['away_team']}"
        if key not in games:
            games[key] = []
        games[key].append(p)

    for matchup, entries in games.items():
        print(f"\n  {matchup}")
        # Use first bookmaker as representative
        e = entries[0]
        if e["home_ml"] is not None:
            home_prob = odds_to_probability(e["home_ml"])
            away_prob = odds_to_probability(e["away_ml"]) if e["away_ml"] else 0
            print(f"    ML: Home {e['home_ml']:+d} ({home_prob:.0%}) | "
                  f"Away {e['away_ml']:+d} ({away_prob:.0%})")
        if e["spread"] is not None:
            print(f"    Spread: {e['spread']:+.1f} ({e['spread_price']:+d})")
        if e["total"] is not None:
            print(f"    Total: {e['total']:.1f} O{e['over_price']:+d}")
        print(f"    Books: {len(entries)} ({', '.join(set(x['bookmaker'] for x in entries[:3]))})")
