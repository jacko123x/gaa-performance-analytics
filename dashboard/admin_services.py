from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd
from load_data import (
    load_kickout_stats,
    load_matches,
    load_player_match_data,
    load_scoring_sources,
    load_shooting_detail,
    load_team_stats,
    load_turnover_stats,
)
from validation import run_data_quality_checks, validate_team_stats


DATASET_CONFIG = {
    "Matches": {
        "key": "matches",
        "primary_key": ["MatchID"],
    },
    "Team stats": {
        "key": "team_stats",
        "primary_key": ["MatchID", "Team"],
    },
    "Shooting": {
        "key": "shooting",
        "primary_key": ["MatchID", "Team", "Period", "ShotType"],
    },
    "Scoring sources": {
        "key": "scoring_sources",
        "primary_key": ["MatchID", "Team", "Source"],
    },
    "Kickouts": {
        "key": "kickouts",
        "primary_key": ["MatchID", "Team", "Period", "KickoutType"],
    },
    "Turnovers": {
        "key": "turnovers",
        "primary_key": ["MatchID", "Team", "Period"],
    },
    "Player data": {
        "key": "player_data",
        "primary_key": ["MatchID", "PlayerName"],
    },
}

DATASET_LOADERS = {
    "matches": lambda: load_matches(include_unpublished=True),
    "team_stats": lambda: load_team_stats(include_unpublished=True),
    "shooting": lambda: load_shooting_detail(include_unpublished=True),
    "scoring_sources": lambda: load_scoring_sources(include_unpublished=True),
    "kickouts": lambda: load_kickout_stats(include_unpublished=True),
    "turnovers": lambda: load_turnover_stats(include_unpublished=True),
    "player_data": lambda: load_player_match_data(include_unpublished=True),
}

DATASET_LABELS = {
    config["key"]: label
    for label, config in DATASET_CONFIG.items()
}
IMPORT_DATASET_ORDER = list(DATASET_LOADERS)


def _read_dataset(dataset_key):
    return DATASET_LOADERS[dataset_key]()


def _normalise_boolean_column(data, column):
    if column not in data.columns:
        return
    data[column] = (
        data[column].astype(str).str.strip().str.lower()
        .isin(["true", "yes", "1"])
    )


def _validate_candidate(candidate, original, config, dataset_label, match_ids):
    errors = []
    if candidate.empty:
        errors.append("At least one row is required.")
        return errors

    missing_columns = [
        column for column in original.columns if column not in candidate.columns
    ]
    extra_columns = [
        column for column in candidate.columns if column not in original.columns
    ]
    if missing_columns:
        errors.append(f"Missing columns: {', '.join(missing_columns)}.")
    if extra_columns:
        errors.append(f"Unexpected columns: {', '.join(extra_columns)}.")
    if errors:
        return errors

    numeric_columns = set(original.select_dtypes(include="number").columns)
    for column in numeric_columns:
        raw_values = candidate[column]
        converted = pd.to_numeric(raw_values, errors="coerce")
        supplied = raw_values.notna() & raw_values.astype(str).str.strip().ne("")
        if (supplied & converted.isna()).any():
            errors.append(f"Column {column} must contain numbers only.")
        elif converted.fillna(0).lt(0).any():
            errors.append(f"Column {column} cannot contain negative values.")
        else:
            # Blank numeric cells follow the same zero-default as load_data.py.
            candidate[column] = converted.fillna(0)

    optional_columns = (
        {"Notes"} | numeric_columns
        if dataset_label == "Player data"
        else numeric_columns
    )
    for column in original.columns:
        if column in optional_columns:
            continue
        blank_values = (
            candidate[column].isna()
            | candidate[column].astype(str).str.strip().eq("")
        )
        if blank_values.any():
            errors.append(f"Required column {column} cannot be blank.")

    for column in config["primary_key"]:
        has_blank_key = (
            candidate[column].isna().any()
            or candidate[column].astype(str).str.strip().eq("").any()
        )
        if has_blank_key:
            errors.append(f"Primary-key column {column} cannot be blank.")
    duplicate_count = int(
        candidate.duplicated(config["primary_key"], keep=False).sum()
    )
    if duplicate_count:
        errors.append(
            f"{duplicate_count} rows have duplicate primary-key values."
        )

    if dataset_label != "Matches":
        unknown_ids = sorted(set(candidate["MatchID"].astype(str)) - match_ids)
        if unknown_ids:
            errors.append(f"Unknown MatchID values: {', '.join(unknown_ids)}.")

    if dataset_label == "Team stats" and not errors:
        errors.extend(validate_team_stats(candidate))
    return errors


