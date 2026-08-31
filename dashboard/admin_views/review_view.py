import streamlit as st

from admin_operations import execute_admin_action
from admin_services import (
    IMPORT_DATASET_ORDER,
    _quality_report,
    _read_dataset,
)
from src.database.admin_repository import (
    load_audit_events_db,
    load_match_lifecycle_db,
    transition_match_status_db,
)


def _change_status(match_id, new_status, actor_username, details=None):
    success, _ = execute_admin_action(
        "match_status_change_failed",
        lambda: transition_match_status_db(
            match_id,
            new_status,
            username=actor_username,
            details=details,
        ),
        username=actor_username,
        match_id=match_id,
        target_status=new_status,
    )
    if success:
        st.cache_data.clear()
        st.rerun()


def _render_match_review(team_name, actor_username):
    st.subheader("Review and publish matches")
    st.caption(
        "Draft and Review matches stay out of official analytics. Only a "
        "Published match appears in the championship and player dashboards."
    )
    lifecycle = load_match_lifecycle_db()
    if lifecycle.empty:
        st.info("Import a match before starting the review workflow.")
        return

    summary_columns = [
        "MatchID",
        "Date",
        "Fixture",
        "Status",
        "Complete",
        "Updated",
        "PublishedBy",
    ]
    st.dataframe(
        lifecycle[summary_columns],
        hide_index=True,
        width="stretch",
        column_config={
            "Complete": st.column_config.CheckboxColumn(disabled=True),
        },
    )

    selected_match = st.selectbox(
        "Match to review",
        lifecycle["MatchID"].tolist(),
        key="review_match_id",
    )
    selected = lifecycle[
        lifecycle["MatchID"] == selected_match
    ].iloc[0]
    status = selected["Status"]

    status_col, completeness_col, published_col = st.columns(3)
    status_col.metric("Workflow status", status)
    completeness_col.metric(
        "Dataset completeness",
        "Complete" if selected["Complete"] else "Incomplete",
    )
    published_col.metric(
        "Published by",
        selected["PublishedBy"] or "—",
    )

    if not selected["Complete"]:
        st.error(
            f"Missing data: {selected['Missing']}. Complete every dataset "
            "before submitting this match for review."
        )

    current_data = {
        key: _read_dataset(key)
        for key in IMPORT_DATASET_ORDER
    }
    report = _quality_report(current_data, team_name)
    review_items = report[
        (report["Status"] == "Review")
        & report["MatchID"].isin(["All", selected_match])
    ]
    if review_items.empty:
        st.success("No data-quality review items were found for this match.")
        issues_acknowledged = True
    else:
        st.warning(
            f"There are {len(review_items)} reconciliation items to review."
        )
        st.dataframe(review_items, hide_index=True, width="stretch")
        issues_acknowledged = st.checkbox(
            "I reviewed these items and accept them for this workflow step",
            key=f"review_ack_{selected_match}_{status}",
        )

    if status == "Draft":
        if st.button(
            "Submit for coach review",
            type="primary",
            icon=":material/rate_review:",
            disabled=not selected["Complete"] or not issues_acknowledged,
        ):
            _change_status(
                selected_match,
                "Review",
                actor_username,
                details={"quality_review_items": len(review_items)},
            )
    elif status == "Review":
        publish_col, return_col = st.columns(2)
        with publish_col:
            if st.button(
                "Publish to analytics",
                type="primary",
                icon=":material/publish:",
                disabled=(
                    not selected["Complete"]
                    or not issues_acknowledged
                ),
            ):
                _change_status(
                    selected_match,
                    "Published",
                    actor_username,
                    details={"quality_review_items": len(review_items)},
                )
        with return_col:
            if st.button(
                "Return to draft",
                icon=":material/edit_note:",
            ):
                _change_status(
                    selected_match,
                    "Draft",
                    actor_username,
                )
    else:
        st.info(
            "This match is live in analytics. Reopening it removes it from "
            "official views until it is reviewed and published again."
        )
        confirm_reopen = st.checkbox(
            "I understand this match will temporarily leave analytics",
            key=f"reopen_confirm_{selected_match}",
        )
        if st.button(
            "Reopen as draft",
            icon=":material/edit:",
            disabled=not confirm_reopen,
        ):
            _change_status(
                selected_match,
                "Draft",
                actor_username,
            )

    st.markdown("#### Audit history")
    audit = load_audit_events_db(selected_match)
    if audit.empty:
        st.caption("No recorded changes yet. Existing data predates auditing.")
        return
    st.dataframe(
        audit[["When", "User", "Action", "Dataset"]],
        hide_index=True,
        width="stretch",
    )
    event_number = st.selectbox(
        "Inspect audit event",
        range(len(audit)),
        format_func=lambda index: (
            f"{audit.iloc[index]['When']} — "
            f"{audit.iloc[index]['Action']}"
        ),
        key=f"audit_event_{selected_match}",
    )
    event = audit.iloc[event_number]
    st.json(
        {
            "before": event["Before"],
            "after": event["After"],
            "details": event["Details"],
        },
        expanded=False,
    )
