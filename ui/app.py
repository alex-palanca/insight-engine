import textwrap
import env_ini as env# noqa: F401
import streamlit as st
import services



# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ISOLATE · Intelligence Briefing",
    page_icon="📰",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# Styling — keeps the ORIGINAL colorway (blue accent, white cards, soft-blue
# page, rounded cards) and adapts to Streamlit's light/dark theme via CSS
# variables rather than forcing light like the original did.
# Novelty tiers are shades of the existing blue accent + slate, so they stay
# inside the original palette instead of introducing new hues.
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    textwrap.dedent(
        """\
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --accent:      #1d4ed8;   /* primary blue (badges, selected, NEW)     */
        --accent-2:    #2563eb;   /* link blue                                */
        --accent-soft: #eff6ff;   /* badge / NEW tint                          */
        --developing:  #3b82f6;   /* lighter blue = DEVELOPING                 */
        --developing-soft:#e8f0fe;
        --signal:      #94a3b8;   /* slate = SIGNAL / uncorroborated           */
        --signal-soft: #f1f5f9;
        --wip:         #b0771f;   /* amber, reserved ONLY for WIP flags        */
        --wip-soft:    #fdf4e3;

        --ink:    #0f172a;        /* headings          */
        --body:   #334155;        /* paragraph text    */
        --muted:  #64748b;        /* meta text         */
        --hair:   #e2e8f0;        /* hairlines         */
        --card:   #ffffff;
        --page-1: #f4f7ff;
        --page-2: #eef2ff;
    }

    /* Dark-mode overrides — respects Streamlit's theme instead of forcing light */
    [data-theme="dark"] {
        --accent-soft: #16233f;
        --developing-soft: #172136;
        --signal-soft: #1e293b;
        --wip-soft: #2a2113;
        --ink:   #f1f5f9;
        --body:  #cbd5e1;
        --muted: #94a3b8;
        --hair:  #2a3444;
        --card:  #0f172a;
        --page-1:#0b1220;
        --page-2:#0d1526;
    }

    .stApp {
        background: linear-gradient(180deg, var(--page-1) 0%, var(--page-2) 100%);
        font-family: 'Inter', system-ui, sans-serif;
    }
    .block-container {
        padding: 1.5rem 1.1rem 3rem;
        max-width: 1080px;
        margin: 0 auto;
    }
    @media (min-width: 768px) {
        .block-container { padding: 2rem 2rem 3rem; }
    }

    /* ── Hero (original centered hero-card, made theme-adaptive) ── */
    .hero-card {
        width: 100%;
        max-width: 1080px;
        margin: 0 auto 1.5rem;
        border-radius: 28px;
        padding: 1.8rem 2rem;
        background: var(--card);
        box-shadow: 0 22px 60px rgba(15, 23, 42, 0.08);
        border: 1px solid var(--hair);
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
        background: var(--accent-soft);
        color: var(--accent);
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        font-size: 0.82rem;
    }
    .hero-card h1 {
        margin: 0;
        font-size: clamp(2rem, 5vw, 2.8rem);
        color: var(--ink);
        text-align: center;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    @media (max-width: 768px) {
        .hero-card { padding: 1.3rem 1.2rem; margin-bottom: 1.2rem; }
        .hero-card h1 { font-size: 2rem; }
    }

    /* ── Metric strip ─────────────────────────────────────────── */
    .metrics {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 0.6rem;
        margin-bottom: 1.4rem;
    }
    @media (min-width: 620px) { .metrics { grid-template-columns: repeat(4, 1fr); } }
    .metric {
        background: var(--card);
        border: 1px solid var(--hair);
        border-radius: 16px;
        padding: 0.8rem 1rem;
        box-shadow: 0 8px 22px rgba(15, 23, 42, 0.04);
    }
    .metric-k {
        font-size: 0.68rem; letter-spacing: 0.08em; text-transform: uppercase;
        color: var(--muted); font-weight: 600;
    }
    .metric-v { font-size: 1.5rem; font-weight: 700; color: var(--ink); margin-top: 0.15rem; line-height: 1.1; }
    .metric-v.wip { color: var(--wip); font-size: 1rem; }

    /* ── Segmented nav ────────────────────────────────────────── */
    div[data-testid="stSegmentedControl"] { margin-bottom: 1.2rem; }
    div[data-testid="stSegmentedControl"] button {
        border-radius: 999px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.1rem !important;
    }

    /* ── Tabs ─────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.4rem; padding: 0.35rem;
        background: var(--card);
        border: 1px solid var(--hair);
        border-radius: 14px;
        margin-bottom: 0.4rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px; padding: 0.55rem 1rem; height: auto;
        color: var(--muted); font-weight: 600; font-size: 0.9rem;
    }
    .stTabs [aria-selected="true"] { background: var(--accent-soft) !important; color: var(--accent) !important; }
    .stTabs [data-baseweb="tab-highlight"] { background: transparent; }
    [data-testid="stTab"] {
        background: var(--card);
        border: 1px solid var(--hair);
        border-radius: 22px;
        padding: 1.8rem 1.9rem;
        box-shadow: 0 16px 40px rgba(15, 23, 42, 0.06);
        margin-top: 0.4rem;
    }
    @media (max-width: 640px) { [data-testid="stTab"] { padding: 1.2rem 1.1rem; } }

    /* ── Briefing prose ───────────────────────────────────────── */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: var(--ink); letter-spacing: -0.01em; }
    .stMarkdown h2 { border-bottom: 1px solid var(--hair); padding-bottom: 0.3rem; margin-top: 1.5rem; }
    .stMarkdown p, .stMarkdown li { line-height: 1.75; color: var(--body); font-size: 1.04rem; }
    .stMarkdown a { color: var(--accent-2); text-decoration: none; border-bottom: 1px solid transparent; }
    .stMarkdown a:hover { border-bottom-color: var(--accent-2); }

    /* ── Intel cards ──────────────────────────────────────────── */
    .card {
        position: relative;
        background: var(--card);
        border: 1px solid var(--hair);
        border-left: 4px solid var(--signal);
        border-radius: 16px;
        padding: 1rem 1.15rem 0.9rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 8px 22px rgba(15, 23, 42, 0.04);
    }
    .card.k-new        { border-left-color: var(--accent); }
    .card.k-developing { border-left-color: var(--developing); }
    .card.k-signal     { border-left-color: var(--signal); }

    .kicker {
        display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;
        font-size: 0.72rem; color: var(--muted); font-weight: 600;
        text-transform: uppercase; letter-spacing: 0.05em;
        margin-bottom: 0.4rem;
    }
    .pill {
        font-size: 0.62rem; font-weight: 700; letter-spacing: 0.06em;
        text-transform: uppercase; padding: 0.14rem 0.5rem; border-radius: 999px;
    }
    .pill.new        { background: var(--accent-soft);     color: var(--accent); }
    .pill.developing { background: var(--developing-soft); color: var(--developing); }
    .pill.signal     { background: var(--signal-soft);     color: var(--muted); }
    .pill.wip        { background: var(--wip-soft); color: var(--wip); border: 1px dashed var(--wip); }

    .card-title { font-size: 1.14rem; font-weight: 700; color: var(--ink); line-height: 1.25; margin-bottom: 0.3rem; }
    .card-summary { font-size: 0.98rem; line-height: 1.55; color: var(--body); margin-bottom: 0.5rem; }
    .card-delta { font-size: 0.94rem; color: var(--body); margin: 0.3rem 0 0.5rem; padding-left: 0.7rem; border-left: 2px solid var(--developing); }
    .card-delta strong { color: var(--ink); }

    .tags { display: flex; gap: 0.32rem; flex-wrap: wrap; margin: 0.4rem 0; }
    .tag { font-size: 0.68rem; background: var(--signal-soft); border: 1px solid var(--hair); color: var(--muted); padding: 0.1rem 0.45rem; border-radius: 6px; }
    .entities { display: flex; gap: 0.32rem; flex-wrap: wrap; margin: 0.3rem 0; }
    .ent { font-size: 0.68rem; font-weight: 600; background: var(--accent-soft); color: var(--accent); padding: 0.1rem 0.45rem; border-radius: 6px; }

    .links a { display: inline-block; font-size: 0.82rem; color: var(--accent-2); text-decoration: none; margin-top: 0.24rem; border-bottom: 1px solid transparent; }
    .links a:hover { border-bottom-color: var(--accent-2); }
    .links .none { font-size: 0.8rem; color: var(--muted); }
    .corro { color: var(--muted); }
    .corro.wip { color: var(--wip); }

    .sec-label { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); margin: 1.6rem 0 0.9rem; }

    .wip-note {
        background: var(--wip-soft);
        border: 1px dashed var(--wip);
        border-radius: 12px;
        padding: 0.75rem 0.95rem;
        color: var(--wip);
        font-size: 0.85rem;
        margin-bottom: 1rem;
    }
    .empty {
        background: var(--card); border: 1px dashed var(--hair); border-radius: 12px;
        padding: 1.4rem; text-align: center; color: var(--muted); font-size: 0.9rem;
    }

    div[data-testid="stJson"] { border-radius: 12px; border: 1px solid var(--hair); }
    .stSelectbox label, .stRadio label { color: var(--muted); font-weight: 600; font-size: 0.8rem; }
    #MainMenu, footer { visibility: hidden; }
    </style>
    """
    ),
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def esc(text) -> str:
    if text is None:
        return ""
    # Collapse embedded newlines/whitespace runs (common in LLM-generated summaries
    # and deltas) — a raw "\n" here would land at column 0 inside the indented
    # f-string templates below, poisoning textwrap.dedent's common-prefix
    # calculation and causing the whole card to render as a literal code block.
    normalized = " ".join(str(text).split())
    return normalized.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def hero(dateline: str = ""):
    # Single-line HTML: a multi-line template mixing flush-left open/close tags
    # with indented inner content defeats textwrap.dedent (the common prefix
    # across all lines is 0) and, if any interpolated piece is ever empty, the
    # resulting blank line ends the HTML block and the leftover indentation on
    # the next line gets swallowed into an indented code block (shown as raw
    # text). Keeping it on one line sidesteps that entirely.
    st.markdown(
        '<div class="hero-card">'
        '<div class="hero-header-row"><span class="hero-badge">ISOLATE</span></div>'
        "<h1>Intelligence Briefing Hub</h1>"
        "</div>",
        unsafe_allow_html=True,
    )


