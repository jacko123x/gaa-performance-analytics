"""Cached data assembly for every analytics view."""

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from load_data import (
    load_kickout_stats,
    load_matches,
    load_match_summary,
    load_player_match_data,
    load_scoring_sources,
    load_shooting_detail,
    load_turnover_stats,
)
from metrics import (
    add_kickout_metrics,
    add_player_metrics,
    add_shooting_metrics,
    add_team_metrics,
    add_turnover_metrics,
)


@dataclass
class DashboardData:
    matches: pd.DataFrame
    team: pd.DataFrame
    shooting: pd.DataFrame
    scoring_sources: pd.DataFrame
    kickouts: pd.DataFrame
    turnovers: pd.DataFrame
    players: pd.DataFrame


@st.cache_data(ttl=30, max_entries=2)
def load_dashboard_data(team_name: str) -> DashboardData:
    """Load published data, calculate metrics, and scope team datasets."""

    matches = load_matches()
    team = add_team_metrics(load_match_summary())
    shooting = add_shooting_metrics(load_shooting_detail())
    scoring_sources = load_scoring_sources()
    kickouts = add_kickout_metrics(load_kickout_stats())
    turnovers = add_turnover_metrics(load_turnover_stats())
    players = add_player_metrics(load_player_match_data())

    return DashboardData(
        matches=matches,
        team=team[team["Team"] == team_name].copy(),
        shooting=shooting[shooting["Team"] == team_name].copy(),
        scoring_sources=scoring_sources[
            scoring_sources["Team"] == team_name
        ].copy(),
        kickouts=kickouts[kickouts["Team"] == team_name].copy(),
        turnovers=turnovers[turnovers["Team"] == team_name].copy(),
        players=players,
    )
