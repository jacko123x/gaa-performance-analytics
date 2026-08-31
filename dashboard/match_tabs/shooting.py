
import pandas as pd
import plotly.express as px
import streamlit as st

from match_formatting import AMBER, format_pct, format_scope_count


def render_shooting(match_shooting, show_averages):
    st.header("Shooting Analysis")


    period_selection = st.radio(
        "Period",
        options=[
            "FT",
            "1H",
            "2H",
        ],
        horizontal=True,
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

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Avg Shots" if show_averages else "Shots",
            format_scope_count(
                row["ShotsTaken"],
                show_averages,
            ),
        )

        col2.metric(
            "Avg Scores" if show_averages else "Scores",
            format_scope_count(
                row["ShotsScored"],
                show_averages,
            ),
        )

        col3.metric(
            "Conversion",
            format_pct(
                row["ShotConversionPct"]
            ),
        )

        col4.metric(
            "Avg Misses" if show_averages else "Misses",
            format_scope_count(
                row["Misses"],
                show_averages,
            ),
        )


    shot_types = period_shooting[
        period_shooting["ShotType"]
        != "Overall"
    ].copy()


    if not shot_types.empty:

        st.subheader(
            "Conversion by Shot Type"
        )

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

        st.subheader("Miss Analysis")

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
