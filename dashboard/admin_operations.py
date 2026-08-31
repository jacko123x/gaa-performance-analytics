"""Safe execution wrapper for database-changing Admin actions."""

from uuid import uuid4

import streamlit as st

from src.logging_config import get_logger, log_exception


LOGGER = get_logger("gaa_analytics.admin_ui")


def execute_admin_action(event, action, **context):
    try:
        return True, action()
    except Exception as error:
        reference = uuid4().hex[:10].upper()
        log_exception(
            LOGGER,
            event,
            error=error,
            reference=reference,
            **context,
        )
        st.error(
            "The change could not be saved. No partial update was applied. "
            f"Support reference: {reference}",
            icon=":material/error:",
        )
        return False, None
