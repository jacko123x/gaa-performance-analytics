# ==========================================================
# Imports
# ==========================================================

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# ==========================================================
# Project setup
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT / "src"))
sys.path.append(str(PROJECT_ROOT / "dashboard"))


# ==========================================================
# Project imports
# ==========================================================

from load_data import (
    DATASETS,
    DATA_DIR,
    load_matches,
    load_match_summary,
    load_shooting_detail,
    load_scoring_sources,
    load_kickout_stats,
    load_turnover_stats,
    load_player_match_data,
)

from metrics import (
    add_team_metrics,
    add_shooting_metrics,
    add_kickout_metrics,
    add_turnover_metrics,
    add_player_metrics,
)

from championship_overview import (
    render_championship_overview,
)
from match_comparison import render_match_comparison
from player_championship import render_player_championship
from squad_leaderboards import render_squad_leaderboards
from data_quality import render_data_quality
from auth import (
    available_views,
    current_user,
    require_login,
    render_account_controls,
)
from admin import render_admin


# ==========================================================
# Constants
# ==========================================================

TEAM_NAME = "Austin Stacks"

AMBER = "#F59E0B"
DARK_AMBER = "#B45309"
LIGHT_AMBER = "#FCD34D"
DARK = "#1F2937"
GREY = "#6B7280"


# ==========================================================
# Streamlit setup
# ==========================================================

st.set_page_config(
    page_title="Austin Stacks Performance",
    page_icon="🏐",
    layout="wide",
)

if not require_login():
    st.stop()

render_account_controls()
SIGNED_IN_USER = current_user()


# ==========================================================
# Helper functions
# ==========================================================

def format_pct(value):
    if pd.isna(value):
        return "-"
    return f"{value:.1f}%"


def format_number(value, decimals=1):
    if pd.isna(value):
        return "-"
    return f"{value:.{decimals}f}"


def format_signed(value, decimals=0):
    if pd.isna(value):
        return "-"
    return f"{value:+.{decimals}f}"


def format_scope_count(value, show_average=False):
    if pd.isna(value):
        return "-"
    if show_average:
        return format_number(value, decimals=1)
    return str(int(value))


