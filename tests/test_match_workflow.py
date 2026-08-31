import pandas as pd
import pytest

from src.database.admin_repository import (
    import_match_bundle_db,
    load_audit_events_db,
    load_match_lifecycle_db,
    replace_match_dataset_db,
    transition_match_status_db,
)
from src.database.repository import load_matches_db, load_team_stats_db


def _match_ids(frame):
    return set(frame.get("MatchID", pd.Series(dtype=str)))


def test_match_is_hidden_until_published(sample_bundle, caplog):
    caplog.set_level("INFO")
    match_id = import_match_bundle_db(
        sample_bundle,
        username="test_admin",
    )

    lifecycle = load_match_lifecycle_db().set_index("MatchID")
    assert lifecycle.loc[match_id, "Status"] == "Draft"
    assert bool(lifecycle.loc[match_id, "Complete"])
    assert match_id not in _match_ids(load_matches_db())

    transition_match_status_db(
        match_id,
        "Review",
        username="test_admin",
    )
    assert match_id not in _match_ids(load_matches_db())

    transition_match_status_db(
        match_id,
        "Published",
        username="test_coach",
    )
    assert match_id in _match_ids(load_matches_db())
    assert len(load_audit_events_db(match_id)) == 3
    event_names = [record.getMessage() for record in caplog.records]
    assert "match_imported" in event_names
    assert event_names.count("match_status_changed") == 2


def test_editing_published_data_reopens_match(sample_bundle, caplog):
    caplog.set_level("INFO")
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
        username="test_coach",
    )

    before = sample_bundle["team_stats"].copy()
    after = before.copy()
    after.loc[0, "Attacks"] = 13
    replace_match_dataset_db(
        "team_stats",
        match_id,
        after,
        username="test_admin",
        before_data=before,
    )

    lifecycle = load_match_lifecycle_db().set_index("MatchID")
    assert lifecycle.loc[match_id, "Status"] == "Draft"
    assert match_id not in _match_ids(load_team_stats_db())
    event = load_audit_events_db(match_id).iloc[0]
    assert event["Action"] == "dataset_replaced"
    assert event["Details"]["previous_status"] == "Published"
    assert event["After"][0]["Attacks"] == 13
    assert any(
        record.getMessage() == "match_dataset_replaced"
        for record in caplog.records
    )


def test_invalid_status_transition_is_rejected(sample_bundle):
    match_id = import_match_bundle_db(
        sample_bundle,
        username="test_admin",
    )

    with pytest.raises(ValueError, match="Cannot move"):
        transition_match_status_db(
            match_id,
            "Published",
            username="test_admin",
        )
