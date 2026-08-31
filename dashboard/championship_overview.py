from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st


AMBER = "#F59E0B"
DARK_AMBER = "#B45309"
DARK = "#1F2937"
GREY = "#6B7280"

KPI_PALETTE = {
    "strong": {
        "accent": "#22C55E",
        "background": "rgba(34, 197, 94, 0.14)",
        "badge": "rgba(34, 197, 94, 0.24)",
        "label": "Strong",
    },
    "middle": {
        "accent": "#F59E0B",
        "background": "rgba(245, 158, 11, 0.14)",
        "badge": "rgba(245, 158, 11, 0.24)",
        "label": "Middle",
    },
    "review": {
        "accent": "#EF4444",
        "background": "rgba(239, 68, 68, 0.14)",
        "badge": "rgba(239, 68, 68, 0.24)",
        "label": "Review",
    },
    "neutral": {
        "accent": "#3B82F6",
        "background": "rgba(59, 130, 246, 0.12)",
        "badge": "rgba(59, 130, 246, 0.22)",
        "label": "Context",
    },
}


def _format_signed(value, decimals=0):
    return f"{value:+.{decimals}f}"


def _performance_band(
    value,
    strong_threshold,
    middle_threshold,
    higher_is_better=True,
):
    if pd.isna(value):
        return "neutral"
    if higher_is_better:
        if value >= strong_threshold:
            return "strong"
        if value >= middle_threshold:
            return "middle"
    else:
        if value <= strong_threshold:
            return "strong"
        if value <= middle_threshold:
            return "middle"
    return "review"


def _metric_card(label, value, band, note=None):
    palette = KPI_PALETTE[band]
    note_html = (
        f'<div style="font-size:0.75rem;opacity:0.68;margin-top:0.35rem;">'
        f"{escape(note)}</div>"
        if note
        else ""
    )
    st.markdown(
        f"""
<div style="
    min-height:132px;
    padding:1rem 1.05rem;
    border:1px solid {palette['accent']}66;
    border-left:5px solid {palette['accent']};
    border-radius:0.75rem;
    background:{palette['background']};
    box-shadow:0 5px 18px rgba(0, 0, 0, 0.10);
">
    <div style="font-size:0.82rem;font-weight:650;opacity:0.78;">
        {escape(label)}
    </div>
    <div style="font-size:1.8rem;font-weight:750;line-height:1.2;margin-top:0.3rem;">
        {escape(str(value))}
    </div>
    <span style="
        display:inline-block;
        margin-top:0.55rem;
        padding:0.14rem 0.48rem;
        border-radius:999px;
        background:{palette['badge']};
        color:{palette['accent']};
        font-size:0.68rem;
        font-weight:750;
        letter-spacing:0.04em;
        text-transform:uppercase;
    ">{palette['label']}</span>
    {note_html}
</div>
""",
        unsafe_allow_html=True,
    )


def _render_metric_grid(cards, columns_per_row=4):
    for start in range(0, len(cards), columns_per_row):
        row_cards = cards[start:start + columns_per_row]
        columns = st.columns(len(row_cards))
        for column, card in zip(columns, row_cards):
            with column:
                _metric_card(**card)


def _build_match_trends(matches, team_data, team_name):
    match_columns = [
        "MatchID",
        "Date",
        "Round",
        "Venue",
        "HomeTeam",
        "AwayTeam",
        "HomeScore",
        "AwayScore",
        "Result",
    ]

    trends = team_data.copy()

    missing_match_columns = [
        column
        for column in match_columns
        if column != "MatchID"
        and column not in trends.columns
    ]

    if missing_match_columns:
        trends = trends.merge(
            matches[
                ["MatchID", *missing_match_columns]
            ],
            on="MatchID",
            how="left",
            validate="one_to_one",
        )

    trends["OpponentLabel"] = trends.apply(
        lambda row: (
            row["AwayTeam"]
            if row["HomeTeam"] == team_name
            else row["HomeTeam"]
        ),
        axis=1,
    )

    trends["ScoresFor"] = trends.apply(
        lambda row: (
            row["HomeScore"]
            if row["HomeTeam"] == team_name
            else row["AwayScore"]
        ),
        axis=1,
    )

    trends["ScoresAgainst"] = trends.apply(
        lambda row: (
            row["AwayScore"]
            if row["HomeTeam"] == team_name
            else row["HomeScore"]
        ),
        axis=1,
    )

    trends["ScoreDifferential"] = (
        trends["ScoresFor"]
        - trends["ScoresAgainst"]
    )

    trends["Match"] = trends.apply(
        lambda row: (
            f"{row['MatchID']} · {row['OpponentLabel']}"
        ),
        axis=1,
    )

    return trends.sort_values(
        ["Date", "Round", "MatchID"]
    ).reset_index(drop=True)


