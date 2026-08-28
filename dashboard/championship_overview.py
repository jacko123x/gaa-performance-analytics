import pandas as pd
import plotly.express as px
import streamlit as st


AMBER = "#F59E0B"
DARK_AMBER = "#B45309"
DARK = "#1F2937"
GREY = "#6B7280"


def _format_signed(value, decimals=0):
    return f"{value:+.{decimals}f}"


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

    with st.container(horizontal=True):
        st.metric(
            "Games played",
            len(match_trends),
            border=True,
        )
        st.metric(
            "W / D / L",
            f"{wins} / {draws} / {losses}",
            help="Wins–draws–losses",
            border=True,
        )
        st.metric(
            "Avg score for",
            f"{average_scores_for:.1f}",
            border=True,
        )
        st.metric(
            "Avg score against",
            f"{average_scores_against:.1f}",
            border=True,
        )
        st.metric(
            "Avg scoring differential",
            _format_signed(
                average_score_differential,
                decimals=1,
            ),
            border=True,
        )

    with st.container(horizontal=True):
        st.metric(
            "Avg attacks",
            f"{match_trends['Attacks'].mean():.1f}",
            border=True,
        )
        st.metric(
            "Shot conversion",
            f"{match_trends['ShotConversionPct'].mean():.1f}%",
            border=True,
        )
        st.metric(
            "Attack → shot",
            f"{match_trends['AttackToShotPct'].mean():.1f}%",
            border=True,
        )
        st.metric(
            "Attack → score",
            f"{match_trends['AttackToScorePct'].mean():.1f}%",
            border=True,
        )
        st.metric(
            "Own KO retention",
            f"{own_retention:.1f}%",
            border=True,
        )
        st.metric(
            "Opposition KOs won",
            f"{opposition_kickouts_won:.1f}%",
            border=True,
        )
        st.metric(
            "Avg turnover differential",
            _format_signed(
                average_turnover_differential,
                decimals=1,
            ),
            border=True,
        )
        st.metric(
            "Avg frees conceded",
            f"{match_trends['FreesConceded'].mean():.1f}",
            border=True,
        )

    st.caption(
        "Rates are arithmetic averages of the selected match-level rates."
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