def aggregate_player_matches(players):
    """Combine player rows across selected matches and recalculate rates."""

    if players.empty:
        return players.copy()

    summed_columns = [
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

    available_summed_columns = [
        column
        for column in summed_columns
        if column in players.columns
    ]

    grouped = (
        players.groupby("PlayerName", as_index=False)[
            available_summed_columns
        ]
        .sum()
    )

    identity = (
        players.sort_values("Date")
        .groupby("PlayerName", as_index=False)
        .agg(
            SquadNumber=("SquadNumber", "last"),
            Position=("Position", "last"),
            Captain=("Captain", "max"),
        )
    )

    participation = (
        players.groupby("PlayerName", as_index=False)
        .agg(
            Appearances=("MatchID", "nunique"),
            Starts=("Started", "sum"),
        )
    )

    grouped = (
        grouped.merge(identity, on="PlayerName")
        .merge(participation, on="PlayerName")
    )

    grouped["Started"] = grouped["Starts"] > 0

    return add_player_metrics(grouped)


# ==========================================================
# Load data
# ==========================================================

def dashboard_data_version():
    dataset_keys = [
        "matches",
        "team_stats",
        "shooting",
        "scoring_sources",
        "kickouts",
        "turnovers",
        "player_data",
    ]

    return tuple(
        (
            DATASETS[key],
            (DATA_DIR / DATASETS[key]).stat().st_mtime_ns,
        )
        for key in dataset_keys
    )


@st.cache_data(max_entries=3)
def load_dashboard_data(data_version):
    # The version is part of the cache key, so updated CSVs reload.
    _ = data_version

    matches = load_matches()

    team = add_team_metrics(
        load_match_summary()
    )

    shooting = add_shooting_metrics(
        load_shooting_detail()
    )

    scoring_sources = load_scoring_sources()

    kickouts = add_kickout_metrics(
        load_kickout_stats()
    )

    turnovers = add_turnover_metrics(
        load_turnover_stats()
    )

    players = add_player_metrics(
        load_player_match_data()
    )

    return (
        matches,
        team,
        shooting,
        scoring_sources,
        kickouts,
        turnovers,
        players,
    )


try:

    (
        matches,
        team_data,
        shooting_data,
        scoring_sources,
        kickout_data,
        turnover_data,
        player_data,
    ) = load_dashboard_data(
        dashboard_data_version()
    )

except Exception as error:

    st.error(
        f"Error loading dashboard data: {error}"
    )

    st.stop()


# ==========================================================
# Filter Austin Stacks
# ==========================================================

team_data = team_data[
    team_data["Team"] == TEAM_NAME
].copy()

shooting_data = shooting_data[
    shooting_data["Team"] == TEAM_NAME
].copy()

scoring_sources = scoring_sources[
    scoring_sources["Team"] == TEAM_NAME
].copy()

kickout_data = kickout_data[
    kickout_data["Team"] == TEAM_NAME
].copy()

turnover_data = turnover_data[
    turnover_data["Team"] == TEAM_NAME
].copy()


# ==========================================================
# Header
# ==========================================================

st.title("Austin Stacks Performance Platform")

st.caption(
    "Club Championship 2026"
)


# ==========================================================
# Analysis view
# ==========================================================

analysis_view = st.sidebar.selectbox(
    "Analysis view",
    options=available_views(SIGNED_IN_USER["role"]),
)

if analysis_view == "Championship overview":
    render_championship_overview(
        matches=matches,
        team_data=team_data,
        shooting_data=shooting_data,
        scoring_sources=scoring_sources,
        kickout_data=kickout_data,
        turnover_data=turnover_data,
        team_name=TEAM_NAME,
    )
    st.stop()

if analysis_view == "Player championship":
    render_player_championship(player_data)
    st.stop()

if analysis_view == "My player profile":
    render_player_championship(
        player_data,
        fixed_player=SIGNED_IN_USER["player_name"],
        show_squad_table=False,
    )
    st.stop()

if analysis_view == "Squad leaderboards":
    render_squad_leaderboards(player_data)
    st.stop()

if analysis_view == "Match comparison":
    render_match_comparison(
        matches=matches,
        team_data=team_data,
        scoring_sources=scoring_sources,
        kickout_data=kickout_data,
        turnover_data=turnover_data,
        team_name=TEAM_NAME,
    )
    st.stop()

if analysis_view == "Data quality":
    render_data_quality(
        matches=matches,
        team_data=team_data,
        shooting_data=shooting_data,
        scoring_sources=scoring_sources,
        kickout_data=kickout_data,
        turnover_data=turnover_data,
        player_data=player_data,
        team_name=TEAM_NAME,
    )
    st.stop()

if analysis_view == "Admin":
    render_admin(
        matches=matches,
        player_data=player_data,
        team_name=TEAM_NAME,
    )
    st.stop()

st.header("Match analysis")


# ==========================================================
# Match selector
# ==========================================================

match_options = matches[
    [
        "MatchID",
        "Date",
        "AwayTeam",
        "HomeTeam",
    ]
].copy()


match_labels = {}

for row in match_options.itertuples():

    if row.HomeTeam == TEAM_NAME:
        opponent = row.AwayTeam
    else:
        opponent = row.HomeTeam

    label = (
        f"{row.MatchID} — "
        f"{opponent} — "
        f"{row.Date.strftime('%d %b %Y')}"
    )

    match_labels[label] = row.MatchID


all_matches_label = "All matches — averages"

selected_match_label = st.sidebar.selectbox(
    "Select match",
    options=[
        all_matches_label,
        *match_labels.keys(),
    ],
)

if selected_match_label == all_matches_label:
    selected_match_ids = matches[
        "MatchID"
    ].drop_duplicates().tolist()
else:
    selected_match_ids = [
        match_labels[selected_match_label]
    ]

show_averages = len(selected_match_ids) > 1


# ==========================================================
# Filter datasets to selected match
# ==========================================================

match_team = team_data[
    team_data["MatchID"].isin(selected_match_ids)
].copy()

match_shooting = shooting_data[
    shooting_data["MatchID"].isin(selected_match_ids)
].copy()

match_scoring_sources = scoring_sources[
    scoring_sources["MatchID"].isin(
        selected_match_ids
    )
].copy()

match_kickouts = kickout_data[
    kickout_data["MatchID"].isin(selected_match_ids)
].copy()

match_turnovers = turnover_data[
    turnover_data["MatchID"].isin(selected_match_ids)
].copy()

match_players = player_data[
    player_data["MatchID"].isin(selected_match_ids)
].copy()

if show_averages:
    match_team = pd.DataFrame(
        [match_team.mean(numeric_only=True)]
    )

    match_shooting = (
        match_shooting.groupby(
            ["Team", "Period", "ShotType"],
            as_index=False,
        )
        .mean(numeric_only=True)
    )

    match_scoring_sources = (
        match_scoring_sources.groupby(
            ["Team", "Source"],
            as_index=False,
        )["Scores"]
        .mean()
    )

    match_kickouts = (
        match_kickouts.groupby(
            ["Team", "Period", "KickoutType"],
            as_index=False,
        )
        .mean(numeric_only=True)
    )

    match_turnovers = (
        match_turnovers.groupby(
            ["Team", "Period"],
            as_index=False,
        )
        .mean(numeric_only=True)
    )

    match_players = aggregate_player_matches(
        match_players
    )
else:
    selected_match_id = selected_match_ids[0]

    match_info = matches[
        matches["MatchID"] == selected_match_id
    ].iloc[0]


# ==========================================================
# Match scoreline
# ==========================================================

if show_averages:
    st.subheader("All selected matches")
    st.caption(
        f"{len(selected_match_ids)} matches selected | "
        "Team figures are per-match averages. "
        "Player figures are totals across the selection."
    )
else:
    home_team = match_info["HomeTeam"]
    away_team = match_info["AwayTeam"]

    home_team_stats = match_team[
        match_team["Team"] == home_team
    ]

    away_team_stats = match_team[
        match_team["Team"] == away_team
    ]


    if not home_team_stats.empty:

        home_goals = int(
            home_team_stats["Goals"].iloc[0]
        )

        home_points_display = int(
            home_team_stats["Points"].iloc[0]
            + (
                home_team_stats[
                    "TwoPointers"
                ].iloc[0] * 2
            )
        )

        home_score_display = (
            f"{home_goals}-{home_points_display}"
        )

    else:

        home_score_display = str(
            match_info["HomeScore"]
        )


    if not away_team_stats.empty:

        away_goals = int(
            away_team_stats["Goals"].iloc[0]
        )

        away_points_display = int(
            away_team_stats["Points"].iloc[0]
            + (
                away_team_stats[
                    "TwoPointers"
                ].iloc[0] * 2
            )
        )

        away_score_display = (
            f"{away_goals}-{away_points_display}"
        )

    else:

        away_score_display = (
            f"0-{int(match_info['AwayScore'])}"
        )


    st.markdown(
        f"""
    <div style="
        text-align:center;
        margin-top:10px;
        margin-bottom:5px;
    ">
        <div style="
            font-size:32px;
            font-weight:700;
        ">
            {home_team}
            &nbsp;
            <span style="color:{AMBER};">
                {home_score_display}
            </span>
            &nbsp;&nbsp;—&nbsp;&nbsp;
            <span style="color:{AMBER};">
                {away_score_display}
            </span>
            &nbsp;
            {away_team}
        </div>
    </div>
        """,
        unsafe_allow_html=True,
    )


    st.caption(
        f"{match_info['Competition']} | "
        f"Round {match_info['Round']} | "
        f"{match_info['Venue']} | "
        f"{match_info['Date'].strftime('%d %B %Y')}"
    )


# ==========================================================
# Main tabs
# ==========================================================

(
    overview_tab,
    attack_tab,
    shooting_tab,
    kickout_tab,
    turnover_tab,
    scoring_tab,
    players_tab,
    leaders_tab,
) = st.tabs(
    [
        "Overview",
        "Attack",
        "Shooting",
        "Kickouts",
        "Turnovers",
        "Scoring Sources",
        "Players",
        "Squad Leaders",
    ]
)


# ==========================================================
# OVERVIEW
# ==========================================================

with overview_tab:

    st.header(
        "Selected Match Averages"
        if show_averages
        else "Match Overview"
    )

    if match_team.empty:

        st.warning(
            "No team data available for this match."
        )

    else:

        row = match_team.iloc[0]

        turnover_ft = match_turnovers[
            match_turnovers["Period"] == "FT"
        ]

        if not turnover_ft.empty:

            turnover_diff = turnover_ft[
                "TurnoverDifferential"
            ].iloc[0]

        else:

            turnover_diff = None


        own_ko = match_kickouts[
            (
                match_kickouts["Period"] == "FT"
            )
            &
            (
                match_kickouts["KickoutType"] == "Own"
            )
        ]


        opp_ko = match_kickouts[
            (
                match_kickouts["Period"] == "FT"
            )
            &
            (
                match_kickouts["KickoutType"]
                == "Opponent"
            )
        ]


        own_ko_pct = (
            own_ko["WinPct"].iloc[0]
            if not own_ko.empty
            else None
        )


        opp_ko_pct = (
            opp_ko["WinPct"].iloc[0]
            if not opp_ko.empty
            else None
        )


        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Avg Attacks" if show_averages else "Attacks",
            format_scope_count(
                row["Attacks"],
                show_averages,
            ),
        )

        col2.metric(
            "Attack → Shot",
            format_pct(
                row["AttackToShotPct"]
            ),
        )

        col3.metric(
            "Attack → Score",
            format_pct(
                row["AttackToScorePct"]
            ),
        )

        col4.metric(
            "Shot Conversion",
            format_pct(
                row["ShotConversionPct"]
            ),
        )


        col5, col6, col7, col8 = st.columns(4)

        col5.metric(
            (
                "Avg Empty Attacks"
                if show_averages
                else "Empty Attacks"
            ),
            format_scope_count(
                row["EmptyAttacks"],
                show_averages,
            ),
        )

        col6.metric(
            "Own KO Retention",
            format_pct(
                own_ko_pct
            ),
        )

        col7.metric(
            "Opp KO Won",
            format_pct(
                opp_ko_pct
            ),
        )

        col8.metric(
            "Turnover Diff",
            (
                format_signed(
                    turnover_diff
                )
                if turnover_diff is not None
                else "-"
            ),
        )


        st.divider()

        st.subheader("Match Performance")

        overview_metrics = pd.DataFrame(
            {
                "Metric": [
                    "Attacks",
                    "Shots",
                    "Scores",
                    "Empty Attacks",
                ],
                "Value": [
                    row["Attacks"],
                    row["TotalShots"],
                    row["TotalScores"],
                    row["EmptyAttacks"],
                ],
            }
        )

        fig = px.bar(
            overview_metrics,
            x="Metric",
            y="Value",
            title="Attacking Output",
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
# ATTACK
# ==========================================================

with attack_tab:

    st.header(
        "Average Attack Efficiency"
        if show_averages
        else "Attack Efficiency"
    )

    if not match_team.empty:

        row = match_team.iloc[0]

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Attack → Shot",
            format_pct(
                row["AttackToShotPct"]
            ),
        )

        col2.metric(
            "Attack → Score",
            format_pct(
                row["AttackToScorePct"]
            ),
        )

        col3.metric(
            "Shot Conversion",
            format_pct(
                row["ShotConversionPct"]
            ),
        )


        st.subheader("Attack Funnel")

        funnel_data = pd.DataFrame(
            {
                "Stage": [
                    "Attacks",
                    "Shots",
                    "Scores",
                ],
                "Count": [
                    row["Attacks"],
                    row["TotalShots"],
                    row["TotalScores"],
                ],
            }
        )

        fig = px.funnel(
            funnel_data,
            x="Count",
            y="Stage",
            title="Attack → Shot → Score",
            color_discrete_sequence=[AMBER],
        )

        fig.update_layout(
            height=500,
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )


        st.subheader(
            "Open Play vs Placed Ball"
        )

        conversion_data = pd.DataFrame(
            {
                "Type": [
                    "Overall",
                    "Play",
                    "Placed",
                ],
                "Conversion": [
                    row["ShotConversionPct"],
                    row["PlayConversionPct"],
                    row["PlacedConversionPct"],
                ],
            }
        )

        fig = px.bar(
            conversion_data,
            x="Type",
            y="Conversion",
            title="Shot Conversion %",
            color_discrete_sequence=[AMBER],
            text_auto=".1f",
        )

        fig.update_layout(
            yaxis_title="Conversion %",
            showlegend=False,
            height=450,
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )


