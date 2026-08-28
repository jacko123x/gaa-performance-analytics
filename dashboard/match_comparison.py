import pandas as pd
import plotly.express as px
import streamlit as st


AMBER = "#F59E0B"
DARK = "#1F2937"


def _build_comparison_data(
    matches,
    team_data,
    kickout_data,
    turnover_data,
    team_name,
):
    comparison = team_data.copy()

    required_match_columns = [
        "Date",
        "Round",
        "HomeTeam",
        "AwayTeam",
        "HomeScore",
        "AwayScore",
        "Result",
    ]
    missing_columns = [
        column
        for column in required_match_columns
        if column not in comparison.columns
    ]

    if missing_columns:
        comparison = comparison.merge(
            matches[["MatchID", *missing_columns]],
            on="MatchID",
            how="left",
            validate="one_to_one",
        )

    comparison["OpponentLabel"] = comparison.apply(
        lambda row: (
            row["AwayTeam"]
            if row["HomeTeam"] == team_name
            else row["HomeTeam"]
        ),
        axis=1,
    )
    comparison["ScoresFor"] = comparison.apply(
        lambda row: (
            row["HomeScore"]
            if row["HomeTeam"] == team_name
            else row["AwayScore"]
        ),
        axis=1,
    )
    comparison["ScoresAgainst"] = comparison.apply(
        lambda row: (
            row["AwayScore"]
            if row["HomeTeam"] == team_name
            else row["HomeScore"]
        ),
        axis=1,
    )
    comparison["MatchLabel"] = comparison.apply(
        lambda row: (
            f"{row['MatchID']} — {row['OpponentLabel']} — "
            f"{row['Date'].strftime('%d %b %Y')}"
        ),
        axis=1,
    )

    own_kickouts = kickout_data[
        (kickout_data["Period"] == "FT")
        & (kickout_data["KickoutType"] == "Own")
    ][["MatchID", "WinPct"]].rename(
        columns={"WinPct": "OwnKickoutRetentionPct"}
    )

    full_time_turnovers = turnover_data[
        turnover_data["Period"] == "FT"
    ][
        [
            "MatchID",
            "TurnoversWon",
            "TurnoversLost",
            "TurnoverDifferential",
            "ForcedTurnoverPct",
        ]
    ]

    # Use the dedicated turnover file as the single source of truth.
    # Team summary data also contains a derived TurnoversWon column.
    comparison = comparison.drop(
        columns=["TurnoversWon"],
        errors="ignore",
    )

    return (
        comparison.merge(
            own_kickouts,
            on="MatchID",
            how="left",
            validate="one_to_one",
        )
        .merge(
            full_time_turnovers,
            on="MatchID",
            how="left",
            validate="one_to_one",
        )
        .sort_values(["Date", "Round", "MatchID"])
        .reset_index(drop=True)
    )


def _format_value(value, kind):
    if kind == "percentage":
        return f"{value:.1f}%"
    if kind == "decimal":
        return f"{value:.1f}"
    if kind == "signed":
        return f"{value:+.0f}"
    return str(int(value))


def _format_delta(value, kind):
    if kind == "percentage":
        return f"{value:+.1f} pp vs A"
    if kind == "decimal":
        return f"{value:+.1f} vs A"
    return f"{value:+.0f} vs A"


def _render_match_summary(label, row):
    with st.container(border=True):
        st.subheader(label)
        st.markdown(f"**{row['MatchLabel']}**")
        st.caption(
            f"{row['Result']} | "
            f"Score {int(row['ScoresFor'])}–"
            f"{int(row['ScoresAgainst'])} | "
            f"Round {row['Round']}"
        )


def _render_change_metrics(match_a, match_b):
    metric_definitions = [
        (
            "Attacks",
            "Attacks",
            "count",
            "normal",
        ),
        (
            "Shots",
            "TotalShots",
            "count",
            "normal",
        ),
        (
            "Shot conversion",
            "ShotConversionPct",
            "percentage",
            "normal",
        ),
        (
            "Attack → shot",
            "AttackToShotPct",
            "percentage",
            "normal",
        ),
        (
            "Attack → score",
            "AttackToScorePct",
            "percentage",
            "normal",
        ),
        (
            "Own KO retention",
            "OwnKickoutRetentionPct",
            "percentage",
            "normal",
        ),
        (
            "Turnover differential",
            "TurnoverDifferential",
            "signed",
            "normal",
        ),
        (
            "Frees conceded",
            "FreesConceded",
            "count",
            "inverse",
        ),
    ]

    with st.container(horizontal=True):
        for label, column, kind, delta_color in metric_definitions:
            value_a = match_a[column]
            value_b = match_b[column]
            st.metric(
                label,
                _format_value(value_b, kind),
                delta=_format_delta(
                    value_b - value_a,
                    kind,
                ),
                delta_color=delta_color,
                border=True,
                help="Match B value; change is relative to Match A",
            )


