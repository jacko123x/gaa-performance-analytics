from pathlib import Path

import pandas as pd


# ==========================================================
# Project paths
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


# ==========================================================
# Dataset filenames
# ==========================================================

DATASETS = {
    "matches": "club2026matches.csv",
    "team_stats": "club2026team_match_stats.csv",
    "shooting": "club2026shooting_detail.csv",
    "scoring_sources": "club2026scoring_sources.csv",
    "kickouts": "club2026kickout_stats.csv",
    "turnovers": "club2026turnover_stats.csv",
    "player_data": "club2026player_match_data.csv",
    "squad_numbers": "club2026squad_numbers.csv",
}


# ==========================================================
# Generic loader
# ==========================================================

def load_csv(filename: str) -> pd.DataFrame:
    file_path = DATA_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(
            f"Data file not found: {file_path}"
        )

    return pd.read_csv(file_path)


# ==========================================================
# Core datasets
# ==========================================================

def load_matches() -> pd.DataFrame:
    df = load_csv(DATASETS["matches"])

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(
            df["Date"],
            errors="coerce",
        )

    return df


def load_team_stats() -> pd.DataFrame:
    return load_csv(DATASETS["team_stats"])


def load_shooting_detail() -> pd.DataFrame:
    return load_csv(DATASETS["shooting"])


def load_scoring_sources() -> pd.DataFrame:
    return load_csv(DATASETS["scoring_sources"])


def load_kickout_stats() -> pd.DataFrame:
    return load_csv(DATASETS["kickouts"])


def load_turnover_stats() -> pd.DataFrame:
    return load_csv(DATASETS["turnovers"])


# ==========================================================
# Player data
# ==========================================================

def load_player_match_data() -> pd.DataFrame:
    player_data = load_csv(
        DATASETS["player_data"]
    )

    # ------------------------------------------------------
    # Date conversion
    # ------------------------------------------------------

    if "Date" in player_data.columns:
        player_data["Date"] = pd.to_datetime(
            player_data["Date"],
            errors="coerce",
        )

    # ------------------------------------------------------
    # Numeric columns
    # ------------------------------------------------------

    numeric_columns = [
        "SquadNumber",
        "MinutesPlayed",
        "Possessions",
        "HandpassesTotal",
        "Handpasses1H",
        "Handpasses2H",
        "HandpassesCompleted",
        "FootpassesTotal",
        "Footpasses1H",
        "Footpasses2H",
        "FootpassesCompleted",
        "IncompletePasses",
        "KickoutsWon",
        "BreakingBallsWon",
        "TurnoversWon",
        "TurnoversLost",
        "FreesWon",
        "FreesConceded",
        "Assists",
        "Points",
        "PointsPlay",
        "PointsFree",
        "Points45",
        "Goals",
        "TwoPointers",
        "ShotAttempts",
        "Scores",
        "ShotConversionPct",
        "YellowCards",
        "BlackCards",
        "RedCards",
    ]

    for column in numeric_columns:
        if column in player_data.columns:
            player_data[column] = pd.to_numeric(
                player_data[column],
                errors="coerce",
            ).fillna(0)

    # ------------------------------------------------------
    # Boolean columns
    # ------------------------------------------------------

    boolean_columns = [
        "Captain",
        "Started",
    ]

    for column in boolean_columns:
        if column in player_data.columns:

            player_data[column] = (
                player_data[column]
                .astype(str)
                .str.strip()
                .str.lower()
                .map(
                    {
                        "yes": True,
                        "no": False,
                        "true": True,
                        "false": False,
                        "1": True,
                        "0": False,
                    }
                )
                .fillna(False)
            )

    # ------------------------------------------------------
    # Text cleanup
    # ------------------------------------------------------

    text_columns = [
        "MatchID",
        "Opponent",
        "HomeAway",
        "Result",
        "DataType",
        "PlayerName",
        "Position",
        "Notes",
    ]

    for column in text_columns:
        if column in player_data.columns:
            player_data[column] = (
                player_data[column]
                .fillna("")
                .astype(str)
                .str.strip()
            )

    return player_data


def load_squad_numbers() -> pd.DataFrame:
    return load_csv(
        DATASETS["squad_numbers"]
    )


# ==========================================================
# Joined match + team dataset
# ==========================================================

def load_match_summary() -> pd.DataFrame:
    matches = load_matches()
    team_stats = load_team_stats()

    return team_stats.merge(
        matches,
        on="MatchID",
        how="left",
        suffixes=("", "_match"),
    )


# ==========================================================
# Test runner
# ==========================================================

if __name__ == "__main__":

    matches = load_matches()
    team_stats = load_team_stats()
    shooting = load_shooting_detail()
    scoring_sources = load_scoring_sources()
    kickouts = load_kickout_stats()
    turnovers = load_turnover_stats()
    player_data = load_player_match_data()
    match_summary = load_match_summary()

    print(
        "\n========== CLUB 2026 DATA ==========\n"
    )

    print(f"Matches:          {len(matches)}")
    print(f"Team stats:       {len(team_stats)}")
    print(f"Shooting rows:    {len(shooting)}")
    print(
        f"Scoring sources:  "
        f"{len(scoring_sources)}"
    )
    print(f"Kickout rows:     {len(kickouts)}")
    print(f"Turnover rows:    {len(turnovers)}")
    print(
        f"Player rows:      "
        f"{len(player_data)}"
    )

    print(
        f"Unique players:   "
        f"{player_data['PlayerName'].nunique()}"
    )

    print(
        f"Player matches:   "
        f"{player_data['MatchID'].nunique()}"
    )

    print(
        "\n========== MATCHES ==========\n"
    )
    print(matches)

    print(
        "\n========== TEAM STATS ==========\n"
    )
    print(team_stats)

    print(
        "\n========== SHOOTING ==========\n"
    )
    print(shooting)

    print(
        "\n========== SCORING SOURCES ==========\n"
    )
    print(scoring_sources)

    print(
        "\n========== KICKOUTS ==========\n"
    )
    print(kickouts)

    print(
        "\n========== TURNOVERS ==========\n"
    )
    print(turnovers)

    print(
        "\n========== PLAYER DATA ==========\n"
    )

    player_preview_columns = [
        "MatchID",
        "SquadNumber",
        "PlayerName",
        "Position",
        "Started",
        "MinutesPlayed",
        "Possessions",
        "HandpassesTotal",
        "HandpassesCompleted",
        "FootpassesTotal",
        "FootpassesCompleted",
        "TurnoversWon",
        "TurnoversLost",
        "Assists",
        "Points",
        "Goals",
        "TwoPointers",
        "ShotAttempts",
        "Scores",
        "ShotConversionPct",
    ]

    available_preview_columns = [
        column
        for column in player_preview_columns
        if column in player_data.columns
    ]

    print(
        player_data[
            available_preview_columns
        ].head(10)
    )