from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st

from match_formatting import render_metric_tiles
from player_championship import build_player_championship_summary


AMBER = "#F59E0B"

METRIC_STYLE = {
    "Possessions": ("purple", "#A78BFA"),
    "Pass accuracy": ("blue", "#60A5FA"),
    "Turnovers won": ("green", "#4ADE80"),
    "Breaking balls": ("green", "#4ADE80"),
    "Kickouts won": ("green", "#4ADE80"),
    "Assists": ("amber", "#FBBF24"),
    "Score contribution": ("amber", "#FBBF24"),
}


METRICS = {
    "Possessions": {
        "total": "Possessions",
        "per_60": "PossessionsPer60",
    },
    "Pass accuracy": {
        "total": "PassAccuracyPct",
        "per_60": "PassAccuracyPct",
    },
    "Turnovers won": {
        "total": "TurnoversWon",
        "per_60": "TurnoversWonPer60",
    },
    "Breaking balls": {
        "total": "BreakingBallsWon",
        "per_60": "BreakingBallsWonPer60",
    },
    "Kickouts won": {
        "total": "KickoutsWon",
        "per_60": "KickoutsWonPer60",
    },
    "Assists": {
        "total": "Assists",
        "per_60": "AssistsPer60",
    },
    "Score contribution": {
        "total": "ScoreContributions",
        "per_60": "ScoreContributionsPer60",
    },
}


def build_squad_leaderboard(
    summary,
    metric_label,
    ranking_mode,
    minimum_minutes=0,
    minimum_passes=0,
):
    """Return a consistently filtered and ordered championship ranking."""

    mode_key = (
        "total"
        if ranking_mode == "Championship totals"
        else "per_60"
    )
    metric_column = METRICS[metric_label][mode_key]
    leaderboard = summary[summary["Games"].gt(0)].copy()

    if ranking_mode == "Per 60":
        leaderboard = leaderboard[
            leaderboard["MinutesPlayed"] >= minimum_minutes
        ]

    if metric_label == "Pass accuracy":
        leaderboard = leaderboard[
            leaderboard["TotalPasses"] >= minimum_passes
        ]

    leaderboard = (
        leaderboard.dropna(subset=[metric_column])
        .sort_values(
            [metric_column, "MinutesPlayed", "PlayerName"],
            ascending=[False, False, True],
        )
        .reset_index(drop=True)
    )
    leaderboard.insert(0, "Rank", range(1, len(leaderboard) + 1))
    return leaderboard, metric_column


def _format_ranking_value(value, metric_label, ranking_mode):
    if pd.isna(value):
        return "-"
    if metric_label == "Pass accuracy":
        return f"{value:.1f}%"
    if ranking_mode == "Per 60":
        return f"{value:.1f}"
    return f"{value:.0f}"


def _render_category_leaders(
    summary,
    ranking_mode,
    minimum_minutes,
    minimum_passes,
):
    st.markdown("#### Category leaders")
    tiles = []
    for metric_label in METRICS:
        leaderboard, metric_column = build_squad_leaderboard(
            summary,
            metric_label,
            ranking_mode,
            minimum_minutes,
            minimum_passes,
        )
        if leaderboard.empty:
            leader_name = "No qualifier"
            leader_value = "-"
        else:
            leader = leaderboard.iloc[0]
            leader_name = leader["PlayerName"]
            leader_value = _format_ranking_value(
                leader[metric_column],
                metric_label,
                ranking_mode,
            )

        tiles.append(
            {
                "label": metric_label,
                "value": leader_value,
                "detail": leader_name,
                "tone": METRIC_STYLE[metric_label][0],
            }
        )
    render_metric_tiles(tiles, columns_per_row=4, compact=True)


