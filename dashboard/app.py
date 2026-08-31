# ==========================================================
# Imports
# ==========================================================

import sys
from pathlib import Path
from uuid import uuid4

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError


# ==========================================================
# Project setup
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "src"))
sys.path.append(str(PROJECT_ROOT / "dashboard"))

from src.settings import (  # noqa: E402
    ConfigurationError,
    apply_secret_values,
    get_settings,
)

try:
    apply_secret_values(st.secrets.to_dict())
except StreamlitSecretNotFoundError:
    pass

try:
    SETTINGS = get_settings()
except ConfigurationError as error:
    st.set_page_config(page_title="Configuration error", layout="centered")
    st.error(f"Application configuration error: {error}")
    st.stop()

from src.logging_config import (  # noqa: E402
    configure_logging,
    get_logger,
    log_event,
    log_exception,
)

configure_logging(SETTINGS.log_level, SETTINGS.json_logs)
LOGGER = get_logger("gaa_analytics.app")


# ==========================================================
# Project imports
# ==========================================================

from championship_overview import (
    render_championship_overview,
)
from match_comparison import render_match_comparison
from player_championship import render_player_championship
from squad_leaderboards import render_squad_leaderboards
from data_quality import render_data_quality
from auth import (
    available_views,
    current_user,
    require_login,
    render_account_controls,
)
from admin import render_admin
from dashboard_data import load_dashboard_data
from match_analysis import render_match_analysis
from maintenance import render_maintenance_screen
from src.health import check_database_readiness


# ==========================================================
# Constants
# ==========================================================

TEAM_NAME = SETTINGS.team_name

# ==========================================================
# Streamlit setup
# ==========================================================

st.set_page_config(
    page_title=SETTINGS.app_title,
    page_icon="🏐",
    layout="wide",
)


@st.cache_data(ttl=10, max_entries=1, show_spinner=False)
def load_database_readiness():
    return check_database_readiness()


def show_maintenance(reason, event, error=None):
    reference = st.session_state.setdefault(
        "maintenance_reference",
        uuid4().hex[:10].upper(),
    )
    log_key = f"maintenance_logged_{reference}_{event}"
    if not st.session_state.get(log_key):
        if error is None:
            log_event(
                LOGGER,
                event,
                level=30,
                reference=reference,
                reason=reason,
            )
        else:
            log_exception(
                LOGGER,
                event,
                error=error,
                reference=reference,
                reason=reason,
            )
        st.session_state[log_key] = True
    if render_maintenance_screen(
        SETTINGS.app_title,
        reference,
        reason,
    ):
        load_database_readiness.clear()
        st.rerun()
    st.stop()


readiness = load_database_readiness()
if not readiness.ready:
    show_maintenance(
        readiness.reason,
        "application_not_ready",
    )

st.session_state.pop("maintenance_reference", None)

if not require_login():
    st.stop()

render_account_controls()
SIGNED_IN_USER = current_user()

st.markdown(
    """
    <style>
    [data-testid="stSidebar"] [role="radiogroup"] {
        gap: 0.55rem;
    }

    [data-testid="stSidebar"] [role="radiogroup"] > label {
        width: 100%;
        min-height: 3.35rem;
        margin: 0;
        padding: 0.85rem 1rem;
        border: 1px solid transparent;
        border-radius: 0.7rem;
        align-items: center;
        transition:
            background-color 150ms ease,
            border-color 150ms ease,
            transform 150ms ease;
    }

    [data-testid="stSidebar"] [role="radiogroup"] > label > div:first-child {
        display: none;
    }

    [data-testid="stSidebar"] [role="radiogroup"] > label p {
        font-size: 1.08rem;
        font-weight: 600;
        line-height: 1.25;
    }

    [data-testid="stSidebar"] [role="radiogroup"] > label:hover {
        background-color: rgba(245, 158, 11, 0.14);
        border-color: rgba(245, 158, 11, 0.35);
        transform: translateX(2px);
    }

    [data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked),
    [data-testid="stSidebar"] [role="radiogroup"] > label:has(
        [aria-checked="true"]
    ) {
        background-color: #F59E0B;
        border-color: #FBBF24;
        box-shadow: 0 5px 14px rgba(245, 158, 11, 0.2);
    }

    [data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) p,
    [data-testid="stSidebar"] [role="radiogroup"] > label:has(
        [aria-checked="true"]
    ) p {
        color: #111827;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


try:
    dashboard_data = load_dashboard_data(TEAM_NAME)

except Exception as error:
    show_maintenance(
        "dashboard_data_unavailable",
        "dashboard_data_load_failed",
        error,
    )

matches = dashboard_data.matches
team_data = dashboard_data.team
shooting_data = dashboard_data.shooting
scoring_sources = dashboard_data.scoring_sources
kickout_data = dashboard_data.kickouts
turnover_data = dashboard_data.turnovers
player_data = dashboard_data.players


# ==========================================================
# Header
# ==========================================================

st.title(SETTINGS.app_title)

st.caption(
    SETTINGS.season_label
)


# ==========================================================
# Analysis view
# ==========================================================

analysis_view = st.sidebar.radio(
    "Analysis view",
    options=available_views(SIGNED_IN_USER["role"]),
    key="analysis_view",
)

if analysis_view == "Championship overview":
    render_championship_overview(
        matches=matches,
        team_data=team_data,
        shooting_data=shooting_data,
        scoring_sources=scoring_sources,
        kickout_data=kickout_data,
        turnover_data=turnover_data,
        team_name=TEAM_NAME,
    )
    st.stop()

if analysis_view == "Player championship":
    render_player_championship(player_data)
    st.stop()

if analysis_view == "My player profile":
    render_player_championship(
        player_data,
        fixed_player=SIGNED_IN_USER["player_name"],
        show_squad_table=False,
    )
    st.stop()

if analysis_view == "Squad leaderboards":
    render_squad_leaderboards(player_data)
    st.stop()

if analysis_view == "Match comparison":
    render_match_comparison(
        matches=matches,
        team_data=team_data,
        scoring_sources=scoring_sources,
        kickout_data=kickout_data,
        turnover_data=turnover_data,
        team_name=TEAM_NAME,
    )
    st.stop()

if analysis_view == "Data quality":
    render_data_quality(
        matches=matches,
        team_data=team_data,
        shooting_data=shooting_data,
        scoring_sources=scoring_sources,
        kickout_data=kickout_data,
        turnover_data=turnover_data,
        player_data=player_data,
        team_name=TEAM_NAME,
    )
    st.stop()

if analysis_view == "Admin":
    render_admin(
        team_name=TEAM_NAME,
        actor_username=SIGNED_IN_USER["username"],
    )
    st.stop()

render_match_analysis(
    matches=matches,
    team_data=team_data,
    shooting_data=shooting_data,
    scoring_sources=scoring_sources,
    kickout_data=kickout_data,
    turnover_data=turnover_data,
    player_data=player_data,
    team_name=TEAM_NAME,
)
