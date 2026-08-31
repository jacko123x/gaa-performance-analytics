
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
)


def render_kickouts(match_kickouts, show_averages):
    st.header("Kickout Analysis")


    kickout_period = st.radio(
        "Kickout Period",
        options=[
            "FT",
            "1H",
            "2H",
        ],
        horizontal=True,
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


    col1, col2 = st.columns(2)


    if not own.empty:

        own_row = own.iloc[0]

        col1.metric(
            (
                "Avg Own Kickouts Won"
                if show_averages
                else "Own Kickouts Won"
            ),
            f"{format_scope_count(own_row['Won'], show_averages)}/"
            f"{format_scope_count(own_row['Taken'], show_averages)}",
        )

        col1.metric(
            "Own Retention %",
            format_pct(
                own_row["WinPct"]
            ),
        )


    if not opponent.empty:

        opp_row = opponent.iloc[0]

        col2.metric(
            (
                "Avg Opponent Kickouts Won"
                if show_averages
                else "Opponent Kickouts Won"
            ),
            f"{format_scope_count(opp_row['Won'], show_averages)}/"
            f"{format_scope_count(opp_row['Taken'], show_averages)}",
        )

        col2.metric(
            "Opposition KO Win %",
            format_pct(
                opp_row["WinPct"]
            ),
        )


    st.subheader("Kickout Comparison")

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


    st.subheader(
        "Kickout Win Type"
    )

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
