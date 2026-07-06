import sys
from pathlib import Path
import json
from urllib.parse import urlparse
# Ensure the project root is on sys.path so ui imports work from any cwd.
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
from storage.s3_client import S3Storage as s3


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
    except Exception as exc:
        print(f"Database connection failed: {exc}")
        return None


def get_events() -> list[dict]:
    """Fetch all events from the PostgreSQL events table, including linked article URLs."""
    db_service = get_db_service()
    if not db_service:
        return []

    from storage.db_service import Event

    with db_service._SessionMarker() as session:
        try:
            rows = session.query(Event).order_by(Event.importance.asc(), Event.created_at.desc()).all()
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

                result.append(
                    {
                        "id": row.id,
                        "name": row.name,
                        "summary": row.summary,
                        "tags": row.tags or [],
                        "importance": row.importance,
                        "category": row.category,
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "article_links": article_links,
                    }
                )
            return result
        except Exception as exc:
            print(f"Failed to load events: {exc}")
            return []


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
        except Exception as exc:
            print(f"Failed to load sources: {exc}")
            return []


def get_database_tables() -> dict[str, list[dict]]:
    """Return the current events and sources tables for dashboard display."""
    return {
        "events": get_events(),
        "sources": get_sources(),
    }


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

def get_markdown_report(date: str) -> str:
    """Fetches the intermediate markdown context for a specific date."""
    try:
        content = cloud.get_file_content(f"markdown/{date}.md")
        return content
    except Exception as e:
        print(f"Error fetching markdown for {date}: {e}")
        return None

def get_raw_articles(date: str) -> list | dict:
    """Fetches and parses the raw JSON articles for a specific date."""
    try:
        content = cloud.get_file_content(f"articles/{date}.json")
        return json.loads(content)
    except Exception as e:
        print(f"Error fetching JSON for {date}: {e}")
        return None
