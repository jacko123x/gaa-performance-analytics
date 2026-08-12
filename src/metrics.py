import numpy as np
import pandas as pd


def safe_percentage(numerator, denominator):
    """
    Calculate percentage safely.
    Returns NaN when denominator is zero.
    """

    return np.where(
        denominator > 0,
        (numerator / denominator) * 100,
        np.nan,
    )


# ==========================================================
# Team metrics
# ==========================================================

def add_team_metrics(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["ShotConversionPct"] = safe_percentage(
        df["TotalScores"],
        df["TotalShots"],
    )

    df["PlayConversionPct"] = safe_percentage(
        df["ScoresPlay"],
        df["ShotsPlay"],
    )

    df["PlacedConversionPct"] = safe_percentage(
        df["ScoresPlaced"],
        df["ShotsPlaced"],
    )

    df["AttackToShotPct"] = safe_percentage(
        df["TotalShots"],
        df["Attacks"],
    )

    df["AttackToScorePct"] = safe_percentage(
        df["TotalScores"],
        df["Attacks"],
    )

    df["EmptyAttacks"] = (
        df["Attacks"]
        - df["TotalShots"]
    )

    df["KickoutRetentionPct"] = safe_percentage(
        df["KickoutsWon"],
        df["KickoutsWon"] + df["KickoutsLost"],
    )

    # These columns represent turnovers won.
    # True turnover differential is calculated from turnover_stats.csv.
    df["TurnoversWon"] = (
        df["ForcedTurnovers"]
        + df["UnforcedTurnovers"]
    )

    return df


# ==========================================================
# Shooting metrics
# ==========================================================

def add_shooting_metrics(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["ShotConversionPct"] = safe_percentage(
        df["ShotsScored"],
        df["ShotsTaken"],
    )

    df["Misses"] = (
        df["Wides"]
        + df["Shorts"]
        + df["Blocked"]
        + df["Post"]
        + df["Saved"]
    )

    return df


# ==========================================================
# Kickout metrics
# ==========================================================

def add_kickout_metrics(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["WinPct"] = safe_percentage(
        df["Won"],
        df["Taken"],
    )

    df["CleanWinPct"] = safe_percentage(
        df["CleanWins"],
        df["Won"],
    )

    df["BreakWinPct"] = safe_percentage(
        df["BreakWins"],
        df["Won"],
    )

    return df


# ==========================================================
# Turnover metrics
# ==========================================================

def add_turnover_metrics(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["TurnoversWon"] = (
        df["TurnoversWonForced"]
        + df["TurnoversWonUnforced"]
    )

    df["TurnoversLost"] = (
        df["TurnoversLostForced"]
        + df["TurnoversLostUnforced"]
    )

    df["TurnoverDifferential"] = (
        df["TurnoversWon"]
        - df["TurnoversLost"]
    )

    df["ForcedTurnoverPct"] = safe_percentage(
        df["TurnoversWonForced"],
        df["TurnoversWon"],
    )

    df["UnforcedTurnoverPct"] = safe_percentage(
        df["TurnoversWonUnforced"],
        df["TurnoversWon"],
    )

    return df


# ==========================================================
# Player metrics
# ==========================================================

def add_player_metrics(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # ------------------------------------------------------
    # Passing
    # ------------------------------------------------------

    df["TotalPasses"] = (
        df["HandpassesTotal"]
        + df["FootpassesTotal"]
    )

    df["CompletedPasses"] = (
        df["HandpassesCompleted"]
        + df["FootpassesCompleted"]
    )

    df["PassAccuracyPct"] = safe_percentage(
        df["CompletedPasses"],
        df["TotalPasses"],
    )

    df["HandpassAccuracyPct"] = safe_percentage(
        df["HandpassesCompleted"],
        df["HandpassesTotal"],
    )

    df["FootpassAccuracyPct"] = safe_percentage(
        df["FootpassesCompleted"],
        df["FootpassesTotal"],
    )

    df["HandpassSharePct"] = safe_percentage(
        df["HandpassesTotal"],
        df["TotalPasses"],
    )

    df["FootpassSharePct"] = safe_percentage(
        df["FootpassesTotal"],
        df["TotalPasses"],
    )

    # ------------------------------------------------------
    # Possession / defensive contribution
    # ------------------------------------------------------

    df["TurnoverDifferential"] = (
        df["TurnoversWon"]
        - df["TurnoversLost"]
    )

    df["FreeDifferential"] = (
        df["FreesWon"]
        - df["FreesConceded"]
    )

    # ------------------------------------------------------
    # Scoring
    # ------------------------------------------------------

    df["TotalScoreValue"] = (
        df["Points"]
        + (df["Goals"] * 3)
        + (df["TwoPointers"] * 2)
    )

    df["ScoreContributions"] = (
        df["Scores"]
        + df["Assists"]
    )

    df["CalculatedShotConversionPct"] = safe_percentage(
        df["Scores"],
        df["ShotAttempts"],
    )

    # ------------------------------------------------------
    # Per 60 metrics
    # ------------------------------------------------------

    df["PossessionsPer60"] = np.where(
        df["MinutesPlayed"] > 0,
        (
            df["Possessions"]
            / df["MinutesPlayed"]
        ) * 60,
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

    df["TurnoversWonPer60"] = np.where(
        df["MinutesPlayed"] > 0,
        (
            df["TurnoversWon"]
            / df["MinutesPlayed"]
        ) * 60,
        np.nan,
    )

    df["TurnoversLostPer60"] = np.where(
        df["MinutesPlayed"] > 0,
        (
            df["TurnoversLost"]
            / df["MinutesPlayed"]
        ) * 60,
        np.nan,
    )

    df["BreakingBallsWonPer60"] = np.where(
        df["MinutesPlayed"] > 0,
        (
            df["BreakingBallsWon"]
            / df["MinutesPlayed"]
        ) * 60,
        np.nan,
    )

    df["KickoutsWonPer60"] = np.where(
        df["MinutesPlayed"] > 0,
        (
            df["KickoutsWon"]
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

    df["ScoreValuePer60"] = np.where(
        df["MinutesPlayed"] > 0,
        (
            df["TotalScoreValue"]
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