import numbers

import pandas as pd


RESULT_COLUMNS = [
    "MatchID",
    "Category",
    "Check",
    "Status",
    "Expected",
    "Actual",
    "Difference",
    "Details",
]


def validate_team_stats(df: pd.DataFrame) -> list[str]:
    """Retain the original lightweight team-stat validation API."""

    errors = []
    if df.duplicated(subset=["MatchID", "Team"]).any():
        errors.append("Duplicate MatchID + Team rows found.")
    if (df["TotalScores"] > df["TotalShots"]).any():
        errors.append("Some rows have TotalScores greater than TotalShots.")
    if (df["ScoresPlay"] > df["ShotsPlay"]).any():
        errors.append("Some rows have ScoresPlay greater than ShotsPlay.")
    if (df["ScoresPlaced"] > df["ShotsPlaced"]).any():
        errors.append("Some rows have ScoresPlaced greater than ShotsPlaced.")

    numeric_columns = [
        "Goals", "Points", "TwoPointers", "Wides", "Shorts",
        "KickoutsWon", "KickoutsLost", "ForcedTurnovers",
        "UnforcedTurnovers", "FreesConceded", "BreakingBallWon",
        "Attacks", "TotalShots", "TotalScores", "ShotsPlay",
        "ScoresPlay", "ShotsPlaced", "ScoresPlaced",
    ]
    for column in numeric_columns:
        if column in df.columns and (df[column].dropna() < 0).any():
            errors.append(f"Negative values found in {column}.")
    return errors


def _display_value(value):
    if value is None or pd.isna(value):
        return "-"
    if isinstance(value, numbers.Number):
        return str(int(value)) if float(value).is_integer() else f"{value:.1f}"
    return str(value)


def _add_check(
    results,
    match_id,
    category,
    check,
    passed,
    expected,
    actual,
    details,
):
    difference = None
    if (
        isinstance(expected, numbers.Number)
        and isinstance(actual, numbers.Number)
        and not pd.isna(expected)
        and not pd.isna(actual)
    ):
        difference = actual - expected
    results.append(
        {
            "MatchID": match_id,
            "Category": category,
            "Check": check,
            "Status": "Pass" if passed else "Review",
            "Expected": _display_value(expected),
            "Actual": _display_value(actual),
            "Difference": difference,
            "Details": details,
        }
    )


def _team_rows(data, team_name):
    if "Team" not in data.columns:
        return data.copy()
    return data[data["Team"] == team_name].copy()


def _add_dataset_integrity_checks(results, datasets, known_match_ids):
    key_columns = {
        "Team stats": ["MatchID", "Team"],
        "Shooting": ["MatchID", "Team", "Period", "ShotType"],
        "Scoring sources": ["MatchID", "Team", "Source"],
        "Kickouts": ["MatchID", "Team", "Period", "KickoutType"],
        "Turnovers": ["MatchID", "Team", "Period"],
        "Players": ["MatchID", "PlayerName"],
    }
    for label, data in datasets.items():
        keys = key_columns[label]
        duplicate_count = int(data.duplicated(keys, keep=False).sum())
        _add_check(
            results,
            "All",
            "Structure",
            f"{label}: unique rows",
            duplicate_count == 0,
            0,
            duplicate_count,
            f"Duplicate rows using key: {' + '.join(keys)}.",
        )

        unknown_ids = sorted(set(data["MatchID"].dropna()) - known_match_ids)
        _add_check(
            results,
            "All",
            "Structure",
            f"{label}: valid MatchID values",
            not unknown_ids,
            "All IDs in matches file",
            ", ".join(unknown_ids) if unknown_ids else "All valid",
            "Rows with an unknown MatchID cannot be joined reliably.",
        )


def _add_coverage_checks(results, match_id, datasets):
    shooting = datasets["Shooting"]
    kickouts = datasets["Kickouts"]
    turnovers = datasets["Turnovers"]
    coverage = [
        ("Team stats row present", len(datasets["Team stats"]) == 1, 1, len(datasets["Team stats"])),
        (
            "FT overall shooting row present",
            len(shooting[(shooting["Period"] == "FT") & (shooting["ShotType"] == "Overall")]) == 1,
            1,
            len(shooting[(shooting["Period"] == "FT") & (shooting["ShotType"] == "Overall")]),
        ),
        ("Scoring-source rows present", len(datasets["Scoring sources"]) > 0, "> 0", len(datasets["Scoring sources"])),
        (
            "Kickout period/type rows present",
            kickouts[["Period", "KickoutType"]].drop_duplicates().shape[0] == 6,
            6,
            kickouts[["Period", "KickoutType"]].drop_duplicates().shape[0],
        ),
        ("Turnover period rows present", turnovers["Period"].nunique() == 3, 3, turnovers["Period"].nunique()),
        ("Player rows present", len(datasets["Players"]) > 0, "> 0", len(datasets["Players"])),
    ]
    for check, passed, expected, actual in coverage:
        _add_check(
            results,
            match_id,
            "Coverage",
            check,
            passed,
            expected,
            actual,
            "Confirms the match has the rows needed by the dashboard.",
        )


