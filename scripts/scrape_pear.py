"""PEARatings.com scraper — pulls all college baseball ratings and team data.

Discovered API endpoints:
    /api/cbase/teams          — list all team names
    /api/cbase/ratings        — all team ratings (NET, SOS, SOR, ELO, RPI, PRR, RQI, power_rating)
    /api/cbase/team/{name}    — individual team detail (stats + schedule)

Usage:
    python scripts/scrape_pear.py                    # Scrape all ratings
    python scripts/scrape_pear.py --team Alabama     # Single team detail
    python scripts/scrape_pear.py --all-teams        # All teams with full detail
    python scripts/scrape_pear.py --output data/pear # Output directory
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import time
import urllib.request
from pathlib import Path

import certifi

BASE_URL = "https://pearatings.com/api/cbase"
SSL_CTX = ssl.create_default_context(cafile=certifi.where())
HEADERS = {"User-Agent": "ForgeStream/1.0 (college baseball research)"}
RATE_LIMIT = 0.5  # seconds between requests


def fetch_json(endpoint: str) -> dict | list | None:
    """Fetch JSON from PEARatings API."""
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        resp = urllib.request.urlopen(req, context=SSL_CTX)
        return json.loads(resp.read().decode())
    except Exception as e:
        print(f"  ERROR {url}: {e}")
        return None


def get_teams() -> list[str]:
    """Get list of all team names."""
    data = fetch_json("/teams")
    if data and "teams" in data:
        return data["teams"]
    return []


def get_ratings() -> dict:
    """Get all team ratings."""
    return fetch_json("/ratings") or {}


def get_team_detail(team: str) -> dict:
    """Get detailed stats + schedule for a team."""
    # URL-encode the team name
    encoded = urllib.parse.quote(team)
    return fetch_json(f"/team/{encoded}") or {}


def scrape_all_ratings(output_dir: Path) -> None:
    """Scrape the full ratings table and save."""
    print("Fetching ratings for all teams...")
    data = get_ratings()
    if not data:
        print("  No data returned")
        return

    teams = data.get("teams", [])
    date = data.get("date", "unknown")
    count = data.get("count", len(teams))
    print(f"  {count} teams as of {date}")

    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "pear_ratings.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  Saved to {path}")

    # Also save as CSV-friendly format
    if teams:
        csv_path = output_dir / "pear_ratings.csv"
        keys = list(teams[0].keys())
        with open(csv_path, "w") as f:
            f.write(",".join(keys) + "\n")
            for t in teams:
                f.write(",".join(str(t.get(k, "")) for k in keys) + "\n")
        print(f"  CSV saved to {csv_path}")

    # Print top 10
    print(f"\n  Top 10 by NET:")
    for t in sorted(teams, key=lambda x: x.get("NET", 999))[:10]:
        print(f"    {t['NET']:3d}. {t['Team']:20s} power={t.get('power_rating',0):.2f} "
              f"SOS={t.get('SOS','?'):>3} ELO={t.get('ELO',0):.0f} RPI={t.get('RPI','?')}")


def scrape_team(team: str, output_dir: Path) -> dict:
    """Scrape detailed data for one team."""
    print(f"Fetching {team}...")
    data = get_team_detail(team)
    if not data:
        print(f"  No data for {team}")
        return {}

    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = team.replace(" ", "_").replace("/", "-").replace(".", "")
    path = output_dir / f"team_{safe_name}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

    # Summary
    t = data.get("team", {})
    print(f"  {team}: {t.get('G',0):.0f}G ERA={t.get('ERA',0):.2f} "
          f"RS={t.get('RS',0):.0f} RA={t.get('RA',0):.0f} RPG={t.get('RPG',0):.1f}")

    upcoming = data.get("upcoming_games", [])
    recent = data.get("recent_games", [])
    print(f"  Recent games: {len(recent)} | Upcoming: {len(upcoming)}")

    return data


def scrape_all_teams(output_dir: Path) -> None:
    """Scrape detailed data for every team."""
    teams = get_teams()
    print(f"Found {len(teams)} teams. Scraping all...")

    output_dir.mkdir(parents=True, exist_ok=True)
    for i, team in enumerate(teams):
        scrape_team(team, output_dir / "teams")
        if i < len(teams) - 1:
            time.sleep(RATE_LIMIT)
        if (i + 1) % 50 == 0:
            print(f"  Progress: {i+1}/{len(teams)}")

    print(f"\nDone. {len(teams)} teams scraped to {output_dir}/teams/")


def main():
    import urllib.parse  # noqa: needed for get_team_detail

    parser = argparse.ArgumentParser(description="Scrape PEARatings.com college baseball data")
    parser.add_argument("--team", help="Scrape a specific team")
    parser.add_argument("--all-teams", action="store_true", help="Scrape all teams with full detail")
    parser.add_argument("--output", default="data/pear", help="Output directory")
    args = parser.parse_args()

    output_dir = Path(args.output)

    # Always get ratings
    scrape_all_ratings(output_dir)

    if args.team:
        scrape_team(args.team, output_dir / "teams")
    elif args.all_teams:
        scrape_all_teams(output_dir)


if __name__ == "__main__":
    # Ensure urllib.parse is available for team detail
    import urllib.parse  # noqa
    main()
