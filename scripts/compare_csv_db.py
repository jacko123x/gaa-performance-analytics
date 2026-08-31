import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


from src.csv_io import (
    load_kickout_stats_csv,
    load_matches_csv,
    load_player_match_data_csv,
    load_scoring_sources_csv,
    load_shooting_detail_csv,
    load_team_stats_csv,
    load_turnover_stats_csv,
)

from src.database.repository import (
    load_matches_db,
    load_team_stats_db,
    load_shooting_detail_db,
    load_scoring_sources_db,
    load_kickout_stats_db,
    load_turnover_stats_db,
    load_player_match_data_db,
)


checks = [
    ("matches", load_matches_csv, load_matches_db),
    ("team_stats", load_team_stats_csv, load_team_stats_db),
    ("shooting", load_shooting_detail_csv, load_shooting_detail_db),
    ("scoring_sources", load_scoring_sources_csv, load_scoring_sources_db),
    ("kickouts", load_kickout_stats_csv, load_kickout_stats_db),
    ("turnovers", load_turnover_stats_csv, load_turnover_stats_db),
    ("player_data", load_player_match_data_csv, load_player_match_data_db),
]


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize CSV-loaded and DB-loaded DataFrames so equivalent
    values compare correctly.

    Examples:
        60   == 60.0
        1.0  == 1
        NaN  == None / blank
    """

    df = df.copy()

    # ---------------------------------------------------------
    # Normalize dates
    # ---------------------------------------------------------

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(
            df["Date"],
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")

    for column in ["Captain", "Started"]:
        if column in df.columns:
            df[column] = (
                df[column]
                .astype(str)
                .str.strip()
                .str.lower()
                .map(
                    {
                        "true": 1,
                        "false": 0,
                        "yes": 1,
                        "no": 0,
                        "1": 1,
                        "0": 0,
                        "1.0": 1,
                        "0.0": 0,
                    }
                )
                .fillna(0)
            )

    # ---------------------------------------------------------
    # Normalize numeric columns
    # ---------------------------------------------------------

    for column in df.columns:
        if column == "Date":
            continue

        original = df[column]

        converted = pd.to_numeric(
            original,
            errors="coerce",
        )

        # Count meaningful original values.
        original_non_null = (
            original
            .replace("", pd.NA)
            .notna()
            .sum()
        )

        converted_non_null = converted.notna().sum()

        # If every populated value can be converted to a number,
        # treat this as a numeric column.
        if (
            original_non_null > 0
            and original_non_null == converted_non_null
        ):
            df[column] = converted

    # ---------------------------------------------------------
    # Normalize text / boolean / null columns
    # ---------------------------------------------------------

    for column in df.columns:
        if pd.api.types.is_numeric_dtype(df[column]):
            continue

        df[column] = (
            df[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        # Normalize common boolean representations.
        df[column] = df[column].replace(
            {
                "True": "true",
                "False": "false",
                "TRUE": "true",
                "FALSE": "false",
                "Yes": "true",
                "No": "false",
                "YES": "true",
                "NO": "false",
            }
        )

    # ---------------------------------------------------------
    # Normalize numeric NaNs
    # ---------------------------------------------------------

    for column in df.columns:
        if pd.api.types.is_numeric_dtype(df[column]):
            df[column] = df[column].fillna(0).astype("Float64")

    # ---------------------------------------------------------
    # Sort consistently
    # ---------------------------------------------------------

    return (
        df.sort_values(
            by=list(df.columns),
            kind="stable",
            na_position="last",
        )
        .reset_index(drop=True)
    )


def compare_dataframes(
    name: str,
    csv_df: pd.DataFrame,
    db_df: pd.DataFrame,
) -> bool:
    print()
    print("=" * 60)
    print(name)
    print("=" * 60)

    print(f"CSV rows: {len(csv_df)}")
    print(f"DB rows:  {len(db_df)}")

    # ---------------------------------------------------------
    # Row count check
    # ---------------------------------------------------------

    if len(csv_df) != len(db_df):
        print("❌ Row count mismatch")
        return False

    print("✓ Row counts match")

    # ---------------------------------------------------------
    # Column check
    # ---------------------------------------------------------

    if list(csv_df.columns) != list(db_df.columns):
        print("❌ Column order/name mismatch")

        print()
        print("CSV columns:")
        print(list(csv_df.columns))

        print()
        print("DB columns:")
        print(list(db_df.columns))

        print()
        print(
            "CSV only:",
            set(csv_df.columns) - set(db_df.columns),
        )

        print(
            "DB only:",
            set(db_df.columns) - set(csv_df.columns),
        )

        return False

    print("✓ Columns match")

    # ---------------------------------------------------------
    # Normalize data
    # ---------------------------------------------------------

    csv_normalized = normalize_dataframe(csv_df)
    db_normalized = normalize_dataframe(db_df)

    # ---------------------------------------------------------
    # Value comparison
    # ---------------------------------------------------------

    try:
        pd.testing.assert_frame_equal(
            csv_normalized,
            db_normalized,
            check_dtype=False,
            check_exact=False,
            rtol=1e-9,
            atol=1e-9,
        )

        print("✓ Data values match")
        return True

    except AssertionError:
        print("❌ Data mismatch detected")

        # Create copies using string representation solely
        # for displaying meaningful differences.
        csv_display = csv_normalized.copy()
        db_display = db_normalized.copy()

        for column in csv_display.columns:
            csv_display[column] = (
                csv_display[column]
                .astype(str)
                .replace("<NA>", "")
                .replace("nan", "")
            )

            db_display[column] = (
                db_display[column]
                .astype(str)
                .replace("<NA>", "")
                .replace("nan", "")
            )

        comparison = csv_display.compare(
            db_display,
            keep_shape=False,
            keep_equal=False,
        )

        if comparison.empty:
            print(
                "No meaningful value differences found. "
                "The mismatch is likely caused by dtype representation."
            )
        else:
            print()
            print("Differences:")
            print(comparison)

        return False


def main():
    all_passed = True

    print()
    print("=" * 60)
    print("GAA Analytics CSV vs PostgreSQL Validation")
    print("=" * 60)

    for name, csv_loader, db_loader in checks:
        csv_df = csv_loader()
        db_df = db_loader()

        passed = compare_dataframes(
            name,
            csv_df,
            db_df,
        )

        if not passed:
            all_passed = False

    print()
    print("=" * 60)

    if all_passed:
        print("ALL CSV AND DATABASE DATA MATCH")
        print("Database migration validation PASSED.")
    else:
        print("ONE OR MORE DATASETS DO NOT MATCH")
        print("Database migration validation FAILED.")

    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