def _add_team_checks(results, match, team_row, team_name):
    match_id = match["MatchID"]
    recorded_score = match["HomeScore"] if match["HomeTeam"] == team_name else match["AwayScore"]
    calculated_score = team_row["Goals"] * 3 + team_row["Points"] + team_row["TwoPointers"] * 2
    _add_check(
        results,
        match_id,
        "Score",
        "Team score value matches match result",
        calculated_score == recorded_score,
        recorded_score,
        calculated_score,
        "Calculated as Goals × 3 + Points + TwoPointers × 2.",
    )

    scoring_events = team_row["Goals"] + team_row["Points"] + team_row["TwoPointers"]
    _add_check(
        results,
        match_id,
        "Score",
        "Team scoring events match TotalScores",
        scoring_events == team_row["TotalScores"],
        team_row["TotalScores"],
        scoring_events,
        "Each goal, point and two-pointer is one successful shot.",
    )

    for check, expected, actual in [
        ("Play + placed shots match TotalShots", team_row["TotalShots"], team_row["ShotsPlay"] + team_row["ShotsPlaced"]),
        ("Play + placed scores match TotalScores", team_row["TotalScores"], team_row["ScoresPlay"] + team_row["ScoresPlaced"]),
    ]:
        _add_check(
            results,
            match_id,
            "Team totals",
            check,
            expected == actual,
            expected,
            actual,
            "Checks that the team total equals its component categories.",
        )


def _add_shooting_checks(results, match_id, shooting_rows, team_row):
    miss_columns = ["Wides", "Shorts", "Blocked", "Post", "Saved"]
    for shot in shooting_rows.itertuples(index=False):
        label = f"{shot.Period} {shot.ShotType}"
        _add_check(
            results,
            match_id,
            "Shooting",
            f"{label}: scores do not exceed shots",
            shot.ShotsScored <= shot.ShotsTaken,
            f"≤ {int(shot.ShotsTaken)}",
            shot.ShotsScored,
            "ShotsScored must be less than or equal to ShotsTaken.",
        )
        outcomes = shot.ShotsScored + sum(getattr(shot, column) for column in miss_columns)
        _add_check(
            results,
            match_id,
            "Shooting",
            f"{label}: shot outcomes reconcile",
            outcomes == shot.ShotsTaken,
            shot.ShotsTaken,
            outcomes,
            "Scores + wides + shorts + blocked + post + saved.",
        )

    ft_overall = shooting_rows[(shooting_rows["Period"] == "FT") & (shooting_rows["ShotType"] == "Overall")]
    if len(ft_overall) == 1 and team_row is not None:
        ft = ft_overall.iloc[0]
        for label, expected, actual in [
            ("FT shots match team TotalShots", team_row["TotalShots"], ft["ShotsTaken"]),
            ("FT scores match team TotalScores", team_row["TotalScores"], ft["ShotsScored"]),
        ]:
            _add_check(
                results,
                match_id,
                "Shooting",
                label,
                expected == actual,
                expected,
                actual,
                "Reconciles shooting detail with the team summary.",
            )


def _add_kickout_checks(results, match_id, kickout_rows):
    win_type_columns = ["CleanWins", "BreakWins", "FreeWins", "SidelineWins"]
    for kickout in kickout_rows.itertuples(index=False):
        label = f"{kickout.Period} {kickout.KickoutType}"
        outcomes = kickout.Won + kickout.Lost
        _add_check(
            results,
            match_id,
            "Kickouts",
            f"{label}: won + lost = taken",
            outcomes == kickout.Taken,
            kickout.Taken,
            outcomes,
            "Every kickout must have a won or lost outcome.",
        )
        win_types = sum(getattr(kickout, column) for column in win_type_columns)
        _add_check(
            results,
            match_id,
            "Kickouts",
            f"{label}: win types = won",
            win_types == kickout.Won,
            kickout.Won,
            win_types,
            "Clean + break + free + sideline wins must equal Won.",
        )

    period_columns = ["Taken", "Won", "Lost", *win_type_columns]
    for kickout_type in ["Own", "Opponent"]:
        rows = kickout_rows[kickout_rows["KickoutType"] == kickout_type]
        ft = rows[rows["Period"] == "FT"]
        halves = rows[rows["Period"].isin(["1H", "2H"])]
        if len(ft) == 1 and halves["Period"].nunique() == 2:
            mismatches = [column for column in period_columns if ft[column].iloc[0] != halves[column].sum()]
            _add_check(
                results,
                match_id,
                "Kickouts",
                f"{kickout_type}: FT = 1H + 2H",
                not mismatches,
                "All kickout fields reconcile",
                ", ".join(mismatches) if mismatches else "All reconcile",
                "Checks full-time kickout figures against both halves.",
            )


