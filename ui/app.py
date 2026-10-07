import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import textwrap
import streamlit as st
import services
import html
import logging
from typing import Any


logger = logging.getLogger(__name__)


# =============================================================================
# Page configuration
# =============================================================================

st.set_page_config(
    page_title="ISOLATE · Intelligence Briefing",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# Theme and layout
# =============================================================================

st.markdown(
    textwrap.dedent(
        """
        <style>
        @import url(
            'https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Inter:wght@400;500;600;700&display=swap'
        );

        :root {
            --bg: #080b10;
            --bg-raised: #0d1118;
            --surface: #111720;
            --surface-2: #151c27;
            --surface-3: #1a2330;

            --border: #263140;
            --border-soft: #1b2430;

            --text: #eef3f8;
            --text-2: #c1ccd8;
            --muted: #7f8c9d;
            --muted-2: #596677;

            --blue: #5ba7ff;
            --blue-soft: rgba(91, 167, 255, 0.12);

            --cyan: #55d6c2;
            --cyan-soft: rgba(85, 214, 194, 0.12);

            --amber: #e7b55b;
            --amber-soft: rgba(231, 181, 91, 0.12);

            --green: #70d39a;
            --green-soft: rgba(112, 211, 154, 0.12);
        }

        html,
        body,
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] > .main {
            background: var(--bg) !important;
        }

        .stApp {
            min-width: 0;
            background:
                radial-gradient(
                    circle at 70% -10%,
                    rgba(47, 131, 230, 0.11),
                    transparent 36rem
                ),
                var(--bg) !important;
            color: var(--text) !important;
            font-family: "Inter", system-ui, sans-serif;
        }

        /*
         * Do not alter Streamlit's internal header/main offsets.
         * The previous version used internal selectors here, which caused
         * the custom topbar to collide with Streamlit's own header.
         */
        [data-testid="stHeader"] {
            background: #080b10 !important;
            border-bottom: 1px solid var(--border-soft) !important;
        }

        .block-container {
            width: 100%;
            max-width: 1500px;
            margin: 0 auto;
            padding: 5rem 2.4rem 3rem;
        }

        @media (max-width: 900px) {
            .block-container {
                padding: 1.25rem 1rem 2rem;
            }
        }

        #MainMenu,
        footer {
            visibility: hidden;
        }

        /* ------------------------------------------------------------------ */
        /* Sidebar                                                             */
        /* ------------------------------------------------------------------ */

        [data-testid="stSidebar"] {
            width: 245px !important;
            border-right: 1px solid var(--border-soft) !important;
            background: #0a0e14 !important;
        }

        [data-testid="stSidebar"] > div:first-child {
            padding: 1.25rem 0.9rem;
        }

        [data-testid="stSidebar"] * {
            color: var(--text-2);
        }

        [data-testid="stSidebar"] hr {
            margin: 1.4rem 0;
            border-color: var(--border-soft);
        }

        [data-testid="stSidebar"] .stButton button {
            width: 100%;
            min-height: 2.35rem;
            justify-content: flex-start;
            border: 1px solid transparent;
            border-radius: 7px;
            background: transparent;
            color: var(--muted);
            text-align: left;
        }

        [data-testid="stSidebar"] .stButton button:hover {
            border-color: var(--border);
            background: var(--surface);
            color: var(--text);
        }

        [data-testid="stSidebar"] .stButton button[kind="primary"] {
            border-color: rgba(91, 167, 255, 0.32);
            background: var(--blue-soft);
            color: var(--blue);
        }


        /* ------------------------------------------------------------------ */
        /* Native Streamlit widgets                                            */
        /* ------------------------------------------------------------------ */

        [data-testid="stTextInput"] input,
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        [data-testid="stMultiSelect"] div[data-baseweb="select"] > div {
            min-height: 2.55rem;
            border: 1px solid var(--border) !important;
            border-radius: 8px !important;
            background: var(--surface) !important;
            color: var(--text) !important;
        }

        [data-testid="stTextInput"] input:focus,
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within,
        [data-testid="stMultiSelect"] div[data-baseweb="select"] > div:focus-within {
            border-color: var(--blue) !important;
            box-shadow: 0 0 0 1px var(--blue) !important;
        }

        [data-testid="stTextInput"] input::placeholder {
            color: var(--muted-2) !important;
        }

        [data-baseweb="popover"],
        [data-baseweb="menu"] {
            background: var(--surface-2) !important;
            border: 1px solid var(--border) !important;
        }

        [role="option"] {
            color: var(--text-2) !important;
        }

        [role="option"]:hover {
            background: var(--surface-3) !important;
        }

        [data-testid="stExpander"] {
            overflow: hidden;
            border: 1px solid var(--border-soft) !important;
            border-radius: 8px !important;
            background: var(--bg-raised) !important;
        }

        [data-testid="stExpander"] summary {
            color: var(--text-2) !important;
        }

        [data-testid="stExpander"] summary:hover {
            color: var(--text) !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.25rem;
            padding: 0.25rem;
            border-bottom: 1px solid var(--border);
            background: transparent;
        }

        .stTabs [data-baseweb="tab"] {
            height: 2.25rem;
            padding: 0.35rem 0.85rem;
            border-radius: 6px 6px 0 0;
            color: var(--muted);
            font-size: 0.82rem;
            font-weight: 600;
        }

        .stTabs [aria-selected="true"] {
            background: var(--blue-soft) !important;
            color: var(--blue) !important;
        }

        .stTabs [data-baseweb="tab-highlight"] {
            background: var(--blue) !important;
        }

        .stMarkdown p,
        .stMarkdown li {
            color: var(--text-2);
            line-height: 1.7;
        }

        .stMarkdown h1,
        .stMarkdown h2,
        .stMarkdown h3,
        .stMarkdown h4 {
            color: var(--text);
        }

        .stMarkdown h2 {
            padding-bottom: 0.45rem;
            border-bottom: 1px solid var(--border);
        }

        /* ------------------------------------------------------------------ */
        /* Header                                                              */
        /* ------------------------------------------------------------------ */

        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            min-height: 3rem;
            margin: 0 0 1.8rem;
            padding: 0 0 0.9rem;
            border-bottom: 1px solid var(--border-soft);
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 0.7rem;
        }

        .brand-mark {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 2rem;
            height: 2rem;
            border: 1px solid rgba(91, 167, 255, 0.5);
            border-radius: 7px;
            background: var(--blue-soft);
            color: var(--blue);
            font-family: "DM Mono", monospace;
            font-size: 1.1rem;
        }

        .brand-name {
            color: var(--text);
            font-size: 1rem;
            font-weight: 700;
            letter-spacing: 0.13em;
        }

        .brand-subtitle {
            margin-top: 0.12rem;
            color: var(--muted);
            font-family: "DM Mono", monospace;
            font-size: 0.68rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }

        .topbar-context {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--muted);
            font-family: "DM Mono", monospace;
            font-size: 0.66rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }

        .topbar-page {
            color: var(--text-2);
        }

        .topbar-divider {
            color: var(--muted-2);
        }

        .topbar-status {
            color: var(--green);
        }

        .status-dot {
            width: 0.48rem;
            height: 0.48rem;
            border-radius: 50%;
            background: var(--green);
            box-shadow: 0 0 10px rgba(112, 211, 154, 0.7);
        }

        .eyebrow {
            margin-bottom: 0.35rem;
            color: var(--blue);
            font-family: "DM Mono", monospace;
            font-size: 0.68rem;
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }

        .section-heading {
            display: flex;
            align-items: end;
            justify-content: space-between;
            gap: 1rem;
            margin: 0.3rem 0 1rem;
        }

        .page-title {
            margin: 0;
            color: var(--text);
            font-size: clamp(1.7rem, 3vw, 2.45rem);
            font-weight: 700;
            letter-spacing: -0.04em;
            line-height: 1.05;
        }

        .page-description {
            max-width: 650px;
            margin-top: 0.55rem;
            color: var(--muted);
            font-size: 0.9rem;
            line-height: 1.55;
        }

        .mono {
            color: var(--muted);
            font-family: "DM Mono", monospace;
            font-size: 0.72rem;
        }

        /* ------------------------------------------------------------------ */
        /* Metrics                                                             */
        /* ------------------------------------------------------------------ */

        .metric-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.65rem;
            margin: 1.25rem 0 1.5rem;
        }

        @media (max-width: 800px) {
            .metric-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }

        .metric-tile {
            min-height: 5.8rem;
            padding: 0.9rem 1rem;
            border: 1px solid var(--border);
            border-radius: 9px;
            background: var(--surface);
        }

        .metric-label {
            color: var(--muted);
            font-family: "DM Mono", monospace;
            font-size: 0.63rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .metric-value {
            margin-top: 0.45rem;
            color: var(--text);
            font-size: 1.55rem;
            font-weight: 700;
            letter-spacing: -0.04em;
        }

        .metric-value.blue {
            color: var(--blue);
        }

        .metric-value.cyan {
            color: var(--cyan);
        }

        .metric-value.amber {
            color: var(--amber);
        }

        .metric-foot {
            margin-top: 0.3rem;
            color: var(--muted-2);
            font-family: "DM Mono", monospace;
            font-size: 0.62rem;
        }

        /* ------------------------------------------------------------------ */
        /* Loading skeletons                                                   */
        /* ------------------------------------------------------------------ */

        .loading-label {
            display: flex;
            align-items: center;
            gap: 0.55rem;
            margin: 0.5rem 0 0.9rem;
            color: var(--muted);
            font-family: "DM Mono", monospace;
            font-size: 0.68rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }

        .loading-spinner {
            width: 0.7rem;
            height: 0.7rem;
            border: 2px solid var(--border);
            border-top-color: var(--blue);
            border-radius: 50%;
            animation: isolate-spin 0.8s linear infinite;
        }

        @keyframes isolate-spin {
            to {
                transform: rotate(360deg);
            }
        }

        .skeleton {
            position: relative;
            overflow: hidden;
            border: 1px solid var(--border);
            border-radius: 9px;
            background: var(--surface);
        }

        .skeleton::after {
            position: absolute;
            inset: 0;
            background: linear-gradient(
                90deg,
                transparent 0%,
                rgba(255, 255, 255, 0.025) 35%,
                rgba(255, 255, 255, 0.08) 50%,
                rgba(255, 255, 255, 0.025) 65%,
                transparent 100%
            );
            content: "";
            transform: translateX(-100%);
            animation: isolate-shimmer 1.45s ease-in-out infinite;
        }

        @keyframes isolate-shimmer {
            to {
                transform: translateX(100%);
            }
        }

        .skeleton-metrics {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.65rem;
            margin: 1.25rem 0 1.5rem;
        }

        .skeleton-metric {
            height: 5.8rem;
        }

        .skeleton-card {
            height: 11rem;
            margin-bottom: 0.75rem;
        }

        .skeleton-source-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.7rem;
        }

        .skeleton-source {
            height: 8rem;
        }

        @media (max-width: 800px) {
            .skeleton-metrics,
            .skeleton-source-grid {
                grid-template-columns: 1fr;
            }
        }

        /* ------------------------------------------------------------------ */
        /* Intelligence cards                                                  */
        /* ------------------------------------------------------------------ */

        .intel-card {
            position: relative;
            margin-bottom: 0.75rem;
            padding: 1rem 1.05rem 0.95rem 1.15rem;
            border: 1px solid var(--border);
            border-radius: 9px;
            background: var(--surface);
        }

        .intel-card:hover {
            border-color: #344256;
            background: var(--surface-2);
        }

        .intel-card::before {
            position: absolute;
            top: 0.85rem;
            bottom: 0.85rem;
            left: 0;
            width: 3px;
            border-radius: 0 4px 4px 0;
            background: var(--muted-2);
            content: "";
        }

        .intel-card.new::before {
            background: var(--blue);
            box-shadow: 0 0 13px rgba(91, 167, 255, 0.35);
        }

        .intel-card.developing::before {
            background: var(--cyan);
            box-shadow: 0 0 13px rgba(85, 214, 194, 0.3);
        }

        .card-topline,
        .score-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 0.55rem;
        }

        .card-meta {
            color: var(--muted);
            font-family: "DM Mono", monospace;
            font-size: 0.66rem;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .status-chip,
        .tag-chip,
        .score-chip {
            display: inline-flex;
            align-items: center;
            padding: 0.2rem 0.48rem;
            border-radius: 5px;
            font-family: "DM Mono", monospace;
            font-size: 0.62rem;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .status-chip.new,
        .score-chip.high {
            background: var(--blue-soft);
            color: var(--blue);
        }

        .status-chip.developing,
        .score-chip.mid {
            background: var(--cyan-soft);
            color: var(--cyan);
        }

        .status-chip.signal,
        .score-chip.low {
            background: rgba(127, 140, 157, 0.12);
            color: var(--muted);
        }

        .status-chip.wip {
            background: var(--amber-soft);
            color: var(--amber);
        }

        .card-title {
            margin-bottom: 0.35rem;
            color: var(--text);
            font-size: 1.04rem;
            font-weight: 600;
            line-height: 1.3;
        }

        .card-summary {
            margin-bottom: 0.65rem;
            color: var(--text-2);
            font-size: 0.87rem;
            line-height: 1.55;
        }

        .card-delta {
            margin: 0.7rem 0;
            padding: 0.55rem 0.7rem;
            border-left: 2px solid var(--cyan);
            border-radius: 0 5px 5px 0;
            background: var(--cyan-soft);
            color: var(--text-2);
            font-size: 0.83rem;
            line-height: 1.5;
        }

        .card-delta strong {
            color: var(--cyan);
        }

        .chips {
            display: flex;
            flex-wrap: wrap;
            gap: 0.35rem;
            margin: 0.55rem 0;
        }

        .tag-chip {
            border: 1px solid var(--border);
            background: var(--bg-raised);
            color: var(--muted);
            text-transform: none;
        }

        .entity-chip {
            padding: 0.2rem 0.48rem;
            border-radius: 5px;
            background: var(--blue-soft);
            color: var(--blue);
            font-size: 0.67rem;
            font-weight: 600;
        }

        .card-footer {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin-top: 0.75rem;
            padding-top: 0.65rem;
            border-top: 1px solid var(--border-soft);
        }

        .source-count {
            color: var(--muted);
            font-family: "DM Mono", monospace;
            font-size: 0.66rem;
        }

        .article-link {
            color: var(--blue);
            font-family: "DM Mono", monospace;
            font-size: 0.68rem;
            text-decoration: none;
        }

        .article-link:hover {
            color: var(--text);
            text-decoration: underline;
        }

        /* ------------------------------------------------------------------ */
        /* Score meters                                                        */
        /* ------------------------------------------------------------------ */

        .score-meter {
            display: grid;
            grid-template-columns: 92px 1fr 24px;
            align-items: center;
            gap: 0.55rem;
            margin: 0.32rem 0;
        }

        .score-label,
        .score-number {
            color: var(--muted);
            font-family: "DM Mono", monospace;
            font-size: 0.62rem;
            text-transform: uppercase;
        }

        .score-number {
            color: var(--text-2);
            text-align: right;
        }

        .score-track {
            height: 5px;
            overflow: hidden;
            border-radius: 999px;
            background: var(--surface-3);
        }

        .score-fill {
            height: 100%;
            border-radius: inherit;
            background: var(--muted-2);
        }

        .score-fill.mid {
            background: var(--cyan);
        }

        .score-fill.high {
            background: var(--blue);
            box-shadow: 0 0 9px rgba(91, 167, 255, 0.45);
        }

        /* ------------------------------------------------------------------ */
        /* Empty and source states                                             */
        /* ------------------------------------------------------------------ */

        .empty-state {
            padding: 2.5rem 1.25rem;
            border: 1px dashed var(--border);
            border-radius: 9px;
            background: var(--bg-raised);
            color: var(--muted);
            font-family: "DM Mono", monospace;
            font-size: 0.75rem;
            text-align: center;
        }

        .warning-state {
            margin: 0.75rem 0 1rem;
            padding: 0.75rem 0.9rem;
            border: 1px solid rgba(231, 181, 91, 0.35);
            border-radius: 7px;
            background: var(--amber-soft);
            color: var(--amber);
            font-size: 0.8rem;
            line-height: 1.45;
        }

        .source-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.7rem;
        }

        @media (max-width: 800px) {
            .source-grid {
                grid-template-columns: 1fr;
            }
        }

        .source-card {
            padding: 0.95rem;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--surface);
        }

        .source-card:hover {
            border-color: #344256;
            background: var(--surface-2);
        }

        .source-name {
            margin: 0.4rem 0;
            color: var(--text);
            font-size: 0.94rem;
            font-weight: 600;
        }

        .source-meta {
            color: var(--muted);
            font-family: "DM Mono", monospace;
            font-size: 0.64rem;
            line-height: 1.5;
            text-transform: uppercase;
        }

        .source-card a {
            display: inline-block;
            margin-top: 0.65rem;
            color: var(--blue);
            font-family: "DM Mono", monospace;
            font-size: 0.67rem;
            text-decoration: none;
        }

        .source-card a:hover {
            text-decoration: underline;
        }
        </style>
        """
    ),
    unsafe_allow_html=True,
)


# =============================================================================
# Generic helpers
# =============================================================================

def esc(value: Any) -> str:
    if value is None:
        return ""

    normalized = " ".join(str(value).split())
    return html.escape(normalized, quote=True)


def safe_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def safe_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def render_empty(message: str) -> None:
    st.markdown(
        f'<div class="empty-state">{esc(message)}</div>',
        unsafe_allow_html=True,
    )


def render_warning(message: str) -> None:
    st.markdown(
        f'<div class="warning-state">{esc(message)}</div>',
        unsafe_allow_html=True,
    )


def format_timestamp(value: Any) -> str:
    if not value:
        return "unknown time"

    return (
        str(value)
        .replace("T", " ")
        .replace("Z", "")
        .replace("+00:00", "")[:16]
    )


# =============================================================================
# Loading states
# =============================================================================

def render_loading_label(label: str) -> None:
    st.markdown(
        '<div class="loading-label">'
        '<span class="loading-spinner"></span>'
        f'<span>{esc(label)}</span>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_event_loading_state() -> None:
    st.markdown(
        '<div class="loading-label">'
        '<span class="loading-spinner"></span>'
        '<span>Loading live event stream</span>'
        '</div>'
        '<div class="skeleton-metrics">'
        '<div class="skeleton skeleton-metric"></div>'
        '<div class="skeleton skeleton-metric"></div>'
        '<div class="skeleton skeleton-metric"></div>'
        '<div class="skeleton skeleton-metric"></div>'
        '</div>'
        '<div class="skeleton skeleton-card"></div>'
        '<div class="skeleton skeleton-card"></div>'
        '<div class="skeleton skeleton-card"></div>',
        unsafe_allow_html=True,
    )


def render_briefing_loading_state() -> None:
    st.markdown(
        '<div class="loading-label">'
        '<span class="loading-spinner"></span>'
        '<span>Loading briefing index</span>'
        '</div>'
        '<div class="skeleton-metrics">'
        '<div class="skeleton skeleton-metric"></div>'
        '<div class="skeleton skeleton-metric"></div>'
        '<div class="skeleton skeleton-metric"></div>'
        '<div class="skeleton skeleton-metric"></div>'
        '</div>'
        '<div class="skeleton skeleton-card"></div>',
        unsafe_allow_html=True,
    )


def render_source_loading_state() -> None:
    st.markdown(
        '<div class="loading-label">'
        '<span class="loading-spinner"></span>'
        '<span>Loading source registry</span>'
        '</div>'
        '<div class="skeleton-source-grid">'
        '<div class="skeleton skeleton-source"></div>'
        '<div class="skeleton skeleton-source"></div>'
        '<div class="skeleton skeleton-source"></div>'
        '<div class="skeleton skeleton-source"></div>'
        '</div>',
        unsafe_allow_html=True,
    )


def load_with_placeholder(
    placeholder_renderer,
    loader,
):
    slot = st.empty()

    with slot.container():
        placeholder_renderer()

    try:
        return loader()
    finally:
        slot.empty()


# =============================================================================
# Header and metrics
# =============================================================================

def render_topbar(page_name: str) -> None:
    st.markdown(
        '<div class="topbar">'
        '<div class="brand">'
        '<div class="brand-mark">◈</div>'
        '<div>'
        '<div class="brand-name">ISOLATE</div>'
        '<div class="brand-subtitle">intelligence briefing system</div>'
        '</div>'
        '</div>'
        '<div class="topbar-context">'
        f'<span class="topbar-page">{esc(page_name)}</span>'
        '<span class="topbar-divider">/</span>'
        '<span class="status-dot"></span>'
        '<span class="topbar-status">online</span>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_heading(
    eyebrow: str,
    title: str,
    description: str = "",
    right_text: str = "",
) -> None:
    description_html = (
        f'<div class="page-description">{esc(description)}</div>'
        if description
        else ""
    )

    right_html = (
        f'<div class="mono">{esc(right_text)}</div>'
        if right_text
        else ""
    )

    st.markdown(
        '<div class="section-heading">'
        '<div>'
        f'<div class="eyebrow">{esc(eyebrow)}</div>'
        f'<h1 class="page-title">{esc(title)}</h1>'
        f'{description_html}'
        '</div>'
        f'{right_html}'
        '</div>',
        unsafe_allow_html=True,
    )


def render_metric_grid(
    metrics: list[tuple[str, str, str, str]],
) -> None:
    tiles = []

    for label, value, tone, foot in metrics:
        tiles.append(
            '<div class="metric-tile">'
            f'<div class="metric-label">{esc(label)}</div>'
            f'<div class="metric-value {esc(tone)}">{esc(value)}</div>'
            f'<div class="metric-foot">{esc(foot)}</div>'
            '</div>'
        )

    st.markdown(
        f'<div class="metric-grid">{"".join(tiles)}</div>',
        unsafe_allow_html=True,
    )


# =============================================================================
# Event functions
# =============================================================================

def classify_event(event: dict) -> tuple[str, str]:
    status = event.get("status")
    first_seen = event.get("first_seen_at")
    last_updated = event.get("last_updated_at")
    article_count = event.get("article_count")

    if any(
        value is None
        for value in (
            status,
            first_seen,
            last_updated,
            article_count,
        )
    ):
        return "signal", "wip"

    if status == "closed":
        return "signal", "signal"

    if first_seen == last_updated:
        return "new", "new"

    if safe_int(article_count) <= 1:
        return "signal", "signal"

    return "developing", "developing"


def event_matches_query(
    event: dict,
    query: str,
) -> bool:
    words = query.lower().split()

    if not words:
        return True

    entities = safe_list(event.get("entities"))

    entity_names = [
        str(entity.get("name") or "")
        for entity in entities
        if isinstance(entity, dict)
    ]

    domains = [
        str(domain)
        for domain in safe_list(event.get("domains"))
    ]

    haystack = " ".join(
        [
            str(event.get("name") or ""),
            str(event.get("summary") or ""),
            " ".join(entity_names),
            " ".join(domains),
        ]
    ).lower()

    return all(word in haystack for word in words)


def event_sort_key(
    event: dict,
    sort_label: str,
):
    if sort_label == "Article count":
        return safe_int(event.get("article_count"))

    return event.get("last_updated_at") or ""


def render_event_timeline(timeline: list[dict]) -> None:
    for entry in reversed(timeline):
        entry = safe_dict(entry)

        event_type = entry.get("type")
        timestamp = format_timestamp(entry.get("timestamp"))
        articles_added = safe_int(entry.get("articles_added"))
        sources_added = safe_int(entry.get("sources_added"))
        names = safe_list(entry.get("source_names"))

        if event_type == "created":
            label = (
                f"Event created · {articles_added} article"
                f"{'s' if articles_added != 1 else ''} · "
                f"{sources_added} source"
                f"{'s' if sources_added != 1 else ''}"
            )
        else:
            parts = []

            if articles_added:
                parts.append(
                    f"+{articles_added} article"
                    f"{'s' if articles_added != 1 else ''}"
                )

            if sources_added:
                source_text = (
                    f"+{sources_added} source"
                    f"{'s' if sources_added != 1 else ''}"
                )

                if names:
                    source_text += f" · {', '.join(map(str, names[:3]))}"

                parts.append(source_text)

            label = " · ".join(parts) or "Matched, no new corroboration"

        st.markdown(
            f"**{esc(timestamp)}**  \n"
            f"{esc(label)}"
        )

        if entry.get("delta_text"):
            st.markdown(f"> {esc(entry.get('delta_text'))}")


def render_event_card(event: dict) -> None:
    state_class, state_label = classify_event(event)

    status_text = {
        "new": "new",
        "developing": "developing",
        "signal": "signal",
        "wip": "schema pending",
    }.get(state_label, "signal")

    title = esc(event.get("name") or "Untitled event")
    summary = esc(
        str(event.get("summary") or "No summary available")[:320]
    )

    source_count = event.get("source_count")
    article_count = event.get("article_count")

    if isinstance(source_count, int) and isinstance(article_count, int):
        source_text = (
            f"{source_count} source"
            f"{'s' if source_count != 1 else ''} · "
            f"{article_count} article"
            f"{'s' if article_count != 1 else ''}"
        )
    else:
        source_text = "corroboration unavailable"

    entities = [
        entity
        for entity in safe_list(event.get("entities"))
        if isinstance(entity, dict)
    ]

    entity_html = ""

    if entities:
        entity_html = (
            '<div class="chips">'
            + "".join(
                f'<span class="entity-chip">'
                f'{esc(entity.get("name"))}'
                '</span>'
                for entity in entities[:8]
            )
            + "</div>"
        )

    delta_html = ""

    if event.get("delta_text"):
        delta_html = (
            '<div class="card-delta">'
            '<strong>Latest change</strong><br>'
            f'{esc(event.get("delta_text"))}'
            '</div>'
        )

    links = [
        link
        for link in safe_list(event.get("article_links"))
        if isinstance(link, dict)
    ]

    links_html = ""

    for link in links[:5]:
        url = str(link.get("url") or "").strip()

        if not url:
            continue

        links_html += (
            f'<a class="article-link" href="{esc(url)}" '
            'target="_blank" rel="noopener noreferrer">'
            f'↗ {esc(link.get("label") or "open article")}'
            '</a><br>'
        )

    if not links_html:
        links_html = '<span class="mono">no linked articles</span>'

    st.markdown(
        f'<div class="intel-card {state_class}">'
        '<div class="card-topline">'
        f'<div class="card-meta">{esc(source_text)}</div>'
        f'<span class="status-chip {state_class}">'
        f'{esc(status_text)}'
        '</span>'
        '</div>'
        f'<div class="card-title">{title}</div>'
        f'<div class="card-summary">{summary}</div>'
        f'{delta_html}'
        f'{entity_html}'
        '<div class="card-footer">'
        '<div class="source-count">'
        f'last update · {esc(format_timestamp(event.get("last_updated_at")))}'
        '</div>'
        f'<div>{links_html}</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    timeline = [
        entry
        for entry in safe_list(event.get("timeline"))
        if isinstance(entry, dict)
    ]

    if timeline:
        update_count = sum(
            1
            for entry in timeline
            if entry.get("type") == "update"
        )

        with st.expander(
            f"Timeline · {update_count} update"
            f"{'s' if update_count != 1 else ''}"
        ):
            render_event_timeline(timeline)


# =============================================================================
# Article functions
# =============================================================================

METRIC_LABELS = {
    "immediacy": "Immediacy",
    "scale": "Scale",
    "permanence": "Permanence",
    "reverberance": "Reverberance",
    "novelty": "Novelty",
}

ARTICLE_SORT_OPTIONS = ["Total"] + list(METRIC_LABELS.values())

ARTICLE_SORT_KEYS = {
    "Total": None,
    **{
        label: key
        for key, label in METRIC_LABELS.items()
    },
}


def score_tier(value: int, maximum: int) -> str:
    ratio = value / maximum if maximum else 0

    if ratio > 0.8:
        return "high"

    if ratio >= 0.5:
        return "mid"

    return "low"


def render_score_meters(metrics: dict) -> str:
    blocks = []

    for key, label in METRIC_LABELS.items():
        value = max(
            0,
            min(20, safe_int(metrics.get(key))),
        )

        tier = score_tier(value, 20)
        width = round((value / 20) * 100)

        blocks.append(
            '<div class="score-meter">'
            f'<div class="score-label">{esc(label)}</div>'
            '<div class="score-track">'
            f'<div class="score-fill {tier}" '
            f'style="width:{width}%"></div>'
            '</div>'
            f'<div class="score-number">{value}</div>'
            '</div>'
        )

    return "".join(blocks)


def render_article_card(article: dict) -> None:
    title = esc(article.get("title") or "Untitled article")
    summary = esc(
        article.get("ai_summary") or "No AI summary available"
    )

    source = esc(article.get("source") or "Unknown source")
    category = esc(article.get("category") or "")
    score = max(
        0,
        min(100, safe_int(article.get("score"))),
    )

    score_class = score_tier(score, 100)
    metrics = safe_dict(article.get("metrics"))

    tags = [
        tag
        for tag in safe_list(article.get("article_tags"))
        if tag is not None
    ]

    tags_html = ""

    if tags:
        tags_html = (
            '<div class="chips">'
            + "".join(
                f'<span class="tag-chip">{esc(tag)}</span>'
                for tag in tags
            )
            + '</div>'
        )

    link = str(article.get("link") or "").strip()

    if link:
        link_html = (
            f'<a class="article-link" href="{esc(link)}" '
            'target="_blank" rel="noopener noreferrer">'
            '↗ read source'
            '</a>'
        )
    else:
        link_html = '<span class="mono">no source link</span>'

    meta = f"{source} · {category}" if category else source

    st.markdown(
        '<div class="intel-card">'
        '<div class="score-header">'
        f'<div class="card-meta">{meta}</div>'
        f'<span class="score-chip {score_class}">'
        f'{score}/100'
        '</span>'
        '</div>'
        f'<div class="card-title">{title}</div>'
        f'<div class="card-summary">{summary}</div>'
        f'{render_score_meters(metrics)}'
        f'{tags_html}'
        '<div class="card-footer">'
        f'<div class="source-count">{link_html}</div>'
        '<div class="mono">impact profile</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


# =============================================================================
# Source functions
# =============================================================================

def render_sources(sources: list[dict]) -> None:
    cards = []

    for source in sources:
        source = safe_dict(source)

        name = esc(source.get("name") or "Unnamed source")
        category = esc(
            source.get("category") or "uncategorized"
        )
        tier = esc(source.get("tier") or "unknown tier")
        region = esc(source.get("region") or "")
        url = str(source.get("url") or "").strip()

        meta = f"{category} · {tier}"

        if region:
            meta += f" · {region}"

        tags = [
            tag
            for tag in safe_list(source.get("source_tags"))
            if tag is not None
        ]

        tags_html = ""

        if tags:
            tags_html = (
                '<div class="chips">'
                + "".join(
                    f'<span class="tag-chip">{esc(tag)}</span>'
                    for tag in tags[:6]
                )
                + '</div>'
            )

        if url:
            link_html = (
                f'<a href="{esc(url)}" target="_blank" '
                'rel="noopener noreferrer">'
                f'↗ {esc(source.get("link_label") or "open source")}'
                '</a>'
            )
        else:
            link_html = '<span class="mono">no source url</span>'

        cards.append(
            '<div class="source-card">'
            f'<div class="source-meta">{esc(meta)}</div>'
            f'<div class="source-name">{name}</div>'
            f'{tags_html}'
            f'{link_html}'
            '</div>'
        )

    st.markdown(
        f'<div class="source-grid">{"".join(cards)}</div>',
        unsafe_allow_html=True,
    )


# =============================================================================
# Pages
# =============================================================================

def render_briefings_page() -> None:
    render_topbar("briefings")

    files = load_with_placeholder(
        render_briefing_loading_state,
        lambda: services.get_briefing_files(),
    )

    files = files or []

    render_heading(
        "Daily intelligence",
        "Briefings",
        "Read the latest synthesized intelligence edition and inspect "
        "the evidence behind it.",
        f"{len(files)} editions available",
    )

    if not files:
        render_warning(
            "No briefing files were returned. Check your storage "
            "configuration and credentials."
        )
        render_empty(
            "No briefings published yet. "
            "The pipeline writes one after each scheduled run."
        )
        return

    selected = st.selectbox(
        "Edition",
        files,
        format_func=services.get_briefing_date,
        label_visibility="collapsed",
        key="briefing_edition",
    )

    date_str = services.get_briefing_date(selected)

    try:
        briefing_content = services.briefing_loader(selected)
    except Exception:
        logger.exception(
            "Unable to load briefing %s.",
            selected,
        )
        briefing_content = None

    try:
        raw_articles = services.get_raw_articles(date_str)
    except Exception:
        logger.exception(
            "Unable to load raw articles for %s.",
            date_str,
        )
        raw_articles = None

    try:
        new_count, developing_count = (
            services.get_event_stats_for_date(date_str)
        )
    except Exception:
        logger.exception(
            "Unable to load event statistics for %s.",
            date_str,
        )
        new_count, developing_count = None, None

    article_count = (
        len(raw_articles)
        if isinstance(raw_articles, (list, dict))
        else None
    )

    render_metric_grid(
        [
            (
                "Edition",
                date_str,
                "blue",
                "selected briefing",
            ),
            (
                "Articles",
                (
                    str(article_count)
                    if article_count is not None
                    else "—"
                ),
                "",
                "raw article records",
            ),
            (
                "New events",
                (
                    str(new_count)
                    if new_count is not None
                    else "—"
                ),
                "cyan",
                "first seen in edition",
            ),
            (
                "Developing",
                (
                    str(developing_count)
                    if developing_count is not None
                    else "—"
                ),
                "amber",
                "continued activity",
            ),
        ]
    )

    tab_briefing, tab_articles = st.tabs(
        ["Briefing", "Articles"]
    )

    with tab_briefing:
        if briefing_content:
            st.markdown(briefing_content)
        else:
            render_empty("This briefing is empty.")

    with tab_articles:
        articles = (
            raw_articles
            if isinstance(raw_articles, list)
            else []
        )

        if not articles:
            render_empty(
                f"No raw article data stored for {date_str}."
            )
            return

        sort_label = st.selectbox(
            "Article ordering",
            ARTICLE_SORT_OPTIONS,
            label_visibility="collapsed",
            key="article_ordering",
        )

        metric = ARTICLE_SORT_KEYS.get(sort_label)

        def article_sort_key(article: dict) -> int:
            if metric is None:
                return safe_int(article.get("score"))

            return safe_int(
                safe_dict(article.get("metrics")).get(metric)
            )

        for article in sorted(
            articles,
            key=article_sort_key,
            reverse=True,
        ):
            if isinstance(article, dict):
                render_article_card(article)


def render_monitor_page() -> None:
    render_topbar("live monitor")

    all_events = load_with_placeholder(
        render_event_loading_state,
        lambda: services.get_live_events(),
    )

    all_events = [
        event
        for event in (all_events or [])
        if isinstance(event, dict)
    ]

    render_heading(
        "Continuous tracking",
        "Live monitor",
        "Follow open events as new articles and sources are attached "
        "across ingestion runs.",
        f"{len(all_events)} open events",
    )

    query = st.text_input(
        "Search events",
        placeholder="Search event, entity, domain, or summary",
        label_visibility="collapsed",
        key="event_search",
    )

    filtered_events = [
        event
        for event in all_events
        if event_matches_query(event, query)
    ]

    domains = sorted(
        {
            str(domain)
            for event in all_events
            for domain in safe_list(event.get("domains"))
            if domain
        }
    )

    selected_domains = []

    if domains:
        selected_domains = st.multiselect(
            "Domain filter",
            domains,
            placeholder="All domains",
            key="event_domains",
        )

        if selected_domains:
            filtered_events = [
                event
                for event in filtered_events
                if any(
                    domain in selected_domains
                    for domain in safe_list(event.get("domains"))
                )
            ]

    col_sort, col_direction = st.columns([2, 1])

    with col_sort:
        sort_label = st.selectbox(
            "Order",
            ["Last updated", "Article count"],
            label_visibility="collapsed",
            key="event_sort",
        )

    with col_direction:
        descending = st.toggle(
            "Newest first",
            value=True,
            key="event_descending",
        )

    filtered_events = sorted(
        filtered_events,
        key=lambda event: event_sort_key(
            event,
            sort_label,
        ),
        reverse=descending,
    )

    new_count = sum(
        1
        for event in filtered_events
        if classify_event(event)[1] == "new"
    )

    developing_count = sum(
        1
        for event in filtered_events
        if classify_event(event)[1] == "developing"
    )

    render_metric_grid(
        [
            (
                "Visible",
                str(len(filtered_events)),
                "blue",
                "events after filters",
            ),
            (
                "New",
                str(new_count),
                "cyan",
                "first-seen events",
            ),
            (
                "Developing",
                str(developing_count),
                "amber",
                "multi-source activity",
            ),
            (
                "Domains",
                str(len(domains)),
                "",
                "registered in result set",
            ),
        ]
    )

    if not filtered_events:
        render_empty(
            "No open events match the current search and filters."
        )
        return

    for event in filtered_events:
        render_event_card(event)


def render_explorer_page() -> None:
    render_topbar("source explorer")

    sources = load_with_placeholder(
        render_source_loading_state,
        lambda: services.get_sources(),
    )

    sources = [
        source
        for source in (sources or [])
        if isinstance(source, dict)
    ]

    render_heading(
        "Feed registry",
        "Source explorer",
        "Inspect the sources used by the ingestion pipeline, including "
        "category, tier, region, and tags.",
        f"{len(sources)} registered sources",
    )

    if not sources:
        render_warning(
            "No sources were returned. The database may be unavailable "
            "or the source registry may be empty."
        )
        render_empty("No source records available.")
        return

    search = st.text_input(
        "Search sources",
        placeholder="Search source name, category, region, or tag",
        label_visibility="collapsed",
        key="source_search",
    ).lower()

    if search:
        filtered = []

        for source in sources:
            searchable = " ".join(
                [
                    str(source.get("name") or ""),
                    str(source.get("category") or ""),
                    str(source.get("tier") or ""),
                    str(source.get("region") or ""),
                    " ".join(
                        str(tag)
                        for tag in safe_list(
                            source.get("source_tags")
                        )
                    ),
                ]
            ).lower()

            if search in searchable:
                filtered.append(source)

        sources = filtered

    if not sources:
        render_empty("No sources match the current search.")
        return

    render_metric_grid(
        [
            (
                "Visible",
                str(len(sources)),
                "blue",
                "after search",
            ),
            (
                "Categories",
                str(
                    len(
                        {
                            source.get("category")
                            for source in sources
                            if source.get("category")
                        }
                    )
                ),
                "cyan",
                "source classes",
            ),
            (
                "Regions",
                str(
                    len(
                        {
                            source.get("region")
                            for source in sources
                            if source.get("region")
                        }
                    )
                ),
                "amber",
                "geographic coverage",
            ),
            (
                "Tagged",
                str(
                    sum(
                        bool(source.get("source_tags"))
                        for source in sources
                    )
                ),
                "",
                "sources with metadata",
            ),
        ]
    )

    render_sources(sources)


# =============================================================================
# Application shell
# =============================================================================

if "page" not in st.session_state:
    st.session_state.page = "Briefings"

with st.sidebar:
    st.markdown(
        '<div class="brand">'
        '<div class="brand-mark">◈</div>'
        '<div>'
        '<div class="brand-name">ISOLATE</div>'
        '<div class="brand-subtitle">control surface</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    st.markdown(
        '<div class="mono">WORKSPACE</div>',
        unsafe_allow_html=True,
    )

    if st.button(
        "▣  Briefings",
        use_container_width=True,
        type=(
            "primary"
            if st.session_state.page == "Briefings"
            else "secondary"
        ),
    ):
        st.session_state.page = "Briefings"
        st.rerun()

    if st.button(
        "◌  Live monitor",
        use_container_width=True,
        type=(
            "primary"
            if st.session_state.page == "Live Monitor"
            else "secondary"
        ),
    ):
        st.session_state.page = "Live Monitor"
        st.rerun()

    if st.button(
        "⌁  Source explorer",
        use_container_width=True,
        type=(
            "primary"
            if st.session_state.page == "Explorer"
            else "secondary"
        ),
    ):
        st.session_state.page = "Explorer"
        st.rerun()

    st.markdown("---")

    st.markdown(
        '<div class="mono">SYSTEM</div>'
        '<div class="mono" style="margin-top:0.55rem;">'
        'storage · database · pipeline'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="topbar-context" style="margin-top:0.8rem;">'
        '<span class="status-dot"></span>'
        '<span class="topbar-status">interface ready</span>'
        '</div>',
        unsafe_allow_html=True,
    )


if st.session_state.page == "Briefings":
    render_briefings_page()
elif st.session_state.page == "Live Monitor":
    render_monitor_page()
elif st.session_state.page == "Explorer":
    render_explorer_page()