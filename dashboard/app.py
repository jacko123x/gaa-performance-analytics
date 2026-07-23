# -----------------------------
# Imports
# -----------------------------
# sys and pathlib help us import files from the src folder.
# Streamlit builds the web dashboard.
# pandas helps us format missing values.
# Plotly creates interactive charts.

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# -----------------------------
# Project setup
# -----------------------------
# This finds the root folder of the project and allows this dashboard file
# to import functions from the src folder.

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT / "src"))


# -----------------------------
# Import project functions
# -----------------------------
# load_season_data reads and joins the team-level CSV files.
# load_player_match_data reads the player-level CSV file.
# add_metrics calculates the team KPIs.

from load_data import load_player_match_data, load_season_data
from metrics import add_metrics, add_player_metrics


# -----------------------------
# App constants
# -----------------------------
# Austin Stacks amber/orange colour used across the dashboard.

AMBER = "#F59E0B"


# -----------------------------
# Streamlit page setup
# -----------------------------
# Sets browser tab title and uses wide layout for charts and tables.

st.set_page_config(
    page_title="Austin Stacks Analytics",
    layout="wide",
)


# -----------------------------
# Dashboard title
# -----------------------------

st.title("Austin Stacks Analytics Platform")
st.subheader("County League 2026")


# -----------------------------
# Load and prepare data
# -----------------------------
# Load match/team data, calculate KPIs, then filter to Austin Stacks only.
# Player match data is loaded separately for future player analysis.

try:
    season = add_metrics(load_season_data())

    stacks = season[
        season["Team"] == "Austin Stacks"
    ].copy()

    player_data = add_player_metrics(
        load_player_match_data()
    )

except FileNotFoundError as error:
    st.error(str(error))
    st.stop()

except Exception as error:
    st.error(f"An error occurred while loading the data: {error}")
    st.stop()


# -----------------------------
# Season overview KPI cards
# -----------------------------
# These are headline season metrics for Austin Stacks.

st.header("Season Overview")

avg_turnover = stacks["TurnoverDifferential"].mean()

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "Matches",
    stacks["MatchID"].nunique(),
)

col2.metric(
    "Avg Shot %",
    f"{stacks['ShotConversion'].mean():.1f}%",
)

col3.metric(
    "Avg Kickout Win %",
    f"{stacks['KickoutWinRate'].mean():.1f}%",
)

col4.metric(
    "Avg Turnover Diff",
    f"{avg_turnover:+.1f}",
)

col5.metric(
    "Avg Attack → Shot %",
    f"{stacks['AttackShotRate'].mean():.1f}%",
)


# -----------------------------
# Match-by-match trend charts
# -----------------------------
# These charts show how key KPIs changed across opponents.

st.header("Match-by-Match Trends")


# Shot conversion chart
fig1 = px.line(
    stacks,
    x="Opponent",
    y="ShotConversion",
    markers=True,
    title="Shot Conversion % by Opponent",
    color_discrete_sequence=[AMBER],
)

fig1.update_traces(
    line=dict(width=4),
    marker=dict(size=10),
)

fig1.update_layout(
    xaxis_title="Opponent",
    yaxis_title="Shot Conversion %",
)

st.plotly_chart(
    fig1,
    width="stretch",
)


# Kickout win rate chart
fig2 = px.line(
    stacks,
    x="Opponent",
    y="KickoutWinRate",
    markers=True,
    title="Kickout Win Rate % by Opponent",
    color_discrete_sequence=[AMBER],
)

fig2.update_traces(
    line=dict(width=4),
    marker=dict(size=10),
)

fig2.update_layout(
    xaxis_title="Opponent",
    yaxis_title="Kickout Win Rate %",
)

st.plotly_chart(
    fig2,
    width="stretch",
)


# Turnover differential chart
fig3 = px.bar(
    stacks,
    x="Opponent",
    y="TurnoverDifferential",
    title="Turnover Differential by Opponent",
    color_discrete_sequence=[AMBER],
)

