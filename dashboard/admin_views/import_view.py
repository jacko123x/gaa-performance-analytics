import pandas as pd
import streamlit as st

from admin_operations import execute_admin_action
from admin_services import (
    DATASET_LABELS,
    IMPORT_DATASET_ORDER,
    _build_import_template_archive,
    _quality_report,
    _read_dataset,
    _validate_import_bundle,
)
from src.database.admin_repository import import_match_bundle_db


def _render_new_match_import(team_name, actor_username):
    st.subheader("Import a complete new match")
    st.caption(
        "Upload all seven datasets. The complete match is validated first "
        "and then saved to PostgreSQL as one atomic transaction."
    )

    imported_match = st.session_state.get("wizard_import_success")
    if imported_match:
        st.success(
            f"{imported_match} was imported as a Draft. All seven "
            "datasets were committed to PostgreSQL and are ready for review."
        )
        if st.button(
            "Import another match",
            icon=":material/add:",
            key="wizard_import_another",
        ):
            st.session_state.pop("wizard_import_success", None)
            for dataset_key in IMPORT_DATASET_ORDER:
                st.session_state.pop(
                    f"wizard_upload_{dataset_key}",
                    None,
                )
            st.rerun()
        return

    current_data = {
        key: _read_dataset(key)
        for key in IMPORT_DATASET_ORDER
    }
    st.download_button(
        "Download seven-file template pack",
        data=_build_import_template_archive(current_data),
        file_name="new_match_import_templates.zip",
        mime="application/zip",
        icon=":material/download:",
    )

    st.markdown("#### Upload match files")
    upload_columns = st.columns(2)
    uploads = {}
    for index, dataset_key in enumerate(IMPORT_DATASET_ORDER):
        with upload_columns[index % 2]:
            uploads[dataset_key] = st.file_uploader(
                f"{DATASET_LABELS[dataset_key]} CSV",
                type=["csv"],
                key=f"wizard_upload_{dataset_key}",
            )

    if not any(uploads.values()):
        st.info(
            "Download the templates, complete them with one shared new "
            "MatchID, then upload all seven files."
        )
        return

    bundle = {}
    parse_errors = []
    summary_rows = []
    for dataset_key, upload in uploads.items():
        label = DATASET_LABELS[dataset_key]
        if upload is None:
            summary_rows.append(
                {"Dataset": label, "File": "Missing", "Rows": 0}
            )
            continue
        try:
            data = pd.read_csv(upload)
        except Exception as error:
            parse_errors.append(f"{label}: could not read CSV: {error}")
            summary_rows.append(
                {"Dataset": label, "File": upload.name, "Rows": 0}
            )
            continue

        bundle[dataset_key] = data
        summary_rows.append(
            {
                "Dataset": label,
                "File": upload.name,
                "Rows": len(data),
            }
        )

    st.dataframe(
        pd.DataFrame(summary_rows),
        hide_index=True,
        width="stretch",
    )

    errors, candidates, match_id = _validate_import_bundle(
        bundle,
        current_data,
    )
    errors = [*parse_errors, *errors]
    if errors:
        for error in errors:
            st.error(error, icon=":material/error:")
        return

    report = _quality_report(candidates, team_name)
    review_items = report[
        (report["Status"] == "Review")
        & report["MatchID"].isin(["All", match_id])
    ]

    if review_items.empty:
        st.success(
            f"{match_id} passed structural and cross-dataset validation."
        )
        review_confirmed = True
    else:
        st.warning(
            f"{match_id} has {len(review_items)} reconciliation items "
            "to review before import."
        )
        st.dataframe(
            review_items,
            hide_index=True,
            width="stretch",
        )
        review_confirmed = st.checkbox(
            "I reviewed these items and want to import the match",
            key="wizard_review_confirmed",
        )

    if st.button(
        f"Import {match_id}",
        type="primary",
        icon=":material/upload:",
        disabled=not review_confirmed,
        key="wizard_commit",
    ):
        success, imported_match = execute_admin_action(
            "match_import_failed",
            lambda: import_match_bundle_db(
                bundle,
                username=actor_username,
            ),
            username=actor_username,
            match_id=match_id,
        )
        if not success:
            return

        st.cache_data.clear()
        st.session_state["wizard_import_success"] = imported_match
        st.rerun()
