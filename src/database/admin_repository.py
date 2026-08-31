from datetime import date, datetime

import pandas as pd
from sqlalchemy import delete, func, select

from src.database.db import SessionLocal
from src.database.models import (
    AuditEvent,
    KickoutStat,
    Match,
    Player,
    PlayerMatchStat,
    ScoringSource,
    ShootingDetail,
    TeamMatchStat,
    TurnoverStat,
    utc_now,
)
from src.logging_config import get_logger, log_event


MATCH_STATUSES = ("Draft", "Review", "Published")
ALLOWED_STATUS_TRANSITIONS = {
    "Draft": {"Review"},
    "Review": {"Draft", "Published"},
    "Published": {"Draft"},
}
LOGGER = get_logger("gaa_analytics.admin")


def _text(value, default=None):
    if pd.isna(value):
        return default
    cleaned = str(value).strip()
    return cleaned if cleaned else default


def _integer(value, default=0):
    if pd.isna(value) or str(value).strip() == "":
        return default
    return int(float(value))


def _float(value, default=None):
    if pd.isna(value) or str(value).strip() == "":
        return default
    return float(value)


def _boolean(value, default=False):
    if pd.isna(value):
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "yes", "y", "1"}


def _date(value):
    if pd.isna(value) or str(value).strip() == "":
        return None
    if isinstance(value, date):
        return value
    return pd.to_datetime(value, errors="raise").date()


def _json_value(value):
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (date, datetime, pd.Timestamp)):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value


def _frame_snapshot(data):
    return [
        {key: _json_value(value) for key, value in row.items()}
        for row in data.dropna(how="all").to_dict("records")
    ]


def _add_audit_event(
    session,
    *,
    username,
    action,
    match=None,
    dataset=None,
    before_data=None,
    after_data=None,
    details=None,
):
    session.add(
        AuditEvent(
            username=username,
            action=action,
            match_id=match.id if match else None,
            dataset=dataset,
            before_data=before_data,
            after_data=after_data,
            details=details,
        )
    )


def _match_for_code(session, match_code):
    match = session.scalar(
        select(Match).where(Match.match_code == match_code)
    )
    if match is None:
        raise ValueError(f"Unknown MatchID: {match_code}")
    return match


def _save_matches(session, rows):
    for row in rows:
        match_code = _text(row.get("MatchID"))
        if match_code is None:
            raise ValueError("MatchID cannot be blank")

        match = session.scalar(
            select(Match).where(Match.match_code == match_code)
        )
        if match is None:
            match = Match(match_code=match_code)
            session.add(match)

        match.date = _date(row.get("Date"))
        match.competition = _text(row.get("Competition"))
        match.round = _text(row.get("Round"))
        match.venue = _text(row.get("Venue"))
        match.home_team = _text(row.get("HomeTeam"))
        match.away_team = _text(row.get("AwayTeam"))
        match.home_score = _integer(row.get("HomeScore"), default=None)
        match.away_score = _integer(row.get("AwayScore"), default=None)
        match.result = _text(row.get("Result"))


def _team_stat(row, match_id):
    return TeamMatchStat(
        match_id=match_id,
        team=_text(row.get("Team")),
        opponent=_text(row.get("Opponent")),
        goals=_integer(row.get("Goals")),
        points=_integer(row.get("Points")),
        two_pointers=_integer(row.get("TwoPointers")),
        wides=_integer(row.get("Wides")),
        shorts=_integer(row.get("Shorts")),
        kickouts_won=_integer(row.get("KickoutsWon")),
        kickouts_lost=_integer(row.get("KickoutsLost")),
        forced_turnovers=_integer(row.get("ForcedTurnovers")),
        unforced_turnovers=_integer(row.get("UnforcedTurnovers")),
        frees_conceded=_integer(row.get("FreesConceded")),
        breaking_ball_won=_integer(row.get("BreakingBallWon")),
        attacks=_integer(row.get("Attacks")),
        total_shots=_integer(row.get("TotalShots")),
        total_scores=_integer(row.get("TotalScores")),
        shots_play=_integer(row.get("ShotsPlay")),
        scores_play=_integer(row.get("ScoresPlay")),
        shots_placed=_integer(row.get("ShotsPlaced")),
        scores_placed=_integer(row.get("ScoresPlaced")),
    )


