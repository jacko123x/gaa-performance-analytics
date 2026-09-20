from html import escape

import pandas as pd
import streamlit as st


AMBER = "#F59E0B"
DARK_AMBER = "#B45309"
LIGHT_AMBER = "#FCD34D"
DARK = "#1F2937"
GREY = "#6B7280"

METRIC_TONES = {
    "blue": ("#60A5FA", "rgba(59, 130, 246, 0.10)"),
    "purple": ("#A78BFA", "rgba(139, 92, 246, 0.10)"),
    "green": ("#4ADE80", "rgba(34, 197, 94, 0.10)"),
    "amber": ("#FBBF24", "rgba(245, 158, 11, 0.10)"),
    "red": ("#F87171", "rgba(239, 68, 68, 0.09)"),
}


def format_pct(value):
    if pd.isna(value):
        return "-"
    return f"{value:.1f}%"


def format_number(value, decimals=1):
    if pd.isna(value):
        return "-"
    return f"{value:.{decimals}f}"


def format_signed(value, decimals=0):
    if pd.isna(value):
        return "-"
    return f"{value:+.{decimals}f}"


def format_scope_count(value, show_average=False):
    if pd.isna(value):
        return "-"
    if show_average:
        return format_number(value, decimals=1)
    return str(int(value))


def metric_tile(label, value, tone="blue", detail=None, compact=False):
    """Render one compact, colour-coded dashboard metric tile."""

    accent, background = METRIC_TONES[tone]
    detail_html = (
        f'<div style="font-size:0.69rem;opacity:0.62;margin-top:0.2rem;">'
        f"{escape(str(detail))}</div>"
        if detail
        else ""
    )
    min_height = "76px" if compact else "92px"
    value_size = "1.35rem" if compact else "1.55rem"
    st.markdown(
        f"""
<div style="
    min-height:{min_height};
    padding:0.72rem 0.85rem;
    border:1px solid rgba(148, 163, 184, 0.20);
    border-left:3px solid {accent};
    border-radius:0.6rem;
    background:linear-gradient(115deg, {background}, rgba(15, 23, 42, 0.02));
    box-shadow:0 2px 9px rgba(0, 0, 0, 0.08);
">
    <div style="font-size:0.72rem;font-weight:650;opacity:0.68;">
        {escape(str(label))}
    </div>
    <div style="font-size:{value_size};font-weight:760;line-height:1.15;
        margin-top:0.28rem;color:{accent};">
        {escape(str(value))}
    </div>
    {detail_html}
</div>
""",
        unsafe_allow_html=True,
    )


def render_metric_tiles(tiles, columns_per_row=4, compact=False):
    """Render metric definitions in a stable, wrapping grid."""

    for start in range(0, len(tiles), columns_per_row):
        columns = st.columns(columns_per_row, gap="small")
        row = tiles[start:start + columns_per_row]
        for column, tile in zip(columns, row):
            with column:
                metric_tile(**tile, compact=compact)