def metric_strip(items):
    """items: list of (label, value, is_wip)."""
    cells = ""
    for label, value, is_wip in items:
        vclass = "metric-v wip" if is_wip else "metric-v"
        cells += (
            f'<div class="metric"><div class="metric-k">{esc(label)}</div>'
            f'<div class="{vclass}">{esc(value)}</div></div>'
        )
    st.markdown(f'<div class="metrics">{cells}</div>', unsafe_allow_html=True)


def classify_event(event: dict):
    """
    Returns (css_class, pill_label). NEW/DEVELOPING/SIGNAL depend on the
    event-persistence schema, which is shipping INCREMENTALLY (e.g. first_seen_at
    may exist before last_updated_at / status / article_count). We only trust the
    classification when the WHOLE set is present; otherwise we show the WIP marker
    rather than silently mislabelling everything as one tier.
    """
    status = event.get("status")
    first_seen = event.get("first_seen_at")
    last_updated = event.get("last_updated_at")
    article_count = event.get("article_count")

    # Require the full set before classifying. A NEW event legitimately has
    # first_seen == last_updated, so we can't use "they differ" as presence —
    # we check the raw fields are all non-None instead.
    fields_ready = (
        status is not None
        and first_seen is not None
        and last_updated is not None
        and article_count is not None
    )
    if not fields_ready:
        return "k-signal", "wip"

    if status == "closed":
        return "k-signal", "signal"
    if first_seen == last_updated:
        return "k-new", "new"
    if article_count <= 1:
        return "k-signal", "signal"
    return "k-developing", "developing"