def _add_match_labels(data, match_trends):
    labels = match_trends[
        ["MatchID", "Match", "Date"]
    ]

    return (
        data.merge(
            labels,
            on="MatchID",
            how="inner",
            validate="many_to_one",
        )
        .sort_values(["Date", "Match"])
    )


def _line_chart(
    data,
    value_columns,
    labels,
    title,
    y_title,
    percentage=False,
):
    chart_data = data[
        ["Match", *value_columns]
    ].rename(columns=labels)

    friendly_columns = [
        labels.get(column, column)
        for column in value_columns
    ]

    chart_data = chart_data.melt(
        id_vars="Match",
        value_vars=friendly_columns,
        var_name="Metric",
        value_name="Value",
    )

    figure = px.line(
        chart_data,
        x="Match",
        y="Value",
        color="Metric",
        markers=True,
        title=title,
        color_discrete_sequence=[
            AMBER,
            DARK,
            DARK_AMBER,
            GREY,
        ],
    )

    figure.update_traces(
        line={"width": 3},
        marker={"size": 9},
    )

    figure.update_layout(
        xaxis_title="Championship match",
        yaxis_title=y_title,
        legend_title_text="",
        hovermode="x unified",
        height=430,
    )

    if percentage:
        figure.update_yaxes(
            ticksuffix="%",
            range=[0, 100],
        )

    return figure