def _replace_match_rows(original, edited_rows, match_id, dataset_label):
    edited_rows = edited_rows.dropna(how="all").copy()
    if dataset_label == "Matches":
        if match_id != "New match":
            edited_rows["MatchID"] = match_id
            remaining = original[original["MatchID"] != match_id]
        else:
            remaining = original
    else:
        edited_rows["MatchID"] = match_id
        remaining = original[original["MatchID"] != match_id]
    return pd.concat([remaining, edited_rows], ignore_index=True)


def _quality_report(data, team_name):
    data = {
        key: frame.copy()
        for key, frame in data.items()
    }
    for frame in data.values():
        numeric_columns = frame.select_dtypes(include="number").columns
        frame[numeric_columns] = frame[numeric_columns].fillna(0)
    return run_data_quality_checks(
        matches=data["matches"],
        team_data=data["team_stats"],
        shooting_data=data["shooting"],
        scoring_sources=data["scoring_sources"],
        kickout_data=data["kickouts"],
        turnover_data=data["turnovers"],
        player_data=data["player_data"],
        team_name=team_name,
    )


def _cross_dataset_report(candidate, dataset_key, team_name):
    data = {
        key: _read_dataset(key)
        for key in IMPORT_DATASET_ORDER
    }
    data[dataset_key] = candidate
    return _quality_report(data, team_name)


def _build_import_template_archive(current_data):
    buffer = BytesIO()
    instructions = (
        "NEW MATCH IMPORT\n\n"
        "1. Keep every header unchanged.\n"
        "2. Use one new MatchID in every file.\n"
        "3. The matches file must contain exactly one row.\n"
        "4. Upload all seven completed files together in Admin.\n"
    )

    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("README.txt", instructions)
        for index, dataset_key in enumerate(
            IMPORT_DATASET_ORDER,
            start=1,
        ):
            template = current_data[dataset_key].head(0)
            archive.writestr(
                f"{index:02d}_{dataset_key}.csv",
                template.to_csv(index=False),
            )

    return buffer.getvalue()


def _validate_import_bundle(bundle, current_data):
    errors = []

    for dataset_key in IMPORT_DATASET_ORDER:
        label = DATASET_LABELS[dataset_key]
        if dataset_key not in bundle:
            errors.append(f"{label}: file is required.")
            continue

        uploaded = bundle[dataset_key]
        if uploaded.empty:
            errors.append(f"{label}: file must contain at least one row.")
            continue

        expected_columns = list(current_data[dataset_key].columns)
        missing_columns = [
            column
            for column in expected_columns
            if column not in uploaded.columns
        ]
        extra_columns = [
            column
            for column in uploaded.columns
            if column not in expected_columns
        ]
        if missing_columns:
            errors.append(
                f"{label}: missing columns: "
                f"{', '.join(missing_columns)}."
            )
        if extra_columns:
            errors.append(
                f"{label}: unexpected columns: "
                f"{', '.join(extra_columns)}."
            )

    if errors:
        return errors, None, None

    match_rows = bundle["matches"].dropna(how="all")
    if len(match_rows) != 1:
        errors.append("Matches: file must contain exactly one row.")
        return errors, None, None

    match_id = str(match_rows.iloc[0]["MatchID"]).strip()
    if not match_id or match_id.lower() == "nan":
        errors.append("Matches: MatchID cannot be blank.")
        return errors, None, None

    existing_match_ids = set(
        current_data["matches"]["MatchID"].astype(str)
    )
    if match_id in existing_match_ids:
        errors.append(f"MatchID already exists: {match_id}.")

    for dataset_key in IMPORT_DATASET_ORDER:
        label = DATASET_LABELS[dataset_key]
        uploaded_ids = set(
            bundle[dataset_key]["MatchID"]
            .dropna()
            .astype(str)
            .str.strip()
        )
        if uploaded_ids != {match_id}:
            supplied = ", ".join(sorted(uploaded_ids)) or "none"
            errors.append(
                f"{label}: expected only MatchID {match_id}; "
                f"found {supplied}."
            )

    if errors:
        return errors, None, match_id

    candidates = {}
    valid_match_ids = existing_match_ids | {match_id}
    for dataset_key in IMPORT_DATASET_ORDER:
        label = DATASET_LABELS[dataset_key]
        original = current_data[dataset_key]
        uploaded = bundle[dataset_key][original.columns]
        candidate = pd.concat(
            [original, uploaded],
            ignore_index=True,
        )
        candidates[dataset_key] = candidate
        dataset_errors = _validate_candidate(
            candidate,
            original,
            DATASET_CONFIG[label],
            label,
            valid_match_ids,
        )
        errors.extend(
            f"{label}: {error}"
            for error in dataset_errors
        )

    return errors, candidates, match_id