def _shooting_stat(row, match_id):
    return ShootingDetail(
        match_id=match_id,
        team=_text(row.get("Team")),
        period=_text(row.get("Period")),
        shot_type=_text(row.get("ShotType")),
        shots_taken=_integer(row.get("ShotsTaken")),
        shots_scored=_integer(row.get("ShotsScored")),
        wides=_integer(row.get("Wides")),
        shorts=_integer(row.get("Shorts")),
        blocked=_integer(row.get("Blocked")),
        post=_integer(row.get("Post")),
        saved=_integer(row.get("Saved")),
    )


def _scoring_source(row, match_id):
    return ScoringSource(
        match_id=match_id,
        team=_text(row.get("Team")),
        source=_text(row.get("Source")),
        scores=_integer(row.get("Scores")),
    )


def _kickout_stat(row, match_id):
    return KickoutStat(
        match_id=match_id,
        team=_text(row.get("Team")),
        period=_text(row.get("Period")),
        kickout_type=_text(row.get("KickoutType")),
        taken=_integer(row.get("Taken")),
        won=_integer(row.get("Won")),
        lost=_integer(row.get("Lost")),
        clean_wins=_integer(row.get("CleanWins")),
        break_wins=_integer(row.get("BreakWins")),
        free_wins=_integer(row.get("FreeWins")),
        sideline_wins=_integer(row.get("SidelineWins")),
    )


def _turnover_stat(row, match_id):
    return TurnoverStat(
        match_id=match_id,
        team=_text(row.get("Team")),
        period=_text(row.get("Period")),
        turnovers_won_forced=_integer(row.get("TurnoversWonForced")),
        turnovers_won_unforced=_integer(row.get("TurnoversWonUnforced")),
        turnovers_lost_forced=_integer(row.get("TurnoversLostForced")),
        turnovers_lost_unforced=_integer(row.get("TurnoversLostUnforced")),
    )


def _player_match_stat(session, row, match_id):
    player_name = _text(row.get("PlayerName"))
    player = session.scalar(
        select(Player).where(Player.player_name == player_name)
    )
    if player is None:
        player = Player(
            player_name=player_name,
            squad_number=_integer(row.get("SquadNumber"), default=None),
        )
        session.add(player)
        session.flush()
    elif row.get("SquadNumber") is not None:
        player.squad_number = _integer(
            row.get("SquadNumber"),
            default=None,
        )

    return PlayerMatchStat(
        match_id=match_id,
        player_id=player.id,
        date=_date(row.get("Date")),
        opponent=_text(row.get("Opponent")),
        home_away=_text(row.get("HomeAway")),
        result=_text(row.get("Result")),
        data_type=_text(row.get("DataType")),
        squad_number=_integer(row.get("SquadNumber"), default=None),
        position=_text(row.get("Position")),
        captain=_boolean(row.get("Captain")),
        started=_boolean(row.get("Started")),
        minutes_played=_float(row.get("MinutesPlayed")),
        possessions=_integer(row.get("Possessions")),
        handpasses_total=_integer(row.get("HandpassesTotal")),
        handpasses_1h=_integer(row.get("Handpasses1H")),
        handpasses_2h=_integer(row.get("Handpasses2H")),
        handpasses_completed=_integer(row.get("HandpassesCompleted")),
        footpasses_total=_integer(row.get("FootpassesTotal")),
        footpasses_1h=_integer(row.get("Footpasses1H")),
        footpasses_2h=_integer(row.get("Footpasses2H")),
        footpasses_completed=_integer(row.get("FootpassesCompleted")),
        incomplete_passes=_integer(row.get("IncompletePasses")),
        kickouts_won=_integer(row.get("KickoutsWon")),
        breaking_balls_won=_integer(row.get("BreakingBallsWon")),
        turnovers_won=_integer(row.get("TurnoversWon")),
        turnovers_lost=_integer(row.get("TurnoversLost")),
        frees_won=_integer(row.get("FreesWon")),
        frees_conceded=_integer(row.get("FreesConceded")),
        assists=_integer(row.get("Assists")),
        points=_integer(row.get("Points")),
        points_play=_integer(row.get("PointsPlay")),
        points_free=_integer(row.get("PointsFree")),
        points_45=_integer(row.get("Points45")),
        goals=_integer(row.get("Goals")),
        two_pointers=_integer(row.get("TwoPointers")),
        shot_attempts=_integer(row.get("ShotAttempts")),
        scores=_integer(row.get("Scores")),
        shot_conversion_pct=_float(row.get("ShotConversionPct")),
        yellow_cards=_integer(row.get("YellowCards")),
        black_cards=_integer(row.get("BlackCards")),
        red_cards=_integer(row.get("RedCards")),
        notes=_text(row.get("Notes")),
    )


