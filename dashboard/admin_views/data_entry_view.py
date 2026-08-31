import pandas as pd
import streamlit as st

from admin_operations import execute_admin_action
from admin_services import (
    DATASET_CONFIG,
    _cross_dataset_report,
    _read_dataset,
    _replace_match_rows,
    _validate_candidate,
)
from src.database.admin_repository import replace_match_dataset_db


def _render_data_entry(team_name, actor_username):
    st.subheader("Match data entry")
    st.caption(
        "Edit rows directly or upload replacement rows for one match. "
        "Validated changes are saved to PostgreSQL in one transaction."
    )

    matches = _read_dataset("matches")
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
        success, _ = execute_admin_action(
            "match_dataset_replace_failed",
            lambda: replace_match_dataset_db(
                dataset_key,
                saved_match,
                edited_rows[original.columns],
                username=actor_username,
                before_data=existing_rows,
            ),
            username=actor_username,
            match_id=saved_match,
            dataset=dataset_key,
        )
        if not success:
            return
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
            "The match is now a Draft. "
            f"Review items after save: {last_save['reviews']}."
        )
