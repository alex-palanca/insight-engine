import json
import logging
from datetime import date

from storage.s3_client import S3Storage


today = date.today()
cloud = S3Storage()
logger = logging.getLogger(__name__)


def upload_articles(date: str, content):
    cloud.upload_content(
        content,
        cloud.article_key(date)
    )


def upload_briefing(date: str, file_input):
    cloud.upload_content(
        file_input,
        cloud.briefing_key(date)
    )


def upload_markdown(date: str, content):
    cloud.upload_content(
        content,
        cloud.markdown_key(date)
    )


def obtain_markdown(date: str):
    markdown = cloud.get_file_content(
        cloud.markdown_key(date)
    )
    return markdown


def download_articles(date: str):
    cloud.download_file(
        f"output/articles/{date}.json",
        cloud.article_key(date)
    )


def download_briefing(date: str):
    cloud.download_file(
        f"output/briefings/IB_{date}.md",
        cloud.briefing_key(date)
    )

def get_recent_briefings(limit: int = 2, before: str | None = None) -> list[str]:
    """
    Fetch the text of the most recent briefings, newest first.

    Lists and sorts existing keys rather than computing calendar dates
    backwards: a failed or skipped run leaves a gap, and date arithmetic
    would fetch a 404 for that day instead of the real previous briefing.
    IB_YYYY-MM-DD.md sorts lexicographically in chronological order, so a
    reverse sort gives newest-first directly.

    Args:
        limit: How many briefings to return.
        before: Optional ISO date. Excludes this date and later. Defaults to
            today, so today's own briefing can never be fed back as "what the
            reader already saw" on a re-run, even if the caller forgets to
            pass it explicitly.

    Returns:
        Briefing markdown, newest first. Missing or unreadable briefings are
        skipped with a warning: partial history weakens repetition checking
        but must never fail the synthesis run.
    """
    try:
        keys = sorted(cloud.list_files("briefings"), reverse=True)
    except Exception:
        logger.warning("Could not list briefings in storage.", exc_info=True)
        return []

    # briefing_key() builds the same 'briefings/IB_<date>.md' shape, so
    # comparing against it keeps the key format in one place.
    cutoff = cloud.briefing_key(before or today.isoformat())
    keys = [k for k in keys if k < cutoff]

    briefings = []
    for key in keys[:limit]:
        try:
            content = cloud.get_file_content(key)
            if content:
                briefings.append(content)
        except Exception:
            logger.warning("Could not read briefing %s; skipping.", key, exc_info=True)

    logger.info("Loaded %d recent briefing(s).", len(briefings))
    return briefings


def save_articles(articles):
    json_articles = json.dumps(articles, indent=2, ensure_ascii=False)

    logger.info("Uploading articles to S3.")
    upload_articles(date.today().isoformat(), json_articles)
