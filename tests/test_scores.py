import pytest

from src.scores import format_match_score, parse_match_score


@pytest.mark.parametrize(
    ("value", "total", "goals", "points", "scoreline"),
    [
        (16, 16, None, None, None),
        ("16", 16, None, None, None),
        ("16.0", 16, None, None, None),
        ("0-16", 16, 0, 16, "0-16"),
        ("1 - 14", 17, 1, 14, "1-14"),
        ("2–12", 18, 2, 12, "2-12"),
    ],
)
def test_parse_match_score(value, total, goals, points, scoreline):
    parsed = parse_match_score(value)

    assert parsed.total == total
    assert parsed.goals == goals
    assert parsed.points == points
    assert parsed.scoreline == scoreline


@pytest.mark.parametrize("value", [None, "", "one-fourteen", -1, 16.5])
def test_parse_match_score_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        parse_match_score(value)


def test_format_match_score_prefers_gaa_components():
    assert format_match_score(17, 1, 14) == "1-14"
    assert format_match_score(17) == "17"