DATASET_MODELS = {
    "team_stats": (TeamMatchStat, _team_stat),
    "shooting": (ShootingDetail, _shooting_stat),
    "scoring_sources": (ScoringSource, _scoring_source),
    "kickouts": (KickoutStat, _kickout_stat),
    "turnovers": (TurnoverStat, _turnover_stat),
}

BUNDLE_DATASET_ORDER = [
    "matches",
    "team_stats",
    "shooting",
    "scoring_sources",
    "kickouts",
    "turnovers",
    "player_data",
]


def _replace_match_dataset(
    session,
    dataset_key,
    match_code,
    data: pd.DataFrame,
):
    rows = data.dropna(how="all").to_dict("records")

    if dataset_key == "matches":
        _save_matches(session, rows)
        return

    match = _match_for_code(session, match_code)

    if dataset_key == "player_data":
        session.execute(
            delete(PlayerMatchStat).where(
                PlayerMatchStat.match_id == match.id
            )
        )
        for row in rows:
            session.add(_player_match_stat(session, row, match.id))
        return

    try:
        model, builder = DATASET_MODELS[dataset_key]
    except KeyError as error:
        raise ValueError(f"Unsupported dataset: {dataset_key}") from error

    session.execute(delete(model).where(model.match_id == match.id))
    session.add_all([builder(row, match.id) for row in rows])


def replace_match_dataset_db(
    dataset_key,
    match_code,
    data: pd.DataFrame,
    *,
    username="system",
    before_data=None,
) -> None:
    """Replace one match's dataset atomically in PostgreSQL."""

    row_count = len(data.dropna(how="all"))
    with SessionLocal.begin() as session:
        _replace_match_dataset(
            session,
            dataset_key,
            match_code,
            data,
        )
        session.flush()
        match = _match_for_code(session, match_code)
        previous_status = match.status
        match.status = "Draft"
        match.updated_at = utc_now()
        match.published_at = None
        match.published_by = None
        _add_audit_event(
            session,
            username=username,
            action="dataset_replaced",
            match=match,
            dataset=dataset_key,
            before_data=(
                _frame_snapshot(before_data)
                if isinstance(before_data, pd.DataFrame)
                else before_data
            ),
            after_data=_frame_snapshot(data),
            details={
                "previous_status": previous_status,
                "new_status": "Draft",
                "row_count": row_count,
            },
        )
    log_event(
        LOGGER,
        "match_dataset_replaced",
        username=username,
        match_id=match_code,
        dataset=dataset_key,
        previous_status=previous_status,
        new_status="Draft",
        row_count=row_count,
    )


def _import_match_bundle(session, bundle):
    missing_datasets = [
        key for key in BUNDLE_DATASET_ORDER if key not in bundle
    ]
    if missing_datasets:
        raise ValueError(
            "Missing datasets: " + ", ".join(missing_datasets)
        )

    match_rows = bundle["matches"].dropna(how="all")
    if len(match_rows) != 1:
        raise ValueError("The matches dataset must contain exactly one row")

    match_code = _text(match_rows.iloc[0].get("MatchID"))
    if match_code is None:
        raise ValueError("MatchID cannot be blank")
    if session.scalar(
        select(Match.id).where(Match.match_code == match_code)
    ) is not None:
        raise ValueError(f"MatchID already exists: {match_code}")

    _replace_match_dataset(
        session,
        "matches",
        match_code,
        match_rows,
    )
    session.flush()

    for dataset_key in BUNDLE_DATASET_ORDER[1:]:
        _replace_match_dataset(
            session,
            dataset_key,
            match_code,
            bundle[dataset_key],
        )

    return match_code


