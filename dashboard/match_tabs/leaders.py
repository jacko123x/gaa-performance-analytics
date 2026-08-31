
import plotly.express as px
import streamlit as st

from match_formatting import AMBER, format_number, format_pct


def render_leaders(match_players, show_averages):
    st.header(
        "Squad Leaders — Selected Match Totals"
        if show_averages
        else "Squad Leaders"
    )


    if match_players.empty:

        st.warning(
            "No player data available for this match."
        )

    else:

        # Players with game time only
        active_players = match_players[
            match_players[
                "MinutesPlayed"
            ] > 0
        ].copy()


        metric_options = {
            "Possessions": "Possessions",
            "Total Passes": "TotalPasses",
            "Pass Accuracy %": "PassAccuracyPct",
            "Handpass Accuracy %": "HandpassAccuracyPct",
            "Footpass Accuracy %": "FootpassAccuracyPct",
            "Turnovers Won": "TurnoversWon",
            "Turnover Differential": "TurnoverDifferential",
            "Breaking Balls Won": "BreakingBallsWon",
            "Kickouts Won": "KickoutsWon",
            "Frees Won": "FreesWon",
            "Assists": "Assists",
            "Score Value": "TotalScoreValue",
            "Shot Conversion %": "CalculatedShotConversionPct",
            "Possessions per 60": "PossessionsPer60",
            "Passes per 60": "PassesPer60",
            "Turnovers Won per 60": "TurnoversWonPer60",
            "Score Value per 60": "ScoreValuePer60",
        }


        selected_metric_label = st.selectbox(
            "Leaderboard Metric",
            options=list(
                metric_options.keys()
            ),
        )


        selected_metric = metric_options[
            selected_metric_label
        ]


        # --------------------------------------------------
        # Special filters
        # --------------------------------------------------

        comparison_data = active_players.copy()


        if selected_metric in [
            "PassAccuracyPct",
            "HandpassAccuracyPct",
            "FootpassAccuracyPct",
        ]:

            min_passes = st.slider(
                "Minimum passes attempted",
                min_value=0,
                max_value=max(
                    1,
                    int(
                        active_players[
                            "TotalPasses"
                        ].max()
                    ),
                ),
                value=5,
            )

            comparison_data = (
                comparison_data[
                    comparison_data[
                        "TotalPasses"
                    ] >= min_passes
                ]
            )


        if selected_metric == (
            "CalculatedShotConversionPct"
        ):

            min_shots = st.slider(
                "Minimum shot attempts",
                min_value=1,
                max_value=max(
                    1,
                    int(
                        active_players[
                            "ShotAttempts"
                        ].max()
                    ),
                ),
                value=1,
            )

            comparison_data = (
                comparison_data[
                    comparison_data[
                        "ShotAttempts"
                    ] >= min_shots
                ]
            )


        leaderboard = (
            comparison_data[
                [
                    "PlayerName",
                    "Position",
                    "MinutesPlayed",
                    selected_metric,
                ]
            ]
            .dropna(
                subset=[
                    selected_metric
                ]
            )
            .sort_values(
                selected_metric,
                ascending=False,
            )
        )


        if leaderboard.empty:

            st.warning(
                "No players meet the selected criteria."
            )

        else:

            # --------------------------------------------------
            # Top 3 cards
            # --------------------------------------------------

            top_three = leaderboard.head(3)

            top_columns = st.columns(
                min(
                    3,
                    len(top_three),
                )
            )


            for index, (_, player) in enumerate(
                top_three.iterrows()
            ):

                value = player[
                    selected_metric
                ]

                if "Pct" in selected_metric:

                    display_value = (
                        format_pct(value)
                    )

                else:

                    display_value = (
                        format_number(
                            value,
                            1,
                        )
                    )


                top_columns[index].metric(
                    player[
                        "PlayerName"
                    ],
                    display_value,
                )


            # --------------------------------------------------
            # Leaderboard chart
            # --------------------------------------------------

            chart_data = (
                leaderboard
                .head(15)
                .sort_values(
                    selected_metric,
                    ascending=True,
                )
            )


            fig = px.bar(
                chart_data,
                x=selected_metric,
                y="PlayerName",
                orientation="h",
                title=selected_metric_label,
                color_discrete_sequence=[
                    AMBER
                ],
                hover_data=[
                    "Position",
                    "MinutesPlayed",
                ],
                text=selected_metric,
            )


            fig.update_traces(
                textposition="outside",
            )


            fig.update_layout(
                height=650,
                yaxis_title="Player",
                xaxis_title=(
                    selected_metric_label
                ),
                showlegend=False,
            )


            st.plotly_chart(
                fig,
                width="stretch",
            )


            # --------------------------------------------------
            # Leaderboard table
            # --------------------------------------------------

            table_data = leaderboard.copy()

            table_data.insert(
                0,
                "Rank",
                range(
                    1,
                    len(table_data) + 1,
                ),
            )


            if "Pct" in selected_metric:

                table_data[
                    selected_metric
                ] = table_data[
                    selected_metric
                ].map(
                    format_pct
                )


            st.dataframe(
                table_data,
                hide_index=True,
                width="stretch",
            )
