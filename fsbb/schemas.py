"""Pydantic models for data validation."""

from pydantic import BaseModel
from datetime import date


class Team(BaseModel):
    id: int | None = None
    name: str
    conference: str
    division: str = "D1"
    total_rs: int = 0
    total_ra: int = 0
    games_played: int = 0
    wins: int = 0
    losses: int = 0
    pythag_pct: float | None = None
    bt_rating: float = 0.0
    sos: float | None = None
    power_rating: float | None = None
    elo: float = 1500.0


class Game(BaseModel):
    id: int | None = None
    date: date
    home_team: str
    away_team: str
    home_runs: int | None = None
    away_runs: int | None = None
    innings: int = 9
    status: str = "scheduled"
    source: str = "ncaa"


class Prediction(BaseModel):
    game_id: int
    model_version: str
    home_win_prob: float
    predicted_total_runs: float | None = None


class MatchupResult(BaseModel):
    home_team: str
    away_team: str
    home_win_prob: float
    away_win_prob: float
    predicted_total_runs: float | None = None
    home_bt_rating: float
    away_bt_rating: float
    home_pythag: float
    away_pythag: float
    confidence: str  # "low", "medium", "high"
    model_version: str = "v0.1"
