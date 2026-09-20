
import plotly.express as px
import streamlit as st

from match_formatting import AMBER, format_scope_count, render_metric_tiles


def render_scoring_sources(match_scoring_sources, show_averages):
    st.header("Scoring sources")
    value_format = ".1f" if show_averages else ".0f"


    total_sources = (
        match_scoring_sources["Scores"].sum()
    )


    turnover_scores = (
        match_scoring_sources.loc[
            match_scoring_sources[
                "Source"
            ] == "Turnover",
            "Scores",
        ].sum()
    )


    render_metric_tiles(
        [
            {
                "label": "Avg scores" if show_averages else "Scores",
                "value": format_scope_count(total_sources, show_averages),
                "tone": "amber",
            },
            {
                "label": (
                    "Avg scores from turnovers"
                    if show_averages
                    else "Scores from turnovers"
                ),
                "value": format_scope_count(turnover_scores, show_averages),
                "tone": "green",
            },
        ],
        columns_per_row=2,
        compact=True,
    )


    fig = px.bar(
        match_scoring_sources.sort_values(
            "Scores",
            ascending=False,
        ),
        x="Source",
        y="Scores",
        title="Where Scores Came From",
        color_discrete_sequence=[AMBER],
        text="Scores",
    )

    fig.update_traces(
        textposition="outside",
        texttemplate=f"%{{y:{value_format}}}",
        hovertemplate=(
            "<b>%{x}</b><br>"
            f"Scores: %{{y:{value_format}}}"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        showlegend=False,
        height=500,
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )


    st.subheader(
        "Scoring source distribution"
    )

    pie_data = match_scoring_sources[
        match_scoring_sources["Scores"] > 0
    ].copy()


    fig = px.pie(
        pie_data,
        names="Source",
        values="Scores",
        hole=0.38,
    )


    fig.update_traces(
        textposition="inside",
        texttemplate=(
            "%{label}<br>"
            f"%{{value:{value_format}}} · %{{percent:.1%}}"
        ),
        hovertemplate=(
            "<b>%{label}</b><br>"
            f"Scores: %{{value:{value_format}}}<br>"
            "Share: %{percent:.1%}"
            "<extra></extra>"
        ),
        textfont_size=13,
        marker=dict(
            line=dict(
                width=1.5,
            )
        ),
    )


    fig.update_layout(
        height=570,
        uniformtext_minsize=11,
        uniformtext_mode="hide",

        legend=dict(
            font=dict(
                size=14,
            ),
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02,
        ),

        margin=dict(
            l=10,
            r=190,
            t=20,
            b=10,
        ),
    )


    fig.add_annotation(
        text=(
            f"<b>{format_scope_count(total_sources, show_averages)}</b>"
            "<br>Scores"
        ),
        x=0.5,
        y=0.5,
        font_size=18,
        showarrow=False,
    )


    st.plotly_chart(
        fig,
        width="stretch",
    )


# ==========================================================
