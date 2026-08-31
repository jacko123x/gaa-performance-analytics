"""Safe user-facing presentation for unavailable application services."""

import streamlit as st


def render_maintenance_screen(app_title, reference, reason=None):
    st.title(app_title)
    st.space("medium")
    _, content, _ = st.columns([1, 1.5, 1])
    with content.container(border=True):
        st.subheader(
            ":material/construction: Dashboard temporarily unavailable",
            text_alignment="center",
        )
        if reason in {"schema_incomplete", "schema_outdated"}:
            st.write(
                "The dashboard database is being prepared or upgraded. "
                "Please try again shortly."
            )
        else:
            st.write(
                "The dashboard cannot reach its data service right now. "
                "Your data has not been changed. Please try again shortly."
            )
        st.caption(
            f"Support reference: {reference}",
            text_alignment="center",
        )
        return st.button(
            "Try again",
            icon=":material/refresh:",
            width="stretch",
        )
