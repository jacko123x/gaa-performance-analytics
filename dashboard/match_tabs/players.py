
from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st

from match_formatting import (
    AMBER,
    DARK,
    format_pct,
    format_signed,
    render_metric_tiles,
)


def render_players(match_players, show_averages):
    st.header("Player performance")

    if match_players.empty:

        st.warning(
            "No player data available for this match."
        )

    else:

        player_options = sorted(
            match_players[
                "PlayerName"
            ]
            .dropna()
            .unique()
            .tolist()
        )


        selected_player = st.selectbox(
            "Select player",
            options=player_options,
        )


        player_row = match_players[
            match_players["PlayerName"]
            == selected_player
        ].iloc[0]


        # --------------------------------------------------
        # Player header
        # --------------------------------------------------

        if show_averages:
            player_context = (
                f"Squad #{int(player_row['SquadNumber'])} | "
                f"{int(player_row['Appearances'])} appearances | "
                f"{int(player_row['Starts'])} starts | "
                f"{int(player_row['MinutesPlayed'])} total minutes"
            )
        else:
            player_status = (
                "Starter"
                if player_row["Started"]
                else "Substitute"
            )

            player_context = (
                f"Squad #{int(player_row['SquadNumber'])} | "
                f"{player_status} | "
                f"{int(player_row['MinutesPlayed'])} minutes"
            )

        player_name_html = escape(str(selected_player))
        position_html = escape(str(player_row["Position"]))
        context_html = escape(player_context)
        st.markdown(
            f"""
<div style="padding:0.75rem 0.9rem;margin:0.4rem 0 0.7rem;
    border:1px solid rgba(96,165,250,0.26);border-radius:0.65rem;
    background:linear-gradient(100deg,rgba(59,130,246,0.15),
        rgba(245,158,11,0.05));">
    <div style="font-size:1.15rem;font-weight:750;">
        {player_name_html} <span style="color:#60A5FA;">· {position_html}</span>
    </div>
    <div style="font-size:0.72rem;opacity:0.64;margin-top:0.25rem;">
        {context_html}
    </div>
</div>
""",
            unsafe_allow_html=True,
        )


        # --------------------------------------------------
        # Main KPI row
        # --------------------------------------------------

        turnover_diff = player_row["TurnoverDifferential"]
        render_metric_tiles(
            [
                {
                    "label": "Possessions",
                    "value": int(player_row["Possessions"]),
                    "tone": "purple",
                },
                {
                    "label": "Total passes",
                    "value": int(player_row["TotalPasses"]),
                    "tone": "blue",
                },
                {
                    "label": "Pass accuracy",
                    "value": format_pct(player_row["PassAccuracyPct"]),
                    "tone": "blue",
                },
                {
                    "label": "Turnover differential",
                    "value": format_signed(turnover_diff),
                    "tone": "green" if turnover_diff >= 0 else "red",
                },
                {
                    "label": "Breaking balls won",
                    "value": int(player_row["BreakingBallsWon"]),
                    "tone": "green",
                },
                {
                    "label": "Kickouts won",
                    "value": int(player_row["KickoutsWon"]),
                    "tone": "green",
                },
                {
                    "label": "Assists",
                    "value": int(player_row["Assists"]),
                    "tone": "amber",
                },
                {
                    "label": "Score value",
                    "value": int(player_row["TotalScoreValue"]),
                    "tone": "amber",
                },
            ],
            columns_per_row=4,
            compact=True,
        )


        # --------------------------------------------------
        # Passing profile
        # --------------------------------------------------

        st.markdown("#### Passing profile")

        pass_col1, pass_col2 = st.columns(2)


        with pass_col1:

            passing_data = pd.DataFrame(
                {
                    "Pass Type": [
                        "Handpass",
                        "Footpass",
                    ],
                    "Attempted": [
                        player_row[
                            "HandpassesTotal"
                        ],
                        player_row[
                            "FootpassesTotal"
                        ],
                    ],
                    "Completed": [
                        player_row[
                            "HandpassesCompleted"
                        ],
                        player_row[
                            "FootpassesCompleted"
                        ],
                    ],
                }
            )


            fig = px.bar(
                passing_data,
                x="Pass Type",
                y=[
                    "Attempted",
                    "Completed",
                ],
                barmode="group",
                title="Pass Volume",
                color_discrete_sequence=[
                    AMBER,
                    DARK,
                ],
            )

            fig.update_layout(
                height=450,
                legend_title_text="",
            )

            st.plotly_chart(
                fig,
                width="stretch",
            )


        with pass_col2:

            accuracy_data = pd.DataFrame(
                {
                    "Pass Type": [
                        "Overall",
                        "Handpass",
                        "Footpass",
                    ],
                    "Accuracy": [
                        player_row[
                            "PassAccuracyPct"
                        ],
                        player_row[
                            "HandpassAccuracyPct"
                        ],
                        player_row[
                            "FootpassAccuracyPct"
                        ],
                    ],
                }
            )


            fig = px.bar(
                accuracy_data,
                x="Pass Type",
                y="Accuracy",
                title="Pass Accuracy %",
                color_discrete_sequence=[
                    AMBER
                ],
                text_auto=".1f",
            )

            fig.update_layout(
                height=450,
                yaxis_title="Accuracy %",
                showlegend=False,
            )

            st.plotly_chart(
                fig,
                width="stretch",
            )


        # --------------------------------------------------
        # Possession contribution
        # --------------------------------------------------

        st.subheader(
            "Possession Contribution"
        )


        possession_data = pd.DataFrame(
            {
                "Metric": [
                    "Possessions",
                    "Turnovers Won",
                    "Turnovers Lost",
                    "Breaking Balls",
                    "Kickouts Won",
                    "Frees Won",
                ],
                "Value": [
                    player_row[
                        "Possessions"
                    ],
                    player_row[
                        "TurnoversWon"
                    ],
                    player_row[
                        "TurnoversLost"
                    ],
                    player_row[
                        "BreakingBallsWon"
                    ],
                    player_row[
                        "KickoutsWon"
                    ],
                    player_row[
                        "FreesWon"
                    ],
                ],
            }
        )


        fig = px.bar(
            possession_data,
            x="Metric",
            y="Value",
            title="Possession & Defensive Contribution",
            color_discrete_sequence=[
                AMBER
            ],
            text="Value",
        )

        fig.update_traces(
            textposition="outside",
        )

        fig.update_layout(
            height=450,
            showlegend=False,
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )


        # --------------------------------------------------
        # Scoring profile
        # --------------------------------------------------

        st.subheader(
            "Scoring Profile"
        )


        score_col1, score_col2 = st.columns(
            2
        )


        with score_col1:

            scoring_data = pd.DataFrame(
                {
                    "Type": [
                        "From Play",
                        "Free",
                        "45",
                        "Goals",
                        "Two Pointers",
                    ],
                    "Value": [
                        player_row[
                            "PointsPlay"
                        ],
                        player_row[
                            "PointsFree"
                        ],
                        player_row[
                            "Points45"
                        ],
                        player_row[
                            "Goals"
                        ],
                        player_row[
                            "TwoPointers"
                        ],
                    ],
                }
            )


            fig = px.bar(
                scoring_data,
                x="Type",
                y="Value",
                title="Scoring Breakdown",
                color_discrete_sequence=[
                    AMBER
                ],
                text="Value",
            )

            fig.update_layout(
                height=450,
                showlegend=False,
            )

            st.plotly_chart(
                fig,
                width="stretch",
            )


        with score_col2:

            shot_data = pd.DataFrame(
                {
                    "Metric": [
                        "Attempts",
                        "Scores",
                    ],
                    "Value": [
                        player_row[
                            "ShotAttempts"
                        ],
                        player_row[
                            "Scores"
                        ],
                    ],
                }
            )


            fig = px.bar(
                shot_data,
                x="Metric",
                y="Value",
                title=(
                    "Shot Output — "
                    f"{format_pct(
                        player_row[
                            'CalculatedShotConversionPct'
                        ]
                    )}"
                ),
                color_discrete_sequence=[
                    AMBER,
                    DARK,
                ],
                text="Value",
            )

            fig.update_layout(
                height=450,
                showlegend=False,
            )

            st.plotly_chart(
                fig,
                width="stretch",
            )


        # --------------------------------------------------
        # Per 60 metrics
        # --------------------------------------------------

        st.subheader(
            "Per 60 Minute Output"
        )


        per60_data = pd.DataFrame(
            {
                "Metric": [
                    "Possessions",
                    "Passes",
                    "Turnovers Won",
                    "Breaking Balls",
                    "Assists",
                    "Score Value",
                ],
                "Per60": [
                    player_row[
                        "PossessionsPer60"
                    ],
                    player_row[
                        "PassesPer60"
                    ],
                    player_row[
                        "TurnoversWonPer60"
                    ],
                    player_row[
                        "BreakingBallsWonPer60"
                    ],
                    player_row[
                        "AssistsPer60"
                    ],
                    player_row[
                        "ScoreValuePer60"
                    ],
                ],
            }
        )


        fig = px.bar(
            per60_data,
            x="Metric",
            y="Per60",
            title="Output per 60 Minutes",
            color_discrete_sequence=[
                AMBER
            ],
            text_auto=".1f",
        )

        fig.update_layout(
            height=450,
            showlegend=False,
            yaxis_title="Per 60",
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )


        # --------------------------------------------------
        # Player data table
        # --------------------------------------------------

        st.subheader(
            "Selected Match Totals"
            if show_averages
            else "Match Stats"
        )


        player_display_columns = [
            "PlayerName",
            "Position",
            "MinutesPlayed",
            "Possessions",
            "TotalPasses",
            "CompletedPasses",
            "PassAccuracyPct",
            "TurnoversWon",
            "TurnoversLost",
            "BreakingBallsWon",
            "KickoutsWon",
            "FreesWon",
            "FreesConceded",
            "Assists",
            "Points",
            "PointsPlay",
            "PointsFree",
            "Points45",
            "Goals",
            "TwoPointers",
            "ShotAttempts",
            "Scores",
            "CalculatedShotConversionPct",
        ]


        player_display = pd.DataFrame(
            [player_row[
                player_display_columns
            ]]
        )


        player_display[
            "PassAccuracyPct"
        ] = player_display[
            "PassAccuracyPct"
        ].map(format_pct)


        player_display[
            "CalculatedShotConversionPct"
        ] = player_display[
            "CalculatedShotConversionPct"
        ].map(format_pct)


        st.dataframe(
            player_display,
            hide_index=True,
            width="stretch",
        )


# ==========================================================