def import_match_bundle_db(bundle, *, username="system") -> str:
    """Import every dataset for one new match in a single transaction."""

    with SessionLocal.begin() as session:
        match_code = _import_match_bundle(session, bundle)
        match = _match_for_code(session, match_code)
        match.status = "Draft"
        match.updated_at = utc_now()
        _add_audit_event(
            session,
            username=username,
            action="match_imported",
            match=match,
            after_data={
                key: _frame_snapshot(value)
                for key, value in bundle.items()
            },
            details={
                "status": "Draft",
                "row_counts": {
                    key: len(value.dropna(how="all"))
                    for key, value in bundle.items()
                },
            },
        )
    log_event(
        LOGGER,
        "match_imported",
        username=username,
        match_id=match_code,
        status="Draft",
        row_counts={
            key: len(value.dropna(how="all"))
            for key, value in bundle.items()
        },
    )
    return match_code


def load_match_lifecycle_db() -> pd.DataFrame:
    """Return every match with publication state and dataset completeness."""

    child_models = {
        "Team stats": TeamMatchStat,
        "Shooting": ShootingDetail,
        "Scoring sources": ScoringSource,
        "Kickouts": KickoutStat,
        "Turnovers": TurnoverStat,
        "Player data": PlayerMatchStat,
    }
    with SessionLocal() as session:
        matches = session.scalars(
            select(Match).order_by(Match.date, Match.id)
        ).all()
        rows = []
        for match in matches:
            counts = {
                label: session.scalar(
                    select(func.count())
                    .select_from(model)
                    .where(model.match_id == match.id)
                )
                for label, model in child_models.items()
            }
            missing = [label for label, count in counts.items() if not count]
            rows.append(
                {
                    "MatchID": match.match_code,
                    "Date": match.date,
                    "Fixture": f"{match.home_team} v {match.away_team}",
                    "Status": match.status,
                    "Complete": not missing,
                    "Missing": ", ".join(missing),
                    "Updated": match.updated_at,
                    "Published": match.published_at,
                    "PublishedBy": match.published_by,
                    **counts,
                }
            )
        return pd.DataFrame(rows)


def transition_match_status_db(
    match_code,
    new_status,
    *,
    username,
    details=None,
) -> None:
    if new_status not in MATCH_STATUSES:
        raise ValueError(f"Unknown match status: {new_status}")

    with SessionLocal.begin() as session:
        match = _match_for_code(session, match_code)
        old_status = match.status
        if new_status not in ALLOWED_STATUS_TRANSITIONS[old_status]:
            raise ValueError(
                f"Cannot move {match_code} from {old_status} to {new_status}"
            )
        match.status = new_status
        match.updated_at = utc_now()
        if new_status == "Published":
            match.published_at = utc_now()
            match.published_by = username
        else:
            match.published_at = None
            match.published_by = None
        _add_audit_event(
            session,
            username=username,
            action="status_changed",
            match=match,
            before_data={"status": old_status},
            after_data={"status": new_status},
            details=details,
        )
    log_event(
        LOGGER,
        "match_status_changed",
        username=username,
        match_id=match_code,
        previous_status=old_status,
        new_status=new_status,
        published=new_status == "Published",
    )


def load_audit_events_db(match_code=None) -> pd.DataFrame:
    with SessionLocal() as session:
        statement = (
            select(AuditEvent, Match)
            .outerjoin(Match, AuditEvent.match_id == Match.id)
            .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
        )
        if match_code:
            statement = statement.where(Match.match_code == match_code)
        rows = session.execute(statement).all()
        return pd.DataFrame(
            [
                {
                    "When": event.created_at,
                    "User": event.username,
                    "MatchID": match.match_code if match else None,
                    "Action": event.action,
                    "Dataset": event.dataset,
                    "Before": event.before_data,
                    "After": event.after_data,
                    "Details": event.details,
                }
                for event, match in rows
            ]
        )
