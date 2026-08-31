
import pandas as pd
import plotly.express as px
import streamlit as st

from match_formatting import (
    AMBER,
    format_pct,
    format_scope_count,
    format_signed,
)


def render_turnovers(match_turnovers, show_averages):
    st.header("Turnover Analysis")


    turnover_period = st.radio(
        "Turnover Period",
        options=[
            "FT",
            "1H",
            "2H",
        ],
        horizontal=True,
    )


    period_turnovers = match_turnovers[
        match_turnovers["Period"]
        == turnover_period
    ]


    if not period_turnovers.empty:

        row = period_turnovers.iloc[0]

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            (
                "Avg Turnovers Won"
                if show_averages
                else "Turnovers Won"
            ),
            format_scope_count(
                row["TurnoversWon"],
                show_averages,
            ),
        )

        col2.metric(
            (
                "Avg Turnovers Lost"
                if show_averages
                else "Turnovers Lost"
            ),
            format_scope_count(
                row["TurnoversLost"],
                show_averages,
            ),
        )

        col3.metric(
            (
                "Avg Differential"
                if show_averages
                else "Differential"
            ),
            format_signed(
                row["TurnoverDifferential"],
                decimals=(
                    1
                    if show_averages
                    else 0
                ),
            ),
        )

        col4.metric(
            "Forced Won %",
            format_pct(
                row["ForcedTurnoverPct"]
            ),
        )


        st.subheader(
            "Turnover Breakdown"
        )

        turnover_breakdown = pd.DataFrame(
            {
                "Type": [
                    "Won Forced",
                    "Won Unforced",
                    "Lost Forced",
                    "Lost Unforced",
                ],
                "Count": [
                    row[
                        "TurnoversWonForced"
                    ],
                    row[
                        "TurnoversWonUnforced"
                    ],
                    row[
                        "TurnoversLostForced"
                    ],
                    row[
                        "TurnoversLostUnforced"
                    ],
                ],
            }
        )

        fig = px.bar(
            turnover_breakdown,
            x="Type",
            y="Count",
            title="Turnover Breakdown",
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
