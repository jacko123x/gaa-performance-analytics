
import pandas as pd
import plotly.express as px
import streamlit as st

from match_formatting import (
    AMBER,
    format_pct,
    format_scope_count,
    format_signed,
    render_metric_tiles,
)


def render_overview(match_team, match_turnovers, match_kickouts, show_averages):
    st.header(
        "Selected match averages"
        if show_averages
        else "Match overview"
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


        turnover_tone = (
            "green"
            if turnover_diff is not None and turnover_diff >= 0
            else "red"
        )
        render_metric_tiles(
            [
                {
                    "label": "Avg attacks" if show_averages else "Attacks",
                    "value": format_scope_count(row["Attacks"], show_averages),
                    "tone": "purple",
                },
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
                {
                    "label": (
                        "Avg empty attacks"
                        if show_averages
                        else "Empty attacks"
                    ),
                    "value": format_scope_count(
                        row["EmptyAttacks"], show_averages
                    ),
                    "tone": "red",
                },
                {
                    "label": "Own KO retention",
                    "value": format_pct(own_ko_pct),
                    "tone": "green",
                },
                {
                    "label": "Opposition KOs won",
                    "value": format_pct(opp_ko_pct),
                    "tone": "blue",
                },
                {
                    "label": "Turnover differential",
                    "value": (
                        format_signed(turnover_diff)
                        if turnover_diff is not None
                        else "-"
                    ),
                    "tone": turnover_tone,
                },
            ],
            columns_per_row=4,
            compact=True,
        )

        st.markdown("#### Attacking output")

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
