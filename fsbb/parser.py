"""Play-by-play text parser.

Converts NCAA narrative play descriptions into structured event data.
Verified patterns from live API data (game 6542839, Kentucky vs Missouri, April 5 2026).

Input:  "DURNIN, Kam flied out to cf (0-1 K)."
Output: {"event_type": "flyout", "batter_name": "DURNIN, Kam",
         "hit_direction": "cf", "pitch_count": "0-1", "pitch_sequence": "K"}
"""

from __future__ import annotations

import re
from typing import Any

# Compile all patterns once at import time
_PATTERNS = {
    # Outs
    "strikeout":     re.compile(r"^(.+?)\s+struck out\s+(swinging|looking)", re.I),
    "groundout":     re.compile(r"^(.+?)\s+grounded out to\s+(.+?)[\s(.]", re.I),
    "flyout":        re.compile(r"^(.+?)\s+flied out to\s+(.+?)[\s(,.]", re.I),
    "lineout":       re.compile(r"^(.+?)\s+lined out to\s+(.+?)[\s(,.]", re.I),
    "popout":        re.compile(r"^(.+?)\s+popped up to\s+(.+?)[\s(,.]", re.I),
    "foulout":       re.compile(r"^(.+?)\s+fouled out to\s+(.+?)[\s(,.]", re.I),

    # Hits — capture multi-word directions like "up the middle", "to left center"
    "single":        re.compile(r"^(.+?)\s+singled\s+(.+?)(?:\s*\(|;\s|,\s*RBI|\.\s*$)", re.I),
    "double":        re.compile(r"^(.+?)\s+doubled\s+(.+?)(?:\s*\(|;\s|,\s*RBI|\.\s*$)", re.I),
    "triple":        re.compile(r"^(.+?)\s+tripled\s+(.+?)(?:\s*\(|;\s|,\s*RBI|\.\s*$)", re.I),
    "homer":         re.compile(r"^(.+?)\s+homered\s+(.+?)(?:\s*\(|;\s|,\s*RBI|\.\s*$)", re.I),

    # Walks / HBP — handle "walked," and "walked ("
    "walk":          re.compile(r"^(.+?)\s+walked(?:\s*[,(.]|\s*$)", re.I),
    "hbp":           re.compile(r"^(.+?)\s+hit by pitch", re.I),

    # Reaching on error
    "error":         re.compile(r"^(.+?)\s+reached on\s+(?:a |an )?(?:throwing |fielding )?error", re.I),

    # Sacrifice
    "sac_bunt":      re.compile(r"out on a sacrifice bunt|SAC, bunt", re.I),
    "sac_fly":       re.compile(r"flied out.+?SF,\s*RBI|sac fly|sacrifice fly", re.I),

    # Baserunning
    "stolen_base":   re.compile(r"^(.+?)\s+stole\s+(second|third|home)", re.I),
    "caught_steal":  re.compile(r"caught stealing|out at.+?caught stealing", re.I),
    "wild_pitch":    re.compile(r"advanced.+?on a wild pitch|wild pitch", re.I),

    # Substitutions
    "pitcher_sub":   re.compile(r"^(.+?)\s+to p for\s+(.+?)\.?\s*$", re.I),
    "pinch_hit":     re.compile(r"pinch hit", re.I),
}

# Pitch count in parentheses: (2-2 KFBBFS) or (0-1 K)
_PITCH_COUNT = re.compile(r"\((\d+-\d+)\s+([KBFS]+)\)")

# RBI indicator
_RBI = re.compile(r"(\d+)\s*RBI|RBI", re.I)

# Score after play
_SCORED = re.compile(r"scored", re.I)


def parse_play_text(text: str) -> dict[str, Any]:
    """Parse a single play description into structured fields.

    Returns dict with: event_type, batter_name, hit_direction,
    pitch_count, pitch_sequence, rbi, runs_scored, is_error, is_sacrifice,
    stolen_base, caught_stealing, wild_pitch,
    pitcher_sub_in, pitcher_sub_out
    """
    result: dict[str, Any] = {
        "event_type": "other",
        "batter_name": None,
        "hit_direction": None,
        "pitch_count": None,
        "pitch_sequence": None,
        "rbi": 0,
        "runs_scored": 0,
        "is_error": 0,
        "is_sacrifice": 0,
        "stolen_base": 0,
        "caught_stealing": 0,
        "wild_pitch": 0,
        "pitcher_sub_in": None,
        "pitcher_sub_out": None,
    }

    if not text or text.strip() == "No play.":
        result["event_type"] = "no_play"
        return result

    # Extract pitch count if present
    pc = _PITCH_COUNT.search(text)
    if pc:
        result["pitch_count"] = pc.group(1)
        result["pitch_sequence"] = pc.group(2)

    # Count RBIs
    rbi_match = _RBI.search(text)
    if rbi_match:
        try:
            result["rbi"] = int(rbi_match.group(1)) if rbi_match.group(1) else 1
        except (ValueError, IndexError):
            result["rbi"] = 1

    # Count runs scored
    result["runs_scored"] = len(_SCORED.findall(text))

    # Check for special events first
    if _PATTERNS["wild_pitch"].search(text):
        result["wild_pitch"] = 1

    if _PATTERNS["caught_steal"].search(text):
        result["caught_stealing"] = 1
        result["event_type"] = "caught_stealing"
        return result

    # Pitcher substitution
    ps = _PATTERNS["pitcher_sub"].search(text)
    if ps:
        result["event_type"] = "pitcher_sub"
        result["pitcher_sub_in"] = ps.group(1).strip()
        result["pitcher_sub_out"] = ps.group(2).strip()
        return result

    # Error (check BEFORE sacrifice — "reached on error ... SAC, bunt" is an error)
    err_m = _PATTERNS["error"].search(text)
    if err_m:
        result["event_type"] = "error"
        result["batter_name"] = err_m.group(1).strip()
        result["is_error"] = 1
        if _PATTERNS["sac_bunt"].search(text):
            result["is_sacrifice"] = 1
        return result

    # Sacrifice fly (check before flyout)
    if _PATTERNS["sac_fly"].search(text):
        result["event_type"] = "sac_fly"
        result["is_sacrifice"] = 1
        m = _PATTERNS["flyout"].search(text)
        if m:
            result["batter_name"] = m.group(1).strip()
            result["hit_direction"] = m.group(2).strip()
        return result

    # Sac bunt
    if _PATTERNS["sac_bunt"].search(text):
        result["event_type"] = "sac_bunt"
        result["is_sacrifice"] = 1
        m = re.match(r"^(.+?)\s+(?:reached|out)", text, re.I)
        if m:
            result["batter_name"] = m.group(1).strip()
        return result

    # Stolen base
    sb = _PATTERNS["stolen_base"].search(text)
    if sb:
        result["event_type"] = "stolen_base"
        result["stolen_base"] = 1
        result["batter_name"] = sb.group(1).strip()
        return result

    # Standard at-bat outcomes (order matters)
    # Standard at-bat outcomes (error already handled above)
    for event_type in ["homer", "triple", "double", "single",
                       "strikeout", "groundout", "flyout", "lineout",
                       "popout", "foulout", "walk", "hbp"]:
        m = _PATTERNS[event_type].search(text)
        if m:
            result["event_type"] = event_type
            result["batter_name"] = m.group(1).strip()
            if event_type in ("groundout", "flyout", "lineout", "popout",
                              "foulout", "single", "double", "triple", "homer"):
                if m.lastindex and m.lastindex >= 2:
                    result["hit_direction"] = m.group(2).strip()
            break

    return result
