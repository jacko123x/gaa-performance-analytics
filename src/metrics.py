import numpy as np
import pandas as pd


def safe_percentage(
    numerator: pd.Series,
    denominator: pd.Series,
) -> pd.Series:
    """
    Calculate a percentage while safely handling zero denominators.

    Returns NaN where the denominator is zero.
    """

    return pd.Series(
        np.where(
            denominator > 0,
            (numerator / denominator) * 100,
            np.nan,
        ),
        index=numerator.index,
    )


def add_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate derived team-level performance metrics.
    """

    df = df.copy()

    df["ShotConversion"] = safe_percentage(
        df["TotalScores"],
        df["TotalShots"],
    )

    df["PlayConversion"] = safe_percentage(
        df["ScoresPlay"],
        df["ShotsPlay"],
    )

    df["PlacedConversion"] = safe_percentage(
        df["ScoresPlaced"],
        df["ShotsPlaced"],
    )

    df["KickoutWinRate"] = safe_percentage(
        df["KickoutsWon"],
        df["KickoutsWon"] + df["KickoutsLost"],
    )

    df["TurnoverDifferential"] = (
        df["ForcedTurnovers"]
        - df["UnforcedTurnovers"]
    )

    df["ScoresPerAttack"] = np.where(
        df["Attacks"] > 0,
        df["TotalScores"] / df["Attacks"],
        np.nan,
    )

    df["AttackShotRate"] = safe_percentage(
        df["TotalShots"],
        df["Attacks"],
    )

    return df


def add_player_metrics(
    player_data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate derived player-level performance metrics.

    The original player dataframe is copied so it is not
    modified directly.
    """

    df = player_data.copy()

    # -----------------------------
    # Passing metrics
    # -----------------------------

    df["TotalPasses"] = (
        df["HandpassesTotal"]
        + df["FootpassesTotal"]
    )

    df["CompletedPasses"] = (
        df["TotalPasses"]
        - df["IncompletePasses"]
    ).clip(lower=0)

    df["PassAccuracyPct"] = safe_percentage(
        df["CompletedPasses"],
        df["TotalPasses"],
    )

    df["HandpassSharePct"] = safe_percentage(
        df["HandpassesTotal"],
        df["TotalPasses"],
    )

    df["FootpassSharePct"] = safe_percentage(
        df["FootpassesTotal"],
        df["TotalPasses"],
    )

    # -----------------------------
    # Scoring metrics
    # -----------------------------

    df["TotalScores"] = (
        df["Points"]
        + df["Goals"]
        + df["TwoPointers"]
    )

    df["TotalScoreValue"] = (
        df["Points"]
        + (df["Goals"] * 3)
        + (df["TwoPointers"] * 2)
    )

    df["CalculatedShotConversionPct"] = safe_percentage(
        df["TotalScores"],
        df["ShotAttempts"],
    )

    df["DirectScoreContributions"] = (
        df["TotalScores"]
        + df["Assists"]
    )

    # -----------------------------
    # Discipline and possession
    # -----------------------------

    df["FreeDifferential"] = (
        df["FreesWon"]
        - df["FreesConceded"]
    )

    # -----------------------------
    # Per-minute and per-60 metrics
    # -----------------------------

    df["PassesPerMinute"] = np.where(
        df["MinutesPlayed"] > 0,
        df["TotalPasses"] / df["MinutesPlayed"],
        np.nan,
    )

    df["PassesPer60"] = np.where(
        df["MinutesPlayed"] > 0,
        (
            df["TotalPasses"]
            / df["MinutesPlayed"]
        ) * 60,
        np.nan,
    )

    df["ScoreValuePer60"] = np.where(
        df["MinutesPlayed"] > 0,
        (
            df["TotalScoreValue"]
            / df["MinutesPlayed"]
        ) * 60,
        np.nan,
    )

    df["AssistsPer60"] = np.where(
        df["MinutesPlayed"] > 0,
        (
            df["Assists"]
            / df["MinutesPlayed"]
        ) * 60,
        np.nan,
    )

    df["FreesWonPer60"] = np.where(
        df["MinutesPlayed"] > 0,
        (
            df["FreesWon"]
            / df["MinutesPlayed"]
        ) * 60,
        np.nan,
    )

    return df