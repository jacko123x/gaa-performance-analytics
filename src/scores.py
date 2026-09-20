"""Parsing and formatting helpers for GAA match scores."""

from dataclasses import dataclass
import math
import numbers
import re


SCORELINE_PATTERN = re.compile(r"^(\d+)\s*[-\u2013\u2014]\s*(\d+)$")
WHOLE_NUMBER_PATTERN = re.compile(r"^\d+(?:\.0+)?$")


@dataclass(frozen=True)
class ParsedScore:
    total: int
    goals: int | None = None
    points: int | None = None

    @property
    def scoreline(self) -> str | None:
        if self.goals is None or self.points is None:
            return None
        return f"{self.goals}-{self.points}"


def parse_match_score(value, *, field_name="Score") -> ParsedScore:
    """Accept a whole-point total or conventional goals-points notation."""

    if value is None or (
        isinstance(value, numbers.Real)
        and not isinstance(value, bool)
        and math.isnan(float(value))
    ):
        raise ValueError(f"{field_name} cannot be blank")

    if isinstance(value, bool):
        raise ValueError(
            f"{field_name} must be a total such as 16 or a score such as 0-16"
        )

    if isinstance(value, numbers.Real):
        numeric_value = float(value)
        if numeric_value < 0 or not numeric_value.is_integer():
            raise ValueError(
                f"{field_name} must be a non-negative whole number or a "
                "GAA score such as 0-16"
            )
        return ParsedScore(total=int(numeric_value))

    cleaned = str(value).strip()
    scoreline_match = SCORELINE_PATTERN.fullmatch(cleaned)
    if scoreline_match:
        goals, points = (int(part) for part in scoreline_match.groups())
        return ParsedScore(
            total=(goals * 3) + points,
            goals=goals,
            points=points,
        )

    if WHOLE_NUMBER_PATTERN.fullmatch(cleaned):
        return ParsedScore(total=int(float(cleaned)))

    raise ValueError(
        f"{field_name} must be a total such as 16 or a GAA score such as 0-16"
    )


def format_match_score(total, goals=None, points=None) -> str:
    """Prefer stored GAA components, falling back to the numeric total."""

    if goals is not None and points is not None:
        return f"{int(goals)}-{int(points)}"
    if total is None:
        return "-"
    return str(int(total))
