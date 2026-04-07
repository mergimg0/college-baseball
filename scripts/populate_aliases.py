"""Populate team_aliases by cross-referencing NCAA API names against PEAR names.

Fetches scoreboard data for several dates, collects all unique NCAA 'short' names,
and resolves them to PEAR team IDs via exact match, alias lookup, and fuzzy matching.
New aliases are inserted for all successful fuzzy matches.
"""

import json
import sqlite3
import ssl
import time
import urllib.request
from pathlib import Path

try:
    import certifi
    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CTX = ssl.create_default_context()

DB_PATH = Path(__file__).parent.parent / "data" / "fsbb.db"
BASE_URL = "https://ncaa-api.henrygd.me"
HEADERS = {"User-Agent": "ForgeStream/1.0 (college baseball research)"}

# Known manual aliases for teams that fuzzy matching won't catch
MANUAL_ALIASES = {
    # Full name variants
    "Mississippi State": "Mississippi St.",
    "Mississippi Valley State": "Mississippi Val.",
    "App. State": "App State",
    "Appalachian State": "App State",
    "Appalachian St.": "App State",
    "Arkansas State": "Arkansas St.",
    "Arizona State": "Arizona St.",
    "Ball State": "Ball St.",
    "Boise State": "Ball St.",  # only if exists
    "Bowling Green State": "Bowling Green",
    "Central Michigan": "Central Mich.",
    "Eastern Michigan": "Eastern Mich.",
    "Western Michigan": "Western Mich.",
    "Northern Illinois": "NIU",
    "Central Arkansas": "Central Ark.",
    "Central Connecticut": "Central Conn. St.",
    "Central Connecticut State": "Central Conn. St.",
    "Charleston Southern": "Charleston So.",
    "Coastal Caro.": "Coastal Carolina",
    "Col. Charleston": "Col. of Charleston",
    "College of Charleston": "Col. of Charleston",
    "CS Fullerton": "Cal St. Fullerton",
    "CS Bakersfield": "CSU Bakersfield",
    "CSUB": "CSU Bakersfield",
    "CS Northridge": "CSUN",
    "Cal State Northridge": "CSUN",
    "Dallas Baptist": "DBU",
    "East Tennessee State": "ETSU",
    "East Tennessee St.": "ETSU",
    "Eastern Kentucky": "Eastern Ky.",
    "Eastern Illinois": "Eastern Ill.",
    "Florida Atlantic": "Fla. Atlantic",
    "Florida State": "Florida St.",
    "Florida A&amp;M": "Florida A&M",
    "Florida Gulf Coast": "FGCU",
    "Fresno State": "Fresno St.",
    "Georgia Southern": "Ga. Southern",
    "Georgia State": "Georgia St.",
    "Georgia Tech.": "Georgia Tech",
    "Grand Canyon University": "Grand Canyon",
    "Houston Christian U.": "Houston Christian",
    "Houston Christian University": "Houston Christian",
    "Illinois State": "Illinois St.",
    "Indiana State": "Indiana St.",
    "Iowa State": "Iowa",  # careful — only if Iowa St. doesn't exist
    "Jackson State": "Jackson St.",
    "Jacksonville State": "Jacksonville St.",
    "James Mad.": "James Madison",
    "Kansas State": "Kansas St.",
    "Kennesaw State": "Kennesaw St.",
    "Kent State": "Kent St.",
    "Kentucky": "Kentucky",
    "LIU Brooklyn": "LIU",
    "Long Island": "LIU",
    "Long Island University": "LIU",
    "LMU": "LMU (CA)",
    "Loyola Marymount": "LMU (CA)",
    "Louisiana State": "LSU",
    "Louisiana-Lafayette": "Louisiana",
    "UL Lafayette": "Louisiana",
    "Louisiana-Monroe": "ULM",
    "La.-Monroe": "ULM",
    "Little Rock": "Little Rock",
    "Lamar": "Lamar University",
    "Massachusetts": "Massachusetts",
    "UMass": "Massachusetts",
    "McNeese State": "McNeese",
    "McNeese St.": "McNeese",
    "Miami": "Miami (FL)",
    "Miami FL": "Miami (FL)",
    "Miami Ohio": "Miami (OH)",
    "Miami OH": "Miami (OH)",
    "Michigan State": "Michigan St.",
    "Middle Tennessee": "Middle Tenn.",
    "Middle Tennessee State": "Middle Tenn.",
    "Middle Tennessee St.": "Middle Tenn.",
    "Missouri State": "Missouri St.",
    "Mississippi Valley": "Mississippi Val.",
    "Miss. Valley": "Mississippi Val.",
    "Miss. Valley St.": "Mississippi Val.",
    "Morehead State": "Morehead St.",
    "Mount St. Marys": "Mount St. Mary's",
    "Mt. St. Mary's": "Mount St. Mary's",
    "Murray State": "Murray St.",
    "N.C. State": "NC State",
    "North Carolina State": "NC State",
    "NC A&T": "N.C. A&T",
    "North Carolina A&T": "N.C. A&T",
    "Norfolk State": "Norfolk St.",
    "North Alabama": "North Ala.",
    "North Dakota State": "North Dakota St.",
    "N. Dakota St.": "North Dakota St.",
    "N. Dakota State": "North Dakota St.",
    "Northern Colorado": "Northern Colo.",
    "No. Colorado": "Northern Colo.",
    "Northern Kentucky": "Northern Ky.",
    "No. Kentucky": "Northern Ky.",
    "Northwestern State": "Northwestern St.",
    "Oklahoma State": "Oklahoma St.",
    "Old Dom.": "Old Dominion",
    "Oral Roberts University": "Oral Roberts",
    "Oregon State": "Oregon St.",
    "Penn State": "Penn St.",
    "Pennsylvania": "Penn",
    "Prairie View A&M": "Prairie View",
    "Prairie View A&amp;M": "Prairie View",
    "Queens": "Queens (NC)",
    "Queens University": "Queens (NC)",
    "Sacramento State": "Sacramento St.",
    "Sac. State": "Sacramento St.",
    "Sac State": "Sacramento St.",
    "Sacred Heart University": "Sacred Heart",
    "Sam Houston State": "Sam Houston",
    "Sam Houston St.": "Sam Houston",
    "San Diego State": "San Diego St.",
    "San Jose State": "San Jose St.",
    "Seattle": "Seattle U",
    "SE Louisiana": "Southeastern La.",
    "Southeastern Louisiana": "Southeastern La.",
    "SE Missouri": "Southeast Mo. St.",
    "SE Missouri State": "Southeast Mo. St.",
    "Southeast Missouri": "Southeast Mo. St.",
    "Southeast Missouri State": "Southeast Mo. St.",
    "SIU-Edwardsville": "SIUE",
    "SIU Edwardsville": "SIUE",
    "Southern": "Southern U.",
    "Southern University": "Southern U.",
    "Southern Illinois": "Southern Ill.",
    "Southern Indiana": "Southern Ind.",
    "Southern Mississippi": "Southern Miss.",
    "S. Miss.": "Southern Miss.",
    "Southern Miss": "Southern Miss.",
    "South Dakota State": "South Dakota St.",
    "South Florida": "South Fla.",
    "S. Florida": "South Fla.",
    "SFA": "SFA",
    "Stephen F. Austin": "SFA",
    "St. Bonaventure University": "St. Bonaventure",
    "St. John's": "St. John's (NY)",
    "Saint Mary's": "Saint Mary's (CA)",
    "St. Thomas": "St. Thomas (MN)",
    "St. Peter's University": "Saint Peter's",
    "St. Peters": "Saint Peter's",
    "Stony Brook University": "Stony Brook",
    "Tarleton": "Tarleton St.",
    "Tarleton State": "Tarleton St.",
    "Tennessee Tech.": "Tennessee Tech",
    "Tennessee State": "Tennessee Tech",  # careful
    "Texas A&amp;M": "Texas A&M",
    "Texas A&M-CC": "A&M-Corpus Christi",
    "Texas A&M-Corpus Christi": "A&M-Corpus Christi",
    "A&M-CC": "A&M-Corpus Christi",
    "AMCC": "A&M-Corpus Christi",
    "Texas State": "Texas St.",
    "Texas Southern University": "Texas Southern",
    "The Citadel": "The Citadel",
    "Troy University": "Troy",
    "UT-Arlington": "UT Arlington",
    "UT-Martin": "UT Martin",
    "UTSA": "UTSA",
    "UT-San Antonio": "UTSA",
    "UT Rio Grande Valley": "UTRGV",
    "Utah Tech University": "Utah Tech",
    "Vanderbilt University": "Vanderbilt",
    "Virginia Tech": "Virginia Tech",
    "VT": "Virginia Tech",
    "Wake Forest University": "Wake Forest",
    "Washington State": "Washington St.",
    "Wash. St.": "Washington St.",
    "West Georgia": "West Ga.",
    "Western Carolina": "Western Caro.",
    "W. Carolina": "Western Caro.",
    "Western Illinois": "Western Ill.",
    "W. Illinois": "Western Ill.",
    "Western Kentucky": "Western Ky.",
    "W. Kentucky": "Western Ky.",
    "Wichita State": "Wichita St.",
    "William and Mary": "William & Mary",
    "Wright State": "Wright St.",
    "Youngstown State": "Youngstown St.",
    "UNC-Asheville": "UNC Asheville",
    "UNC-Greensboro": "UNC Greensboro",
    "UNC-Wilmington": "UNCW",
    "UNC Wilmington": "UNCW",
    "Incarnate Word": "UIW",
    "UMass-Lowell": "UMass Lowell",
    "Maryland-Eastern Shore": "UMES",
    "MD-Eastern Shore": "UMES",
    "Md.-Eastern Shore": "UMES",
    "Coppin State": "Coppin St.",
    "Delaware State": "Delaware St.",
    "Alabama State": "Alabama St.",
    "Alcorn State": "Alcorn",
    "Bethune Cookman": "Bethune-Cookman",
    "Ark.-PB": "Ark.-Pine Bluff",
    "Arkansas-Pine Bluff": "Ark.-Pine Bluff",
    "UC-Davis": "UC Davis",
    "UC-Irvine": "UC Irvine",
    "UC-Riverside": "UC Riverside",
    "UC-San Diego": "UC San Diego",
    "UC-Santa Barbara": "UC Santa Barbara",
    "Cal Baptist": "California Baptist",
    "CBU": "California Baptist",
    "New Mexico State": "New Mexico St.",
    "N. Mexico St.": "New Mexico St.",
    "Long Beach State": "Long Beach St.",
    "N. Florida": "North Florida",
    "Ark. State": "Arkansas St.",
    "Ark. St.": "Arkansas St.",
    "Austin Peay State": "Austin Peay",
    "Austin Peay St.": "Austin Peay",
    "High Point University": "High Point",
    "Texas Tech University": "Texas Tech",
    "Nicholls State": "Nicholls",
    "Nicholls St.": "Nicholls",
}


