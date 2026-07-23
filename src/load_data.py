from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


def load_matches() -> pd.DataFrame:
    return pd.read_csv(
        DATA_DIR / "Stacks 2026 County League Team Stats - matches.csv"
    )


def load_team_stats() -> pd.DataFrame:
    return pd.read_csv(
        DATA_DIR / "Stacks 2026 County League Team Stats - team_match_stats.csv"
    )


def load_player_match_data() -> pd.DataFrame:
    file_path = DATA_DIR / "gaa_player_match_data.csv"

    if not file_path.exists():
        raise FileNotFoundError(
            f"Player match data file was not found: {file_path}"
        )

    player_data = pd.read_csv(file_path)

    if "Date" in player_data.columns:
        player_data["Date"] = pd.to_datetime(
            player_data["Date"],
            errors="coerce",
        )

    numeric_columns = [
        "SquadNumber",
        "MinutesPlayed",
        "HandpassesTotal",
        "Handpasses1H",
        "Handpasses2H",
        "HandpassTarget",
        "FootpassesTotal",
        "Footpasses1H",
        "Footpasses2H",
        "FootpassTarget",
        "IncompletePasses",
        "FreesWon",
        "FreesConceded",
        "Assists",
        "Points",
        "Goals",
        "TwoPointers",
        "ShotAttempts",
        "Scores",
        "ShotConversionPct",
    ]

    for column in numeric_columns:
        if column in player_data.columns:
            player_data[column] = pd.to_numeric(
                player_data[column],
                errors="coerce",
            ).fillna(0)

    if "Started" in player_data.columns:
        player_data["Started"] = (
            player_data["Started"]
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
        )

    return player_data


def load_season_data() -> pd.DataFrame:
    matches = load_matches()
    team_stats = load_team_stats()

    season = team_stats.merge(
        matches,
        on="MatchID",
        how="left",
        suffixes=("", "_match"),
    )

    return season


if __name__ == "__main__":
    from metrics import add_metrics
    from validation import validate_team_stats

    matches = load_matches()
    team_stats = load_team_stats()
    player_data = load_player_match_data()

    season = load_season_data()
    season = add_metrics(season)

    errors = validate_team_stats(team_stats)

    print(f"Matches loaded: {len(matches)}")
    print(f"Team records loaded: {len(team_stats)}")
    print(f"Player match records loaded: {len(player_data)}")
    print(
        f"Unique players loaded: "
        f"{player_data['PlayerName'].nunique()}"
    )
    print(
        f"Player matches loaded: "
        f"{player_data['MatchID'].nunique()}"
    )

    if errors:
        print("Validation errors:")

        for error in errors:
            print(f"- {error}")
    else:
        print("Validation passed.")

    print("\nTeam season data:")

    print(
        season[
            [
                "MatchID",
                "Team",
                "Opponent",
                "ShotConversion",
                "KickoutWinRate",
                "TurnoverDifferential",
                "ScoresPerAttack",
            ]
        ]
    )

    print("\nPlayer match data sample:")

    print(
        player_data[
            [
                "MatchID",
                "PlayerName",
                "Position",
                "Started",
                "MinutesPlayed",
                "HandpassesTotal",
                "FootpassesTotal",
                "Scores",
                "DataType",
            ]
        ].head(10)
    )
