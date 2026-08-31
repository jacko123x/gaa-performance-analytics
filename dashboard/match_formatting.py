import pandas as pd


AMBER = "#F59E0B"
DARK_AMBER = "#B45309"
LIGHT_AMBER = "#FCD34D"
DARK = "#1F2937"
GREY = "#6B7280"


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
