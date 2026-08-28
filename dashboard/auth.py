import hmac

import streamlit as st


# Demo-only credentials. This is an access gate for trying the login flow,
# not a secure replacement for managed authentication.
DEMO_USERNAME = "coach"
DEMO_PASSWORD = "stacks2026"


def _credentials_match(username, password):
    return hmac.compare_digest(
        username.strip(),
        DEMO_USERNAME,
    ) and hmac.compare_digest(
        password,
        DEMO_PASSWORD,
    )


def require_login():
    """Render the login gate and return True for an authenticated session."""

    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("authenticated_user", None)

    if st.session_state["authenticated"]:
        return True

    st.title(
        "Austin Stacks Performance Platform",
        text_alignment="center",
    )
    st.caption(
        "Club Championship 2026",
        text_alignment="center",
    )
    st.space("medium")

    _, login_column, _ = st.columns([1, 1.25, 1])
    with login_column.container(border=True):
        st.subheader(
            ":material/lock: Dashboard access",
            text_alignment="center",
        )
        st.caption(
            "Sign in to view team and player performance data.",
            text_alignment="center",
        )

        with st.form("dashboard_login", clear_on_submit=True):
            username = st.text_input(
                "Username",
                autocomplete="username",
            )
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
            if _credentials_match(username, password):
                st.session_state["authenticated"] = True
                st.session_state["authenticated_user"] = username.strip()
                st.rerun()
            else:
                st.error(
                    "The username or password is incorrect.",
                    icon=":material/error:",
                )

        st.caption(
            "Demo access only · Session resets when the browser session ends",
            text_alignment="center",
        )

    return False


def render_account_controls():
    """Show the current demo user and allow the session to be locked."""

    with st.sidebar:
        st.caption(
            f"Signed in as **{st.session_state['authenticated_user']}**"
        )
        if st.button(
            "Log out",
            icon=":material/logout:",
            width="stretch",
        ):
            st.session_state["authenticated"] = False
            st.session_state["authenticated_user"] = None
            st.rerun()
