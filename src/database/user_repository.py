import pandas as pd
from sqlalchemy import select

from src.database.db import SessionLocal
from src.database.models import Player, User
from src.database.security import hash_password
from src.logging_config import get_logger, log_event


USER_COLUMNS = [
    "UserID",
    "Username",
    "DisplayName",
    "Role",
    "PlayerName",
    "Active",
]
LOGGER = get_logger("gaa_analytics.users")


def load_users_db() -> pd.DataFrame:
    with SessionLocal() as session:
        rows = session.execute(
            select(User, Player)
            .outerjoin(Player, User.player_id == Player.id)
            .order_by(User.id)
        ).all()

        return pd.DataFrame(
            [
                {
                    "UserID": user.id,
                    "Username": user.username,
                    "DisplayName": user.display_name,
                    "Role": user.role,
                    "PlayerName": player.player_name if player else "",
                    "Active": user.is_active,
                }
                for user, player in rows
            ],
            columns=USER_COLUMNS,
        )


def find_active_user_db(username: str):
    normalized_username = username.strip().lower()

    with SessionLocal() as session:
        row = session.execute(
            select(User, Player)
            .outerjoin(Player, User.player_id == Player.id)
            .where(
                User.username == normalized_username,
                User.is_active.is_(True),
            )
        ).one_or_none()

        if row is None:
            return None

        user, player = row
        return {
            "Username": user.username,
            "DisplayName": user.display_name,
            "Role": user.role,
            "PlayerName": player.player_name if player else "",
            "PasswordHash": user.password_hash,
        }


def _optional_int(value):
    if pd.isna(value) or str(value).strip() == "":
        return None
    return int(value)


def _save_users(session, users: pd.DataFrame, default_password: str) -> None:
    players = {
        player.player_name: player
        for player in session.scalars(select(Player)).all()
    }
    existing_users = {
        user.id: user
        for user in session.scalars(select(User)).all()
    }
    retained_ids = set()

    for row in users.to_dict("records"):
        user_id = _optional_int(row.get("UserID"))
        username = str(row["Username"]).strip().lower()
        display_name = str(row["DisplayName"]).strip() or username
        player_name = str(row.get("PlayerName", "")).strip()
        player = players.get(player_name) if player_name else None

        if player_name and player is None:
            raise ValueError(f"Unknown player: {player_name}")

        if user_id is None:
            user = User(
                password_hash=hash_password(default_password),
            )
            session.add(user)
        else:
            user = existing_users.get(user_id)
            if user is None:
                raise ValueError(f"Unknown user ID: {user_id}")
            retained_ids.add(user_id)

        user.username = username
        user.display_name = display_name
        user.role = str(row["Role"]).strip()
        user.player = player
        user.is_active = bool(row["Active"])

    for user_id, user in existing_users.items():
        if user_id not in retained_ids:
            session.delete(user)


def save_users_db(
    users: pd.DataFrame,
    default_password: str,
    *,
    actor_username="system",
) -> None:
    with SessionLocal.begin() as session:
        _save_users(session, users, default_password)
    log_event(
        LOGGER,
        "users_saved",
        username=actor_username,
        user_count=len(users),
        active_count=int(users["Active"].astype(bool).sum()),
    )
