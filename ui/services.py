import json
import logging
import streamlit as st
from urllib.parse import urlparse
from storage.s3_client import S3Storage as s3
from sqlalchemy.orm import selectinload


logger = logging.getLogger(__name__)
cloud = s3()


def build_link_label(url: str, source_name: str | None = None) -> str:
    """Create a readable label for a URL such as 'BBC | news'."""
    if not url:
        return "Untitled link"

    parsed = urlparse(url)
    host = (parsed.netloc or "").lower().replace("www.", "")

    known_publishers = {
        "bbc.co.uk": "BBC",
        "bbc.com": "BBC",
        "reuters.com": "Reuters",
        "apnews.com": "AP News",
        "axios.com": "Axios",
        "techcrunch.com": "TechCrunch",
        "theverge.com": "The Verge",
        "wired.com": "Wired",
        "arstechnica.com": "Ars Technica",
        "cnn.com": "CNN",
        "nytimes.com": "The New York Times",
        "washingtonpost.com": "The Washington Post",
        "forbes.com": "Forbes",
        "bloomberg.com": "Bloomberg",
        "ft.com": "Financial Times",
        "theguardian.com": "The Guardian",
        "aljazeera.com": "Al Jazeera",
        "cnbc.com": "CNBC",
        "theregister.com": "The Register",
        "zdnet.com": "ZDNet",
        "venturebeat.com": "VentureBeat",
        "engadget.com": "Engadget",
    }

    publisher = source_name or known_publishers.get(host) or host.split(".")[0].title()
    segments = [segment for segment in parsed.path.strip("/").split("/") if segment]
    section = None
    for segment in segments:
        if segment.isdigit() or segment in {"article", "articles", "story", "stories", "video", "videos"}:
            continue
        section = segment.replace("-", " ").replace("_", " ").strip()
        break

    if section and section.lower() not in {"home", "index"}:
        return f"{publisher} | {section.title()}"
    return publisher


def get_db_service():
    """Create a database service client for PostgreSQL-backed tables."""
    try:
        from storage.db_service import NeonDatabaseService
        return NeonDatabaseService()
    except Exception:
        logger.exception("Database connection failed.")
        return None


@st.cache_data(ttl=3600,show_spinner="Loading events...")
def get_events() -> list[dict]:
    """Fetch all events from the PostgreSQL events table, including linked article URLs."""
    db_service = get_db_service()
    if not db_service:
        return []

    from storage.db_service import Event

    with db_service._SessionMarker() as session:
        try:
            rows = session.query(Event).options(selectinload(Event.articles),selectinload(Event.updates)).order_by(Event.source_count.desc(),Event.last_updated_at.desc()).all()
            result = []
            for row in rows:
                article_links = []
                for article in row.articles:
                    if article.link:
                        article_links.append(
                            {
                                "url": article.link,
                                "label": build_link_label(article.link, article.source.name if article.source else None),
                            }
                        )

                # Timeline: a synthesized "created" point (no EventUpdate row exists
                # for creation -- create_event_metadata never inserts one) followed by
                # one entry per EventUpdate round. attached_at is NULL exactly for an
                # event's creation-batch articles (clustering_engine only sets it when
                # matching articles to an ALREADY-open event later), and each
                # EventUpdate.article_ids is the exact set attached that round, so
                # grouping is exact -- no timestamp-fuzzy matching needed. Each article
                # is attached exactly once (clustering only matches unclustered
                # articles), so rounds never overlap.
                creation_articles = [a for a in row.articles if a.attached_at is None]
                articles_by_id = {a.id: a for a in row.articles}
                seen_source_ids = {a.source_id for a in creation_articles}

                timeline = [{
                    "type": "created",
                    "timestamp": row.first_seen_at.isoformat() if row.first_seen_at else None,
                    "delta_text": None,
                    "articles_added": len(creation_articles),
                    "sources_added": len(seen_source_ids),
                    "source_names": sorted({a.source.name for a in creation_articles if a.source}),
                }]

                for u in sorted(row.updates, key=lambda u: u.created_at):
                    round_articles = [articles_by_id[aid] for aid in (u.article_ids or []) if aid in articles_by_id]
                    round_source_ids = {a.source_id for a in round_articles}
                    new_source_ids = round_source_ids - seen_source_ids
                    seen_source_ids |= round_source_ids

                    timeline.append({
                        "type": "update",
                        "timestamp": u.created_at.isoformat() if u.created_at else None,
                        "delta_text": u.delta_text,
                        "articles_added": len(round_articles),
                        "sources_added": len(new_source_ids),
                        "source_names": sorted({a.source.name for a in round_articles if a.source_id in new_source_ids and a.source}),
                    })

                latest_update = timeline[-1]

                result.append(
                    {
                        "id": row.id,
                        "name": row.name,
                        "summary": row.summary,
                        "event_type": row.event_type,
                        "domains": row.domains or [],
                        "entities": row.entities or [],
                        "status": row.status,
                        "article_count": row.article_count,
                        "source_count": row.source_count,
                        "first_seen_at": row.first_seen_at.isoformat() if row.first_seen_at else None,
                        "last_updated_at": row.last_updated_at.isoformat() if row.last_updated_at else None,
                        "delta_text": latest_update["delta_text"],
                        "timeline": timeline,
                        "article_links": article_links,
                    }
                )
            return result
        except Exception:
            logger.exception("Failed to load events.")
            return []

