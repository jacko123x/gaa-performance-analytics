import pandas as pd
import plotly.express as px
import streamlit as st

from metrics import add_player_metrics


AMBER = "#F59E0B"
DARK = "#1F2937"
GREY = "#6B7280"


SUMMED_COLUMNS = [
    "MinutesPlayed",
    "Possessions",
    "HandpassesTotal",
    "Handpasses1H",
    "Handpasses2H",
    "HandpassesCompleted",
    "FootpassesTotal",
    "Footpasses1H",
    "Footpasses2H",
    "FootpassesCompleted",
    "IncompletePasses",
    "KickoutsWon",
    "BreakingBallsWon",
    "TurnoversWon",
    "TurnoversLost",
    "FreesWon",
    "FreesConceded",
    "Assists",
    "Points",
    "PointsPlay",
    "PointsFree",
    "Points45",
    "Goals",
    "TwoPointers",
    "ShotAttempts",
    "Scores",
    "YellowCards",
    "BlackCards",
    "RedCards",
]


def build_player_championship_summary(player_data):
    """Aggregate player match rows and recalculate season rates."""

    if player_data.empty:
        return player_data.copy()

    available_sums = [
        column
        for column in SUMMED_COLUMNS
        if column in player_data.columns
    ]
    totals = (
        player_data.groupby("PlayerName", as_index=False)[available_sums]
        .sum()
    )

    identity = (
        player_data.sort_values("Date")
        .groupby("PlayerName", as_index=False)
        .agg(
            SquadNumber=("SquadNumber", "last"),
            Position=("Position", "last"),
            Captain=("Captain", "max"),
        )
    )

    appearances = (
        player_data.assign(
            Appeared=player_data["MinutesPlayed"].gt(0)
        )
        .groupby(["PlayerName", "MatchID"], as_index=False)
        .agg(
            Appeared=("Appeared", "max"),
            Started=("Started", "max"),
        )
        .groupby("PlayerName", as_index=False)
        .agg(
            Games=("Appeared", "sum"),
            Starts=("Started", "sum"),
        )
    )

    summary = (
        totals.merge(identity, on="PlayerName", validate="one_to_one")
        .merge(appearances, on="PlayerName", validate="one_to_one")
    )

    summary = add_player_metrics(summary)
    summary["ScoreContributionsPer60"] = (
        summary["ScoreContributions"]
        .div(summary["MinutesPlayed"])
        .mul(60)
        .where(summary["MinutesPlayed"].gt(0))
    )

    return summary.sort_values(
        ["Games", "MinutesPlayed", "PlayerName"],
        ascending=[False, False, True],
    ).reset_index(drop=True)


def _format_pct(value):
    if pd.isna(value):
        return "-"
    return f"{value:.1f}%"


def _format_per_60(value):
    if pd.isna(value):
        return "-"
    return f"{value:.1f}"


def _build_player_trends(player_data, player_name):
    trends = player_data[
        player_data["PlayerName"] == player_name
    ].copy()
    trends = trends.sort_values(["Date", "MatchID"])
    trends["Match"] = (
        trends["MatchID"]
        + " · "
        + trends["Opponent"]
    )
    return trends


def _render_profile_metrics(player):
    with st.container(horizontal=True):
        st.metric(
            "Games / starts",
            f"{int(player['Games'])} / {int(player['Starts'])}",
            border=True,
        )
        st.metric(
            "Minutes",
            f"{int(player['MinutesPlayed'])}",
            border=True,
        )
        st.metric(
            "Possessions",
            f"{int(player['Possessions'])}",
            border=True,
        )
        st.metric(
            "Pass accuracy",
            _format_pct(player["PassAccuracyPct"]),
            border=True,
        )
        st.metric(
            "Turnovers won / lost",
            (
                f"{int(player['TurnoversWon'])} / "
                f"{int(player['TurnoversLost'])}"
            ),
            border=True,
        )

    with st.container(horizontal=True):
        st.metric(
            "Breaking balls",
            f"{int(player['BreakingBallsWon'])}",
            border=True,
        )
        st.metric(
            "Kickouts won",
            f"{int(player['KickoutsWon'])}",
            border=True,
        )
        st.metric(
            "Assists",
            f"{int(player['Assists'])}",
            border=True,
        )
        st.metric(
            "Scores",
            f"{int(player['Scores'])}",
            border=True,
        )
        st.metric(
            "Score value",
            f"{int(player['TotalScoreValue'])}",
            border=True,
            help="Points value including goals and two-pointers",
        )


