
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


def render_turnovers(match_turnovers, show_averages):
    st.header("Turnover analysis")


    turnover_period = st.segmented_control(
        "Turnover period",
        options=[
            "FT",
            "1H",
            "2H",
        ],
        default="FT",
        key="match_turnover_period",
    )


    period_turnovers = match_turnovers[
        match_turnovers["Period"]
        == turnover_period
    ]


    if not period_turnovers.empty:

        row = period_turnovers.iloc[0]

        differential = row["TurnoverDifferential"]
        render_metric_tiles(
            [
                {
                    "label": (
                        "Avg turnovers won"
                        if show_averages
                        else "Turnovers won"
                    ),
                    "value": format_scope_count(
                        row["TurnoversWon"], show_averages
                    ),
                    "tone": "green",
                },
                {
                    "label": (
                        "Avg turnovers lost"
                        if show_averages
                        else "Turnovers lost"
                    ),
                    "value": format_scope_count(
                        row["TurnoversLost"], show_averages
                    ),
                    "tone": "red",
                },
                {
                    "label": (
                        "Avg differential" if show_averages else "Differential"
                    ),
                    "value": format_signed(
                        differential,
                        decimals=1 if show_averages else 0,
                    ),
                    "tone": "green" if differential >= 0 else "red",
                },
                {
                    "label": "Forced won",
                    "value": format_pct(row["ForcedTurnoverPct"]),
                    "tone": "blue",
                },
            ],
            columns_per_row=4,
            compact=True,
        )


        st.markdown("#### Turnover breakdown")

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