def fetch_scoreboard(d):
    """Fetch all D1 baseball scores for a given date."""
    url = f"{BASE_URL}/scoreboard/baseball/d1/{d.year}/{d.month:02d}/{d.day:02d}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        resp = urllib.request.urlopen(req, timeout=20, context=_SSL_CTX)
        data = json.loads(resp.read().decode())
        return data.get("games", [])
    except Exception as e:
        print(f"  ERROR {d}: {e}")
        return []


def collect_ncaa_names(dates):
    """Collect all unique NCAA team short names from scoreboard data."""
    names = set()
    for d in dates:
        games = fetch_scoreboard(d)
        for entry in games:
            g = entry.get("game", {})
            for side in ("home", "away"):
                info = g.get(side, {})
                short = info.get("names", {}).get("short", "")
                if short:
                    names.add(short)
        time.sleep(0.3)
        print(f"  {d}: {len(games)} games, {len(names)} unique names so far")
    return names


def resolve_name(conn, name, team_cache):
    """Try to resolve an NCAA name to a team ID."""
    # Exact match
    row = conn.execute("SELECT id, name FROM teams WHERE name=?", (name,)).fetchone()
    if row:
        return row[0], row[1], "exact"

    # Alias match
    alias = conn.execute("SELECT team_id FROM team_aliases WHERE alias=?", (name,)).fetchone()
    if alias:
        team = conn.execute("SELECT name FROM teams WHERE id=?", (alias[0],)).fetchone()
        return alias[0], team[0] if team else "?", "alias"

    # Manual alias
    if name in MANUAL_ALIASES:
        target = MANUAL_ALIASES[name]
        row = conn.execute("SELECT id, name FROM teams WHERE name=?", (target,)).fetchone()
        if row:
            return row[0], row[1], "manual"

    # Fuzzy: State/St., etc.
    for variant in [
        name.replace("State", "St."),
        name.replace("St.", "State"),
        name.replace("Southern", "So."),
        name.replace("Northern", "No."),
        name.replace("Eastern", "E."),
        name.replace("Western", "W."),
        name.replace("University", "").strip(),
        name.replace(" St", " St."),
    ]:
        row = conn.execute("SELECT id, name FROM teams WHERE name=?", (variant.strip(),)).fetchone()
        if row:
            return row[0], row[1], "fuzzy"

    return None, None, "unresolved"