def _render_record(
    match_trends,
    kickout_data,
    turnover_data,
):
    wins = int((match_trends["Result"] == "Win").sum())
    draws = int((match_trends["Result"] == "Draw").sum())
    losses = int((match_trends["Result"] == "Loss").sum())
    average_scores_for = match_trends["ScoresFor"].mean()
    average_scores_against = match_trends[
        "ScoresAgainst"
    ].mean()
    average_score_differential = match_trends[
        "ScoreDifferential"
    ].mean()

    full_time_kickouts = kickout_data[
        kickout_data["Period"] == "FT"
    ]
    own_retention = full_time_kickouts.loc[
        full_time_kickouts["KickoutType"] == "Own",
        "WinPct",
    ].mean()
    opposition_kickouts_won = full_time_kickouts.loc[
        full_time_kickouts["KickoutType"] == "Opponent",
        "WinPct",
    ].mean()

    average_turnover_differential = turnover_data.loc[
        turnover_data["Period"] == "FT",
        "TurnoverDifferential",
    ].mean()
    average_attacks = match_trends["Attacks"].mean()
    shot_conversion = match_trends["ShotConversionPct"].mean()
    attack_to_shot = match_trends["AttackToShotPct"].mean()
    attack_to_score = match_trends["AttackToScorePct"].mean()
    average_frees_conceded = match_trends["FreesConceded"].mean()
    points_per_game = (
        (wins * 3) + draws
    ) / len(match_trends)
    result_band = _performance_band(points_per_game, 2.0, 1.0)
    scoring_band = _performance_band(
        average_score_differential,
        3.0,
        0.0,
    )

    st.subheader("Championship pulse")
    _render_metric_grid(
        [
            {
                "label": "Games played",
                "value": len(match_trends),
                "band": "neutral",
                "note": "Championship sample",
            },
            {
                "label": "W / D / L",
                "value": f"{wins} / {draws} / {losses}",
                "band": result_band,
                "note": f"{points_per_game:.1f} points per game",
            },
            {
                "label": "Avg score for",
                "value": f"{average_scores_for:.1f}",
                "band": scoring_band,
                "note": "Compared with score against",
            },
            {
                "label": "Avg score against",
                "value": f"{average_scores_against:.1f}",
                "band": scoring_band,
                "note": "Lower than score for is positive",
            },
            {
                "label": "Avg scoring differential",
                "value": _format_signed(
                    average_score_differential,
                    decimals=1,
                ),
                "band": scoring_band,
                "note": "For minus against",
            },
        ],
        columns_per_row=3,
    )

    st.subheader("Performance pulse")
    _render_metric_grid(
        [
            {
                "label": "Avg attacks",
                "value": f"{average_attacks:.1f}",
                "band": _performance_band(average_attacks, 30, 25),
                "note": "Volume benchmark",
            },
            {
                "label": "Shot conversion",
                "value": f"{shot_conversion:.1f}%",
                "band": _performance_band(shot_conversion, 65, 50),
            },
            {
                "label": "Attack → shot",
                "value": f"{attack_to_shot:.1f}%",
                "band": _performance_band(attack_to_shot, 75, 65),
            },
            {
                "label": "Attack → score",
                "value": f"{attack_to_score:.1f}%",
                "band": _performance_band(attack_to_score, 50, 40),
            },
            {
                "label": "Own KO retention",
                "value": f"{own_retention:.1f}%",
                "band": _performance_band(own_retention, 70, 60),
            },
            {
                "label": "Opposition KOs won",
                "value": f"{opposition_kickouts_won:.1f}%",
                "band": _performance_band(
                    opposition_kickouts_won,
                    35,
                    25,
                ),
            },
            {
                "label": "Avg turnover differential",
                "value": _format_signed(
                    average_turnover_differential,
                    decimals=1,
                ),
                "band": _performance_band(
                    average_turnover_differential,
                    1,
                    0,
                ),
            },
            {
                "label": "Avg frees conceded",
                "value": f"{average_frees_conceded:.1f}",
                "band": _performance_band(
                    average_frees_conceded,
                    5,
                    8,
                    higher_is_better=False,
                ),
                "note": "Lower is better",
            },
        ]
    )

    st.caption(
        "Green = strong, amber = middle band, red = review. "
        "Rates are arithmetic averages of match-level rates."
    )
    with st.expander("Performance colour benchmarks"):
        st.markdown(
            """
- **Shot conversion:** strong ≥ 65%, middle ≥ 50%.
- **Attack → shot:** strong ≥ 75%, middle ≥ 65%.
- **Attack → score:** strong ≥ 50%, middle ≥ 40%.
- **Own kickout retention:** strong ≥ 70%, middle ≥ 60%.
- **Opposition kickouts won:** strong ≥ 35%, middle ≥ 25%.
- **Turnover differential:** strong ≥ +1, middle ≥ 0.
- **Frees conceded:** strong ≤ 5, middle ≤ 8.
- **Attacks:** strong ≥ 30, middle ≥ 25 per match.
"""
        )


def _render_attack_trends(match_trends):
    st.header("Attack trends")

    volume_column, efficiency_column = st.columns(2)

    with volume_column.container(border=True):
        figure = px.bar(
            match_trends,
            x="Match",
            y="Attacks",
            title="Attacks by match",
            text_auto=".0f",
            color_discrete_sequence=[AMBER],
        )
        figure.update_layout(
            xaxis_title="Championship match",
            yaxis_title="Attacks",
            showlegend=False,
            height=430,
        )
        st.plotly_chart(figure, width="stretch")

    with efficiency_column.container(border=True):
        figure = _line_chart(
            match_trends,
            [
                "AttackToShotPct",
                "AttackToScorePct",
                "ShotConversionPct",
            ],
            {
                "AttackToShotPct": "Attack → shot",
                "AttackToScorePct": "Attack → score",
                "ShotConversionPct": "Shot conversion",
            },
            "Attack efficiency",
            "Rate",
            percentage=True,
        )
        st.plotly_chart(figure, width="stretch")


