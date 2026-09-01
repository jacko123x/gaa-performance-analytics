import streamlit as st

from admin_operations import execute_admin_action
from admin_services import _normalise_boolean_column
from auth import (
    DEFAULT_SHARED_PASSWORD,
    VALID_ROLES,
    load_users,
    validate_users,
)
from src.database.user_repository import (
    reset_active_user_passwords_db,
    reset_user_password_db,
    save_users_db,
    validate_new_password,
)


def _render_password_management(users, actor_username):
    st.divider()
    st.subheader("Password management")
    st.caption(
        "Reset one account or rotate the shared password for every active "
        "account. Password values are hashed before storage and are never "
        "written to application logs."
    )

    active_users = users[users["Active"].astype(bool)].copy()
    if active_users.empty:
        st.info("Create and save an active account before setting passwords.")
        return

    reset_scope = st.segmented_control(
        "Accounts to update",
        ["One active user", "All active users"],
        default="All active users",
        key="admin_password_reset_scope",
    )
    active_usernames = active_users["Username"].astype(str).tolist()
    display_names = dict(
        zip(
            active_users["Username"].astype(str),
            active_users["DisplayName"].astype(str),
        )
    )

    with st.form("admin_password_reset", clear_on_submit=True):
        selected_username = None
        if reset_scope == "One active user":
            selected_username = st.selectbox(
                "Account",
                active_usernames,
                format_func=lambda username: (
                    f"{display_names[username]} ({username})"
                ),
            )

        new_password = st.text_input(
            "New password",
            type="password",
            autocomplete="new-password",
            help="Use at least 12 characters.",
        )
        confirmed_password = st.text_input(
            "Confirm new password",
            type="password",
            autocomplete="new-password",
        )
        confirmation_phrase = ""
        if reset_scope == "All active users":
            st.warning(
                f"This will replace the login password for all "
                f"{len(active_users)} active accounts. Existing signed-in "
                "browser sessions will remain active until they log out or "
                "end."
            )
            confirmation_phrase = st.text_input(
                'Type "RESET ALL" to confirm',
            )

        submitted = st.form_submit_button(
            "Reset password",
            type="primary",
            icon=":material/password:",
        )

    if not submitted:
        return

    errors = validate_new_password(new_password)
    if new_password != confirmed_password:
        errors.append("The two password entries do not match.")
    if (
        reset_scope == "All active users"
        and confirmation_phrase != "RESET ALL"
    ):
        errors.append('Enter "RESET ALL" exactly to confirm this change.')
    if errors:
        for error in errors:
            st.error(error, icon=":material/error:")
        return

    if reset_scope == "All active users":
        action = lambda: reset_active_user_passwords_db(
            new_password,
            actor_username=actor_username,
        )
        reset_context = "all_active_users"
    else:
        action = lambda: reset_user_password_db(
            selected_username,
            new_password,
            actor_username=actor_username,
        )
        reset_context = "single_active_user"

    success, reset_count = execute_admin_action(
        "user_password_reset_failed",
        action,
        username=actor_username,
        reset_scope=reset_context,
    )
    if success:
        st.success(
            f"Password reset for {reset_count} active "
            f"{'account' if reset_count == 1 else 'accounts'}."
        )


def _render_user_management(player_data, actor_username):
    st.subheader("User management")
    st.caption(
        "Accounts can share one password or use individual passwords. Roles "
        "control which dashboard views are available."
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

    _render_password_management(users, actor_username)
