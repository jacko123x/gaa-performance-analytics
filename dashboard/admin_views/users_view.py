import streamlit as st

from admin_operations import execute_admin_action
from admin_services import _normalise_boolean_column
from auth import (
    DEFAULT_SHARED_PASSWORD,
    VALID_ROLES,
    load_users,
    validate_users,
)
from src.database.user_repository import save_users_db


def _render_user_management(player_data, actor_username):
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
        success, _ = execute_admin_action(
            "users_save_failed",
            lambda: save_users_db(
                edited_users[users.columns],
                DEFAULT_SHARED_PASSWORD,
                actor_username=actor_username,
            ),
            username=actor_username,
            user_count=len(edited_users),
        )
        if success:
            st.success("Users saved to PostgreSQL.")

    for error in errors:
        st.error(error, icon=":material/error:")
