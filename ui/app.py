import sys
from pathlib import Path
import streamlit as st
import services

# Ensure the project root is on sys.path so ui imports work from any cwd.
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))



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

    .block-container {
        padding: 1.8rem 2rem 2rem;
        max-width: 1180px;
        margin: 0 auto;
    }

    /* --- Hero Header Styles --- */
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

    /* --- General UI Components --- */
    .stMetric {
        border-radius: 20px;
        background: rgba(255, 255, 255, 0.95);
        box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
        min-width: 260px;
        padding: 0.8rem 1rem;
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

    /* --- Unified Tabs & Card Styling --- */
    /* Target the tab selector bar */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        padding: 0.4rem;
        background: rgba(255, 255, 255, 0.6);
        border-radius: 16px;
        box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.16);
        margin-bottom: 0.5rem;
    }
    
    /* Target individual unselected tabs */
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px;
        padding: 0.6rem 1.2rem;
        height: auto;
        border: none !important;
        background: transparent;
        color: #475569;
    }
    
    /* Target the selected tab */
    .stTabs [aria-selected="true"] {
        background: #ffffff !important;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
        color: #1d4ed8 !important;
        font-weight: 600;
    }

    /* Turn the entire tab content area into your briefing card */
    [data-testid="stTab"] {
        background: #ffffff;
        border-radius: 24px;
        padding: 2.2rem 2.5rem;
        box-shadow: 0 20px 50px rgba(15, 23, 42, 0.06);
        border: 1px solid rgba(148, 163, 184, 0.14);
        margin-top: 0.5rem;
    }

    /* --- Typography Tweaks --- */
    .stMarkdown p, .stMarkdown li {
        line-height: 1.8;
        color: #334155;
        font-size: 1.05rem;
    }

    /* Make JSON viewer look at home */
    .stJson {
        background: #f8fafc;
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid #e2e8f0;
    }

    @media (max-width: 768px) {
        .block-container { padding: 1rem 1rem 1.5rem; }
        .hero-card { padding: 1.3rem 1.2rem; margin-bottom: 1.2rem; }
        .hero-card h1 { font-size: 2rem; }
        [data-testid="stTab"] { padding: 1.2rem 1.2rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

render_header()

# --- Reusable UI Component for Data Lineage ---
def render_artifacts(date_str: str, briefing_content: str):
    """Renders the Briefing, Markdown, and JSON into beautifully styled native tabs."""
    
    col1, _ = st.columns([1, 8])
    with col1:
        st.metric("Date", date_str)

    # Tabs will now automatically look like your custom briefing cards!
    tab_briefing, tab_markdown, tab_json = st.tabs([
        "🧠 Intelligence Briefing", 
        "📑 Context (Markdown)", 
        "💾 Raw Data (JSON)"
    ])

    with tab_briefing:
        st.markdown(briefing_content)

    with tab_markdown:
        md_content = services.get_markdown_report(date_str)
        if md_content:
            st.markdown(md_content)
        else:
            st.info(f"No intermediate markdown found in S3 for {date_str}.")

    with tab_json:
        json_data = services.get_raw_articles(date_str)
        if json_data:
            st.json(json_data, expanded=True) 
        else:
            st.info(f"No raw JSON data found in S3 for {date_str}.")


# --- Navigation bar ---
with st.container():
    page = st.segmented_control(
        "Navigation",
        ["Today's Briefing", "Historical Briefings", "Database Explorer"],
        default="Today's Briefing"
    )

# --- Page Routing ---
if page == "Database Explorer":
    explorer_view = st.radio(
        "Explorer",
        ["Events", "Sources"],
        horizontal=True,
        label_visibility="collapsed"
    )

    if explorer_view == "Events":
        st.subheader("Events")
        tables = services.get_database_tables()
        events = tables.get("events", [])
        if events:
            for event in events:
                with st.container():
                    article_links = event.get("article_links") or []
                    links_html = "".join(
                        f"<div style='margin-top:0.25rem;'><a href='{link['url']}' target='_blank' rel='noopener noreferrer' style='color:#2563eb;text-decoration:none;'>{link.get('label', 'Open article')}</a></div>"
                        for link in article_links
                    ) or "<div style='margin-top:0.25rem;color:#64748b;'>No linked articles</div>"
                    st.markdown(
                        f"""
                        <div style="border:1px solid #e2e8f0;border-radius:16px;padding:1rem 1rem 0.8rem;margin-bottom:0.8rem;background:#ffffff;box-shadow:0 6px 18px rgba(15,23,42,0.04);">
                          <div style="font-size:0.9rem;color:#64748b;margin-bottom:0.3rem;">{event.get('category') or 'uncategorized'} · {event.get('importance') or 'unknown'}</div>
                          <div style="font-size:1.1rem;font-weight:700;color:#0f172a;margin-bottom:0.35rem;">{event.get('name', 'Untitled event')}</div>
                          <div style="font-size:0.95rem;color:#334155;margin-bottom:0.4rem;">{(event.get('summary') or 'No summary available')[:220]}</div>
                          <div style="font-size:0.82rem;color:#64748b;margin-bottom:0.35rem;">Tags: {', '.join(event.get('tags') or []) if event.get('tags') else 'None'}</div>
                          <div style="font-size:0.88rem;color:#0f172a;font-weight:600;">Articles</div>
                          {links_html}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        else:
            st.info("No events found or the database is unavailable.")
    else:
        st.subheader("Sources")
        tables = services.get_database_tables()
        sources = tables.get("sources", [])
        if sources:
            for source in sources:
                with st.container():
                    source_url = source.get("url", "") or ""
                    source_label = source.get("link_label") or source.get("name", "Source")
                    source_url_html = f"<div style='margin-top:0.25rem;'><a href='{source_url}' target='_blank' rel='noopener noreferrer' style='color:#2563eb;text-decoration:none;'>{source_label}</a></div>" if source_url else "<div style='margin-top:0.25rem;color:#64748b;'>No URL available</div>"
                    st.markdown(
                        f"""
                        <div style="border:1px solid #e2e8f0;border-radius:16px;padding:1rem 1rem 0.8rem;margin-bottom:0.8rem;background:#ffffff;box-shadow:0 6px 18px rgba(15,23,42,0.04);">
                          <div style="font-size:1.05rem;font-weight:700;color:#0f172a;margin-bottom:0.25rem;">{source.get('name', 'Unnamed source')}</div>
                          <div style="font-size:0.9rem;color:#64748b;margin-bottom:0.3rem;">{source.get('category') or 'uncategorized'} · {source.get('tier') or 'unknown tier'}</div>
                          {source_url_html}
                          <div style="font-size:0.82rem;color:#64748b;margin-top:0.35rem;">Tags: {', '.join(source.get('source_tags') or []) if source.get('source_tags') else 'None'}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        else:
            st.info("No sources found or the database is unavailable.")

elif page == "Today's Briefing":
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