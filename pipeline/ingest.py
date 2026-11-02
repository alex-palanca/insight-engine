import logging
from datetime import datetime, time

from config import feed_loader
from ingestion import rss_collector
from storage import db_service as db
from storage import storage_utils as bucket
from telemetry.recorder import TelemetryRecorder

logger = logging.getLogger(__name__) 

recorder = TelemetryRecorder()

def ingest(
        upload_date_str: str = "today",
        min_date: datetime | None = None,
        max_date: datetime | None = None
):
    """Ingest articles from RSS feeds and save to Neon and AWS."""
    run_id = recorder.get_or_create_current_run_id()

    metrics: dict = {"duration_ms": 0}
    started_at = time.perf_counter()

    recorder.start_stage(run_id, "ingest")

    try:
        logger.info("Loading feeds.")
        feeds = feed_loader.load_feeds()

        logger.info("Syncing sources from feeds.yaml.")
        db.sync_sources(feeds)

        logger.info("Starting article collection.")
        if min_date and max_date:
            cleaned_articles, collector_metrics = rss_collector.collect_articles(feeds,300,50,min_date,max_date)
        else:
            cleaned_articles, collector_metrics = rss_collector.collect_articles(feeds,300,50)

        logger.info("Saving cleaned articles to Neon.")
        db_metrics = db.save_articles(cleaned_articles)

        logger.info("Saving cleaned articles to AWS.")
        bucket.upload_articles(upload_date_str,content=cleaned_articles)

        metrics.update(collector_metrics)
        metrics.update(db_metrics)
        metrics["duration_ms"] = int((time.perf_counter() - started_at) * 1000)

        recorder.finish_stage(
            run_id,
            "ingest",
            status="success",
            metrics=metrics,
        )

        logger.info("Ingestion stage completed. Metrics: %s", metrics)    
    
    except Exception as exc:
        metrics["duration_ms"] = int(
            (time.perf_counter() - started_at) * 1000
        )
        metrics["error_type"] = type(exc).__name__

        recorder.finish_stage(
            run_id,
            "ingest",
            status="failed",
            metrics=metrics,
        )

        logger.exception("Ingestion stage failed.")

        raise

