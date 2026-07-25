import logging
from config import feed_loader
import ingestion.rss_collector as rss_collector
from storage import db_service as db


logger = logging.getLogger(__name__) 

def ingest():
    logger.info("Loading feeds.")
    feeds = feed_loader.load_feeds()

    logger.info("Syncing sources from feeds.yaml.")
    db.sync_sources(feeds)

    logger.info("Starting article collection.")
    cleaned_articles = rss_collector.collect_articles(feeds,300,50)

    logger.info("Saving cleaned articles to Neon.")
    db.db_save_return(cleaned_articles)