
import plotly.express as px
import streamlit as st

from match_formatting import AMBER, format_scope_count


def render_scoring_sources(match_scoring_sources, show_averages):
    st.header("Scoring Sources")


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


    col1, col2 = st.columns(2)

    col1.metric(
        "Avg Scores" if show_averages else "Scores",
        format_scope_count(
            total_sources,
            show_averages,
        ),
    )

    col2.metric(
        (
            "Avg Scores from Turnovers"
            if show_averages
            else "Scores from Turnovers"
        ),
        format_scope_count(
            turnover_scores,
            show_averages,
        ),
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
        "Scoring Source Distribution"
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
        textinfo="percent+label+value",
        textfont_size=16,
        marker=dict(
            line=dict(
                width=2,
            )
        ),
    )


    fig.update_layout(
        height=720,

        title={
            "text": "Scoring Source Distribution",
            "x": 0.5,
            "xanchor": "center",
            "font": {
                "size": 24,
            },
        },

        legend=dict(
            font=dict(
                size=16,
            ),
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02,
        ),

        margin=dict(
            l=20,
            r=220,
            t=80,
            b=20,
        ),
    )


    fig.add_annotation(
        text=(
            f"<b>{format_scope_count(total_sources, show_averages)}</b>"
            "<br>Scores"
        ),
        x=0.5,
        y=0.5,
        font_size=22,
        showarrow=False,
    )


    st.plotly_chart(
        fig,
        width="stretch",
    )


# ==========================================================
