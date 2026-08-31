import pandas as pd
import streamlit as st

from auth import (
    DEFAULT_SHARED_PASSWORD,
    VALID_ROLES,
    load_users,
    validate_users,
)
from load_data import (
    load_kickout_stats,
    load_matches,
    load_player_match_data,
    load_scoring_sources,
    load_shooting_detail,
    load_team_stats,
    load_turnover_stats,
)
from src.database.admin_repository import replace_match_dataset_db
from src.database.user_repository import save_users_db
from validation import run_data_quality_checks, validate_team_stats


DATASET_CONFIG = {
    "Matches": {
        "key": "matches",
        "primary_key": ["MatchID"],
    },
    "Team stats": {
        "key": "team_stats",
        "primary_key": ["MatchID", "Team"],
    },
    "Shooting": {
        "key": "shooting",
        "primary_key": ["MatchID", "Team", "Period", "ShotType"],
    },
    "Scoring sources": {
        "key": "scoring_sources",
        "primary_key": ["MatchID", "Team", "Source"],
    },
    "Kickouts": {
        "key": "kickouts",
        "primary_key": ["MatchID", "Team", "Period", "KickoutType"],
    },
    "Turnovers": {
        "key": "turnovers",
        "primary_key": ["MatchID", "Team", "Period"],
    },
    "Player data": {
        "key": "player_data",
        "primary_key": ["MatchID", "PlayerName"],
    },
}

DATASET_LOADERS = {
    "matches": load_matches,
    "team_stats": load_team_stats,
    "shooting": load_shooting_detail,
    "scoring_sources": load_scoring_sources,
    "kickouts": load_kickout_stats,
    "turnovers": load_turnover_stats,
    "player_data": load_player_match_data,
}


def _read_dataset(dataset_key):
    return DATASET_LOADERS[dataset_key]()


def _normalise_boolean_column(data, column):
    if column not in data.columns:
        return
    data[column] = (
        data[column].astype(str).str.strip().str.lower()
        .isin(["true", "yes", "1"])
    )


def _validate_candidate(candidate, original, config, dataset_label, match_ids):
    errors = []
    if candidate.empty:
        errors.append("At least one row is required.")
        return errors

    missing_columns = [
        column for column in original.columns if column not in candidate.columns
    ]
    extra_columns = [
        column for column in candidate.columns if column not in original.columns
    ]
    if missing_columns:
        errors.append(f"Missing columns: {', '.join(missing_columns)}.")
    if extra_columns:
        errors.append(f"Unexpected columns: {', '.join(extra_columns)}.")
    if errors:
        return errors

    numeric_columns = set(original.select_dtypes(include="number").columns)
    for column in numeric_columns:
        raw_values = candidate[column]
        converted = pd.to_numeric(raw_values, errors="coerce")
        supplied = raw_values.notna() & raw_values.astype(str).str.strip().ne("")
        if (supplied & converted.isna()).any():
            errors.append(f"Column {column} must contain numbers only.")
        elif converted.fillna(0).lt(0).any():
            errors.append(f"Column {column} cannot contain negative values.")
        else:
            # Blank numeric cells follow the same zero-default as load_data.py.
            candidate[column] = converted.fillna(0)

    optional_columns = (
        {"Notes"} | numeric_columns
        if dataset_label == "Player data"
        else numeric_columns
    )
    for column in original.columns:
        if column in optional_columns:
            continue
        blank_values = (
            candidate[column].isna()
            | candidate[column].astype(str).str.strip().eq("")
        )
        if blank_values.any():
            errors.append(f"Required column {column} cannot be blank.")

    for column in config["primary_key"]:
        has_blank_key = (
            candidate[column].isna().any()
            or candidate[column].astype(str).str.strip().eq("").any()
        )
        if has_blank_key:
            errors.append(f"Primary-key column {column} cannot be blank.")
    duplicate_count = int(
        candidate.duplicated(config["primary_key"], keep=False).sum()
    )
    if duplicate_count:
        errors.append(
            f"{duplicate_count} rows have duplicate primary-key values."
        )

    if dataset_label != "Matches":
        unknown_ids = sorted(set(candidate["MatchID"].astype(str)) - match_ids)
        if unknown_ids:
            errors.append(f"Unknown MatchID values: {', '.join(unknown_ids)}.")

    if dataset_label == "Team stats" and not errors:
        errors.extend(validate_team_stats(candidate))
    return errors


def _replace_match_rows(original, edited_rows, match_id, dataset_label):
    edited_rows = edited_rows.dropna(how="all").copy()
    if dataset_label == "Matches":
        if match_id != "New match":
            edited_rows["MatchID"] = match_id
            remaining = original[original["MatchID"] != match_id]
        else:
            remaining = original
    else:
        edited_rows["MatchID"] = match_id
        remaining = original[original["MatchID"] != match_id]
    return pd.concat([remaining, edited_rows], ignore_index=True)


def _cross_dataset_report(candidate, dataset_key, team_name):
    data = {key: _read_dataset(key) for key in [
        "matches",
        "team_stats",
        "shooting",
        "scoring_sources",
        "kickouts",
        "turnovers",
        "player_data",
    ]}
    data[dataset_key] = candidate
    for frame in data.values():
        numeric_columns = frame.select_dtypes(include="number").columns
        frame[numeric_columns] = frame[numeric_columns].fillna(0)
    return run_data_quality_checks(
        matches=data["matches"],
        team_data=data["team_stats"],
        shooting_data=data["shooting"],
        scoring_sources=data["scoring_sources"],
        kickout_data=data["kickouts"],
        turnover_data=data["turnovers"],
        player_data=data["player_data"],
        team_name=team_name,
    )


