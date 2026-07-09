import logging
from datetime import datetime, timedelta, time, timezone

import feedparser
from pydantic import ValidationError

from models.article import Article
from utils.text_utils import normalize_text, normalize_url


logger = logging.getLogger(__name__)

now_utc = datetime.now(timezone.utc)
yesterday_utc = now_utc - timedelta(days=1)
threshold_utc = datetime.combine(yesterday_utc.date(), time(15, 0, 0))


def collect_articles(
        feeds: dict,
        max_per_category: int,
        max_per_source: int
) -> list:

    raw_articles = []
    category_counts = {}

    for category, category_feeds in feeds.items():
        category_counts[category] = 0

        if category_counts[category] >= max_per_category:
            continue

        for feed_info in category_feeds:
            if category_counts[category] >= max_per_category:
                break

            try:
                feed_url = feed_info["url"]
                parsed_feed = feedparser.parse(feed_url)

                source_count = 0

                for entry in parsed_feed.entries:
                    if category_counts[category] >= max_per_category:
                        break
                    if feed_info["tier"] != 1:
                        if source_count >= max_per_source:
                            break

                    if not hasattr(entry, "published_parsed") or entry.published_parsed is None:
                        if hasattr(entry, "updated_parsed") and entry.updated_parsed is not None:
                            entry.published_parsed = entry.updated_parsed
                        else:
                            continue

                    entry_utc = datetime(*entry.published_parsed[:6])

                    if entry_utc < threshold_utc:
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

                        category_counts[category] += 1
                        source_count += 1

                    except ValidationError:
                        continue

                logger.info("Collected %s articles from %s.", source_count, feed_info["name"])
            except Exception:
                logger.exception("Failed to collect articles from %s.", feed_url)

    logger.info("Collected %s articles total.", len(raw_articles))
    for category, count in category_counts.items():
        logger.info("Category %s: %s articles.", category, count)

    return raw_articles
