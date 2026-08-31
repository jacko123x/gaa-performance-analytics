from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import func, select

from src.database.db import SessionLocal
from src.database.models import (
    KickoutStat,
    Match,
    Player,
    PlayerMatchStat,
    ScoringSource,
    ShootingDetail,
    TeamMatchStat,
    TurnoverStat,
    User,
)
from src.database.security import hash_password


# ---------------------------------------------------------------------
# Paths / configuration
# ---------------------------------------------------------------------

DATA_DIR = PROJECT_ROOT / "data"

load_dotenv(PROJECT_ROOT / ".env")

# Temporary migration password.
# This lets us migrate the existing shared-password setup into the DB.
SHARED_PASSWORD = os.getenv("INITIAL_SHARED_PASSWORD", "stacks2026")


# ---------------------------------------------------------------------
# CSV files
# ---------------------------------------------------------------------

MATCHES_FILE = DATA_DIR / "club2026matches.csv"
TEAM_STATS_FILE = DATA_DIR / "club2026team_match_stats.csv"
SHOOTING_FILE = DATA_DIR / "club2026shooting_detail.csv"
SCORING_SOURCES_FILE = DATA_DIR / "club2026scoring_sources.csv"
KICKOUT_FILE = DATA_DIR / "club2026kickout_stats.csv"
TURNOVER_FILE = DATA_DIR / "club2026turnover_stats.csv"
PLAYER_DATA_FILE = DATA_DIR / "club2026player_match_data.csv"
USERS_FILE = DATA_DIR / "app_users.csv"


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def clean_string(value):
    """Return stripped string or None for blank/NaN."""
    if pd.isna(value):
        return None

    value = str(value).strip()

    if not value:
        return None

    return value


def to_int(value, default=0):
    """Safely convert CSV value to integer."""
    if pd.isna(value) or value == "":
        return default

    return int(float(value))


def to_float(value, default=None):
    """Safely convert CSV value to float."""
    if pd.isna(value) or value == "":
        return default

    return float(value)


def to_bool(value, default=False):
    """
    Convert common CSV boolean representations.

    Supports:
    True / False
    TRUE / FALSE
    Yes / No
    Y / N
    1 / 0
    """
    if pd.isna(value):
        return default

    if isinstance(value, bool):
        return value

    value = str(value).strip().lower()

    if value in {"true", "yes", "y", "1"}:
        return True

    if value in {"false", "no", "n", "0"}:
        return False

    return default


def to_date(value):
    """Convert CSV date to Python date."""
    if pd.isna(value) or value == "":
        return None

    parsed = pd.to_datetime(value, errors="raise")

    return parsed.date()


