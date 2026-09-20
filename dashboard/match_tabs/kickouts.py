
import plotly.express as px
import streamlit as st

from match_formatting import (
    AMBER,
    DARK,
    DARK_AMBER,
    GREY,
    LIGHT_AMBER,
    format_pct,
    format_scope_count,
    render_metric_tiles,
)


def render_kickouts(match_kickouts, show_averages):
    st.header("Kickout analysis")


    kickout_period = st.segmented_control(
        "Kickout period",
        options=[
            "FT",
            "1H",
            "2H",
        ],
        default="FT",
        key="match_kickout_period",
    )


    ko_period = match_kickouts[
        match_kickouts["Period"]
        == kickout_period
    ].copy()


    own = ko_period[
        ko_period["KickoutType"] == "Own"
    ]

    opponent = ko_period[
        ko_period["KickoutType"] == "Opponent"
    ]


    tiles = []
    if not own.empty:

        own_row = own.iloc[0]
        tiles.extend(
            [
                {
                    "label": (
                        "Avg own KOs won"
                        if show_averages
                        else "Own KOs won"
                    ),
                    "value": (
                        f"{format_scope_count(own_row['Won'], show_averages)} / "
                        f"{format_scope_count(own_row['Taken'], show_averages)}"
                    ),
                    "tone": "purple",
                },
                {
                    "label": "Own retention",
                    "value": format_pct(own_row["WinPct"]),
                    "tone": "green",
                },
            ]
        )


    if not opponent.empty:

        opp_row = opponent.iloc[0]

        tiles.extend(
            [
                {
                    "label": (
                        "Avg opposition KOs won"
                        if show_averages
                        else "Opposition KOs won"
                    ),
                    "value": (
                        f"{format_scope_count(opp_row['Won'], show_averages)} / "
                        f"{format_scope_count(opp_row['Taken'], show_averages)}"
                    ),
                    "tone": "blue",
                },
                {
                    "label": "Opposition KO win rate",
                    "value": format_pct(opp_row["WinPct"]),
                    "tone": "amber",
                },
            ]
        )

    render_metric_tiles(tiles, columns_per_row=4, compact=True)


    st.markdown("#### Kickout comparison")

    fig = px.bar(
        ko_period,
        x="KickoutType",
        y=[
            "Won",
            "Lost",
        ],
        barmode="group",
        title="Kickouts Won vs Lost",
        color_discrete_sequence=[
            AMBER,
            DARK,
        ],
    )

    fig.update_layout(
        legend_title_text="Outcome",
        height=500,
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )


    st.markdown("#### Kickout win type")

    ko_breakdown = ko_period[
        [
            "KickoutType",
            "CleanWins",
            "BreakWins",
            "FreeWins",
            "SidelineWins",
        ]
    ].copy()


    ko_breakdown = ko_breakdown.melt(
        id_vars="KickoutType",
        var_name="WinType",
        value_name="Count",
    )


    fig = px.bar(
        ko_breakdown,
        x="KickoutType",
        y="Count",
        color="WinType",
        barmode="stack",
        title="How Kickouts Were Won",
        color_discrete_sequence=[
            AMBER,
            DARK_AMBER,
            LIGHT_AMBER,
            GREY,
        ],
    )

    fig.update_layout(
        height=500,
        legend_title_text="Win Type",
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )


# ==========================================================
