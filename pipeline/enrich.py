import asyncio
import logging
import time

import storage.storage_utils as bucket
from processing.enrichment import enrich_articles_pipeline
from storage import db_service as db
from telemetry.recorder import TelemetryRecorder

logger = logging.getLogger(__name__) 

recorder = TelemetryRecorder()

def enrich(
    upload_date_str: str = "today",
):
    """Enrich articles from the database and save to Neon and AWS."""
    run_id = recorder.get_or_create_current_run_id()

    metrics: dict = {"duration_ms": 0}
    started_at = time.perf_counter()

    recorder.start_stage(run_id, "enrich")
    
    try:
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
        
    except Exception as exc:
        metrics["duration_ms"] = int(
            (time.perf_counter() - started_at) * 1000
        )
        metrics["error_type"] = type(exc).__name__

        recorder.finish_stage(
            run_id,
            "enrich",
            status="failed",
            metrics=metrics,
        )
        logger.exception("Enrichment stage failed.")
        raise