def _render_shooting_trends(
    match_trends,
    shooting_data,
):
    st.header("Shooting trends")

    conversion_column, misses_column = st.columns(2)

    with conversion_column.container(border=True):
        figure = _line_chart(
            match_trends,
            [
                "ShotConversionPct",
                "PlayConversionPct",
                "PlacedConversionPct",
            ],
            {
                "ShotConversionPct": "Overall",
                "PlayConversionPct": "Open play",
                "PlacedConversionPct": "Placed ball",
            },
            "Conversion by shot type",
            "Conversion",
            percentage=True,
        )
        st.plotly_chart(figure, width="stretch")

    full_time_overall = shooting_data[
        (shooting_data["Period"] == "FT")
        & (shooting_data["ShotType"] == "Overall")
    ].copy()
    full_time_overall = _add_match_labels(
        full_time_overall,
        match_trends,
    )

    miss_columns = [
        "Wides",
        "Shorts",
        "Blocked",
        "Post",
        "Saved",
    ]
    miss_profile = full_time_overall[
        ["Match", *miss_columns]
    ].melt(
        id_vars="Match",
        value_vars=miss_columns,
        var_name="Outcome",
        value_name="Count",
    )

    with misses_column.container(border=True):
        figure = px.bar(
            miss_profile,
            x="Match",
            y="Count",
            color="Outcome",
            barmode="stack",
            title="Miss profile",
            color_discrete_sequence=[
                AMBER,
                DARK_AMBER,
                DARK,
                GREY,
                "#D1D5DB",
            ],
        )
        figure.update_layout(
            xaxis_title="Championship match",
            yaxis_title="Misses",
            legend_title_text="",
            height=430,
        )
        st.plotly_chart(figure, width="stretch")


def _render_possession_trends(
    match_trends,
    kickout_data,
    turnover_data,
):
    st.header("Possession trends")

    kickout_column, turnover_column = st.columns(2)

    full_time_kickouts = kickout_data[
        kickout_data["Period"] == "FT"
    ].copy()
    full_time_kickouts = _add_match_labels(
        full_time_kickouts,
        match_trends,
    )

    kickout_rates = (
        full_time_kickouts.pivot(
            index="Match",
            columns="KickoutType",
            values="WinPct",
        )
        .reindex(match_trends["Match"])
        .reset_index()
        .rename(
            columns={
                "Own": "Own retention",
                "Opponent": "Opposition kickouts won",
            }
        )
    )
    kickout_rates = kickout_rates.reindex(
        columns=[
            "Match",
            "Own retention",
            "Opposition kickouts won",
        ]
    )

    with kickout_column.container(border=True):
        figure = _line_chart(
            kickout_rates,
            [
                "Own retention",
                "Opposition kickouts won",
            ],
            {},
            "Kickout performance",
            "Win rate",
            percentage=True,
        )
        st.plotly_chart(figure, width="stretch")

    full_time_turnovers = turnover_data[
        turnover_data["Period"] == "FT"
    ].copy()
    full_time_turnovers = _add_match_labels(
        full_time_turnovers,
        match_trends,
    )

    with turnover_column.container(border=True):
        figure = _line_chart(
            full_time_turnovers,
            [
                "TurnoversWon",
                "TurnoversLost",
                "TurnoverDifferential",
            ],
            {
                "TurnoversWon": "Won",
                "TurnoversLost": "Lost",
                "TurnoverDifferential": "Differential",
            },
            "Turnover performance",
            "Turnovers",
        )
        figure.add_hline(
            y=0,
            line_dash="dot",
            line_color=GREY,
        )
        st.plotly_chart(figure, width="stretch")

    breakdown_column, forced_column = st.columns(2)

    own_kickouts = full_time_kickouts[
        full_time_kickouts["KickoutType"] == "Own"
    ]
    kickout_breakdown = own_kickouts[
        ["Match", "CleanWins", "BreakWins", "FreeWins"]
    ].melt(
        id_vars="Match",
        var_name="Win type",
        value_name="Wins",
    ).replace(
        {
            "CleanWins": "Clean",
            "BreakWins": "Break",
            "FreeWins": "Free",
        }
    )

    with breakdown_column.container(border=True):
        figure = px.bar(
            kickout_breakdown,
            x="Match",
            y="Wins",
            color="Win type",
            barmode="stack",
            title="How own kickouts were won",
            color_discrete_sequence=[
                AMBER,
                DARK_AMBER,
                GREY,
            ],
        )
        figure.update_layout(
            xaxis_title="Championship match",
            legend_title_text="",
            height=430,
        )
        st.plotly_chart(figure, width="stretch")

    with forced_column.container(border=True):
        figure = _line_chart(
            full_time_turnovers,
            ["ForcedTurnoverPct"],
            {"ForcedTurnoverPct": "Forced turnover rate"},
            "Forced turnover rate",
            "Rate",
            percentage=True,
        )
        figure.update_layout(showlegend=False)
        st.plotly_chart(figure, width="stretch")


