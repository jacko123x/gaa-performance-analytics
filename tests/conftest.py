import os
from pathlib import Path
import tempfile

import pandas as pd
import pytest
from sqlalchemy import text


TEST_DATABASE = Path(tempfile.gettempdir()) / (
    f"gaa_analytics_pytest_{os.getpid()}.db"
)
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{TEST_DATABASE}"

from src.database.db import Base, engine  # noqa: E402
from src.database import models  # noqa: E402, F401
from src.health import expected_schema_revision  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_database():
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS alembic_version"))
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE alembic_version "
                "(version_num VARCHAR(32) NOT NULL)"
            )
        )
        connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
            {"revision": expected_schema_revision()},
        )
    yield
    Base.metadata.drop_all(engine)
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS alembic_version"))


def pytest_sessionfinish(session, exitstatus):
    engine.dispose()
    TEST_DATABASE.unlink(missing_ok=True)


@pytest.fixture
def sample_bundle():
    match_id = "test_match"
    return {
        "matches": pd.DataFrame(
            [
                {
                    "MatchID": match_id,
                    "Date": "2026-09-01",
                    "Competition": "Club Championship",
                    "Round": "Test round",
                    "Venue": "Test venue",
                    "HomeTeam": "Austin Stacks",
                    "AwayTeam": "Test Club",
                    "HomeScore": 10,
                    "AwayScore": 7,
                    "Result": "Win",
                }
            ]
        ),
        "team_stats": pd.DataFrame(
            [
                {
                    "MatchID": match_id,
                    "Team": "Austin Stacks",
                    "Opponent": "Test Club",
                    "Goals": 1,
                    "Points": 7,
                    "TwoPointers": 0,
                    "Attacks": 12,
                    "TotalShots": 10,
                    "TotalScores": 8,
                    "ShotsPlay": 8,
                    "ScoresPlay": 6,
                    "ShotsPlaced": 2,
                    "ScoresPlaced": 2,
                    "KickoutsWon": 5,
                    "KickoutsLost": 2,
                    "ForcedTurnovers": 4,
                    "UnforcedTurnovers": 2,
                    "FreesConceded": 5,
                }
            ]
        ),
        "shooting": pd.DataFrame(
            [
                {
                    "MatchID": match_id,
                    "Team": "Austin Stacks",
                    "Period": "FT",
                    "ShotType": "Play",
                    "ShotsTaken": 8,
                    "ShotsScored": 6,
                    "Wides": 2,
                }
            ]
        ),
        "scoring_sources": pd.DataFrame(
            [
                {
                    "MatchID": match_id,
                    "Team": "Austin Stacks",
                    "Source": "Structured Play",
                    "Scores": 8,
                }
            ]
        ),
        "kickouts": pd.DataFrame(
            [
                {
                    "MatchID": match_id,
                    "Team": "Austin Stacks",
                    "Period": "FT",
                    "KickoutType": "Own",
                    "Taken": 7,
                    "Won": 5,
                    "Lost": 2,
                    "CleanWins": 3,
                    "BreakWins": 2,
                }
            ]
        ),
        "turnovers": pd.DataFrame(
            [
                {
                    "MatchID": match_id,
                    "Team": "Austin Stacks",
                    "Period": "FT",
                    "TurnoversWonForced": 4,
                    "TurnoversWonUnforced": 2,
                    "TurnoversLostForced": 2,
                    "TurnoversLostUnforced": 1,
                }
            ]
        ),
        "player_data": pd.DataFrame(
            [
                {
                    "MatchID": match_id,
                    "Date": "2026-09-01",
                    "Opponent": "Test Club",
                    "HomeAway": "Home",
                    "Result": "Win",
                    "DataType": "Championship",
                    "SquadNumber": 8,
                    "PlayerName": "Test Player",
                    "Position": "Midfield",
                    "Started": True,
                    "MinutesPlayed": 60,
                    "Possessions": 10,
                    "HandpassesTotal": 5,
                    "HandpassesCompleted": 5,
                    "FootpassesTotal": 4,
                    "FootpassesCompleted": 3,
                    "IncompletePasses": 1,
                    "TurnoversWon": 2,
                    "Assists": 1,
                    "Points": 1,
                    "ShotAttempts": 1,
                    "Scores": 1,
                }
            ]
        ),
    }