def _render_per_60_metrics(player):
    st.subheader("Output per 60 minutes")
    with st.container(horizontal=True):
        definitions = [
            ("Possessions", "PossessionsPer60"),
            ("Passes", "PassesPer60"),
            ("Turnovers won", "TurnoversWonPer60"),
            ("Turnovers lost", "TurnoversLostPer60"),
            ("Breaking balls", "BreakingBallsWonPer60"),
            ("Kickouts won", "KickoutsWonPer60"),
            ("Assists", "AssistsPer60"),
            ("Score value", "ScoreValuePer60"),
        ]
        for label, column in definitions:
            st.metric(
                label,
                _format_per_60(player[column]),
                border=True,
            )


def _trend_chart(data, columns, labels, title, percentage=False):
    available = [column for column in columns if column in data.columns]
    chart_data = data[["Match", *available]].melt(
        id_vars="Match",
        var_name="Metric",
        value_name="Value",
    )
    chart_data["Metric"] = chart_data["Metric"].map(labels)

    figure = px.line(
        chart_data,
        x="Match",
        y="Value",
        color="Metric",
        markers=True,
        title=title,
        color_discrete_sequence=[AMBER, DARK, GREY, "#2563EB"],
    )
    figure.update_traces(line={"width": 3}, marker={"size": 9})
    figure.update_layout(
        height=420,
        legend_title_text="",
        xaxis_title="Match",
        yaxis_title="Percentage" if percentage else "Value",
    )
    if percentage:
        figure.update_yaxes(range=[0, 105], ticksuffix="%")
    st.plotly_chart(figure, width="stretch")


def _render_match_trends(trends):
    st.header("Match-by-match trends")
    trend_view = st.segmented_control(
        "Trend view",
        options=["Match totals", "Per 60"],
        default="Match totals",
        key="player_championship_trend_view",
    )

    chart_left, chart_right = st.columns(2)
    if trend_view == "Match totals":
        with chart_left.container(border=True):
            _trend_chart(
                trends,
                ["MinutesPlayed", "Possessions", "TotalPasses"],
                {
                    "MinutesPlayed": "Minutes",
                    "Possessions": "Possessions",
                    "TotalPasses": "Passes",
                },
                "Workload and involvement",
            )
        with chart_right.container(border=True):
            _trend_chart(
                trends,
                ["PassAccuracyPct"],
                {"PassAccuracyPct": "Pass accuracy"},
                "Passing efficiency",
                percentage=True,
            )

        chart_left, chart_right = st.columns(2)
        with chart_left.container(border=True):
            _trend_chart(
                trends,
                [
                    "TurnoversWon",
                    "TurnoversLost",
                    "BreakingBallsWon",
                    "KickoutsWon",
                ],
                {
                    "TurnoversWon": "Turnovers won",
                    "TurnoversLost": "Turnovers lost",
                    "BreakingBallsWon": "Breaking balls",
                    "KickoutsWon": "Kickouts won",
                },
                "Possession and defensive output",
            )
        with chart_right.container(border=True):
            _trend_chart(
                trends,
                ["Assists", "Scores", "TotalScoreValue"],
                {
                    "Assists": "Assists",
                    "Scores": "Scores",
                    "TotalScoreValue": "Score value",
                },
                "Scoring contribution",
            )
    else:
        with chart_left.container(border=True):
            _trend_chart(
                trends,
                ["PossessionsPer60", "PassesPer60"],
                {
                    "PossessionsPer60": "Possessions per 60",
                    "PassesPer60": "Passes per 60",
                },
                "Involvement per 60",
            )
        with chart_right.container(border=True):
            _trend_chart(
                trends,
                [
                    "TurnoversWonPer60",
                    "TurnoversLostPer60",
                    "BreakingBallsWonPer60",
                    "KickoutsWonPer60",
                ],
                {
                    "TurnoversWonPer60": "Turnovers won per 60",
                    "TurnoversLostPer60": "Turnovers lost per 60",
                    "BreakingBallsWonPer60": "Breaking balls per 60",
                    "KickoutsWonPer60": "Kickouts won per 60",
                },
                "Possession output per 60",
            )

        with st.container(border=True):
            _trend_chart(
                trends,
                ["AssistsPer60", "ScoreValuePer60"],
                {
                    "AssistsPer60": "Assists per 60",
                    "ScoreValuePer60": "Score value per 60",
                },
                "Scoring contribution per 60",
            )


