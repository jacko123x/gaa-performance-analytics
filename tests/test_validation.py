import pandas as pd

from src.validation import run_data_quality_checks


def test_quality_checks_sort_mixed_database_and_uploaded_dates(sample_bundle):
    existing_match = sample_bundle["matches"].copy()
    existing_match["Date"] = pd.to_datetime(existing_match["Date"])

    uploaded_match = existing_match.copy()
    uploaded_match["MatchID"] = "uploaded_match"
    uploaded_match["Date"] = "2026-09-05"
    matches = pd.concat(
        [existing_match, uploaded_match],
        ignore_index=True,
    )

    report = run_data_quality_checks(
        matches=matches,
        team_data=sample_bundle["team_stats"].iloc[0:0],
        shooting_data=sample_bundle["shooting"].iloc[0:0],
        scoring_sources=sample_bundle["scoring_sources"].iloc[0:0],
        kickout_data=sample_bundle["kickouts"].iloc[0:0],
        turnover_data=sample_bundle["turnovers"].iloc[0:0],
        player_data=sample_bundle["player_data"].iloc[0:0],
        team_name="Austin Stacks",
    )

    assert not report.empty
    assert "uploaded_match" in set(report["MatchID"])