def _add_turnover_checks(results, match_id, turnover_rows):
    turnover_columns = [
        "TurnoversWonForced",
        "TurnoversWonUnforced",
        "TurnoversLostForced",
        "TurnoversLostUnforced",
    ]
    ft = turnover_rows[turnover_rows["Period"] == "FT"]
    halves = turnover_rows[turnover_rows["Period"].isin(["1H", "2H"])]
    if len(ft) == 1 and halves["Period"].nunique() == 2:
        mismatches = [column for column in turnover_columns if ft[column].iloc[0] != halves[column].sum()]
        _add_check(
            results,
            match_id,
            "Turnovers",
            "FT turnover figures = 1H + 2H",
            not mismatches,
            "All turnover fields reconcile",
            ", ".join(mismatches) if mismatches else "All reconcile",
            "Checks forced/unforced turnovers won and lost.",
        )


def _add_source_checks(results, match_id, source_rows, team_row):
    if team_row is None or source_rows.empty:
        return
    source_total = source_rows["Scores"].sum()
    team_total = team_row["TotalScores"]
    _add_check(
        results,
        match_id,
        "Scoring sources",
        "Scoring sources total = TotalScores",
        source_total == team_total,
        team_total,
        source_total,
        "Every successful shot should have one scoring source.",
    )


def _add_player_checks(results, match_id, player_rows, team_row):
    if player_rows.empty:
        return
    row_rules = [
        ("Player minutes are between 0 and 70", player_rows["MinutesPlayed"].between(0, 70)),
        ("Player scores do not exceed shot attempts", player_rows["Scores"] <= player_rows["ShotAttempts"]),
        (
            "Player handpass halves = total",
            player_rows["Handpasses1H"] + player_rows["Handpasses2H"] == player_rows["HandpassesTotal"],
        ),
        (
            "Player footpass halves = total",
            player_rows["Footpasses1H"] + player_rows["Footpasses2H"] == player_rows["FootpassesTotal"],
        ),
        (
            "Completed passes do not exceed attempted passes",
            (player_rows["HandpassesCompleted"] <= player_rows["HandpassesTotal"])
            & (player_rows["FootpassesCompleted"] <= player_rows["FootpassesTotal"]),
        ),
    ]
    for check, valid_rows in row_rules:
        invalid_players = player_rows.loc[~valid_rows, "PlayerName"].tolist()
        _add_check(
            results,
            match_id,
            "Player rows",
            check,
            not invalid_players,
            0,
            len(invalid_players),
            "Invalid players: " + ", ".join(invalid_players) if invalid_players else "All player rows pass.",
        )

    if team_row is None:
        return
    reconciliation = [
        ("Goals", "Goals", "Goals"),
        ("Points", "Points", "Points"),
        ("Two-pointers", "TwoPointers", "TwoPointers"),
        ("Shot attempts", "ShotAttempts", "TotalShots"),
        ("Scoring events", "Scores", "TotalScores"),
        ("Kickouts won", "KickoutsWon", "KickoutsWon"),
        ("Breaking balls won", "BreakingBallsWon", "BreakingBallWon"),
        ("Turnovers won", "TurnoversWon", None),
        ("Frees conceded", "FreesConceded", "FreesConceded"),
    ]
    for label, player_column, team_column in reconciliation:
        actual = player_rows[player_column].sum()
        expected = (
            team_row["ForcedTurnovers"] + team_row["UnforcedTurnovers"]
            if team_column is None
            else team_row[team_column]
        )
        _add_check(
            results,
            match_id,
            "Player vs team",
            f"Player {label.lower()} = team {label.lower()}",
            actual == expected,
            expected,
            actual,
            "Player rows are summed and compared with the team summary.",
        )


def run_data_quality_checks(
    matches,
    team_data,
    shooting_data,
    scoring_sources,
    kickout_data,
    turnover_data,
    player_data,
    team_name,
):
    """Run cross-file checks and return one auditable row per check."""

    results = []
    team_matches = matches[(matches["HomeTeam"] == team_name) | (matches["AwayTeam"] == team_name)].copy()
    known_match_ids = set(matches["MatchID"].dropna())
    datasets = {
        "Team stats": _team_rows(team_data, team_name),
        "Shooting": _team_rows(shooting_data, team_name),
        "Scoring sources": _team_rows(scoring_sources, team_name),
        "Kickouts": _team_rows(kickout_data, team_name),
        "Turnovers": _team_rows(turnover_data, team_name),
        "Players": player_data.copy(),
    }
    _add_dataset_integrity_checks(results, datasets, known_match_ids)

    for _, match in team_matches.sort_values("Date").iterrows():
        match_id = match["MatchID"]
        match_datasets = {
            label: data[data["MatchID"] == match_id]
            for label, data in datasets.items()
        }
        _add_coverage_checks(results, match_id, match_datasets)
        team_rows = match_datasets["Team stats"]
        team_row = team_rows.iloc[0] if len(team_rows) == 1 else None
        if team_row is not None:
            _add_team_checks(results, match, team_row, team_name)
        _add_shooting_checks(results, match_id, match_datasets["Shooting"], team_row)
        _add_kickout_checks(results, match_id, match_datasets["Kickouts"])
        _add_turnover_checks(results, match_id, match_datasets["Turnovers"])
        _add_source_checks(results, match_id, match_datasets["Scoring sources"], team_row)
        _add_player_checks(results, match_id, match_datasets["Players"], team_row)

    return pd.DataFrame(results, columns=RESULT_COLUMNS)
