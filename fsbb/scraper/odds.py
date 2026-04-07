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
import ssl
import urllib.request

try:
    import certifi
    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CTX = ssl.create_default_context()

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
        resp = urllib.request.urlopen(req, timeout=30, context=_SSL_CTX)
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
        resp = urllib.request.urlopen(urllib.request.Request(url), timeout=30, context=_SSL_CTX)
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


def _strip_mascot(name: str) -> str:
    """Strip mascot suffix from Odds API team names.

    'Michigan Wolverines' → 'Michigan'
    'Oregon St Beavers' → 'Oregon St.'
    'CSU Bakersfield Roadrunners' → 'CSU Bakersfield'
    'Cal Baptist Lancers' → 'California Baptist'
    """
    # Known mappings that don't follow simple last-word-strip
    ODDS_TO_PEAR = {
        "Cal Baptist Lancers": "California Baptist",
        "California Golden Bears": "California",
        "Long Beach State Dirtbags": "Long Beach St.",
        "Sacramento St Hornets": "Sacramento St.",
        "Oregon St Beavers": "Oregon St.",
        "Washington St Cougars": "Washington St.",
        "Michigan St Spartans": "Michigan St.",
        "Mississippi St Bulldogs": "Mississippi St.",
        "Arizona St Sun Devils": "Arizona St.",
        "Fresno St Bulldogs": "Fresno St.",
        "San Diego St Aztecs": "San Diego St.",
        "Boise St Broncos": "Boise St.",
        "Saint Mary's Gaels": "Saint Mary's (CA)",
        "Nevada Wolf Pack": "Nevada",
        "Dallas Baptist Patriots": "Dallas Baptist",
        "Eastern Michigan Eagles": "Eastern Mich.",
        "UC Davis Aggies": "UC Davis",
        "San Francisco Dons": "San Francisco",
        # Multi-word mascots
        "Duke Blue Devils": "Duke",
        "North Carolina Tar Heels": "North Carolina",
        "Texas Tech Red Raiders": "Texas Tech",
        "Tulane Green Wave": "Tulane",
        "Wake Forest Demon Deacons": "Wake Forest",
        "Illinois Fighting Illini": "Illinois",
        "Coastal Carolina Chanticleers": "Coastal Carolina",
        "South Carolina Gamecocks": "South Carolina",
        "Boston College Eagles": "Boston College",
        "North Carolina State Wolfpack": "NC State",
        "Virginia Commonwealth Rams": "VCU",
    }
    if name in ODDS_TO_PEAR:
        return ODDS_TO_PEAR[name]

    # Multi-word mascots: strip 2 words if the result matches a known suffix
    MULTI_WORD_MASCOTS = {
        "Blue Devils", "Tar Heels", "Red Raiders", "Green Wave",
        "Demon Deacons", "Fighting Illini", "Golden Bears", "Sun Devils",
        "Wolf Pack", "Black Bears", "Red Storm", "Golden Eagles",
        "Blue Jays", "Yellow Jackets", "Mean Green", "Golden Flashes",
        "Red Foxes", "Blue Hose", "Black Knights",
    }
    parts = name.rsplit(" ", 2)
    if len(parts) == 3:
        candidate_mascot = f"{parts[1]} {parts[2]}"
        if candidate_mascot in MULTI_WORD_MASCOTS:
            result = parts[0]
            # Normalize "St" → "St." for PEAR compatibility
            if result.endswith(" St"):
                result += "."
            return result

    # Default: strip last word (the mascot)
    parts = name.rsplit(" ", 1)
    result = parts[0] if len(parts) > 1 else name

    # Normalize "St" → "St." for PEAR compatibility
    if result.endswith(" St"):
        result += "."
    return result


def store_odds(conn, parsed_odds: list[dict]) -> int:
    """Match parsed odds to games in DB and store implied probabilities.

    Returns number of games updated.
    """
    import sqlite3 as _sqlite3
    stored = 0
    for o in parsed_odds:
        home_raw = o["home_team"]
        away_raw = o["away_team"]
        commence = o.get("commence_time", "")[:10]  # YYYY-MM-DD

        if not commence or o.get("home_ml") is None:
            continue

        implied = odds_to_probability(o["home_ml"])

        # The Odds API uses "Team Mascot" format (e.g., "Michigan Wolverines")
        # Our DB uses short names (e.g., "Michigan"). Try multiple match strategies.
        home = _strip_mascot(home_raw)
        away = _strip_mascot(away_raw)

        # Find matching game — try stripped name, full name, then alias
        game = None
        for h_try, a_try in [(home, away), (home_raw, away_raw)]:
            game = conn.execute("""
                SELECT g.id FROM games g
                JOIN teams h ON g.home_team_id = h.id
                JOIN teams a ON g.away_team_id = a.id
                WHERE g.date = ? AND (h.name = ? OR EXISTS (
                    SELECT 1 FROM team_aliases WHERE alias = ? AND team_id = h.id
                )) AND (a.name = ? OR EXISTS (
                    SELECT 1 FROM team_aliases WHERE alias = ? AND team_id = a.id
                ))
            """, (commence, h_try, h_try, a_try, a_try)).fetchone()
            if game:
                break

        if game:
            try:
                conn.execute("""
                    UPDATE games SET
                        odds_home_ml=?, odds_away_ml=?, odds_spread=?,
                        odds_total=?, odds_implied_home_prob=?, odds_bookmaker=?
                    WHERE id=?
                """, (o["home_ml"], o["away_ml"], o.get("spread"),
                      o.get("total"), round(implied, 4), o.get("bookmaker"), game[0]))

                # Also store in odds_history for CLV tracking
                conn.execute("""
                    INSERT OR IGNORE INTO odds_history
                        (game_id, bookmaker, market, home_ml, away_ml,
                         spread, total, implied_home_prob)
                    VALUES (?, ?, 'h2h', ?, ?, ?, ?, ?)
                """, (game[0], o.get("bookmaker", "unknown"),
                      o["home_ml"], o["away_ml"], o.get("spread"),
                      o.get("total"), round(implied, 4)))

                stored += 1
            except _sqlite3.OperationalError:
                pass

    conn.commit()
    return stored


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
