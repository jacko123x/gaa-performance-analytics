import pandas as pd

from src.database.repository import (
    load_matches_db,
    load_team_stats_db,
    load_shooting_detail_db,
    load_scoring_sources_db,
    load_kickout_stats_db,
    load_turnover_stats_db,
    load_player_match_data_db,
    load_squad_numbers_db,
)


def load_matches() -> pd.DataFrame:
    return load_matches_db()


def load_team_stats() -> pd.DataFrame:
    return load_team_stats_db()


def load_shooting_detail() -> pd.DataFrame:
    return load_shooting_detail_db()


def load_scoring_sources() -> pd.DataFrame:
    return load_scoring_sources_db()


def load_kickout_stats() -> pd.DataFrame:
    return load_kickout_stats_db()


def load_turnover_stats() -> pd.DataFrame:
    return load_turnover_stats_db()


def load_player_match_data() -> pd.DataFrame:
    return load_player_match_data_db()


def load_squad_numbers() -> pd.DataFrame:
    return load_squad_numbers_db()


def load_match_summary() -> pd.DataFrame:
    team_stats = load_team_stats()
    matches = load_matches()

    return team_stats.merge(
        matches,
        on="MatchID",
        how="left",
    )