def _render_data_entry(matches, team_name):
    st.subheader("Match data entry")
    st.caption(
        "Edit rows directly or upload replacement rows for one match. "
        "Validated changes are saved to PostgreSQL in one transaction."
    )

    control_left, control_right = st.columns(2)
    with control_left:
        dataset_label = st.selectbox(
            "Dataset",
            options=list(DATASET_CONFIG),
            key="admin_dataset",
        )
    config = DATASET_CONFIG[dataset_label]
    dataset_key = config["key"]
    original = _read_dataset(dataset_key)
    st.download_button(
        "Download current dataset",
        data=original.to_csv(index=False).encode("utf-8"),
        file_name=f"{dataset_key}.csv",
        mime="text/csv",
        icon=":material/download:",
    )

    match_options = matches["MatchID"].drop_duplicates().tolist()
    if dataset_label == "Matches":
        match_options = [*match_options, "New match"]
    with control_right:
        match_id = st.selectbox(
            "Match",
            options=match_options,
            key="admin_match",
        )

    input_mode = st.segmented_control(
        "Input method",
        options=["Edit rows", "Upload CSV"],
        default="Edit rows",
        key="admin_input_mode",
    )

    if match_id == "New match":
        existing_rows = pd.DataFrame(
            [{column: None for column in original.columns}]
        )
    else:
        existing_rows = original[original["MatchID"] == match_id].copy()

    if input_mode == "Edit rows":
        edited_rows = st.data_editor(
            existing_rows,
            hide_index=True,
            width="stretch",
            num_rows="dynamic",
            disabled=["MatchID"] if match_id != "New match" else [],
            key=f"admin_editor_{dataset_key}_{match_id}",
        )
    else:
        upload = st.file_uploader(
            "Upload CSV rows",
            type=["csv"],
            key=f"admin_upload_{dataset_key}_{match_id}",
            help="The upload must use the same columns as the selected dataset.",
        )
        if upload is None:
            st.info("Choose a CSV file to preview and validate its rows.")
            return
        try:
            edited_rows = pd.read_csv(upload)
        except Exception as error:
            st.error(f"Could not read the uploaded CSV: {error}")
            return
        st.dataframe(edited_rows, hide_index=True, width="stretch")

    candidate = _replace_match_rows(
        original,
        edited_rows,
        match_id,
        dataset_label,
    )
    errors = _validate_candidate(
        candidate,
        original,
        config,
        dataset_label,
        set(matches["MatchID"].astype(str)),
    )
    if match_id == "New match" and edited_rows.dropna(how="all").empty:
        errors.append("Enter the new match details before saving.")

    if st.button(
        "Validate and save",
        type="primary",
        icon=":material/save:",
        disabled=bool(errors),
    ):
        report = _cross_dataset_report(candidate, dataset_key, team_name)
        review_items = report[report["Status"] == "Review"]
        saved_match = (
            str(edited_rows["MatchID"].iloc[0])
            if match_id == "New match"
            else match_id
        )
        replace_match_dataset_db(
            dataset_key,
            saved_match,
            edited_rows[original.columns],
        )
        st.cache_data.clear()
        st.session_state["admin_last_save"] = {
            "dataset": dataset_label,
            "match": saved_match,
            "reviews": len(review_items),
        }
        st.rerun()

    if errors:
        for error in errors:
            st.error(error, icon=":material/error:")
    else:
        report = _cross_dataset_report(candidate, dataset_key, team_name)
        selected_id = (
            edited_rows["MatchID"].iloc[0]
            if match_id == "New match" and not edited_rows.empty
            else match_id
        )
        review_items = report[
            (report["Status"] == "Review")
            & report["MatchID"].isin(["All", selected_id])
        ]
        if review_items.empty:
            st.success("Draft passes the available validation checks.")
        else:
            st.warning(
                f"Draft has {len(review_items)} reconciliation items to review. "
                "Saving is allowed because some existing player/team differences "
                "may be intentional or awaiting correction."
            )
            st.dataframe(
                review_items,
                hide_index=True,
                width="stretch",
            )

    last_save = st.session_state.pop("admin_last_save", None)
    if last_save:
        st.success(
            f"Saved {last_save['dataset']} for {last_save['match']}. "
            f"Review items after save: {last_save['reviews']}."
        )


def _render_user_management(player_data):
    st.subheader("User management")
    st.caption(
        "All accounts use the shared demo password. Roles control which "
        "dashboard views are available."
    )
    users = load_users()
    player_options = sorted(player_data["PlayerName"].dropna().unique())
    edited_users = st.data_editor(
        users,
        hide_index=True,
        width="stretch",
        num_rows="dynamic",
        key="admin_user_editor",
        disabled=["UserID"],
        column_config={
            "UserID": None,
            "Role": st.column_config.SelectboxColumn(
                options=VALID_ROLES,
                required=True,
            ),
            "PlayerName": st.column_config.SelectboxColumn(
                options=["", *player_options],
            ),
            "Active": st.column_config.CheckboxColumn(),
        },
    )
    _normalise_boolean_column(edited_users, "Active")
    errors = validate_users(edited_users)
    if st.button(
        "Save users",
        type="primary",
        icon=":material/group:",
        disabled=bool(errors),
    ):
        edited_users["Username"] = (
            edited_users["Username"].astype(str).str.strip().str.lower()
        )
        save_users_db(
            edited_users[users.columns],
            DEFAULT_SHARED_PASSWORD,
        )
        st.success("Users saved to PostgreSQL.")

    for error in errors:
        st.error(error, icon=":material/error:")


def render_admin(matches, player_data, team_name):
    st.header("Admin")
    st.caption("Add or edit match data and manage role-based access")
    data_tab, users_tab = st.tabs(["Data entry", "Users"])
    with data_tab:
        _render_data_entry(matches, team_name)
    with users_tab:
        _render_user_management(player_data)