# ==========================================================
# SHOOTING
# ==========================================================

with shooting_tab:

    st.header("Shooting Analysis")


    period_selection = st.radio(
        "Period",
        options=[
            "FT",
            "1H",
            "2H",
        ],
        horizontal=True,
    )


    period_shooting = match_shooting[
        match_shooting["Period"]
        == period_selection
    ].copy()


    overall_shooting = period_shooting[
        period_shooting["ShotType"]
        == "Overall"
    ]


    if not overall_shooting.empty:

        row = overall_shooting.iloc[0]

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Avg Shots" if show_averages else "Shots",
            format_scope_count(
                row["ShotsTaken"],
                show_averages,
            ),
        )

        col2.metric(
            "Avg Scores" if show_averages else "Scores",
            format_scope_count(
                row["ShotsScored"],
                show_averages,
            ),
        )

        col3.metric(
            "Conversion",
            format_pct(
                row["ShotConversionPct"]
            ),
        )

        col4.metric(
            "Avg Misses" if show_averages else "Misses",
            format_scope_count(
                row["Misses"],
                show_averages,
            ),
        )


    shot_types = period_shooting[
        period_shooting["ShotType"]
        != "Overall"
    ].copy()


    if not shot_types.empty:

        st.subheader(
            "Conversion by Shot Type"
        )

        fig = px.bar(
            shot_types,
            x="ShotType",
            y="ShotConversionPct",
            title="Shot Type Conversion %",
            color_discrete_sequence=[AMBER],
            hover_data=[
                "ShotsTaken",
                "ShotsScored",
            ],
        )

        fig.update_layout(
            yaxis_title="Conversion %",
            showlegend=False,
            height=450,
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )


    if not overall_shooting.empty:

        st.subheader("Miss Analysis")

        miss_data = pd.DataFrame(
            {
                "Outcome": [
                    "Wide",
                    "Short",
                    "Blocked",
                    "Post",
                    "Saved",
                ],
                "Count": [
                    row["Wides"],
                    row["Shorts"],
                    row["Blocked"],
                    row["Post"],
                    row["Saved"],
                ],
            }
        )

        fig = px.bar(
            miss_data,
            x="Outcome",
            y="Count",
            title="Missed Shot Outcomes",
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
# KICKOUTS
# ==========================================================

with kickout_tab:

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
# TURNOVERS
# ==========================================================

with turnover_tab:

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
# SCORING SOURCES
# ==========================================================

with scoring_tab:

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
# PLAYERS
# ==========================================================

with players_tab:

    st.header("Player Performance")

    if match_players.empty:

        st.warning(
            "No player data available for this match."
        )

    else:

        player_options = sorted(
            match_players[
                "PlayerName"
            ]
            .dropna()
            .unique()
            .tolist()
        )


        selected_player = st.selectbox(
            "Select Player",
            options=player_options,
        )


        player_row = match_players[
            match_players["PlayerName"]
            == selected_player
        ].iloc[0]


        # --------------------------------------------------
        # Player header
        # --------------------------------------------------

        st.subheader(
            f"{selected_player} "
            f"— {player_row['Position']}"
        )

        if show_averages:
            st.caption(
                f"Squad #{int(player_row['SquadNumber'])} | "
                f"{int(player_row['Appearances'])} appearances | "
                f"{int(player_row['Starts'])} starts | "
                f"{int(player_row['MinutesPlayed'])} total minutes"
            )
        else:
            player_status = (
                "Starter"
                if player_row["Started"]
                else "Substitute"
            )

            st.caption(
                f"Squad #{int(player_row['SquadNumber'])} | "
                f"{player_status} | "
                f"{int(player_row['MinutesPlayed'])} minutes"
            )


        # --------------------------------------------------
        # Main KPI row
        # --------------------------------------------------

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Possessions",
            int(
                player_row["Possessions"]
            ),
        )

        col2.metric(
            "Total Passes",
            int(
                player_row["TotalPasses"]
            ),
        )

        col3.metric(
            "Pass Accuracy",
            format_pct(
                player_row[
                    "PassAccuracyPct"
                ]
            ),
        )

        col4.metric(
            "Turnover Diff",
            format_signed(
                player_row[
                    "TurnoverDifferential"
                ]
            ),
        )


        col5, col6, col7, col8 = st.columns(4)

        col5.metric(
            "Breaking Balls Won",
            int(
                player_row[
                    "BreakingBallsWon"
                ]
            ),
        )

        col6.metric(
            "Kickouts Won",
            int(
                player_row[
                    "KickoutsWon"
                ]
            ),
        )

        col7.metric(
            "Assists",
            int(
                player_row["Assists"]
            ),
        )

        col8.metric(
            "Score Value",
            int(
                player_row[
                    "TotalScoreValue"
                ]
            ),
        )


        st.divider()


        # --------------------------------------------------
        # Passing profile
        # --------------------------------------------------

        st.subheader(
            "Passing Profile"
        )

        pass_col1, pass_col2 = st.columns(2)


        with pass_col1:

            passing_data = pd.DataFrame(
                {
                    "Pass Type": [
                        "Handpass",
                        "Footpass",
                    ],
                    "Attempted": [
                        player_row[
                            "HandpassesTotal"
                        ],
                        player_row[
                            "FootpassesTotal"
                        ],
                    ],
                    "Completed": [
                        player_row[
                            "HandpassesCompleted"
                        ],
                        player_row[
                            "FootpassesCompleted"
                        ],
                    ],
                }
            )


            fig = px.bar(
                passing_data,
                x="Pass Type",
                y=[
                    "Attempted",
                    "Completed",
                ],
                barmode="group",
                title="Pass Volume",
                color_discrete_sequence=[
                    AMBER,
                    DARK,
                ],
            )

            fig.update_layout(
                height=450,
                legend_title_text="",
            )

            st.plotly_chart(
                fig,
                width="stretch",
            )


        with pass_col2:

            accuracy_data = pd.DataFrame(
                {
                    "Pass Type": [
                        "Overall",
                        "Handpass",
                        "Footpass",
                    ],
                    "Accuracy": [
                        player_row[
                            "PassAccuracyPct"
                        ],
                        player_row[
                            "HandpassAccuracyPct"
                        ],
                        player_row[
                            "FootpassAccuracyPct"
                        ],
                    ],
                }
            )


            fig = px.bar(
                accuracy_data,
                x="Pass Type",
                y="Accuracy",
                title="Pass Accuracy %",
                color_discrete_sequence=[
                    AMBER
                ],
                text_auto=".1f",
            )

            fig.update_layout(
                height=450,
                yaxis_title="Accuracy %",
                showlegend=False,
            )

            st.plotly_chart(
                fig,
                width="stretch",
            )


        # --------------------------------------------------
        # Possession contribution
        # --------------------------------------------------

        st.subheader(
            "Possession Contribution"
        )


        possession_data = pd.DataFrame(
            {
                "Metric": [
                    "Possessions",
                    "Turnovers Won",
                    "Turnovers Lost",
                    "Breaking Balls",
                    "Kickouts Won",
                    "Frees Won",
                ],
                "Value": [
                    player_row[
                        "Possessions"
                    ],
                    player_row[
                        "TurnoversWon"
                    ],
                    player_row[
                        "TurnoversLost"
                    ],
                    player_row[
                        "BreakingBallsWon"
                    ],
                    player_row[
                        "KickoutsWon"
                    ],
                    player_row[
                        "FreesWon"
                    ],
                ],
            }
        )


        fig = px.bar(
            possession_data,
            x="Metric",
            y="Value",
            title="Possession & Defensive Contribution",
            color_discrete_sequence=[
                AMBER
            ],
            text="Value",
        )

        fig.update_traces(
            textposition="outside",
        )

        fig.update_layout(
            height=450,
            showlegend=False,
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )


        # --------------------------------------------------
        # Scoring profile
        # --------------------------------------------------

        st.subheader(
            "Scoring Profile"
        )


        score_col1, score_col2 = st.columns(
            2
        )


        with score_col1:

            scoring_data = pd.DataFrame(
                {
                    "Type": [
                        "From Play",
                        "Free",
                        "45",
                        "Goals",
                        "Two Pointers",
                    ],
                    "Value": [
                        player_row[
                            "PointsPlay"
                        ],
                        player_row[
                            "PointsFree"
                        ],
                        player_row[
                            "Points45"
                        ],
                        player_row[
                            "Goals"
                        ],
                        player_row[
                            "TwoPointers"
                        ],
                    ],
                }
            )


            fig = px.bar(
                scoring_data,
                x="Type",
                y="Value",
                title="Scoring Breakdown",
                color_discrete_sequence=[
                    AMBER
                ],
                text="Value",
            )

            fig.update_layout(
                height=450,
                showlegend=False,
            )

            st.plotly_chart(
                fig,
                width="stretch",
            )


        with score_col2:

            shot_data = pd.DataFrame(
                {
                    "Metric": [
                        "Attempts",
                        "Scores",
                    ],
                    "Value": [
                        player_row[
                            "ShotAttempts"
                        ],
                        player_row[
                            "Scores"
                        ],
                    ],
                }
            )


            fig = px.bar(
                shot_data,
                x="Metric",
                y="Value",
                title=(
                    "Shot Output — "
                    f"{format_pct(
                        player_row[
                            'CalculatedShotConversionPct'
                        ]
                    )}"
                ),
                color_discrete_sequence=[
                    AMBER,
                    DARK,
                ],
                text="Value",
            )

            fig.update_layout(
                height=450,
                showlegend=False,
            )

            st.plotly_chart(
                fig,
                width="stretch",
            )


        # --------------------------------------------------
        # Per 60 metrics
        # --------------------------------------------------

        st.subheader(
            "Per 60 Minute Output"
        )


        per60_data = pd.DataFrame(
            {
                "Metric": [
                    "Possessions",
                    "Passes",
                    "Turnovers Won",
                    "Breaking Balls",
                    "Assists",
                    "Score Value",
                ],
                "Per60": [
                    player_row[
                        "PossessionsPer60"
                    ],
                    player_row[
                        "PassesPer60"
                    ],
                    player_row[
                        "TurnoversWonPer60"
                    ],
                    player_row[
                        "BreakingBallsWonPer60"
                    ],
                    player_row[
                        "AssistsPer60"
                    ],
                    player_row[
                        "ScoreValuePer60"
                    ],
                ],
            }
        )


        fig = px.bar(
            per60_data,
            x="Metric",
            y="Per60",
            title="Output per 60 Minutes",
            color_discrete_sequence=[
                AMBER
            ],
            text_auto=".1f",
        )

        fig.update_layout(
            height=450,
            showlegend=False,
            yaxis_title="Per 60",
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )


        # --------------------------------------------------
        # Player data table
        # --------------------------------------------------

        st.subheader(
            "Selected Match Totals"
            if show_averages
            else "Match Stats"
        )


        player_display_columns = [
            "PlayerName",
            "Position",
            "MinutesPlayed",
            "Possessions",
            "TotalPasses",
            "CompletedPasses",
            "PassAccuracyPct",
            "TurnoversWon",
            "TurnoversLost",
            "BreakingBallsWon",
            "KickoutsWon",
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
            "CalculatedShotConversionPct",
        ]


        player_display = pd.DataFrame(
            [player_row[
                player_display_columns
            ]]
        )


        player_display[
            "PassAccuracyPct"
        ] = player_display[
            "PassAccuracyPct"
        ].map(format_pct)


        player_display[
            "CalculatedShotConversionPct"
        ] = player_display[
            "CalculatedShotConversionPct"
        ].map(format_pct)


        st.dataframe(
            player_display,
            hide_index=True,
            width="stretch",
        )