def render_event_card(event: dict):
    css_class, label = classify_event(event)
    pill_map = {
        "new":        '<span class="pill new">● New</span>',
        "developing": '<span class="pill developing">◐ Developing</span>',
        "signal":     '<span class="pill signal">○ Signal</span>',
        "wip":        '<span class="pill wip">⚙ novelty · wip</span>',
    }
    pill = pill_map.get(label, "")
    
    name = esc(event.get("name") or "Untitled event")
    summary = esc((event.get("summary") or "No summary available")[:280])
    links = event.get("article_links") or []

    # New-schema fields, shown as WIP when absent.
    entities = event.get("entities")
    source_count = event.get("source_count")
    delta = event.get("delta_text")

    if isinstance(source_count, int):
        corro = f'<span class="corro">{source_count} sources</span>'
    else:
        corro = f'<span class="corro wip">🚧 {len(links)} link{"s" if len(links) != 1 else ""}</span>'

    if isinstance(entities, list) and entities:
        ent_html = '<div class="entities">' + "".join(
            f'<span class="ent">{esc(e.get("name"))}</span>' for e in entities[:8]
        ) + "</div>"
    else:
        ent_html = '<div class="entities"><span class="pill wip">🚧 entities · wip</span></div>'

    delta_html = f'<div class="card-delta"><strong>What\'s new:</strong> {esc(delta)}</div>' if delta else ""

    links_html = "".join(
        f'<div><a href="{esc(l.get("url"))}" target="_blank" rel="noopener noreferrer">↗ {esc(l.get("label", "Open article"))}</a></div>'
        for l in links
    ) or '<div class="none">No linked articles</div>'

    st.markdown(
        f'<div class="card {css_class}">'
        f'<div class="kicker">{pill}· {corro}</div>'
        f'<div class="card-title">{name}</div>'
        f'<div class="card-summary">{summary}</div>'
        f"{delta_html}"
        f"{ent_html}"
        f'<div class="links">{links_html}</div>'
        "</div>",
        unsafe_allow_html=True,
    )


