"""Explicit CSV import/export helpers.

Runtime dashboard reads and writes use PostgreSQL. These helpers exist only
for migration validation and deliberate CSV interchange.
"""

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_DATA_DIR = PROJECT_ROOT / "data"
CSV_DATASETS = {
    "matches": "club2026matches.csv",
    "team_stats": "club2026team_match_stats.csv",
    "shooting": "club2026shooting_detail.csv",
    "scoring_sources": "club2026scoring_sources.csv",
    "kickouts": "club2026kickout_stats.csv",
    "turnovers": "club2026turnover_stats.csv",
    "player_data": "club2026player_match_data.csv",
    "squad_numbers": "club2026squad_numbers.csv",
    "users": "app_users.csv",
}


def load_csv_dataset(dataset_key: str) -> pd.DataFrame:
    try:
        filename = CSV_DATASETS[dataset_key]
    except KeyError as error:
        raise ValueError(f"Unknown CSV dataset: {dataset_key}") from error

    file_path = CSV_DATA_DIR / filename
    if not file_path.exists():
        raise FileNotFoundError(f"CSV import file not found: {file_path}")

    data = pd.read_csv(file_path)
    if "Date" in data.columns:
        data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    return data


def load_matches_csv() -> pd.DataFrame:
    return load_csv_dataset("matches")


def load_team_stats_csv() -> pd.DataFrame:
    return load_csv_dataset("team_stats")


def load_shooting_detail_csv() -> pd.DataFrame:
    return load_csv_dataset("shooting")


def load_scoring_sources_csv() -> pd.DataFrame:
    return load_csv_dataset("scoring_sources")


def load_kickout_stats_csv() -> pd.DataFrame:
    return load_csv_dataset("kickouts")


def load_turnover_stats_csv() -> pd.DataFrame:
    return load_csv_dataset("turnovers")


def load_player_match_data_csv() -> pd.DataFrame:
    return load_csv_dataset("player_data")
