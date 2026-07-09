from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


def load_matches() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "Stacks 2026 County League Team Stats - matches.csv")


def load_team_stats() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "Stacks 2026 County League Team Stats - team_match_stats.csv")


def load_season_data() -> pd.DataFrame:
    matches = load_matches()
    team_stats = load_team_stats()

    season = team_stats.merge(
        matches,
        on="MatchID",
        how="left",
        suffixes=("", "_match")
    )

    return season


if __name__ == "__main__":

    from metrics import add_metrics

    from validation import validate_team_stats

    matches = load_matches()

    team_stats = load_team_stats()

    season = load_season_data()

    season = add_metrics(season)

    errors = validate_team_stats(team_stats)

    print(f"Matches loaded: {len(matches)}")

    print(f"Team records loaded: {len(team_stats)}")

    if errors:

        print("Validation errors:")

        for error in errors:

            print(f"- {error}")

    else:

        print("Validation passed.")

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