# ==========================================================
# SQUAD LEADERS
# ==========================================================

with leaders_tab:

    st.header(
        "Squad Leaders — Selected Match Totals"
        if show_averages
        else "Squad Leaders"
    )


    if match_players.empty:

        st.warning(
            "No player data available for this match."
        )

    else:

        # Players with game time only
        active_players = match_players[
            match_players[
                "MinutesPlayed"
            ] > 0
        ].copy()


        metric_options = {
            "Possessions": "Possessions",
            "Total Passes": "TotalPasses",
            "Pass Accuracy %": "PassAccuracyPct",
            "Handpass Accuracy %": "HandpassAccuracyPct",
            "Footpass Accuracy %": "FootpassAccuracyPct",
            "Turnovers Won": "TurnoversWon",
            "Turnover Differential": "TurnoverDifferential",
            "Breaking Balls Won": "BreakingBallsWon",
            "Kickouts Won": "KickoutsWon",
            "Frees Won": "FreesWon",
            "Assists": "Assists",
            "Score Value": "TotalScoreValue",
            "Shot Conversion %": "CalculatedShotConversionPct",
            "Possessions per 60": "PossessionsPer60",
            "Passes per 60": "PassesPer60",
            "Turnovers Won per 60": "TurnoversWonPer60",
            "Score Value per 60": "ScoreValuePer60",
        }


        selected_metric_label = st.selectbox(
            "Leaderboard Metric",
            options=list(
                metric_options.keys()
            ),
        )


        selected_metric = metric_options[
            selected_metric_label
        ]


        # --------------------------------------------------
        # Special filters
        # --------------------------------------------------

        comparison_data = active_players.copy()


        if selected_metric in [
            "PassAccuracyPct",
            "HandpassAccuracyPct",
            "FootpassAccuracyPct",
        ]:

            min_passes = st.slider(
                "Minimum passes attempted",
                min_value=0,
                max_value=max(
                    1,
                    int(
                        active_players[
                            "TotalPasses"
                        ].max()
                    ),
                ),
                value=5,
            )

            comparison_data = (
                comparison_data[
                    comparison_data[
                        "TotalPasses"
                    ] >= min_passes
                ]
            )


        if selected_metric == (
            "CalculatedShotConversionPct"
        ):

            min_shots = st.slider(
                "Minimum shot attempts",
                min_value=1,
                max_value=max(
                    1,
                    int(
                        active_players[
                            "ShotAttempts"
                        ].max()
                    ),
                ),
                value=1,
            )

            comparison_data = (
                comparison_data[
                    comparison_data[
                        "ShotAttempts"
                    ] >= min_shots
                ]
            )


        leaderboard = (
            comparison_data[
                [
                    "PlayerName",
                    "Position",
                    "MinutesPlayed",
                    selected_metric,
                ]
            ]
            .dropna(
                subset=[
                    selected_metric
                ]
            )
            .sort_values(
                selected_metric,
                ascending=False,
            )
        )


        if leaderboard.empty:

            st.warning(
                "No players meet the selected criteria."
            )

        else:

            # --------------------------------------------------
            # Top 3 cards
            # --------------------------------------------------

            top_three = leaderboard.head(3)

            top_columns = st.columns(
                min(
                    3,
                    len(top_three),
                )
            )


            for index, (_, player) in enumerate(
                top_three.iterrows()
            ):

                value = player[
                    selected_metric
                ]

                if "Pct" in selected_metric:

                    display_value = (
                        format_pct(value)
                    )

                else:

                    display_value = (
                        format_number(
                            value,
                            1,
                        )
                    )


                top_columns[index].metric(
                    player[
                        "PlayerName"
                    ],
                    display_value,
                )


            # --------------------------------------------------
            # Leaderboard chart
            # --------------------------------------------------

            chart_data = (
                leaderboard
                .head(15)
                .sort_values(
                    selected_metric,
                    ascending=True,
                )
            )


            fig = px.bar(
                chart_data,
                x=selected_metric,
                y="PlayerName",
                orientation="h",
                title=selected_metric_label,
                color_discrete_sequence=[
                    AMBER
                ],
                hover_data=[
                    "Position",
                    "MinutesPlayed",
                ],
                text=selected_metric,
            )


            fig.update_traces(
                textposition="outside",
            )


            fig.update_layout(
                height=650,
                yaxis_title="Player",
                xaxis_title=(
                    selected_metric_label
                ),
                showlegend=False,
            )


            st.plotly_chart(
                fig,
                width="stretch",
            )


            # --------------------------------------------------
            # Leaderboard table
            # --------------------------------------------------

            table_data = leaderboard.copy()

            table_data.insert(
                0,
                "Rank",
                range(
                    1,
                    len(table_data) + 1,
                ),
            )


            if "Pct" in selected_metric:

                table_data[
                    selected_metric
                ] = table_data[
                    selected_metric
                ].map(
                    format_pct
                )


            st.dataframe(
                table_data,
                hide_index=True,
                width="stretch",
            )
