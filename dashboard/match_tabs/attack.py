
import pandas as pd
import plotly.express as px
import streamlit as st

from match_formatting import AMBER, format_pct


def render_attack(match_team, show_averages):
    st.header(
        "Average Attack Efficiency"
        if show_averages
        else "Attack Efficiency"
    )

    if not match_team.empty:

        row = match_team.iloc[0]

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Attack → Shot",
            format_pct(
                row["AttackToShotPct"]
            ),
        )

        col2.metric(
            "Attack → Score",
            format_pct(
                row["AttackToScorePct"]
            ),
        )

        col3.metric(
            "Shot Conversion",
            format_pct(
                row["ShotConversionPct"]
            ),
        )


        st.subheader("Attack Funnel")

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


        st.subheader(
            "Open Play vs Placed Ball"
        )

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
