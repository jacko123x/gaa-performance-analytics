from datetime import UTC, date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.db import Base


def utc_now():
    """Return naive UTC for database columns stored without a timezone."""

    return datetime.now(UTC).replace(tzinfo=None)


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    date: Mapped[date | None] = mapped_column(Date)
    competition: Mapped[str | None] = mapped_column(String(150))
    round: Mapped[str | None] = mapped_column(String(100))
    venue: Mapped[str | None] = mapped_column(String(150))

    home_team: Mapped[str] = mapped_column(String(150), nullable=False)
    away_team: Mapped[str] = mapped_column(String(150), nullable=False)

    home_score: Mapped[int | None] = mapped_column(Integer)
    away_score: Mapped[int | None] = mapped_column(Integer)
    result: Mapped[str | None] = mapped_column(String(20))

    status: Mapped[str] = mapped_column(
        String(20),
        default="Draft",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime)
    published_by: Mapped[str | None] = mapped_column(String(100))

    team_stats = relationship(
        "TeamMatchStat",
        back_populates="match",
        cascade="all, delete-orphan",
    )

    shooting = relationship(
        "ShootingDetail",
        back_populates="match",
        cascade="all, delete-orphan",
    )

    scoring_sources = relationship(
        "ScoringSource",
        back_populates="match",
        cascade="all, delete-orphan",
    )

    kickouts = relationship(
        "KickoutStat",
        back_populates="match",
        cascade="all, delete-orphan",
    )

    turnovers = relationship(
        "TurnoverStat",
        back_populates="match",
        cascade="all, delete-orphan",
    )

    player_stats = relationship(
        "PlayerMatchStat",
        back_populates="match",
        cascade="all, delete-orphan",
    )

    audit_events = relationship(
        "AuditEvent",
        back_populates="match",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('Draft', 'Review', 'Published')",
            name="ck_matches_status",
        ),
    )


class TeamMatchStat(Base):
    __tablename__ = "team_match_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
    )

    team: Mapped[str] = mapped_column(String(150), nullable=False)
    opponent: Mapped[str] = mapped_column(String(150), nullable=False)

    goals: Mapped[int] = mapped_column(Integer, default=0)
    points: Mapped[int] = mapped_column(Integer, default=0)
    two_pointers: Mapped[int] = mapped_column(Integer, default=0)

    wides: Mapped[int] = mapped_column(Integer, default=0)
    shorts: Mapped[int] = mapped_column(Integer, default=0)

    kickouts_won: Mapped[int] = mapped_column(Integer, default=0)
    kickouts_lost: Mapped[int] = mapped_column(Integer, default=0)

    forced_turnovers: Mapped[int] = mapped_column(Integer, default=0)
    unforced_turnovers: Mapped[int] = mapped_column(Integer, default=0)

    frees_conceded: Mapped[int] = mapped_column(Integer, default=0)
    breaking_ball_won: Mapped[int] = mapped_column(Integer, default=0)

    attacks: Mapped[int] = mapped_column(Integer, default=0)

    total_shots: Mapped[int] = mapped_column(Integer, default=0)
    total_scores: Mapped[int] = mapped_column(Integer, default=0)

    shots_play: Mapped[int] = mapped_column(Integer, default=0)
    scores_play: Mapped[int] = mapped_column(Integer, default=0)

    shots_placed: Mapped[int] = mapped_column(Integer, default=0)
    scores_placed: Mapped[int] = mapped_column(Integer, default=0)

    match = relationship("Match", back_populates="team_stats")

    __table_args__ = (
        UniqueConstraint(
            "match_id",
            "team",
            name="uq_team_match_stats_match_team",
        ),
    )


class ShootingDetail(Base):
    __tablename__ = "shooting_detail"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
    )

    team: Mapped[str] = mapped_column(String(150), nullable=False)
    period: Mapped[str] = mapped_column(String(20), nullable=False)
    shot_type: Mapped[str] = mapped_column(String(50), nullable=False)

    shots_taken: Mapped[int] = mapped_column(Integer, default=0)
    shots_scored: Mapped[int] = mapped_column(Integer, default=0)

    wides: Mapped[int] = mapped_column(Integer, default=0)
    shorts: Mapped[int] = mapped_column(Integer, default=0)
    blocked: Mapped[int] = mapped_column(Integer, default=0)
    post: Mapped[int] = mapped_column(Integer, default=0)
    saved: Mapped[int] = mapped_column(Integer, default=0)

    match = relationship("Match", back_populates="shooting")

    __table_args__ = (
        UniqueConstraint(
            "match_id",
            "team",
            "period",
            "shot_type",
            name="uq_shooting_match_team_period_type",
        ),
    )


class ScoringSource(Base):
    __tablename__ = "scoring_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
    )

    team: Mapped[str] = mapped_column(String(150), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    scores: Mapped[int] = mapped_column(Integer, default=0)

    match = relationship("Match", back_populates="scoring_sources")

    __table_args__ = (
        UniqueConstraint(
            "match_id",
            "team",
            "source",
            name="uq_scoring_source_match_team_source",
        ),
    )


class KickoutStat(Base):
    __tablename__ = "kickout_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
    )

    team: Mapped[str] = mapped_column(String(150), nullable=False)
    period: Mapped[str] = mapped_column(String(20), nullable=False)
    kickout_type: Mapped[str] = mapped_column(String(20), nullable=False)

    taken: Mapped[int] = mapped_column(Integer, default=0)
    won: Mapped[int] = mapped_column(Integer, default=0)
    lost: Mapped[int] = mapped_column(Integer, default=0)

    clean_wins: Mapped[int] = mapped_column(Integer, default=0)
    break_wins: Mapped[int] = mapped_column(Integer, default=0)
    free_wins: Mapped[int] = mapped_column(Integer, default=0)
    sideline_wins: Mapped[int] = mapped_column(Integer, default=0)

    match = relationship("Match", back_populates="kickouts")

    __table_args__ = (
        UniqueConstraint(
            "match_id",
            "team",
            "period",
            "kickout_type",
            name="uq_kickout_match_team_period_type",
        ),
    )