@st.cache_data(ttl=3600,show_spinner="Loading events...")
def get_live_events() -> list[dict]:
    """Open events only, most recently active first -- the working set for Live Monitor."""
    events = [e for e in get_events() if e.get("status") == "open"]
    return sorted(events, key=lambda e: e.get("last_updated_at") or "", reverse=True)

@st.cache_data(ttl=3600,show_spinner="Loading events...")
def get_event_stats_for_date(date_str: str) -> tuple[int | None, int | None]:
    """
    (new_count, developing_count) for the events touched on date_str, using the
    same event set and NEW/DEVELOPING split the daily briefing itself draws
    from (see briefing_generator.build_prompt), so the metric strip always
    agrees with what that edition's briefing text says.
    """
    db_service = get_db_service()
    if not db_service:
        return None, None

    try:
        events = db_service.get_delta_events(date_str)
    except Exception:
        logger.exception("Failed to compute event stats for %s.", date_str)
        return None, None

    new_count = sum(1 for e in events if e["first_seen_at"] == e["last_updated_at"])
    return new_count, len(events) - new_count

@st.cache_data(ttl=86400,show_spinner="Loading sources...")
def get_sources() -> list[dict]:
    """Fetch all sources from the PostgreSQL sources table, ordered by category and name."""
    db_service = get_db_service()
    if not db_service:
        return []

    from storage.db_service import Source

    with db_service._SessionMarker() as session:
        try:
            rows = session.query(Source).order_by(Source.category.asc(), Source.name.asc()).all()
            return [
                {
                    "id": row.id,
                    "name": row.name,
                    "category": row.category,
                    "tier": row.tier,
                    "region": row.region,
                    "source_tags": row.source_tags or [],
                    "url": row.url,
                    "link_label": build_link_label(row.url, row.name),
                }
                for row in rows
            ]
        except Exception:
            logger.exception("Failed to load sources.")
            return []

@st.cache_data(ttl=3600,show_spinner="Loading briefings...")
def get_briefing_files():
    files = cloud.list_files("briefings")
    return sorted(files, reverse=True)


def briefing_loader(key):
    return cloud.get_file_content(key)


def get_briefing_date(key):
    filename = key.split("/")[-1]

    return filename.replace(
        "IB_",
        ""
    ).replace(
        ".md",
        ""
    )

@st.cache_data(ttl=3600,show_spinner="Fetching context...")
def get_markdown_report(date: str) -> str:
    """Fetches the intermediate markdown context for a specific date."""
    try:
        content = cloud.get_file_content(f"markdown/{date}.md")
        return content
    except Exception:
        logger.exception("Failed to fetch markdown for %s.", date)
        return None

@st.cache_data(ttl=3600,show_spinner="Fetching articles...")
def get_raw_articles(date: str) -> list | dict:
    """Fetches and parses the raw JSON articles for a specific date."""
    try:
        content = cloud.get_file_content(f"articles/{date}.json")
        return json.loads(content)
    except Exception:
        logger.exception("Failed to fetch article JSON for %s.", date)
        return None
