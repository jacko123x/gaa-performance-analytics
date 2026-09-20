
import pandas as pd
import plotly.express as px
import streamlit as st

from match_formatting import (
    AMBER,
    format_pct,
    format_scope_count,
    render_metric_tiles,
)


def render_shooting(match_shooting, show_averages):
    st.header("Shooting analysis")


    period_selection = st.segmented_control(
        "Period",
        options=[
            "FT",
            "1H",
            "2H",
        ],
        default="FT",
        key="match_shooting_period",
    )


    period_shooting = match_shooting[
        match_shooting["Period"]
        == period_selection
    ].copy()


    overall_shooting = period_shooting[
        period_shooting["ShotType"]
        == "Overall"
    ]


    if not overall_shooting.empty:

        row = overall_shooting.iloc[0]

        render_metric_tiles(
            [
                {
                    "label": "Avg shots" if show_averages else "Shots",
                    "value": format_scope_count(
                        row["ShotsTaken"], show_averages
                    ),
                    "tone": "purple",
                },
                {
                    "label": "Avg scores" if show_averages else "Scores",
                    "value": format_scope_count(
                        row["ShotsScored"], show_averages
                    ),
                    "tone": "green",
                },
                {
                    "label": "Conversion",
                    "value": format_pct(row["ShotConversionPct"]),
                    "tone": "amber",
                },
                {
                    "label": "Avg misses" if show_averages else "Misses",
                    "value": format_scope_count(row["Misses"], show_averages),
                    "tone": "red",
                },
            ],
            columns_per_row=4,
            compact=True,
        )


    shot_types = period_shooting[
        period_shooting["ShotType"]
        != "Overall"
    ].copy()


    if not shot_types.empty:

        st.markdown("#### Conversion by shot type")

        fig = px.bar(
            shot_types,
            x="ShotType",
            y="ShotConversionPct",
            title="Shot Type Conversion %",
            color_discrete_sequence=[AMBER],
            hover_data=[
                "ShotsTaken",
                "ShotsScored",
            ],
        )

        fig.update_layout(
            yaxis_title="Conversion %",
            showlegend=False,
            height=450,
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )


    if not overall_shooting.empty:

        st.markdown("#### Miss analysis")

        miss_data = pd.DataFrame(
            {
                "Outcome": [
                    "Wide",
                    "Short",
                    "Blocked",
                    "Post",
                    "Saved",
                ],
                "Count": [
                    row["Wides"],
                    row["Shorts"],
                    row["Blocked"],
                    row["Post"],
                    row["Saved"],
                ],
            }
        )

        fig = px.bar(
            miss_data,
            x="Outcome",
            y="Count",
            title="Missed Shot Outcomes",
            color_discrete_sequence=[AMBER],
        )

        fig.update_layout(
            showlegend=False,
            height=450,
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )


# ==========================================================