fig3.update_layout(
    xaxis_title="Opponent",
    yaxis_title="Turnover Differential",
)

st.plotly_chart(
    fig3,
    width="stretch",
)


# Attack-to-shot rate chart
# This shows what percentage of attacks resulted in a shot.

fig4 = px.line(
    stacks,
    x="Opponent",
    y="AttackShotRate",
    markers=True,
    title="Attack → Shot Rate % by Opponent",
    color_discrete_sequence=[AMBER],
)

fig4.update_traces(
    line=dict(width=4),
    marker=dict(size=10),
)

fig4.update_layout(
    xaxis_title="Opponent",
    yaxis_title="Attack → Shot Rate %",
)

st.plotly_chart(
    fig4,
    width="stretch",
)


# -----------------------------
# Match data table
# -----------------------------
# This displays the main Austin Stacks match stats.
# Percentages and +/- values are formatted for readability.

st.header("Austin Stacks Match Data")

display_cols = [
    "MatchID",
    "Opponent",
    "Goals",
    "Points",
    "TwoPointers",
    "TotalShots",
    "TotalScores",
    "ShotConversion",
    "KickoutWinRate",
    "TurnoverDifferential",
    "ScoresPerAttack",
    "AttackShotRate",
]

display_df = stacks[display_cols].copy()


# Format shot conversion as percentage
display_df["ShotConversion"] = display_df[
    "ShotConversion"
].map(
    lambda value: (
        ""
        if pd.isna(value)
        else f"{value:.2f}%"
    )
)


# Format kickout win rate as percentage
display_df["KickoutWinRate"] = display_df[
    "KickoutWinRate"
].map(
    lambda value: (
        ""
        if pd.isna(value)
        else f"{value:.2f}%"
    )
)


# Format turnover differential with + or - sign
display_df["TurnoverDifferential"] = display_df[
    "TurnoverDifferential"
].map(
    lambda value: (
        ""
        if pd.isna(value)
        else f"{value:+.0f}"
    )
)


# Format scores per attack as decimal
display_df["ScoresPerAttack"] = display_df[
    "ScoresPerAttack"
].map(
    lambda value: (
        ""
        if pd.isna(value)
        else f"{value:.3f}"
    )
)


# Format attack-to-shot rate as percentage
display_df["AttackShotRate"] = display_df[
    "AttackShotRate"
].map(
    lambda value: (
        ""
        if pd.isna(value)
        else f"{value:.2f}%"
    )
)


# Render table without the dataframe index column
st.dataframe(
    display_df,
    width="stretch",
    hide_index=True,
)


# -----------------------------
# Player data loading check
# -----------------------------
# This confirms that the player CSV has loaded successfully.
# It can later be replaced by a full Player Analytics section.

st.header("Player Data Check")

player_col1, player_col2, player_col3 = st.columns(3)

player_col1.metric(
    "Player Records",
    len(player_data),
)

player_col2.metric(
    "Players",
    player_data["PlayerName"].nunique(),
)

player_col3.metric(
    "Player Matches",
    player_data["MatchID"].nunique(),
)


# -----------------------------
# Player data preview
# -----------------------------
# Show the most useful columns from the first 10 player-match records.

player_preview_cols = [
    "MatchID",
    "Date",
    "Opponent",
    "PlayerName",
    "Position",
    "Started",
    "MinutesPlayed",
    "HandpassesTotal",
    "FootpassesTotal",
    "IncompletePasses",
    "Assists",
    "Points",
    "Goals",
    "TwoPointers",
    "ShotConversionPct",
    "DataType",
]

available_player_preview_cols = [
    column
    for column in player_preview_cols
    if column in player_data.columns
]

st.dataframe(
    player_data[available_player_preview_cols].head(10),
    width="stretch",
    hide_index=True,
)