class TurnoverStat(Base):
    __tablename__ = "turnover_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
    )

    team: Mapped[str] = mapped_column(String(150), nullable=False)
    period: Mapped[str] = mapped_column(String(20), nullable=False)

    turnovers_won_forced: Mapped[int] = mapped_column(Integer, default=0)
    turnovers_won_unforced: Mapped[int] = mapped_column(Integer, default=0)

    turnovers_lost_forced: Mapped[int] = mapped_column(Integer, default=0)
    turnovers_lost_unforced: Mapped[int] = mapped_column(Integer, default=0)

    match = relationship("Match", back_populates="turnovers")

    __table_args__ = (
        UniqueConstraint(
            "match_id",
            "team",
            "period",
            name="uq_turnover_match_team_period",
        ),
    )


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    player_name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    squad_number: Mapped[int | None] = mapped_column(Integer)

    active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )

    match_stats = relationship(
        "PlayerMatchStat",
        back_populates="player",
    )

    users = relationship(
        "User",
        back_populates="player",
    )


class PlayerMatchStat(Base):
    __tablename__ = "player_match_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
    )

    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id"),
        nullable=False,
    )

    date: Mapped[date | None] = mapped_column(Date)
    opponent: Mapped[str | None] = mapped_column(String(150))
    home_away: Mapped[str | None] = mapped_column(String(20))
    result: Mapped[str | None] = mapped_column(String(20))
    data_type: Mapped[str | None] = mapped_column(String(50))

    squad_number: Mapped[int | None] = mapped_column(Integer)
    position: Mapped[str | None] = mapped_column(String(100))

    captain: Mapped[bool] = mapped_column(Boolean, default=False)
    started: Mapped[bool] = mapped_column(Boolean, default=False)

    minutes_played: Mapped[float | None] = mapped_column(Float)

    possessions: Mapped[int] = mapped_column(Integer, default=0)

    handpasses_total: Mapped[int] = mapped_column(Integer, default=0)
    handpasses_1h: Mapped[int] = mapped_column(Integer, default=0)
    handpasses_2h: Mapped[int] = mapped_column(Integer, default=0)
    handpasses_completed: Mapped[int] = mapped_column(Integer, default=0)

    footpasses_total: Mapped[int] = mapped_column(Integer, default=0)
    footpasses_1h: Mapped[int] = mapped_column(Integer, default=0)
    footpasses_2h: Mapped[int] = mapped_column(Integer, default=0)
    footpasses_completed: Mapped[int] = mapped_column(Integer, default=0)

    incomplete_passes: Mapped[int] = mapped_column(Integer, default=0)

    kickouts_won: Mapped[int] = mapped_column(Integer, default=0)
    breaking_balls_won: Mapped[int] = mapped_column(Integer, default=0)

    turnovers_won: Mapped[int] = mapped_column(Integer, default=0)
    turnovers_lost: Mapped[int] = mapped_column(Integer, default=0)

    frees_won: Mapped[int] = mapped_column(Integer, default=0)
    frees_conceded: Mapped[int] = mapped_column(Integer, default=0)

    assists: Mapped[int] = mapped_column(Integer, default=0)

    points: Mapped[int] = mapped_column(Integer, default=0)
    points_play: Mapped[int] = mapped_column(Integer, default=0)
    points_free: Mapped[int] = mapped_column(Integer, default=0)
    points_45: Mapped[int] = mapped_column(Integer, default=0)
    goals: Mapped[int] = mapped_column(Integer, default=0)
    two_pointers: Mapped[int] = mapped_column(Integer, default=0)

    shot_attempts: Mapped[int] = mapped_column(Integer, default=0)
    scores: Mapped[int] = mapped_column(Integer, default=0)
    shot_conversion_pct: Mapped[float | None] = mapped_column(Float)

    yellow_cards: Mapped[int] = mapped_column(Integer, default=0)
    black_cards: Mapped[int] = mapped_column(Integer, default=0)
    red_cards: Mapped[int] = mapped_column(Integer, default=0)

    notes: Mapped[str | None] = mapped_column(Text)

    match = relationship("Match", back_populates="player_stats")
    player = relationship("Player", back_populates="match_stats")

    __table_args__ = (
        UniqueConstraint(
            "match_id",
            "player_id",
            name="uq_player_match_stats_match_player",
        ),
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(150), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False)

    player_id: Mapped[int | None] = mapped_column(
        ForeignKey("players.id"),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )

    player = relationship("Player", back_populates="users")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    match_id: Mapped[int | None] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"),
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    dataset: Mapped[str | None] = mapped_column(String(50))
    before_data: Mapped[dict | list | None] = mapped_column(JSON)
    after_data: Mapped[dict | list | None] = mapped_column(JSON)
    details: Mapped[dict | None] = mapped_column(JSON)

    match = relationship("Match", back_populates="audit_events")