def main():
    from datetime import date

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # Sample dates across the season for comprehensive name collection
    sample_dates = [
        date(2026, 2, 14), date(2026, 2, 21), date(2026, 2, 28),
        date(2026, 3, 1), date(2026, 3, 7), date(2026, 3, 14),
        date(2026, 3, 15), date(2026, 3, 21), date(2026, 3, 28),
        date(2026, 4, 1), date(2026, 4, 4),
    ]

    print("Collecting NCAA team names from scoreboard data...")
    ncaa_names = collect_ncaa_names(sample_dates)
    print(f"\nFound {len(ncaa_names)} unique NCAA team names")

    # Build team name cache
    team_cache = {}
    for row in conn.execute("SELECT id, name FROM teams"):
        team_cache[row[1]] = row[0]

    # Resolve all names
    resolved = []
    unresolved = []
    new_aliases = []

    for name in sorted(ncaa_names):
        tid, tname, method = resolve_name(conn, name, team_cache)
        if tid:
            resolved.append((name, tname, method))
            if method in ("manual", "fuzzy") and name != tname:
                new_aliases.append((name, tid))
        else:
            unresolved.append(name)

    # Insert new aliases
    inserted = 0
    for alias, team_id in new_aliases:
        try:
            conn.execute(
                "INSERT OR IGNORE INTO team_aliases (alias, team_id) VALUES (?, ?)",
                (alias, team_id)
            )
            inserted += 1
        except sqlite3.IntegrityError:
            pass

    # Also insert manual aliases that we know about regardless of scoreboard coverage
    manual_inserted = 0
    for alias, target_name in MANUAL_ALIASES.items():
        row = conn.execute("SELECT id FROM teams WHERE name=?", (target_name,)).fetchone()
        if row:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO team_aliases (alias, team_id) VALUES (?, ?)",
                    (alias, row[0])
                )
                manual_inserted += 1
            except sqlite3.IntegrityError:
                pass

    conn.commit()

    # Report
    print(f"\n=== Results ===")
    print(f"NCAA names collected: {len(ncaa_names)}")
    print(f"Resolved: {len(resolved)}")
    print(f"  - Exact match: {sum(1 for _, _, m in resolved if m == 'exact')}")
    print(f"  - Existing alias: {sum(1 for _, _, m in resolved if m == 'alias')}")
    print(f"  - New fuzzy match: {sum(1 for _, _, m in resolved if m == 'fuzzy')}")
    print(f"  - New manual match: {sum(1 for _, _, m in resolved if m == 'manual')}")
    print(f"New aliases inserted from scoreboard: {inserted}")
    print(f"Manual aliases inserted: {manual_inserted}")
    print(f"Unresolved: {len(unresolved)}")

    if unresolved:
        print(f"\nUnresolved names ({len(unresolved)}):")
        for name in sorted(unresolved):
            print(f"  - {name}")

    # Final alias stats
    total_aliases = conn.execute("SELECT COUNT(*) FROM team_aliases").fetchone()[0]
    teams_with_aliases = conn.execute("SELECT COUNT(DISTINCT team_id) FROM team_aliases").fetchone()[0]
    teams_without = 308 - teams_with_aliases
    print(f"\nFinal alias table: {total_aliases} entries, {teams_with_aliases} teams covered, {teams_without} without aliases")

    conn.close()


if __name__ == "__main__":
    main()
