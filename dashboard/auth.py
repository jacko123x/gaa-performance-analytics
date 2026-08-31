import streamlit as st

from src.database.security import verify_password
from src.database.user_repository import (
    find_active_user_db,
    load_users_db,
)
from src.logging_config import (
    get_logger,
    identifier_fingerprint,
    log_event,
)
from src.settings import get_settings


# New demo accounts receive this password; existing hashes remain unchanged.
DEFAULT_SHARED_PASSWORD = get_settings().initial_shared_password
VALID_ROLES = ["Admin", "Coach", "Player", "Viewer"]
LOGGER = get_logger("gaa_analytics.auth")


def load_users():
    users = load_users_db()
    users["Username"] = users["Username"].str.strip().str.lower()
    users["DisplayName"] = users["DisplayName"].str.strip()
    users["Role"] = users["Role"].str.strip()
    users["PlayerName"] = users["PlayerName"].str.strip()
    users["Active"] = (
        users["Active"].astype(str).str.strip().str.lower()
        .isin(["true", "yes", "1"])
    )
    return users


def validate_users(users):
    errors = []
    usernames = users["Username"].fillna("").astype(str).str.strip().str.lower()
    if usernames.eq("").any():
        errors.append("Every user needs a username.")
    if usernames.duplicated().any():
        errors.append("Usernames must be unique.")
    blank_display_names = (
        users["DisplayName"].fillna("").astype(str).str.strip().eq("")
    )
    if blank_display_names.any():
        errors.append("Every user needs a display name.")
    invalid_roles = sorted(set(users["Role"]) - set(VALID_ROLES))
    if invalid_roles:
        errors.append(f"Invalid roles: {', '.join(invalid_roles)}.")
    active_admins = users[
        users["Active"].astype(bool) & users["Role"].eq("Admin")
    ]
    if active_admins.empty:
        errors.append("At least one active Admin account is required.")
    players_without_profiles = users[
        users["Active"].astype(bool)
        & users["Role"].eq("Player")
        & users["PlayerName"].fillna("").astype(str).str.strip().eq("")
    ]
    if not players_without_profiles.empty:
        errors.append("Every active Player account needs a linked player.")
    return errors


def _find_user(username):
    return find_active_user_db(username)


def _credentials_match(username, password):
    user = _find_user(username)
    if user is None:
        return None
    return (
        user
        if verify_password(password, user["PasswordHash"])
        else None
    )


def require_login():
    """Render the login gate and return True for an authenticated session."""

    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("authenticated_user", None)
    st.session_state.setdefault("authenticated_display_name", None)
    st.session_state.setdefault("authenticated_role", None)
    st.session_state.setdefault("authenticated_player", None)

    if st.session_state["authenticated"]:
        return True

    st.title(
        "Austin Stacks Performance Platform",
        text_alignment="center",
    )
    st.caption("Club Championship 2026", text_alignment="center")
    st.space("medium")

    _, login_column, _ = st.columns([1, 1.25, 1])
    with login_column.container(border=True):
        st.subheader(
            ":material/lock: Dashboard access",
            text_alignment="center",
        )
        st.caption(
            "Sign in to access the views available to your role.",
            text_alignment="center",
        )
        with st.form("dashboard_login", clear_on_submit=True):
            username = st.text_input("Username", autocomplete="username")
            password = st.text_input(
                "Password",
                type="password",
                autocomplete="current-password",
            )
            submitted = st.form_submit_button(
                "Sign in",
                type="primary",
                icon=":material/login:",
                width="stretch",
            )

        if submitted:
            user = _credentials_match(username, password)
            if user is not None:
                st.session_state["authenticated"] = True
                st.session_state["authenticated_user"] = user["Username"]
                st.session_state["authenticated_display_name"] = (
                    user["DisplayName"] or user["Username"]
                )
                st.session_state["authenticated_role"] = user["Role"]
                st.session_state["authenticated_player"] = (
                    user["PlayerName"] or None
                )
                log_event(
                    LOGGER,
                    "login_succeeded",
                    username=user["Username"],
                    role=user["Role"],
                )
                st.rerun()
            else:
                log_event(
                    LOGGER,
                    "login_failed",
                    identifier_hash=identifier_fingerprint(username),
                )
                st.error(
                    "The username or password is incorrect, or the "
                    "account is inactive.",
                    icon=":material/error:",
                )

        st.caption(
            "Demo access only · Session resets when the browser session ends",
            text_alignment="center",
        )
    return False


def current_user():
    return {
        "username": st.session_state["authenticated_user"],
        "display_name": st.session_state["authenticated_display_name"],
        "role": st.session_state["authenticated_role"],
        "player_name": st.session_state["authenticated_player"],
    }


def available_views(role):
    analytics = [
        "Championship overview",
        "Match analysis",
        "Player championship",
        "Squad leaderboards",
        "Match comparison",
        "Data quality",
    ]
    if role == "Admin":
        return [*analytics, "Admin"]
    if role in ["Coach", "Viewer"]:
        return analytics
    if role == "Player":
        return [
            "Championship overview",
            "My player profile",
            "Match comparison",
        ]
    return []


def render_account_controls():
    """Show the current user, role and logout control."""

    user = current_user()
    with st.sidebar:
        st.caption(f"Signed in as **{user['display_name']}**")
        st.badge(user["role"], icon=":material/badge:", color="blue")
        if st.button(
            "Log out",
            icon=":material/logout:",
            width="stretch",
        ):
            log_event(
                LOGGER,
                "logout_succeeded",
                username=user["username"],
                role=user["role"],
            )
            for key in [
                "authenticated",
                "authenticated_user",
                "authenticated_display_name",
                "authenticated_role",
                "authenticated_player",
            ]:
                st.session_state.pop(key, None)
            st.rerun()
