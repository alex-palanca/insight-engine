import logging
from datetime import datetime
import asyncio
from storage import db_service as db
from processing.enrichment import enrich_articles_pipeline
import storage.storage_utils as bucket

logger = logging.getLogger(__name__) 


def enrich(
    upload_date_str: str = "today",
):
    logger.info("Enriching and scoring articles.")
    articles = db.get_articles()
    if articles:
        enriched_articles = asyncio.run(enrich_articles_pipeline(articles))

        logger.info("Saving enriched articles to Neon.")
        db.save_articles(enriched_articles, stage="silver")
        logger.info("Saving cleaned articles to AWS.")
        bucket.upload_articles(upload_date_str,content=enriched_articles)
    else:
        logger.info("Enrichment aborted due to lack of articles to process.")
        return

