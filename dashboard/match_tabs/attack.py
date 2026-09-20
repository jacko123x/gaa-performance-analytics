
import pandas as pd
import plotly.express as px
import streamlit as st

from match_formatting import AMBER, format_pct, render_metric_tiles


def render_attack(match_team, show_averages):
    st.header(
        "Average attack efficiency"
        if show_averages
        else "Attack efficiency"
    )

    if not match_team.empty:

        row = match_team.iloc[0]

        render_metric_tiles(
            [
                {
                    "label": "Attack → shot",
                    "value": format_pct(row["AttackToShotPct"]),
                    "tone": "blue",
                },
                {
                    "label": "Attack → score",
                    "value": format_pct(row["AttackToScorePct"]),
                    "tone": "green",
                },
                {
                    "label": "Shot conversion",
                    "value": format_pct(row["ShotConversionPct"]),
                    "tone": "amber",
                },
            ],
            columns_per_row=3,
            compact=True,
        )


        st.markdown("#### Attack funnel")

        funnel_data = pd.DataFrame(
            {
                "Stage": [
                    "Attacks",
                    "Shots",
                    "Scores",
                ],
                "Count": [
                    row["Attacks"],
                    row["TotalShots"],
                    row["TotalScores"],
                ],
            }
        )

        fig = px.funnel(
            funnel_data,
            x="Count",
            y="Stage",
            title="Attack → Shot → Score",
            color_discrete_sequence=[AMBER],
        )

        fig.update_layout(
            height=500,
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )


        st.markdown("#### Open play vs placed ball")

        conversion_data = pd.DataFrame(
            {
                "Type": [
                    "Overall",
                    "Play",
                    "Placed",
                ],
                "Conversion": [
                    row["ShotConversionPct"],
                    row["PlayConversionPct"],
                    row["PlacedConversionPct"],
                ],
            }
        )

        fig = px.bar(
            conversion_data,
            x="Type",
            y="Conversion",
            title="Shot Conversion %",
            color_discrete_sequence=[AMBER],
            text_auto=".1f",
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


# ==========================================================