def require_file(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")


def check_required_files():
    files = [
        MATCHES_FILE,
        TEAM_STATS_FILE,
        SHOOTING_FILE,
        SCORING_SOURCES_FILE,
        KICKOUT_FILE,
        TURNOVER_FILE,
        PLAYER_DATA_FILE,
        USERS_FILE,
    ]

    for path in files:
        require_file(path)


# ---------------------------------------------------------------------
# Database safety
# ---------------------------------------------------------------------

def ensure_database_empty(session):
    """
    Prevent accidental duplicate imports.

    This migration is intended for the initial CSV -> PostgreSQL load.
    """
    tables = [
        User,
        PlayerMatchStat,
        KickoutStat,
        TurnoverStat,
        ShootingDetail,
        ScoringSource,
        TeamMatchStat,
        Player,
        Match,
    ]

    populated = []

    for model in tables:
        count = session.scalar(
            select(func.count()).select_from(model)
        )

        if count:
            populated.append(
                f"{model.__tablename__}: {count}"
            )

    if populated:
        details = "\n".join(populated)

        raise RuntimeError(
            "Database is not empty.\n"
            "Migration stopped to prevent duplicate data.\n\n"
            f"{details}"
        )


# ---------------------------------------------------------------------
# Matches
# ---------------------------------------------------------------------

def migrate_matches(session):
    df = pd.read_csv(MATCHES_FILE)

    matches = {}

    for _, row in df.iterrows():
        match_code = clean_string(row["MatchID"])

        if not match_code:
            raise ValueError("MatchID cannot be empty")

        match = Match(
            match_code=match_code,
            date=to_date(row["Date"]),
            competition=clean_string(row["Competition"]),
            round=clean_string(row["Round"]),
            venue=clean_string(row["Venue"]),
            home_team=clean_string(row["HomeTeam"]),
            away_team=clean_string(row["AwayTeam"]),
            home_score=clean_string(row["HomeScore"]),
            away_score=clean_string(row["AwayScore"]),
            result=clean_string(row["Result"]),
        )

        session.add(match)

        # Flush generates match.id without committing transaction.
        session.flush()

        matches[match_code] = match

    print(f"✓ Matches: {len(matches)}")

    return matches


# ---------------------------------------------------------------------
# Players
# ---------------------------------------------------------------------

def migrate_players(session):
    df = pd.read_csv(PLAYER_DATA_FILE)

    players = {}

    # One database player per unique PlayerName.
    grouped = df.groupby("PlayerName", dropna=True)

    for player_name, rows in grouped:
        player_name = clean_string(player_name)

        if not player_name:
            continue

        squad_numbers = (
            pd.to_numeric(
                rows["SquadNumber"],
                errors="coerce",
            )
            .dropna()
            .astype(int)
            .tolist()
        )

        squad_number = squad_numbers[0] if squad_numbers else None

        player = Player(
            player_name=player_name,
            squad_number=squad_number,
            active=True,
        )

        session.add(player)
        session.flush()

        players[player_name] = player

    print(f"✓ Players: {len(players)}")

    return players


# ---------------------------------------------------------------------
# Team match stats
# ---------------------------------------------------------------------

def migrate_team_stats(session, matches):
    df = pd.read_csv(TEAM_STATS_FILE)

    count = 0

    for _, row in df.iterrows():
        match = matches.get(clean_string(row["MatchID"]))

        if not match:
            raise ValueError(
                f"Unknown MatchID in team stats: {row['MatchID']}"
            )

        record = TeamMatchStat(
            match_id=match.id,
            team=clean_string(row["Team"]),
            opponent=clean_string(row["Opponent"]),
            goals=to_int(row["Goals"]),
            points=to_int(row["Points"]),
            two_pointers=to_int(row["TwoPointers"]),
            wides=to_int(row["Wides"]),
            shorts=to_int(row["Shorts"]),
            kickouts_won=to_int(row["KickoutsWon"]),
            kickouts_lost=to_int(row["KickoutsLost"]),
            forced_turnovers=to_int(row["ForcedTurnovers"]),
            unforced_turnovers=to_int(row["UnforcedTurnovers"]),
            frees_conceded=to_int(row["FreesConceded"]),
            breaking_ball_won=to_int(row["BreakingBallWon"]),
            attacks=to_int(row["Attacks"]),
            total_shots=to_int(row["TotalShots"]),
            total_scores=to_int(row["TotalScores"]),
            shots_play=to_int(row["ShotsPlay"]),
            scores_play=to_int(row["ScoresPlay"]),
            shots_placed=to_int(row["ShotsPlaced"]),
            scores_placed=to_int(row["ScoresPlaced"]),
        )

        session.add(record)
        count += 1

    print(f"✓ Team match stats: {count}")


# ---------------------------------------------------------------------
# Shooting
# ---------------------------------------------------------------------

def migrate_shooting(session, matches):
    df = pd.read_csv(SHOOTING_FILE)

    count = 0

    for _, row in df.iterrows():
        match = matches.get(clean_string(row["MatchID"]))

        if not match:
            raise ValueError(
                f"Unknown MatchID in shooting detail: {row['MatchID']}"
            )

        record = ShootingDetail(
            match_id=match.id,
            team=clean_string(row["Team"]),
            period=clean_string(row["Period"]),
            shot_type=clean_string(row["ShotType"]),
            shots_taken=to_int(row["ShotsTaken"]),
            shots_scored=to_int(row["ShotsScored"]),
            wides=to_int(row["Wides"]),
            shorts=to_int(row["Shorts"]),
            blocked=to_int(row["Blocked"]),
            post=to_int(row["Post"]),
            saved=to_int(row["Saved"]),
        )

        session.add(record)
        count += 1

    print(f"✓ Shooting detail: {count}")


# ---------------------------------------------------------------------
# Scoring sources
# ---------------------------------------------------------------------

def migrate_scoring_sources(session, matches):
    df = pd.read_csv(SCORING_SOURCES_FILE)

    count = 0

    for _, row in df.iterrows():
        match = matches.get(clean_string(row["MatchID"]))

        if not match:
            raise ValueError(
                f"Unknown MatchID in scoring sources: {row['MatchID']}"
            )

        record = ScoringSource(
            match_id=match.id,
            team=clean_string(row["Team"]),
            source=clean_string(row["Source"]),
            scores=to_int(row["Scores"]),
        )

        session.add(record)
        count += 1

    print(f"✓ Scoring sources: {count}")


# ---------------------------------------------------------------------
# Kickouts
# ---------------------------------------------------------------------

def migrate_kickouts(session, matches):
    df = pd.read_csv(KICKOUT_FILE)

    count = 0

    for _, row in df.iterrows():
        match = matches.get(clean_string(row["MatchID"]))

        if not match:
            raise ValueError(
                f"Unknown MatchID in kickout stats: {row['MatchID']}"
            )

        record = KickoutStat(
            match_id=match.id,
            team=clean_string(row["Team"]),
            period=clean_string(row["Period"]),
            kickout_type=clean_string(row["KickoutType"]),
            taken=to_int(row["Taken"]),
            won=to_int(row["Won"]),
            lost=to_int(row["Lost"]),
            clean_wins=to_int(row["CleanWins"]),
            break_wins=to_int(row["BreakWins"]),
            free_wins=to_int(row["FreeWins"]),
            sideline_wins=to_int(row["SidelineWins"]),
        )

        session.add(record)
        count += 1

    print(f"✓ Kickout stats: {count}")


# ---------------------------------------------------------------------
# Turnovers
# ---------------------------------------------------------------------

def migrate_turnovers(session, matches):
    df = pd.read_csv(TURNOVER_FILE)

    count = 0

    for _, row in df.iterrows():
        match = matches.get(clean_string(row["MatchID"]))

        if not match:
            raise ValueError(
                f"Unknown MatchID in turnover stats: {row['MatchID']}"
            )

        record = TurnoverStat(
            match_id=match.id,
            team=clean_string(row["Team"]),
            period=clean_string(row["Period"]),
            turnovers_won_forced=to_int(
                row["TurnoversWonForced"]
            ),
            turnovers_won_unforced=to_int(
                row["TurnoversWonUnforced"]
            ),
            turnovers_lost_forced=to_int(
                row["TurnoversLostForced"]
            ),
            turnovers_lost_unforced=to_int(
                row["TurnoversLostUnforced"]
            ),
        )

        session.add(record)
        count += 1

    print(f"✓ Turnover stats: {count}")


# ---------------------------------------------------------------------
# Player match data
# ---------------------------------------------------------------------

def migrate_player_match_stats(session, matches, players):
    df = pd.read_csv(PLAYER_DATA_FILE)

    count = 0

    for _, row in df.iterrows():
        match_code = clean_string(row["MatchID"])
        player_name = clean_string(row["PlayerName"])

        match = matches.get(match_code)
        player = players.get(player_name)

        if not match:
            raise ValueError(
                f"Unknown MatchID in player data: {match_code}"
            )

        if not player:
            raise ValueError(
                f"Unknown player in player data: {player_name}"
            )

        record = PlayerMatchStat(
            match_id=match.id,
            player_id=player.id,
            date=to_date(row["Date"]),
            opponent=clean_string(row["Opponent"]),
            home_away=clean_string(row["HomeAway"]),
            result=clean_string(row["Result"]),
            data_type=clean_string(row["DataType"]),
            squad_number=to_int(
                row["SquadNumber"],
                default=None,
            ),
            position=clean_string(row["Position"]),
            captain=to_bool(row["Captain"]),
            started=to_bool(row["Started"]),
            minutes_played=to_float(row["MinutesPlayed"]),
            possessions=to_int(row["Possessions"]),
            handpasses_total=to_int(row["HandpassesTotal"]),
            handpasses_1h=to_int(row["Handpasses1H"]),
            handpasses_2h=to_int(row["Handpasses2H"]),
            handpasses_completed=to_int(
                row["HandpassesCompleted"]
            ),
            footpasses_total=to_int(row["FootpassesTotal"]),
            footpasses_1h=to_int(row["Footpasses1H"]),
            footpasses_2h=to_int(row["Footpasses2H"]),
            footpasses_completed=to_int(
                row["FootpassesCompleted"]
            ),
            incomplete_passes=to_int(row["IncompletePasses"]),
            kickouts_won=to_int(row["KickoutsWon"]),
            breaking_balls_won=to_int(row["BreakingBallsWon"]),
            turnovers_won=to_int(row["TurnoversWon"]),
            turnovers_lost=to_int(row["TurnoversLost"]),
            frees_won=to_int(row["FreesWon"]),
            frees_conceded=to_int(row["FreesConceded"]),
            assists=to_int(row["Assists"]),
            points=to_int(row["Points"]),
            points_play=to_int(row["PointsPlay"]),
            points_free=to_int(row["PointsFree"]),
            points_45=to_int(row["Points45"]),
            goals=to_int(row["Goals"]),
            two_pointers=to_int(row["TwoPointers"]),
            shot_attempts=to_int(row["ShotAttempts"]),
            scores=to_int(row["Scores"]),
            shot_conversion_pct=to_float(
                row["ShotConversionPct"]
            ),
            yellow_cards=to_int(row["YellowCards"]),
            black_cards=to_int(row["BlackCards"]),
            red_cards=to_int(row["RedCards"]),
            notes=clean_string(row["Notes"]),
        )

        session.add(record)
        count += 1

    print(f"✓ Player match stats: {count}")


# ---------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------

def migrate_users(session, players):
    df = pd.read_csv(USERS_FILE)

    count = 0

    for _, row in df.iterrows():
        username = clean_string(row["Username"])
        display_name = clean_string(row["DisplayName"]) or username
        role = clean_string(row["Role"])
        player_name = clean_string(row["PlayerName"])

        player_id = None

        if player_name:
            player = players.get(player_name)

            if not player:
                raise ValueError(
                    f"User '{username}' references unknown "
                    f"player '{player_name}'"
                )

            player_id = player.id

        record = User(
            username=username,
            display_name=display_name,
            password_hash=hash_password(SHARED_PASSWORD),
            role=role,
            player_id=player_id,
            is_active=to_bool(row["Active"], default=True),
        )

        session.add(record)
        count += 1

    print(f"✓ Users: {count}")


# ---------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------

def validate_counts(session):
    """
    Compare imported database counts against source CSV counts.
    """

    expected = {
        Match: len(pd.read_csv(MATCHES_FILE)),
        TeamMatchStat: len(pd.read_csv(TEAM_STATS_FILE)),
        ShootingDetail: len(pd.read_csv(SHOOTING_FILE)),
        ScoringSource: len(pd.read_csv(SCORING_SOURCES_FILE)),
        KickoutStat: len(pd.read_csv(KICKOUT_FILE)),
        TurnoverStat: len(pd.read_csv(TURNOVER_FILE)),
        PlayerMatchStat: len(pd.read_csv(PLAYER_DATA_FILE)),
        User: len(pd.read_csv(USERS_FILE)),
    }

    print("\nValidating row counts...")

    for model, expected_count in expected.items():
        session.flush()

        actual_count = session.scalar(
            select(func.count()).select_from(model)
        )

        if actual_count != expected_count:
            raise ValueError(
                f"{model.__tablename__}: "
                f"expected {expected_count}, "
                f"found {actual_count}"
            )

        print(
            f"✓ {model.__tablename__}: "
            f"{actual_count}/{expected_count}"
        )


# ---------------------------------------------------------------------
# Main migration
# ---------------------------------------------------------------------

def run_migration():
    print()
    print("=" * 60)
    print("GAA Analytics CSV -> PostgreSQL Migration")
    print("=" * 60)

    check_required_files()

    with SessionLocal() as session:
        try:
            # Protect against accidental second import.
            ensure_database_empty(session)

            print("\nImporting data...\n")

            matches = migrate_matches(session)
            players = migrate_players(session)

            migrate_team_stats(session, matches)
            migrate_shooting(session, matches)
            migrate_scoring_sources(session, matches)
            migrate_kickouts(session, matches)
            migrate_turnovers(session, matches)

            migrate_player_match_stats(
                session,
                matches,
                players,
            )

            migrate_users(
                session,
                players,
            )

            validate_counts(session)

            # Nothing becomes permanent until here.
            session.commit()

            print()
            print("=" * 60)
            print("MIGRATION SUCCESSFUL")
            print("=" * 60)
            print()
            print("All CSV data has been committed to PostgreSQL.")

        except Exception as exc:
            session.rollback()

            print()
            print("=" * 60)
            print("MIGRATION FAILED")
            print("=" * 60)
            print()
            print(f"Error: {exc}")
            print()
            print(
                "The transaction was rolled back. "
                "No partial migration was saved."
            )

            raise


if __name__ == "__main__":
    run_migration()
