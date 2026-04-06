"""SQLite database connection and schema management."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "fsbb.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    conference TEXT NOT NULL,
    division TEXT NOT NULL DEFAULT 'D1',
    -- PEAR imported ratings (benchmark)
    pear_power_rating REAL,
    pear_net INTEGER,
    pear_net_score REAL,
    pear_elo REAL,
    pear_sos INTEGER,
    pear_sor INTEGER,
    pear_rpi INTEGER,
    pear_prr INTEGER,
    pear_rqi INTEGER,
    -- Aggregate season stats
    total_rs INTEGER DEFAULT 0,
    total_ra INTEGER DEFAULT 0,
    games_played INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    -- Our computed ratings (updated daily)
    pythag_exp REAL,
    pythag_pct REAL,
    bt_rating REAL DEFAULT 0.0,
    sos REAL,
    power_rating REAL,
    elo REAL DEFAULT 1500.0
);

CREATE TABLE IF NOT EXISTS team_aliases (
    alias TEXT PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id)
);

CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    home_team_id INTEGER NOT NULL REFERENCES teams(id),
    away_team_id INTEGER NOT NULL REFERENCES teams(id),
    home_runs INTEGER,
    away_runs INTEGER,
    innings INTEGER DEFAULT 9,
    status TEXT NOT NULL DEFAULT 'scheduled',
    neutral_site INTEGER DEFAULT 0,
    conference_game INTEGER DEFAULT 0,
    -- Predictions
    our_home_win_prob REAL,
    our_predicted_total REAL,
    our_predicted_winner_id INTEGER,
    pear_home_win_prob REAL,
    -- Results
    actual_winner_id INTEGER,
    our_correct INTEGER,
    pear_correct INTEGER,
    source TEXT DEFAULT 'ncaa',
    UNIQUE(date, home_team_id, away_team_id)
);

CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL REFERENCES games(id),
    model_version TEXT NOT NULL,
    home_win_prob REAL NOT NULL,
    predicted_total_runs REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(game_id, model_version)
);

CREATE TABLE IF NOT EXISTS model_accuracy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    model_version TEXT NOT NULL,
    games_predicted INTEGER,
    games_correct INTEGER,
    accuracy REAL,
    brier_score REAL,
    pear_games_correct INTEGER,
    pear_accuracy REAL,
    pear_brier_score REAL,
    edge REAL,
    UNIQUE(date, model_version)
);

CREATE INDEX IF NOT EXISTS idx_games_date ON games(date);
CREATE INDEX IF NOT EXISTS idx_games_status ON games(status);
CREATE INDEX IF NOT EXISTS idx_teams_conference ON teams(conference);
"""


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Get a database connection with row factory."""
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"

SCHEMA_VERSION_TABLE = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT DEFAULT (datetime('now'))
);
"""


def init_db(db_path: Path | None = None) -> sqlite3.Connection:
    """Initialize database with schema and apply pending migrations."""
    conn = get_connection(db_path)
    conn.executescript(SCHEMA)
    conn.executescript(SCHEMA_VERSION_TABLE)
    conn.commit()
    apply_migrations(conn)
    return conn


def apply_migrations(conn: sqlite3.Connection) -> int:
    """Apply any pending migrations from migrations/ directory.

    Reads numbered SQL files (001_*.sql, 002_*.sql, ...) and applies
    any not yet recorded in schema_version. Returns count applied.
    """
    conn.executescript(SCHEMA_VERSION_TABLE)
    applied = set(
        r[0] for r in conn.execute("SELECT version FROM schema_version").fetchall()
    )

    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql")) if MIGRATIONS_DIR.exists() else []
    count = 0

    for f in migration_files:
        # Extract version number from filename: 001_baseline.sql → 1
        try:
            version = int(f.stem.split("_")[0])
        except (ValueError, IndexError):
            continue

        if version in applied:
            continue

        sql = f.read_text().strip()
        if sql:
            conn.executescript(sql)
        conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
        conn.commit()
        count += 1

    return count


def schema_version(conn: sqlite3.Connection) -> int:
    """Get current schema version."""
    try:
        row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        return row[0] if row and row[0] else 0
    except sqlite3.OperationalError:
        return 0


def reset_db(db_path: Path | None = None) -> sqlite3.Connection:
    """Drop all tables and reinitialize. USE WITH CAUTION."""
    path = db_path or DB_PATH
    if path.exists():
        path.unlink()
    return init_db(db_path)
