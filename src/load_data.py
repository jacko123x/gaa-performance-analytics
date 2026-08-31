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


def load_matches(include_unpublished=False) -> pd.DataFrame:
    return load_matches_db(include_unpublished=include_unpublished)


def load_team_stats(include_unpublished=False) -> pd.DataFrame:
    return load_team_stats_db(include_unpublished=include_unpublished)


def load_shooting_detail(include_unpublished=False) -> pd.DataFrame:
    return load_shooting_detail_db(include_unpublished=include_unpublished)


def load_scoring_sources(include_unpublished=False) -> pd.DataFrame:
    return load_scoring_sources_db(include_unpublished=include_unpublished)


def load_kickout_stats(include_unpublished=False) -> pd.DataFrame:
    return load_kickout_stats_db(include_unpublished=include_unpublished)


def load_turnover_stats(include_unpublished=False) -> pd.DataFrame:
    return load_turnover_stats_db(include_unpublished=include_unpublished)


def load_player_match_data(include_unpublished=False) -> pd.DataFrame:
    return load_player_match_data_db(include_unpublished=include_unpublished)


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