def _render_match_log(trends):
    st.subheader("Championship match log")
    display = trends[
        [
            "Match",
            "Result",
            "Started",
            "MinutesPlayed",
            "Possessions",
            "TotalPasses",
            "PassAccuracyPct",
            "TurnoversWon",
            "TurnoversLost",
            "BreakingBallsWon",
            "KickoutsWon",
            "Assists",
            "Scores",
            "TotalScoreValue",
        ]
    ].rename(
        columns={
            "Started": "Start",
            "MinutesPlayed": "Minutes",
            "PassAccuracyPct": "Pass accuracy",
            "TurnoversWon": "TO won",
            "TurnoversLost": "TO lost",
            "BreakingBallsWon": "Breaks won",
            "KickoutsWon": "KOs won",
            "TotalScoreValue": "Score value",
        }
    )
    st.dataframe(
        display,
        hide_index=True,
        width="stretch",
        column_config={
            "Start": st.column_config.CheckboxColumn(),
            "Pass accuracy": st.column_config.NumberColumn(
                format="%.1f%%"
            ),
        },
    )


def _render_squad_table(summary):
    st.header("Championship squad totals")
    st.caption(
        "Totals and rates across all championship matches. "
        "Games count appearances with minutes played."
    )
    display = summary[
        [
            "PlayerName",
            "Position",
            "Games",
            "Starts",
            "MinutesPlayed",
            "Possessions",
            "PassAccuracyPct",
            "TurnoversWon",
            "TurnoversLost",
            "BreakingBallsWon",
            "KickoutsWon",
            "Assists",
            "Scores",
            "TotalScoreValue",
            "PossessionsPer60",
            "TurnoversWonPer60",
            "ScoreValuePer60",
        ]
    ].rename(
        columns={
            "PlayerName": "Player",
            "MinutesPlayed": "Minutes",
            "PassAccuracyPct": "Pass accuracy",
            "TurnoversWon": "TO won",
            "TurnoversLost": "TO lost",
            "BreakingBallsWon": "Breaks won",
            "KickoutsWon": "KOs won",
            "TotalScoreValue": "Score value",
            "PossessionsPer60": "Possessions / 60",
            "TurnoversWonPer60": "TO won / 60",
            "ScoreValuePer60": "Score value / 60",
        }
    )
    st.dataframe(
        display,
        hide_index=True,
        width="stretch",
        column_config={
            "Player": st.column_config.TextColumn(pinned=True),
            "Pass accuracy": st.column_config.NumberColumn(
                format="%.1f%%"
            ),
            "Possessions / 60": st.column_config.NumberColumn(
                format="%.1f"
            ),
            "TO won / 60": st.column_config.NumberColumn(format="%.1f"),
            "Score value / 60": st.column_config.NumberColumn(
                format="%.1f"
            ),
        },
    )


def render_player_championship(player_data):
    st.header("Player championship dashboard")
    st.caption(
        "Player totals, efficiency and match-by-match performance "
        "across the championship"
    )

    if player_data.empty:
        st.info("No championship player data is available yet.")
        return

    summary = build_player_championship_summary(player_data)
    players_used = int(summary["Games"].gt(0).sum())

    with st.container(horizontal=True):
        st.metric(
            "Championship matches",
            f"{player_data['MatchID'].nunique()}",
            border=True,
        )
        st.metric("Players used", f"{players_used}", border=True)
        st.metric(
            "Total player minutes",
            f"{int(summary['MinutesPlayed'].sum())}",
            border=True,
        )

    player_options = sorted(summary["PlayerName"].tolist())
    default_player = summary.iloc[0]["PlayerName"]
    selected_player = st.selectbox(
        "Select player",
        options=player_options,
        index=player_options.index(default_player),
        key="championship_player",
    )
    player = summary[
        summary["PlayerName"] == selected_player
    ].iloc[0]

    st.subheader(f"{selected_player} — {player['Position']}")
    captain_label = " | Captain" if player["Captain"] else ""
    st.caption(
        f"Squad #{int(player['SquadNumber'])}{captain_label} | "
        f"Championship totals"
    )
    _render_profile_metrics(player)
    _render_per_60_metrics(player)

    trends = _build_player_trends(player_data, selected_player)
    _render_match_trends(trends)
    _render_match_log(trends)
    _render_squad_table(summary)
