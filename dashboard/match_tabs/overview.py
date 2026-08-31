
import pandas as pd
import plotly.express as px
import streamlit as st

from match_formatting import (
    AMBER,
    format_pct,
    format_scope_count,
    format_signed,
)


def render_overview(match_team, match_turnovers, match_kickouts, show_averages):
    st.header(
        "Selected Match Averages"
        if show_averages
        else "Match Overview"
    )

    if match_team.empty:

        st.warning(
            "No team data available for this match."
        )

    else:

        row = match_team.iloc[0]

        turnover_ft = match_turnovers[
            match_turnovers["Period"] == "FT"
        ]

        if not turnover_ft.empty:

            turnover_diff = turnover_ft[
                "TurnoverDifferential"
            ].iloc[0]

        else:

            turnover_diff = None


        own_ko = match_kickouts[
            (
                match_kickouts["Period"] == "FT"
            )
            &
            (
                match_kickouts["KickoutType"] == "Own"
            )
        ]


        opp_ko = match_kickouts[
            (
                match_kickouts["Period"] == "FT"
            )
            &
            (
                match_kickouts["KickoutType"]
                == "Opponent"
            )
        ]


        own_ko_pct = (
            own_ko["WinPct"].iloc[0]
            if not own_ko.empty
            else None
        )


        opp_ko_pct = (
            opp_ko["WinPct"].iloc[0]
            if not opp_ko.empty
            else None
        )


        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Avg Attacks" if show_averages else "Attacks",
            format_scope_count(
                row["Attacks"],
                show_averages,
            ),
        )

        col2.metric(
            "Attack → Shot",
            format_pct(
                row["AttackToShotPct"]
            ),
        )

        col3.metric(
            "Attack → Score",
            format_pct(
                row["AttackToScorePct"]
            ),
        )

        col4.metric(
            "Shot Conversion",
            format_pct(
                row["ShotConversionPct"]
            ),
        )


        col5, col6, col7, col8 = st.columns(4)

        col5.metric(
            (
                "Avg Empty Attacks"
                if show_averages
                else "Empty Attacks"
            ),
            format_scope_count(
                row["EmptyAttacks"],
                show_averages,
            ),
        )

        col6.metric(
            "Own KO Retention",
            format_pct(
                own_ko_pct
            ),
        )

        col7.metric(
            "Opp KO Won",
            format_pct(
                opp_ko_pct
            ),
        )

        col8.metric(
            "Turnover Diff",
            (
                format_signed(
                    turnover_diff
                )
                if turnover_diff is not None
                else "-"
            ),
        )


        st.divider()

        st.subheader("Match Performance")

        overview_metrics = pd.DataFrame(
            {
                "Metric": [
                    "Attacks",
                    "Shots",
                    "Scores",
                    "Empty Attacks",
                ],
                "Value": [
                    row["Attacks"],
                    row["TotalShots"],
                    row["TotalScores"],
                    row["EmptyAttacks"],
                ],
            }
        )

        fig = px.bar(
            overview_metrics,
            x="Metric",
            y="Value",
            title="Attacking Output",
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
