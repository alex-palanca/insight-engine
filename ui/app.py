import sys
from pathlib import Path

# Ensure the project root is on sys.path so ui imports work from any cwd.
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
from ui import services








def render_header():

    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-header-row">
                <span class="hero-badge">ISOLATE</span>
            </div>
            <h1>Intelligence Briefing Hub</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Page configuration
st.set_page_config(
    page_title="ISOLATE - Intelligence Briefing",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

render_header()

# Custom styling
st.markdown(
    """
    <style>
    :root {
        color-scheme: light;
        font-family: Inter, system-ui, sans-serif;
    }

    body,
    body[data-theme='dark'],
    :root[data-theme='dark'] {
        background: linear-gradient(180deg, #f4f7ff 0%, #eef2ff 100%);
        color: #0f172a;
    }

    body {
        background: linear-gradient(180deg, #f4f7ff 0%, #eef2ff 100%);
    }

    .block-container {
        padding: 1.8rem 2rem 2rem;
        max-width: 1180px;
        margin: 0 auto;
    }

    .hero-card {
        width: 100%;
        max-width: 1080px;
        margin: 0 auto 1.5rem;
        border-radius: 28px;
        padding: 1.8rem 2rem;
        background: rgba(255, 255, 255, 0.95);
        box-shadow: 0 22px 60px rgba(15, 23, 42, 0.08);
        border: 1px solid rgba(148, 163, 184, 0.18);
    }

    @media (max-width: 768px) {
        .block-container {
            padding: 1rem 1rem 1.5rem;
        }

        .hero-card {
            padding: 1.3rem 1.2rem;
            margin-bottom: 1.2rem;
        }

        .hero-card h1 {
            font-size: 2rem;
        }

        .hero-description {
            max-width: 100%;
            font-size: 0.95rem;
        }

        .st-segmented-control > div {
            padding: 0.2rem;
        }

        .st-segmented-control button {
            padding: 0.7rem 0.9rem;
            font-size: 0.92rem;
        }

        .stMetric {
            min-width: 0;
            width: 100%;
            margin-bottom: 0.85rem;
        }

        .stSelectbox>div>button,
        .stSelectbox>div>div>button,
        .stButton>button {
            width: 100%;
        }

        .briefing-card {
            padding: 1.4rem 1.4rem;
        }

        .briefing-card .stMarkdown {
            font-size: 0.98rem;
        }
    }

    .hero-header-row {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        justify-content: center;
        margin-bottom: 1rem;
    }

    .hero-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.45rem 0.9rem;
        border-radius: 999px;
        background: #eff6ff;
        color: #1d4ed8;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        font-size: 0.82rem;
    }

    .hero-card h1 {
        margin: 0;
        font-size: 2.8rem;
        color: #0f172a;
        text-align: center;
    }

    .hero-description {
        margin: 1rem auto 0;
        max-width: 760px;
        color: #475569;
        font-size: 1rem;
        line-height: 1.75;
        text-align: center;
    }

    .stMetric {
        border-radius: 20px;
        background: rgba(255, 255, 255, 0.95);
        box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
        min-width: 260px;
        padding: 0.8rem 1rem;
    }

    .stMetric .metric-label,
    .stMetric .metric-value {
        word-break: break-word;
    }

    .stMetric .metric-value {
        min-height: 2.5rem;
    }

    .st-segmented-control > div {
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.96);
        padding: 0.28rem;
        box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.16);
        margin-bottom: 1.3rem;
    }

    .st-segmented-control button {
        border-radius: 999px;
        padding: 0.75rem 1.2rem;
        font-weight: 600;
    }

    .stSelectbox>div>button,
    .stSelectbox>div>div>button,
    .stButton>button {
        border-radius: 16px;
        border: 1px solid rgba(148, 163, 184, 0.18);
        background: rgba(255, 255, 255, 0.96);
    }

    .briefing-card {
        background: #ffffff;
        border-radius: 24px;
        padding: 1.8rem 1.9rem;
        margin-top: 1rem;
        box-shadow: 0 20px 50px rgba(15, 23, 42, 0.06);
        border: 1px solid rgba(148, 163, 184, 0.14);
    }

    .briefing-card .stMarkdown {
        color: #334155;
    }

    .stMarkdown p,
    .stMarkdown li,
    .stMarkdown h2,
    .stMarkdown h3 {
        line-height: 1.75;
    }

    @media (max-width: 768px) {
        .stMetric {
            min-width: 0;
            width: 100%;
            margin-bottom: 1rem;
        }

        .stMetric .metric-value {
            font-size: 1.1rem;
        }

        .st-segmented-control button {
            width: 100%;
            margin-bottom: 0.5rem;
        }

        .stSelectbox>div>button,
        .stSelectbox>div>div>button,
        .stButton>button {
            width: 100%;
        }

        .briefing-card {
            padding: 1.2rem 1.2rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Reusable UI Component for Data Lineage ---
def render_artifacts(date_str: str, briefing_content: str):
    """Renders the Briefing, Markdown, and JSON into organized tabs."""
    
    col1, _ = st.columns([1, 8])
    with col1:
        st.metric("Date", date_str)

    # Use tabs to showcase the Data Lineage
    tab_briefing, tab_markdown, tab_json = st.tabs([
        "🧠 Intelligence Briefing", 
        "📑 Context (Markdown)", 
        "💾 Raw Data (JSON)"
    ])

    with tab_briefing:
        st.markdown('<div class="briefing-card">', unsafe_allow_html=True)
        st.markdown(briefing_content)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_markdown:
        md_content = services.get_markdown_report(date_str)
        if md_content:
            st.markdown('<div class="briefing-card">', unsafe_allow_html=True)
            st.markdown(md_content)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info(f"No intermediate markdown found in S3 for {date_str}.")

    with tab_json:
        json_data = services.get_raw_articles(date_str)
        if json_data:
            # Streamlit's st.json provides a great interactive tree viewer automatically
            st.json(json_data, expanded=False) 
        else:
            st.info(f"No raw JSON data found in S3 for {date_str}.")


# --- Navigation bar ---
with st.container():
    page = st.segmented_control(
        "Navigation",
        ["Today's Briefing", "Historical Briefings"],
        default="Today's Briefing"
    )

# --- Page Routing ---
if page == "Today's Briefing":
    briefing_files = services.get_briefing_files()

    if not briefing_files:
        st.warning("No briefing files found in S3.")
    else:
        latest_briefing = briefing_files[0]
        briefing_date = services.get_briefing_date(latest_briefing)
        content = services.briefing_loader(latest_briefing)
        
        render_artifacts(briefing_date, content)

elif page == "Historical Briefings":
    briefing_files = services.get_briefing_files()

    if not briefing_files:
        st.warning("No historical briefing files found in S3.")
    else:
        selected_file = st.selectbox(
            "Select a briefing",
            briefing_files,
            format_func=services.get_briefing_date
        )

        if selected_file:
            briefing_date = services.get_briefing_date(selected_file)
            content = services.briefing_loader(selected_file)
            
            render_artifacts(briefing_date, content)