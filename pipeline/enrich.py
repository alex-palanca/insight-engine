import logging
import asyncio
from storage import db_service as db
from processing.enrichment import enrich_articles_pipeline
from storage import storage_utils as storage

logger = logging.getLogger(__name__) 


def enrich():
    logger.info("Enriching and scoring articles.")
    articles = db.db_save_return()
    enriched_articles = asyncio.run(enrich_articles_pipeline(articles))

    logger.info("Uploading enriched articles.")
    storage.save_articles(enriched_articles)
    logger.info("Saving enriched articles to Neon.")
    db.db_save_return(enriched_articles, stage="silver")
