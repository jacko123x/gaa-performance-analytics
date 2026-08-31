import pandas as pd
import streamlit as st

from match_formatting import AMBER
from match_tabs.attack import render_attack
from match_tabs.kickouts import render_kickouts
from match_tabs.leaders import render_leaders
from match_tabs.overview import render_overview
from match_tabs.players import render_players
from match_tabs.scoring_sources import render_scoring_sources
from match_tabs.shooting import render_shooting
from match_tabs.turnovers import render_turnovers
from metrics import add_player_metrics

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
        column for column in summed_columns if column in players.columns
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


def render_match_analysis(
    *,
    matches,
    team_data,
    shooting_data,
    scoring_sources,
    kickout_data,
    turnover_data,
    player_data,
    team_name,
):
    st.header("Match analysis")


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

        if row.HomeTeam == team_name:
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
    with overview_tab:
        render_overview(
            match_team,
            match_turnovers,
            match_kickouts,
            show_averages,
        )
    with attack_tab:
        render_attack(match_team, show_averages)
    with shooting_tab:
        render_shooting(match_shooting, show_averages)
    with kickout_tab:
        render_kickouts(match_kickouts, show_averages)
    with turnover_tab:
        render_turnovers(match_turnovers, show_averages)
    with scoring_tab:
        render_scoring_sources(match_scoring_sources, show_averages)
    with players_tab:
        render_players(match_players, show_averages)
    with leaders_tab:
        render_leaders(match_players, show_averages)
