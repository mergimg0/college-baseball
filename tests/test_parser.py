"""Tests for fsbb.parser — play text parsing."""

from fsbb.parser import parse_play_text


def test_strikeout_swinging():
    r = parse_play_text("J. Tharnish struck out swinging (2-2 KFBBFS).")
    assert r["event_type"] == "strikeout"
    assert r["batter_name"] == "J. Tharnish"
    assert r["pitch_count"] == "2-2"
    assert r["pitch_sequence"] == "KFBBFS"


def test_single():
    r = parse_play_text("T. Bell singled up the middle (1-0 B).")
    assert r["event_type"] == "single"
    assert r["batter_name"] == "T. Bell"
    assert r["hit_direction"] == "up the middle"


def test_homer_rbi():
    r = parse_play_text("WARD, Blaize homered to left field, RBI (2-1 BKB).")
    assert r["event_type"] == "homer"
    assert r["rbi"] >= 1


def test_walk():
    r = parse_play_text("SEALS, Pierr walked (3-2 BBBSKFFB).")
    assert r["event_type"] == "walk"
    assert r["pitch_count"] == "3-2"


def test_hbp():
    r = parse_play_text("WOITA, Jase hit by pitch (2-2 KBFBF).")
    assert r["event_type"] == "hbp"


def test_error():
    r = parse_play_text("KNUTSON, Kee reached on a throwing error by p, SAC, bunt.")
    assert r["event_type"] == "error"
    assert r["is_error"] == 1


def test_pitcher_sub():
    r = parse_play_text("R. Mullan to p for B. Cleaver.")
    assert r["event_type"] == "pitcher_sub"
    assert r["pitcher_sub_in"] == "R. Mullan"
    assert r["pitcher_sub_out"] == "B. Cleaver"


def test_wild_pitch():
    r = parse_play_text("WOITA, Jase advanced to second on a wild pitch.")
    assert r["wild_pitch"] == 1


def test_caught_stealing():
    r = parse_play_text("PEER, Kaden out at second p to 1b to ss, caught stealing.")
    assert r["caught_stealing"] == 1


def test_sac_fly():
    r = parse_play_text("DURNIN, Kam flied out to cf, SF, RBI (0-0); MAISONET, Er scored.")
    assert r["event_type"] == "sac_fly"
    assert r["is_sacrifice"] == 1


def test_no_play():
    r = parse_play_text("No play.")
    assert r["event_type"] == "no_play"


def test_walk_rbi():
    r = parse_play_text("CAMPOS, Juli walked, RBI (3-2 BBBKKFB); SEALS, Pierr scored.")
    assert r["event_type"] == "walk"
    assert r["rbi"] >= 1
    assert r["runs_scored"] >= 1


def test_groundout():
    r = parse_play_text("SMITH, John grounded out to ss (1-2 BKF).")
    assert r["event_type"] == "groundout"
    assert r["batter_name"] == "SMITH, John"
    assert r["hit_direction"] == "ss"


def test_double():
    r = parse_play_text("JONES, Mike doubled to left center (0-0).")
    assert r["event_type"] == "double"
    assert r["batter_name"] == "JONES, Mike"
