import logging
from datetime import datetime,date
from storage import db_service as db
from storage import storage_utils as bucket
from config import feed_loader
from ingestion import rss_collector


logger = logging.getLogger(__name__) 

def ingest(
        upload_date_str: str = "today",
        min_date: datetime | None = None,
        max_date: datetime | None = None
):
    logger.info("Loading feeds.")
    feeds = feed_loader.load_feeds()

    logger.info("Syncing sources from feeds.yaml.")
    db.sync_sources(feeds)

    logger.info("Starting article collection.")
    cleaned_articles = rss_collector.collect_articles(feeds,300,50)

    logger.info("Saving cleaned articles to Neon.")
    db.save_articles(cleaned_articles)
    logger.info("Saving cleaned articles to AWS.")
    bucket.upload_articles(upload_date_str,content=cleaned_articles)


