import pytest
from sqlalchemy import select

from src.database.db import SessionLocal
from src.database.models import User
from src.database.security import hash_password, verify_password
from src.database.user_repository import (
    reset_active_user_passwords_db,
    reset_user_password_db,
    validate_new_password,
)


def _seed_users():
    with SessionLocal.begin() as session:
        session.add_all(
            [
                User(
                    username="admin",
                    display_name="Admin",
                    password_hash=hash_password("old-password"),
                    role="Admin",
                    is_active=True,
                ),
                User(
                    username="coach",
                    display_name="Coach",
                    password_hash=hash_password("old-password"),
                    role="Coach",
                    is_active=True,
                ),
                User(
                    username="inactive",
                    display_name="Inactive viewer",
                    password_hash=hash_password("old-password"),
                    role="Viewer",
                    is_active=False,
                ),
            ]
        )


def _password_hashes():
    with SessionLocal() as session:
        return {
            user.username: user.password_hash
            for user in session.scalars(
                select(User).order_by(User.username)
            ).all()
        }


def test_reset_all_updates_only_active_accounts(caplog):
    _seed_users()
    previous_hashes = _password_hashes()
    new_password = "new-shared-password"
    caplog.set_level("INFO")

    reset_count = reset_active_user_passwords_db(
        new_password,
        actor_username="admin",
    )

    updated_hashes = _password_hashes()
    assert reset_count == 2
    assert verify_password(new_password, updated_hashes["admin"])
    assert verify_password(new_password, updated_hashes["coach"])
    assert updated_hashes["admin"] != updated_hashes["coach"]
    assert updated_hashes["inactive"] == previous_hashes["inactive"]

    event = next(
        record
        for record in caplog.records
        if record.getMessage() == "user_passwords_reset"
    )
    assert event.event_data["reset_scope"] == "all_active_users"
    assert event.event_data["user_count"] == 2
    assert new_password not in str(event.event_data)


def test_reset_single_user_leaves_other_accounts_unchanged():
    _seed_users()
    previous_hashes = _password_hashes()
    new_password = "individual-password"

    reset_count = reset_user_password_db(
        " Coach ",
        new_password,
        actor_username="admin",
    )

    updated_hashes = _password_hashes()
    assert reset_count == 1
    assert verify_password(new_password, updated_hashes["coach"])
    assert updated_hashes["admin"] == previous_hashes["admin"]
    assert updated_hashes["inactive"] == previous_hashes["inactive"]


def test_password_reset_rejects_invalid_or_inactive_targets():
    _seed_users()
    previous_hashes = _password_hashes()

    assert validate_new_password("too-short")
    assert validate_new_password(" valid-length-password ")
    with pytest.raises(ValueError, match="at least 12"):
        reset_active_user_passwords_db("too-short")
    with pytest.raises(ValueError, match="No active users"):
        reset_user_password_db("inactive", "valid-new-password")

    assert _password_hashes() == previous_hashes