def _render_scoring_source_trends(
    match_trends,
    scoring_sources,
):
    st.header("Scoring-source trends")

    source_groups = {
        "Own Kickout": "Own kickout",
        "Opponent Kickout": "Opposition kickout",
        "Turnover": "Turnover",
        "Open / Structured Play": "Structured play",
        "Free": "Placed balls",
        "Mark": "Placed balls",
        "45": "Placed balls",
        "Penalty": "Placed balls",
    }

    sources = scoring_sources.copy()
    sources["Source group"] = sources["Source"].map(
        source_groups
    ).fillna(sources["Source"])
    sources = (
        sources.groupby(
            ["MatchID", "Source group"],
            as_index=False,
        )["Scores"]
        .sum()
    )
    sources = _add_match_labels(
        sources,
        match_trends,
    )

    figure = px.bar(
        sources,
        x="Match",
        y="Scores",
        color="Source group",
        barmode="stack",
        title="Where scores originated",
        text_auto=".0f",
        color_discrete_sequence=[
            AMBER,
            DARK_AMBER,
            DARK,
            GREY,
            "#D1D5DB",
        ],
    )
    figure.update_layout(
        xaxis_title="Championship match",
        yaxis_title="Scores",
        legend_title_text="",
        height=500,
    )
    st.plotly_chart(figure, width="stretch")


def _render_comparison_table(match_trends):
    st.header("Game-to-game comparison")

    comparison = match_trends[
        [
            "Match",
            "Result",
            "ScoresFor",
            "ScoresAgainst",
            "ScoreDifferential",
            "Attacks",
            "AttackToShotPct",
            "AttackToScorePct",
            "ShotConversionPct",
            "KickoutRetentionPct",
        ]
    ].copy()

    st.dataframe(
        comparison,
        hide_index=True,
        width="stretch",
        column_config={
            "Match": st.column_config.TextColumn(
                "Championship match",
                pinned=True,
            ),
            "ScoresFor": st.column_config.NumberColumn(
                "For",
                format="%d",
            ),
            "ScoresAgainst": st.column_config.NumberColumn(
                "Against",
                format="%d",
            ),
            "ScoreDifferential": st.column_config.NumberColumn(
                "Score diff",
                format="%+d",
            ),
            "AttackToShotPct": st.column_config.NumberColumn(
                "Attack → shot",
                format="%.1f%%",
            ),
            "AttackToScorePct": st.column_config.NumberColumn(
                "Attack → score",
                format="%.1f%%",
            ),
            "ShotConversionPct": st.column_config.NumberColumn(
                "Shot conversion",
                format="%.1f%%",
            ),
            "KickoutRetentionPct": st.column_config.NumberColumn(
                "Own KO retention",
                format="%.1f%%",
            ),
        },
    )


def render_championship_overview(
    matches,
    team_data,
    shooting_data,
    scoring_sources,
    kickout_data,
    turnover_data,
    team_name,
):
    st.header("Championship overview")
    st.caption(
        "Season-level performance across every championship match"
    )

    match_trends = _build_match_trends(
        matches,
        team_data,
        team_name,
    )

    if match_trends.empty:
        st.info("No championship matches are available yet.")
        return

    _render_record(
        match_trends,
        kickout_data,
        turnover_data,
    )
    _render_attack_trends(match_trends)
    _render_shooting_trends(
        match_trends,
        shooting_data,
    )
    _render_possession_trends(
        match_trends,
        kickout_data,
        turnover_data,
    )
    _render_scoring_source_trends(
        match_trends,
        scoring_sources,
    )
    _render_comparison_table(match_trends)
