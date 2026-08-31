"""Admin area orchestration."""

import streamlit as st

from admin_services import _read_dataset
from admin_views.data_entry_view import _render_data_entry
from admin_views.import_view import _render_new_match_import
from admin_views.review_view import _render_match_review
from admin_views.users_view import _render_user_management


def render_admin(team_name, actor_username):
    st.header("Admin")
    st.caption("Add or edit match data and manage role-based access")
    import_tab, data_tab, review_tab, users_tab = st.tabs(
        ["New match import", "Data entry", "Review & publish", "Users"]
    )
    with import_tab:
        _render_new_match_import(team_name, actor_username)
    with data_tab:
        _render_data_entry(team_name, actor_username)
    with review_tab:
        _render_match_review(team_name, actor_username)
    with users_tab:
        _render_user_management(
            _read_dataset("player_data"),
            actor_username,
        )
