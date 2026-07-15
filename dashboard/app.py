# -----------------------------
# Imports
# -----------------------------
# sys and pathlib help us import files from the src folder.
# Streamlit builds the web dashboard.
# pandas helps us format missing values.
# Plotly creates interactive charts.

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px


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
# load_season_data reads and joins the CSV files.
# add_metrics calculates our KPIs.

from load_data import load_season_data
from metrics import add_metrics


# -----------------------------
# App constants
# -----------------------------
# Austin Stacks amber/orange colour used across the dashboard.

AMBER = "#F59E0B"


# -----------------------------
# Streamlit page setup
# -----------------------------
# Sets browser tab title and uses wide layout for charts/tables.

st.set_page_config(page_title="Austin Stacks Analytics", layout="wide")


# -----------------------------
# Dashboard title
# -----------------------------

st.title("Austin Stacks Analytics Platform")
st.subheader("County League 2026")


# -----------------------------
# Load and prepare data
# -----------------------------
# Load match/team data, calculate KPIs, then filter to Austin Stacks only.

season = add_metrics(load_season_data())
stacks = season[season["Team"] == "Austin Stacks"].copy()


# -----------------------------
# Season overview KPI cards
# -----------------------------
# These are headline season metrics for Austin Stacks.

st.header("Season Overview")

avg_turnover = stacks["TurnoverDifferential"].mean()

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Matches", stacks["MatchID"].nunique())
col2.metric("Avg Shot %", f"{stacks['ShotConversion'].mean():.1f}%")
col3.metric("Avg Kickout Win %", f"{stacks['KickoutWinRate'].mean():.1f}%")
col4.metric("Avg Turnover Diff", f"{avg_turnover:+.1f}")
col5.metric("Avg Attack → Shot %", f"{stacks['AttackShotRate'].mean():.1f}%")


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

fig1.update_traces(line=dict(width=4), marker=dict(size=10))
fig1.update_layout(
    xaxis_title="Opponent",
    yaxis_title="Shot Conversion %",
)

st.plotly_chart(fig1, width="stretch")


# Kickout win rate chart
fig2 = px.line(
    stacks,
    x="Opponent",
    y="KickoutWinRate",
    markers=True,
    title="Kickout Win Rate % by Opponent",
    color_discrete_sequence=[AMBER],
)

fig2.update_traces(line=dict(width=4), marker=dict(size=10))
fig2.update_layout(
    xaxis_title="Opponent",
    yaxis_title="Kickout Win Rate %",
)

st.plotly_chart(fig2, width="stretch")


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

st.plotly_chart(fig3, width="stretch")


# Attack to shot rate chart
# This shows what percentage of attacks resulted in a shot.
fig4 = px.line(
    stacks,
    x="Opponent",
    y="AttackShotRate",
    markers=True,
    title="Attack → Shot Rate % by Opponent",
    color_discrete_sequence=[AMBER],
)

fig4.update_traces(line=dict(width=4), marker=dict(size=10))
fig4.update_layout(
    xaxis_title="Opponent",
    yaxis_title="Attack → Shot Rate %",
)

st.plotly_chart(fig4, width="stretch")


# -----------------------------
# Match data table
# -----------------------------
# This displays the main Austin Stacks match stats.
# We format percentages and +/- values so the table is easier to read.

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
display_df["ShotConversion"] = display_df["ShotConversion"].map(
    lambda x: "" if pd.isna(x) else f"{x:.2f}%"
)


# Format kickout win rate as percentage
display_df["KickoutWinRate"] = display_df["KickoutWinRate"].map(
    lambda x: "" if pd.isna(x) else f"{x:.2f}%"
)


# Format turnover differential with + or - sign
display_df["TurnoverDifferential"] = display_df["TurnoverDifferential"].map(
    lambda x: "" if pd.isna(x) else f"{x:+.0f}"
)


# Format scores per attack as decimal
display_df["ScoresPerAttack"] = display_df["ScoresPerAttack"].map(
    lambda x: "" if pd.isna(x) else f"{x:.3f}"
)


# Format attack to shot rate as percentage
display_df["AttackShotRate"] = display_df["AttackShotRate"].map(
    lambda x: "" if pd.isna(x) else f"{x:.2f}%"
)


# Render table without the dataframe index column
st.dataframe(
    display_df,
    width="stretch",
    hide_index=True,
)
