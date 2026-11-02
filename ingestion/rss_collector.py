import logging
from datetime import UTC, datetime, time, timedelta

import feedparser
from pydantic import ValidationError

from models.article import Article
from utils.text_utils import normalize_text, normalize_url

logger = logging.getLogger(__name__)

now_utc = datetime.now(UTC)
yesterday_utc = now_utc - timedelta(days=1)
threshold_utc = datetime.combine(yesterday_utc.date(), time(15, 0, 0), tzinfo=UTC)

metrics = {
    "feeds_attempted": 0,
    "feeds_succeeded": 0,
    "feeds_failed": 0,
    "entries_seen": 0,
    "entries_missing_date": 0,
    "entries_outside_window": 0,
    "articles_validation_rejected": 0,
    "articles_collected": 0,
    "category_cap_hits": 0,
    "source_cap_hits": 0,
}


def collect_articles(
        feeds: dict,
        max_per_category: int,
        max_per_source: int,
        min_date: datetime = threshold_utc,
        max_date: datetime = now_utc
) -> tuple[list[dict], dict]:
    """Collect articles from RSS feeds, filter by date, and return a list of cleaned articles and metrics."""

    raw_articles = []
    category_counts = {}

    for category, category_feeds in feeds.items():
        category_counts[category] = 0

        if category_counts[category] >= max_per_category:
            metrics["category_cap_hits"] += 1
            continue

        for feed_info in category_feeds:
            if category_counts[category] >= max_per_category:
                metrics["category_cap_hits"] += 1
                break

            try:
                feed_url = feed_info["url"]
                parsed_feed = feedparser.parse(feed_url)

                source_count = 0

                for entry in parsed_feed.entries:
                    metrics["entries_seen"] += 1
                    if category_counts[category] >= max_per_category:
                        metrics["category_cap_hits"] += 1
                        break
                    if feed_info["tier"] != 1:  # noqa: SIM102
                        if source_count >= max_per_source:
                            metrics["source_cap_hits"] += 1
                            break

                    if not hasattr(entry, "published_parsed") or entry.published_parsed is None:
                        if hasattr(entry, "updated_parsed") and entry.updated_parsed is not None:
                            entry.published_parsed = entry.updated_parsed
                        else:
                            metrics["entries_missing_date"] += 1
                            continue

                    entry_utc = datetime(*entry.published_parsed[:6], tzinfo=UTC)

                    if entry_utc < min_date or entry_utc > max_date:
                        metrics["entries_outside_window"] += 1
                        continue

                    article_date = entry_utc.date()
                    yaml_tags = feed_info.get("source_tags", [])

                    native_tags = []
                    if hasattr(entry, "tags"):
                        for tag in entry.tags:
                            if hasattr(tag, "term"):
                                clean_tag = tag.term.lower().replace(" ", "_")
                                native_tags.append(clean_tag)

                    native_tags = list(set(native_tags))

                    try:
                        article = Article(
                            title=normalize_text(entry.get("title", "No Title")),
                            link=normalize_url(entry.get("link", "http://invalid")),
                            published=article_date,
                            source=feed_info["name"],
                            category=category,
                            source_tags=yaml_tags,
                            article_tags=native_tags,
                            summary=entry.get("summary", ""),
                            source_url=feed_info.get("url", "")
                        )

                        raw_articles.append(article.model_dump(mode="json"))
                        metrics["articles_collected"] += 1

                        category_counts[category] += 1
                        source_count += 1

                    except ValidationError:
                        metrics["articles_validation_rejected"] += 1
                        continue

                metrics["feeds_succeeded"] += 1
                logger.info("Collected %s articles from %s.", source_count, feed_info["name"])     

            except Exception:
                metrics["feeds_failed"] += 1
                logger.exception("Failed to collect articles from %s.", feed_url)

    logger.info("Collected %s articles total.", len(raw_articles))
    for category, count in category_counts.items():
        logger.info("Category %s: %s articles.", category, count)

    return raw_articles, metrics
