import pandas as pd


def safe_percentage(numerator, denominator):
    return (numerator / denominator) * 100


def add_metrics(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["ShotConversion"] = safe_percentage(df["TotalScores"], df["TotalShots"])
    df["PlayConversion"] = safe_percentage(df["ScoresPlay"], df["ShotsPlay"])
    df["PlacedConversion"] = safe_percentage(df["ScoresPlaced"], df["ShotsPlaced"])

    df["KickoutWinRate"] = safe_percentage(
        df["KickoutsWon"],
        df["KickoutsWon"] + df["KickoutsLost"]
    )

    df["TurnoverDifferential"] = df["ForcedTurnovers"] - df["UnforcedTurnovers"]

    df["ScoresPerAttack"] = df["TotalScores"] / df["Attacks"]

    df["AttackShotRate"] = safe_percentage(
        df["TotalShots"],
        df["Attacks"]
    )

    return df