def _podium_card(player, value, metric_label, ranking_mode):
    podium = {
        1: ("#FBBF24", "rgba(245, 158, 11, 0.12)", "Leader"),
        2: ("#CBD5E1", "rgba(148, 163, 184, 0.10)", "Second"),
        3: ("#FB923C", "rgba(249, 115, 22, 0.10)", "Third"),
    }
    accent, background, place = podium[player.Rank]
    formatted_value = _format_ranking_value(
        value,
        metric_label,
        ranking_mode,
    )
    st.markdown(
        f"""
<div style="
    min-height:112px;
    padding:0.85rem 0.95rem;
    border:1px solid {accent}55;
    border-top:4px solid {accent};
    border-radius:0.7rem;
    background:linear-gradient(120deg, {background}, rgba(15, 23, 42, 0.02));
    box-shadow:0 3px 12px rgba(0, 0, 0, 0.10);
">
    <div style="display:flex;justify-content:space-between;gap:0.5rem;">
        <span style="font-size:0.78rem;font-weight:720;">
            #{player.Rank} {escape(str(player.PlayerName))}
        </span>
        <span style="font-size:0.62rem;font-weight:760;text-transform:uppercase;
            letter-spacing:0.055em;color:{accent};">{place}</span>
    </div>
    <div style="font-size:1.65rem;font-weight:780;color:{accent};
        line-height:1.1;margin-top:0.4rem;">{escape(formatted_value)}</div>
    <div style="font-size:0.69rem;opacity:0.60;margin-top:0.3rem;">
        {int(player.MinutesPlayed)} minutes · {int(player.Games)} games
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


def _render_top_three(
    leaderboard,
    metric_column,
    metric_label,
    ranking_mode,
):
    top_three = leaderboard.head(3)
    columns = st.columns(3, gap="small")
    for column, player in zip(columns, top_three.itertuples()):
        with column:
            _podium_card(
                player,
                getattr(player, metric_column),
                metric_label,
                ranking_mode,
            )


def _render_leaderboard_chart(
    leaderboard,
    metric_column,
    metric_label,
    ranking_mode,
):
    chart_data = leaderboard.head(15).sort_values(
        metric_column,
        ascending=True,
    )
    display_label = (
        metric_label
        if metric_label == "Pass accuracy"
        else (
            f"{metric_label} per 60"
            if ranking_mode == "Per 60"
            else metric_label
        )
    )

    figure = px.bar(
        chart_data,
        x=metric_column,
        y="PlayerName",
        orientation="h",
        color_discrete_sequence=[METRIC_STYLE[metric_label][1]],
        hover_data={
            "Position": True,
            "Games": True,
            "Starts": True,
            "MinutesPlayed": True,
            metric_column: ":.1f",
        },
        text=metric_column,
    )
    figure.update_traces(
        texttemplate=(
            "%{x:.1f}%"
            if metric_label == "Pass accuracy"
            else (
                "%{x:.1f}"
                if ranking_mode == "Per 60"
                else "%{x:.0f}"
            )
        ),
        textposition="outside",
    )
    figure.update_layout(
        height=max(480, len(chart_data) * 36),
        showlegend=False,
        xaxis_title=display_label,
        yaxis_title="Player",
    )
    if metric_label == "Pass accuracy":
        figure.update_xaxes(range=[0, 105], ticksuffix="%")
    st.plotly_chart(figure, width="stretch")


def _render_ranking_table(
    leaderboard,
    metric_column,
    metric_label,
    ranking_mode,
):
    value_label = (
        metric_label
        if metric_label == "Pass accuracy"
        else (
            f"{metric_label} / 60"
            if ranking_mode == "Per 60"
            else metric_label
        )
    )
    columns = [
        "Rank",
        "PlayerName",
        "Position",
        "Games",
        "Starts",
        "MinutesPlayed",
    ]
    if metric_label == "Pass accuracy":
        columns.append("TotalPasses")
    columns.append(metric_column)

    display = leaderboard[columns].rename(
        columns={
            "PlayerName": "Player",
            "MinutesPlayed": "Minutes",
            "TotalPasses": "Passes",
            metric_column: value_label,
        }
    )
    value_format = (
        "%.1f%%"
        if metric_label == "Pass accuracy"
        else (
            "%.1f"
            if ranking_mode == "Per 60"
            else "%.0f"
        )
    )
    st.dataframe(
        display,
        hide_index=True,
        width="stretch",
        column_config={
            "Player": st.column_config.TextColumn(pinned=True),
            value_label: st.column_config.NumberColumn(
                format=value_format
            ),
        },
    )


def render_squad_leaderboards(player_data):
    st.header("Squad leaderboards")
    st.caption(
        "Championship totals and per-60 rankings across the squad"
    )

    if player_data.empty:
        st.info("No championship player data is available yet.")
        return

    summary = build_player_championship_summary(player_data)
    max_minutes = max(1, int(summary["MinutesPlayed"].max()))
    max_passes = max(1, int(summary["TotalPasses"].max()))

    st.markdown("#### Ranking setup")
    with st.container(border=True):
        filter_left, filter_right = st.columns(2, gap="large")
        with filter_left:
            ranking_mode = st.segmented_control(
                "Ranking basis",
                options=["Championship totals", "Per 60"],
                default="Championship totals",
                key="squad_leaderboard_basis",
                width="stretch",
            )
        with filter_right:
            metric_label = st.selectbox(
                "Leaderboard metric",
                options=list(METRICS),
                key="championship_leaderboard_metric",
                help=(
                    "Score contribution counts successful scoring actions "
                    "plus assists."
                ),
            )

        qualifier_left, qualifier_right = st.columns(2, gap="large")
        if ranking_mode == "Per 60":
            with qualifier_left:
                minimum_minutes = st.slider(
                    "Minimum championship minutes",
                    min_value=1,
                    max_value=max_minutes,
                    value=min(30, max_minutes),
                    key="leaderboard_minimum_minutes",
                )
        else:
            minimum_minutes = 0

        if metric_label == "Pass accuracy":
            with qualifier_right:
                minimum_passes = st.slider(
                    "Minimum passes for accuracy",
                    min_value=1,
                    max_value=max_passes,
                    value=min(10, max_passes),
                    key="leaderboard_minimum_passes",
                )
        else:
            minimum_passes = min(10, max_passes)

    _render_category_leaders(
        summary,
        ranking_mode,
        minimum_minutes,
        minimum_passes,
    )

    st.subheader(f"{metric_label} ranking")
    if ranking_mode == "Per 60":
        qualification = (
            f"Players must have played at least {minimum_minutes} minutes"
        )
        if metric_label == "Pass accuracy":
            qualification += (
                f" and attempted at least {minimum_passes} passes"
            )
        st.caption(f"{qualification}.")
    elif metric_label == "Pass accuracy":
        st.caption(
            f"Players must have attempted at least {minimum_passes} passes."
        )

    leaderboard, metric_column = build_squad_leaderboard(
        summary,
        metric_label,
        ranking_mode,
        minimum_minutes,
        minimum_passes,
    )
    if leaderboard.empty:
        st.warning("No players meet the selected criteria.")
        return

    _render_top_three(
        leaderboard,
        metric_column,
        metric_label,
        ranking_mode,
    )
    _render_leaderboard_chart(
        leaderboard,
        metric_column,
        metric_label,
        ranking_mode,
    )
    _render_ranking_table(
        leaderboard,
        metric_column,
        metric_label,
        ranking_mode,
    )