def _render_comparison_table(match_a, match_b):
    rows = [
        ("Attacks", "Attacks", "count"),
        ("Shots", "TotalShots", "count"),
        ("Scores", "TotalScores", "count"),
        ("Shot conversion", "ShotConversionPct", "percentage"),
        ("Attack → shot", "AttackToShotPct", "percentage"),
        ("Attack → score", "AttackToScorePct", "percentage"),
        (
            "Own KO retention",
            "OwnKickoutRetentionPct",
            "percentage",
        ),
        ("Turnovers won", "TurnoversWon", "count"),
        ("Turnovers lost", "TurnoversLost", "count"),
        (
            "Turnover differential",
            "TurnoverDifferential",
            "signed",
        ),
        (
            "Forced turnover rate",
            "ForcedTurnoverPct",
            "percentage",
        ),
        ("Frees conceded", "FreesConceded", "count"),
    ]

    comparison_rows = []
    for label, column, kind in rows:
        value_a = match_a[column]
        value_b = match_b[column]
        comparison_rows.append(
            {
                "Metric": label,
                "Match A": _format_value(value_a, kind),
                "Match B": _format_value(value_b, kind),
                "Change": _format_delta(
                    value_b - value_a,
                    kind,
                ).replace(" vs A", ""),
            }
        )

    st.dataframe(
        pd.DataFrame(comparison_rows),
        hide_index=True,
        width="stretch",
        column_config={
            "Metric": st.column_config.TextColumn(
                pinned=True,
            ),
        },
    )


def _build_scoring_source_comparison(
    scoring_sources,
    match_a_id,
    match_b_id,
):
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

    data = scoring_sources[
        scoring_sources["MatchID"].isin(
            [match_a_id, match_b_id]
        )
    ].copy()
    data["Source"] = data["Source"].map(
        source_groups
    ).fillna(data["Source"])
    data = (
        data.groupby(
            ["MatchID", "Source"],
            as_index=False,
        )["Scores"]
        .sum()
    )

    source_order = [
        "Own kickout",
        "Opposition kickout",
        "Turnover",
        "Structured play",
        "Placed balls",
    ]
    full_index = pd.MultiIndex.from_product(
        [
            [match_a_id, match_b_id],
            source_order,
        ],
        names=["MatchID", "Source"],
    )

    return (
        data.set_index(["MatchID", "Source"])
        .reindex(full_index, fill_value=0)
        .reset_index()
    )


def _render_scoring_source_changes(
    scoring_sources,
    match_a,
    match_b,
):
    st.header("Scoring-source changes")

    data = _build_scoring_source_comparison(
        scoring_sources,
        match_a["MatchID"],
        match_b["MatchID"],
    )
    match_names = {
        match_a["MatchID"]: "Match A",
        match_b["MatchID"]: "Match B",
    }
    data["Match"] = data["MatchID"].map(
        match_names
    )

    chart_column, table_column = st.columns(2)

    with chart_column.container(border=True):
        figure = px.bar(
            data,
            x="Source",
            y="Scores",
            color="Match",
            barmode="group",
            title="Scoring origin: Match A vs Match B",
            text_auto=".0f",
            color_discrete_map={
                "Match A": DARK,
                "Match B": AMBER,
            },
        )
        figure.update_layout(
            xaxis_title="Scoring source",
            yaxis_title="Scores",
            legend_title_text="",
            height=470,
        )
        st.plotly_chart(figure, width="stretch")

    pivot = data.pivot(
        index="Source",
        columns="Match",
        values="Scores",
    ).reset_index()
    pivot["Change"] = (
        pivot["Match B"] - pivot["Match A"]
    )

    with table_column.container(border=True):
        st.subheader("Source-by-source change")
        st.dataframe(
            pivot,
            hide_index=True,
            width="stretch",
            column_config={
                "Source": st.column_config.TextColumn(
                    pinned=True,
                ),
                "Match A": st.column_config.NumberColumn(
                    format="%.0f",
                ),
                "Match B": st.column_config.NumberColumn(
                    format="%.0f",
                ),
                "Change": st.column_config.NumberColumn(
                    format="%+.0f",
                ),
            },
        )


def render_match_comparison(
    matches,
    team_data,
    scoring_sources,
    kickout_data,
    turnover_data,
    team_name,
):
    st.header("Match comparison")
    st.caption(
        "Compare Match B with Match A to see what changed"
    )

    comparison = _build_comparison_data(
        matches,
        team_data,
        kickout_data,
        turnover_data,
        team_name,
    )

    if len(comparison) < 2:
        st.info(
            "At least two championship matches are needed for comparison."
        )
        return

    match_labels = comparison.set_index(
        "MatchLabel"
    )["MatchID"].to_dict()
    label_options = list(match_labels)

    selector_a, selector_b = st.columns(2)
    with selector_a:
        match_a_label = st.selectbox(
            "Match A",
            options=label_options,
            index=0,
            key="comparison_match_a",
        )
    with selector_b:
        match_b_label = st.selectbox(
            "Match B",
            options=label_options,
            index=len(label_options) - 1,
            key="comparison_match_b",
        )

    match_a_id = match_labels[match_a_label]
    match_b_id = match_labels[match_b_label]

    if match_a_id == match_b_id:
        st.warning(
            "Choose two different matches to see meaningful changes."
        )
        return

    match_a = comparison.loc[
        comparison["MatchID"] == match_a_id
    ].iloc[0]
    match_b = comparison.loc[
        comparison["MatchID"] == match_b_id
    ].iloc[0]

    summary_a, summary_b = st.columns(2)
    with summary_a:
        _render_match_summary("Match A", match_a)
    with summary_b:
        _render_match_summary("Match B", match_b)

    st.header("Performance changes")
    st.caption(
        "Each card shows Match B; the arrow and delta are relative to Match A."
    )
    _render_change_metrics(match_a, match_b)

    st.subheader("Detailed comparison")
    _render_comparison_table(match_a, match_b)

    _render_scoring_source_changes(
        scoring_sources,
        match_a,
        match_b,
    )
