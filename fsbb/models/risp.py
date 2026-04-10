"""RISP (Runners In Scoring Position) analysis from play-by-play data.

Simulates base-state through each half-inning to compute:
- RISP batting average
- Two-out RISP batting average
- Leadoff on-base percentage
- Strand rate
- Two-out rally rate
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field


@dataclass
class HalfInningState:
    """Track base occupancy and outs during a half-inning."""
    bases: list[str | None] = field(default_factory=lambda: [None, None, None])
    outs: int = 0

    @property
    def risp(self) -> bool:
        """Runners in scoring position (2nd or 3rd)."""
        return self.bases[1] is not None or self.bases[2] is not None

    def clear(self):
        self.bases = [None, None, None]
        self.outs = 0


# Base advancement rules per event type
_BATTER_REACHES = {"single", "double", "triple", "homer", "walk", "hbp",
                   "error", "fielder_choice"}
_BATTER_OUT = {"strikeout", "groundout", "flyout", "lineout", "popout",
               "foulout", "double_play", "sac_fly", "sac_bunt"}
_HIT_BASE = {"single": 0, "double": 1, "triple": 2, "walk": 0, "hbp": 0,
             "error": 0, "fielder_choice": 0}

_RUNNER_SCORED = re.compile(r"(.+?)\s+scored", re.I)
_RUNNER_ADVANCED = re.compile(r"(.+?)\s+advanced to\s+(first|second|third|home|second base|third base)", re.I)
_RUNNER_OUT = re.compile(r"(.+?)\s+out at\s+(first|second|third|home)", re.I)
_BASE_MAP = {"first": 0, "second": 1, "third": 2, "home": 3,
             "second base": 1, "third base": 2}


def _parse_runner_movements(raw_text: str) -> list[dict]:
    """Parse semicolon-separated clauses for runner movement."""
    # NCAA PBP uses semicolons or '3a' as clause separators
    text = raw_text.replace("3a", ";")
    movements = []

    for scored in _RUNNER_SCORED.finditer(text):
        name = scored.group(1).strip().rstrip(",. ")
        # Skip if this is the main action (e.g., "homered... scored")
        if name and len(name) > 1:
            movements.append({"player": name, "action": "scored"})

    for adv in _RUNNER_ADVANCED.finditer(text):
        name = adv.group(1).strip().rstrip(",. ")
        base_str = adv.group(2).strip()
        base_num = _BASE_MAP.get(base_str)
        if name and base_num is not None and base_num < 3:
            movements.append({"player": name, "action": "advance", "to_base": base_num})

    for out in _RUNNER_OUT.finditer(text):
        name = out.group(1).strip().rstrip(",. ")
        if name and len(name) > 1:
            movements.append({"player": name, "action": "out"})

    return movements


def process_event(state: HalfInningState, event: dict) -> tuple[HalfInningState, int]:
    """Update base-state based on a play event.

    Returns (updated_state, runs_scored_this_play).
    """
    etype = event.get("event_type", "other")
    batter = event.get("batter_name", "")
    raw = event.get("raw_text", "")
    runs = 0

    if etype in ("no_play", "pitcher_sub", "other"):
        return state, 0

    # Parse explicit runner movements from text
    movements = _parse_runner_movements(raw)

    # Apply explicit runner movements first
    for mv in movements:
        if mv["action"] == "scored":
            runs += 1
            # Remove from bases
            for i in range(3):
                if state.bases[i] is not None:
                    # Fuzzy match — just remove first occupied base from 3rd→1st
                    pass
            # Clear from highest base first (most likely to score)
            for i in [2, 1, 0]:
                if state.bases[i] is not None:
                    state.bases[i] = None
                    break
        elif mv["action"] == "advance" and "to_base" in mv:
            to = mv["to_base"]
            # Remove from current base, place at new
            for i in range(3):
                if i != to and state.bases[i] is not None:
                    state.bases[i] = None
                    if to < 3:
                        state.bases[to] = mv.get("player", "runner")
                    break
        elif mv["action"] == "out":
            state.outs += 1
            for i in range(3):
                if state.bases[i] is not None:
                    state.bases[i] = None
                    break

    # Handle batter outcome
    if etype == "homer":
        # All runners score + batter scores
        for i in range(3):
            if state.bases[i] is not None:
                runs += 1
                state.bases[i] = None
        runs += 1  # batter scores

    elif etype in _BATTER_REACHES and etype != "homer":
        base = _HIT_BASE.get(etype, 0)
        # Default advancement for non-explicit movements
        if etype in ("single", "double", "triple"):
            # Force runners ahead if no explicit movements parsed
            if not movements:
                advance = {"single": 1, "double": 2, "triple": 3}.get(etype, 1)
                for i in [2, 1, 0]:
                    if state.bases[i] is not None:
                        new_base = i + advance
                        state.bases[i] = None
                        if new_base >= 3:
                            runs += 1
                        else:
                            state.bases[new_base] = "runner"
        elif etype in ("walk", "hbp") and not movements:
            # Force advance on walks only if base ahead is occupied
            if state.bases[0] is not None:
                if state.bases[1] is not None:
                    if state.bases[2] is not None:
                        runs += 1
                        state.bases[2] = None
                    state.bases[2] = state.bases[1]
                state.bases[1] = state.bases[0]
            state.bases[0] = None

        # Place batter
        if etype == "triple":
            state.bases[2] = batter
        elif base < 3:
            state.bases[base] = batter

    elif etype in _BATTER_OUT:
        state.outs += 1
        if etype == "double_play" and not any(m["action"] == "out" for m in movements):
            state.outs += 1  # extra out if not already counted in movements
        if etype == "sac_fly" and not movements:
            # Runner on 3rd scores by default
            if state.bases[2] is not None:
                runs += 1
                state.bases[2] = None

    return state, runs


def compute_team_risp(
    conn: sqlite3.Connection,
    team_id: int | None = None,
    cutoff_date: str | None = None,
) -> dict[int, dict]:
    """Compute RISP stats for teams from PBP data.

    Returns {team_id: {risp_avg, risp_pa, two_out_risp_avg, leadoff_obp, strand_rate, ...}}
    """
    where_clauses = ["1=1"]
    params: list = []

    if team_id is not None:
        where_clauses.append("pe.batting_team_id = ?")
        params.append(team_id)
    if cutoff_date is not None:
        where_clauses.append("pe.game_date < ?")
        params.append(cutoff_date)

    events = conn.execute(f"""
        SELECT pe.game_id, pe.inning, pe.is_top, pe.batting_team_id,
               pe.sequence_in_inning, pe.event_type, pe.batter_name,
               pe.raw_text, pe.runs_scored
        FROM play_events pe
        WHERE {' AND '.join(where_clauses)}
          AND pe.event_type NOT IN ('no_play', 'pitcher_sub')
        ORDER BY pe.batting_team_id, pe.game_id, pe.inning, pe.is_top, pe.sequence_in_inning
    """, params).fetchall()

    if not events:
        return {}

    # Accumulate per team
    team_stats: dict[int, dict] = {}

    def ensure_team(tid):
        if tid not in team_stats:
            team_stats[tid] = {
                "risp_pa": 0, "risp_hits": 0, "risp_hr": 0,
                "two_out_risp_pa": 0, "two_out_risp_hits": 0,
                "leadoff_pa": 0, "leadoff_on_base": 0,
                "total_runners": 0, "runners_stranded": 0,
                "total_half_innings": 0,
                "two_out_runs": 0, "two_out_innings": 0,
            }

    # Process events grouped by half-inning
    state = HalfInningState()
    prev_key = None
    is_first_pa = True
    runners_this_inning = 0
    runs_this_inning = 0
    had_two_outs = False

    at_bat_types = _BATTER_REACHES | _BATTER_OUT | {"stolen_base", "caught_stealing"}

    for ev in events:
        tid = ev["batting_team_id"]
        ensure_team(tid)
        key = (ev["game_id"], ev["inning"], ev["is_top"], tid)

        # New half-inning
        if key != prev_key:
            # Finalize previous half-inning
            if prev_key is not None:
                prev_tid = prev_key[3]
                team_stats[prev_tid]["total_runners"] += runners_this_inning
                team_stats[prev_tid]["runners_stranded"] += max(
                    0, runners_this_inning - runs_this_inning
                )
                team_stats[prev_tid]["total_half_innings"] += 1
                if had_two_outs:
                    team_stats[prev_tid]["two_out_innings"] += 1

            state.clear()
            prev_key = key
            is_first_pa = True
            runners_this_inning = 0
            runs_this_inning = 0
            had_two_outs = False

        etype = ev["event_type"]
        if etype == "other":
            continue

        # Is this an at-bat event?
        is_ab = etype in at_bat_types

        if is_ab:
            # RISP check BEFORE the event
            if state.risp:
                team_stats[tid]["risp_pa"] += 1
                if etype in ("single", "double", "triple", "homer"):
                    team_stats[tid]["risp_hits"] += 1
                if etype == "homer":
                    team_stats[tid]["risp_hr"] += 1
                if state.outs == 2:
                    team_stats[tid]["two_out_risp_pa"] += 1
                    if etype in ("single", "double", "triple", "homer"):
                        team_stats[tid]["two_out_risp_hits"] += 1

            # Leadoff PA (first batter of inning)
            if is_first_pa:
                team_stats[tid]["leadoff_pa"] += 1
                if etype in _BATTER_REACHES:
                    team_stats[tid]["leadoff_on_base"] += 1
                is_first_pa = False

            # Track two-out state
            if state.outs >= 2:
                had_two_outs = True

        # Process the event to update base-state
        event_dict = {
            "event_type": etype,
            "batter_name": ev["batter_name"] or "",
            "raw_text": ev["raw_text"] or "",
        }
        state, runs = process_event(state, event_dict)
        runs_this_inning += runs

        # Count runners who reached base
        if etype in _BATTER_REACHES:
            runners_this_inning += 1

        # Two-out runs
        if had_two_outs and runs > 0:
            team_stats[tid]["two_out_runs"] += runs

        # Reset on 3 outs
        if state.outs >= 3:
            state.clear()

    # Finalize last half-inning
    if prev_key is not None:
        prev_tid = prev_key[3]
        team_stats[prev_tid]["total_runners"] += runners_this_inning
        team_stats[prev_tid]["runners_stranded"] += max(
            0, runners_this_inning - runs_this_inning
        )
        team_stats[prev_tid]["total_half_innings"] += 1

    # Compute derived rates
    result = {}
    for tid, s in team_stats.items():
        r = {}
        r["risp_pa"] = s["risp_pa"]
        r["risp_hits"] = s["risp_hits"]
        r["risp_avg"] = s["risp_hits"] / max(s["risp_pa"], 1) if s["risp_pa"] > 0 else None
        r["risp_hr_rate"] = s["risp_hr"] / max(s["risp_pa"], 1) if s["risp_pa"] > 0 else None
        r["two_out_risp_avg"] = (s["two_out_risp_hits"] / max(s["two_out_risp_pa"], 1)
                                 if s["two_out_risp_pa"] > 0 else None)
        r["leadoff_obp"] = (s["leadoff_on_base"] / max(s["leadoff_pa"], 1)
                            if s["leadoff_pa"] > 0 else None)
        r["strand_rate"] = (s["runners_stranded"] / max(s["total_runners"], 1)
                            if s["total_runners"] > 0 else None)
        r["two_out_rally_rate"] = (s["two_out_runs"] / max(s["total_half_innings"], 1)
                                   if s["total_half_innings"] > 0 else None)
        result[tid] = r

    return result