def render_source_card(source: dict):
    name = esc(source.get("name") or "Unnamed source")
    category = esc(source.get("category") or "uncategorized")
    tier = esc(source.get("tier") or "unknown tier")
    region = esc(source.get("region") or "")
    url = source.get("url") or ""
    label = esc(source.get("link_label") or source.get("name") or "Source")
    tags = source.get("source_tags") or []

    meta = f"{category} · {tier}" + (f" · {region}" if region else "")
    tags_html = ('<div class="tags">' + "".join(f'<span class="tag">{esc(t)}</span>' for t in tags) + "</div>") if tags else ""
    link_html = (
        f'<div class="links"><a href="{esc(url)}" target="_blank" rel="noopener noreferrer">↗ {label}</a></div>'
        if url else '<div class="links"><span class="none">No URL available</span></div>'
    )

    st.markdown(
        '<div class="card">'
        f'<div class="kicker"><span>{meta}</span></div>'
        f'<div class="card-title">{name}</div>'
        f"{link_html}"
        f"{tags_html}"
        "</div>",
        unsafe_allow_html=True,
    )


def render_artifacts(date_str: str, briefing_content: str):
    raw = services.get_raw_articles(date_str)
    article_count = len(raw) if isinstance(raw, (list, dict)) else None

    metric_strip([
        ("Edition", date_str, False),
        ("Articles", str(article_count) if article_count is not None else "—", False),
        ("New today", "🚧 wip", True),
        ("Developing", "🚧 wip", True),
    ])

    tab_brief, tab_md, tab_json = st.tabs(["🧠 Briefing", "📑 Context", "💾 Raw"])
    with tab_brief:
        if briefing_content:
            st.markdown(briefing_content)
        else:
            st.markdown('<div class="empty">This briefing is empty.</div>', unsafe_allow_html=True)
    with tab_md:
        md = services.get_markdown_report(date_str)
        if md:
            st.markdown(md)
        else:
            st.markdown(f'<div class="empty">No intermediate context stored for {esc(date_str)}.</div>', unsafe_allow_html=True)
    with tab_json:
        if raw:
            st.json(raw, expanded=False)
        else:
            st.markdown(f'<div class="empty">No raw article data stored for {esc(date_str)}.</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────────────────────────
hero()

page = st.segmented_control(
    "Navigation",
    ["Today", "Archive", "Live Monitor", "Explorer"],
    default="Today",
    label_visibility="collapsed",
)

# ── Today ────────────────────────────────────────────────────────────────────
if page == "Today":
    files = services.get_briefing_files()
    if not files:
        st.markdown('<div class="empty">No briefings published yet. The pipeline writes one after each scheduled run.</div>', unsafe_allow_html=True)
    else:
        latest = files[0]
        date = services.get_briefing_date(latest)
        render_artifacts(date, services.briefing_loader(latest))

# ── Archive ──────────────────────────────────────────────────────────────────
elif page == "Archive":
    files = services.get_briefing_files()
    if not files:
        st.markdown('<div class="empty">No archived briefings yet.</div>', unsafe_allow_html=True)
    else:
        selected = st.selectbox("Select a briefing", files, format_func=services.get_briefing_date)
        if selected:
            date = services.get_briefing_date(selected)
            render_artifacts(date, services.briefing_loader(selected))

# ── Live Monitor (NEW feature — depends on unbuilt event schema) ─────────────
elif page == "Live Monitor":
    st.markdown(
        '<div class="wip-note">⚙ Work in progress — the Live Monitor tracks open events as they '
        'develop across runs (New · Developing · Signal), with each story\'s momentum and latest '
        'delta. It activates once event persistence (status, timestamps, deltas) lands in the '
        'database. Showing current events below with provisional classification.</div>',
        unsafe_allow_html=True,
    )
    events = services.get_database_tables().get("events", [])
    if not events:
        st.markdown('<div class="empty">No events available yet.</div>', unsafe_allow_html=True)
    else:
        for ev in events:
            render_event_card(ev)

# ── Explorer ─────────────────────────────────────────────────────────────────
elif page == "Explorer":
    view = st.radio("Explorer", ["Events", "Sources"], horizontal=True, label_visibility="collapsed")
    tables = services.get_database_tables()

    if view == "Events":
        events = tables.get("events", [])
        st.markdown('<div class="sec-label">Events · lifecycle &amp; corroboration</div>', unsafe_allow_html=True)
        if events:
            for ev in events:
                render_event_card(ev)
        else:
            st.markdown('<div class="empty">No events found, or the database is unavailable.</div>', unsafe_allow_html=True)
    else:
        sources = tables.get("sources", [])
        st.markdown('<div class="sec-label">Sources · feed registry</div>', unsafe_allow_html=True)
        if sources:
            for s in sources:
                render_source_card(s)
        else:
            st.markdown('<div class="empty">No sources found, or the database is unavailable.</div>', unsafe_allow_html=True)