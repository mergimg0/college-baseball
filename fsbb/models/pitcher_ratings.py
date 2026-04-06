"""Pitcher quality ratings.

Rates every pitcher with 10+ IP on a normalized z-score scale.

Quality score = weighted combination of:
  - ERA   (35%) — lower is better
  - K/9   (25%) — higher is better
  - BB/9  (20%) — lower is better
  - WHIP  (20%) — lower is better

Normalized to z-scores relative to all D1 pitchers with 10+ IP.
"""

from __future__ import annotations

import sqlite3

import numpy as np


def compute_pitcher_ratings(conn: sqlite3.Connection) -> int:
    """Rate every pitcher with 10+ IP.

    Stores quality_rating in pitchers table.
    Returns number of pitchers rated.
    """
    pitchers = conn.execute("""
        SELECT id, season_ip, season_era, season_k, season_bb,
               season_hits_allowed, season_er
        FROM pitchers WHERE season_ip >= 10
    """).fetchall()

    if len(pitchers) < 20:
        return 0

    stats = []
    for p in pitchers:
        ip = p[1]
        era = p[2] if p[2] else (p[6] * 9.0 / ip if ip > 0 else 99.0)
        k9 = p[3] * 9.0 / ip
        bb9 = p[4] * 9.0 / ip
        whip = (p[5] + p[4]) / ip
        stats.append({"id": p[0], "era": era, "k9": k9, "bb9": bb9, "whip": whip})

    eras = np.array([s["era"] for s in stats])
    k9s = np.array([s["k9"] for s in stats])
    bb9s = np.array([s["bb9"] for s in stats])
    whips = np.array([s["whip"] for s in stats])

    for i, s in enumerate(stats):
        z_era = -(eras[i] - eras.mean()) / max(eras.std(), 0.01)
        z_k9 = (k9s[i] - k9s.mean()) / max(k9s.std(), 0.01)
        z_bb9 = -(bb9s[i] - bb9s.mean()) / max(bb9s.std(), 0.01)
        z_whip = -(whips[i] - whips.mean()) / max(whips.std(), 0.01)

        rating = 0.35 * z_era + 0.25 * z_k9 + 0.20 * z_bb9 + 0.20 * z_whip

        conn.execute(
            "UPDATE pitchers SET quality_rating = ?, updated_at = datetime('now') WHERE id = ?",
            (round(float(rating), 3), s["id"]),
        )

    conn.commit()
    return len(stats)
