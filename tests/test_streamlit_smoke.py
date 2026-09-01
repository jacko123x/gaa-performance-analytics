import pytest
from sqlalchemy import select, text
import streamlit as st
from streamlit.testing.v1 import AppTest

from src.database.admin_repository import (
    import_match_bundle_db,
    transition_match_status_db,
)
from src.database.db import SessionLocal, engine
from src.database.models import User
from src.database.security import verify_password


def _seed_dashboard(sample_bundle):
    match_id = import_match_bundle_db(
        sample_bundle,
        username="test_admin",
    )
    transition_match_status_db(
        match_id,
        "Review",
        username="test_admin",
    )
    transition_match_status_db(
        match_id,
        "Published",
        username="test_admin",
    )
    with SessionLocal.begin() as session:
        session.add(
            User(
                username="admin",
                display_name="Test Admin",
                password_hash="unused-in-authenticated-smoke-tests",
                role="Admin",
                is_active=True,
            )
        )

    return match_id


@pytest.mark.parametrize(
    "view",
    [
        "Championship overview",
        "Match analysis",
        "Player championship",
        "Squad leaderboards",
        "Match comparison",
        "Data quality",
        "Admin",
    ],
)
def test_admin_dashboard_views_render(sample_bundle, view):
    _seed_dashboard(sample_bundle)

    app = AppTest.from_file("dashboard/app.py", default_timeout=45)
    app.session_state["authenticated"] = True
    app.session_state["authenticated_user"] = "admin"
    app.session_state["authenticated_display_name"] = "Test Admin"
    app.session_state["authenticated_role"] = "Admin"
    app.session_state["authenticated_player"] = None
    app.session_state["analysis_view"] = view
    app.run()

    assert not app.exception
    assert any(radio.value == view for radio in app.radio)
    if view == "Admin":
        assert any("Review & publish" in tab.label for tab in app.tabs)
        assert any(
            subheader.value == "Password management"
            for subheader in app.subheader
        )
        assert any(
            button.label == "Reset password"
            for button in app.button
        )


def test_player_profile_renders(sample_bundle):
    _seed_dashboard(sample_bundle)

    app = AppTest.from_file("dashboard/app.py", default_timeout=45)
    app.session_state["authenticated"] = True
    app.session_state["authenticated_user"] = "player"
    app.session_state["authenticated_display_name"] = "Test Player"
    app.session_state["authenticated_role"] = "Player"
    app.session_state["authenticated_player"] = "Test Player"
    app.session_state["analysis_view"] = "My player profile"
    app.run()

    assert not app.exception
    assert any(
        radio.value == "My player profile"
        for radio in app.radio
    )


def test_admin_can_rotate_active_user_passwords(sample_bundle):
    _seed_dashboard(sample_bundle)
    new_password = "hosted-shared-password"

    app = AppTest.from_file("dashboard/app.py", default_timeout=45)
    app.session_state["authenticated"] = True
    app.session_state["authenticated_user"] = "admin"
    app.session_state["authenticated_display_name"] = "Test Admin"
    app.session_state["authenticated_role"] = "Admin"
    app.session_state["authenticated_player"] = None
    app.session_state["analysis_view"] = "Admin"
    app.run()

    next(
        field for field in app.text_input
        if field.label == "New password"
    ).set_value(new_password)
    next(
        field for field in app.text_input
        if field.label == "Confirm new password"
    ).set_value(new_password)
    next(
        field for field in app.text_input
        if field.label == 'Type "RESET ALL" to confirm'
    ).set_value("RESET ALL")
    next(
        button for button in app.button
        if button.label == "Reset password"
    ).click()
    app.run()

    assert not app.exception
    assert any(
        "Password reset for 1 active account" in message.value
        for message in app.success
    )
    with SessionLocal() as session:
        user = session.scalar(
            select(User).where(User.username == "admin")
        )
        assert verify_password(new_password, user.password_hash)


def test_database_failure_shows_safe_maintenance_screen(sample_bundle):
    _seed_dashboard(sample_bundle)
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE turnover_stats"))
    st.cache_data.clear()

    app = AppTest.from_file("dashboard/app.py", default_timeout=45)
    app.run()

    assert not app.exception
    assert any(
        "Dashboard temporarily unavailable" in subheader.value
        for subheader in app.subheader
    )
    assert any(button.label == "Try again" for button in app.button)
    rendered_text = " ".join(
        [item.value for item in app.markdown]
        + [item.value for item in app.caption]
    )
    assert "postgresql://" not in rendered_text
    assert "sqlite" not in rendered_text.lower()
