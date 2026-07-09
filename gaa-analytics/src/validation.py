import pandas as pd

def validate_team_stats(df: pd.DataFrame) -> list[str]:

    errors = []

    if df.duplicated(subset=["MatchID", "Team"]).any():

        errors.append("Duplicate MatchID + Team rows found.")

    if (df["TotalScores"] > df["TotalShots"]).any():

        errors.append("Some rows have TotalScores greater than TotalShots.")

    if (df["ScoresPlay"] > df["ShotsPlay"]).any():

        errors.append("Some rows have ScoresPlay greater than ShotsPlay.")

    if (df["ScoresPlaced"] > df["ShotsPlaced"]).any():

        errors.append("Some rows have ScoresPlaced greater than ShotsPlaced.")

    numeric_cols = [

        "Goals", "Points", "TwoPointers", "Wides", "Shorts",

        "KickoutsWon", "KickoutsLost", "ForcedTurnovers",

        "UnforcedTurnovers", "FreesConceded", "BreakingBallWon",

        "Attacks", "TotalShots", "TotalScores", "ShotsPlay",

        "ScoresPlay", "ShotsPlaced", "ScoresPlaced"

    ]

    for col in numeric_cols:

        if col in df.columns and (df[col].dropna() < 0).any():

            errors.append(f"Negative values found in {col}.")

    return errors