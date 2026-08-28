import streamlit as st

from validation import run_data_quality_checks


def _build_match_summary(checks):
    match_checks = checks[checks["MatchID"] != "All"]
    summary = (
        match_checks.assign(
            Passed=match_checks["Status"].eq("Pass").astype(int),
            Review=match_checks["Status"].eq("Review").astype(int),
        )
        .groupby("MatchID", as_index=False)
        .agg(
            Checks=("Status", "size"),
            Passed=("Passed", "sum"),
            Review=("Review", "sum"),
        )
    )
    summary["Pass rate"] = summary["Passed"] / summary["Checks"] * 100
    return summary


def render_data_quality(
    matches,
    team_data,
    shooting_data,
    scoring_sources,
    kickout_data,
    turnover_data,
    player_data,
    team_name,
):
    st.header("Data quality")
    st.caption(
        "Automatic cross-file checks to catch manual-entry differences "
        "before they reach the analysis"
    )

    checks = run_data_quality_checks(
        matches=matches,
        team_data=team_data,
        shooting_data=shooting_data,
        scoring_sources=scoring_sources,
        kickout_data=kickout_data,
        turnover_data=turnover_data,
        player_data=player_data,
        team_name=team_name,
    )
    if checks.empty:
        st.info("No matches are available to validate.")
        return

    passed = int(checks["Status"].eq("Pass").sum())
    review = int(checks["Status"].eq("Review").sum())
    pass_rate = passed / len(checks) * 100

    with st.container(horizontal=True):
        st.metric(
            "Matches audited",
            str(matches["MatchID"].nunique()),
            border=True,
        )
        st.metric("Checks run", str(len(checks)), border=True)
        st.metric("Passed", str(passed), border=True)
        st.metric(
            "Needs review",
            str(review),
            delta="Manual check recommended" if review else "All clear",
            delta_color="inverse" if review else "normal",
            border=True,
        )
        st.metric("Pass rate", f"{pass_rate:.1f}%", border=True)

    if review:
        st.warning(
            f"{review} checks need review. This does not automatically mean "
            "the data is wrong—it identifies totals that do not currently "
            "reconcile."
        )
    else:
        st.success("All data-quality checks currently pass.")

    st.subheader("Match audit summary")
    st.dataframe(
        _build_match_summary(checks),
        hide_index=True,
        width="stretch",
        column_config={
            "MatchID": st.column_config.TextColumn(pinned=True),
            "Pass rate": st.column_config.ProgressColumn(
                min_value=0,
                max_value=100,
                format="%.1f%%",
            ),
        },
    )

    st.subheader("Validation report")
    filter_left, filter_right = st.columns(2)
    match_options = [
        "All matches",
        *matches.sort_values("Date")["MatchID"].drop_duplicates().tolist(),
    ]
    with filter_left:
        selected_match = st.selectbox(
            "Match",
            options=match_options,
            key="quality_match_filter",
        )
    with filter_right:
        display_mode = st.segmented_control(
            "Checks to show",
            options=["Issues only", "All checks"],
            default="Issues only",
            key="quality_display_mode",
        )

    visible = checks.copy()
    if selected_match != "All matches":
        visible = visible[visible["MatchID"] == selected_match]
    if display_mode == "Issues only":
        visible = visible[visible["Status"] == "Review"]

    if visible.empty:
        st.success("No review items match the selected filters.")
    else:
        st.dataframe(
            visible,
            hide_index=True,
            width="stretch",
            column_config={
                "MatchID": st.column_config.TextColumn(pinned=True),
                "Difference": st.column_config.NumberColumn(format="%+.0f"),
            },
        )

    st.download_button(
        "Download validation report",
        data=checks.to_csv(index=False).encode("utf-8"),
        file_name="championship_data_quality_report.csv",
        mime="text/csv",
        icon=":material/download:",
    )

    with st.expander("What is checked"):
        st.markdown(
            """
- Match scores reconcile with goals, points and two-pointers.
- Team totals reconcile with their play and placed-ball components.
- Shooting scores never exceed attempts and every shot has an outcome.
- Kickouts reconcile as won + lost = taken, including win types and halves.
- Full-time turnover figures equal the first-half and second-half totals.
- Scoring-source totals equal the team total of successful shots.
- Player row arithmetic is valid and player totals reconcile with team totals.
- Dataset keys are unique and every row uses a known MatchID.
"""
        )
