import logging
import time
from datetime import datetime

from config import feed_loader
from ingestion import rss_collector
from storage import db_service as db
from storage import storage_utils as bucket
from telemetry.recorder import TelemetryRecorder

logger = logging.getLogger(__name__) 


def ingest(
        run_id: str,
        recorder: TelemetryRecorder,
        upload_date_str: str = "today",
        min_date: datetime | None = None,
        max_date: datetime | None = None
):
    """Ingest articles from RSS feeds and save to Neon and AWS."""

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

        metrics.update(collector_metrics)

        logger.info("Saving cleaned articles to Neon.")
        db_metrics = db.save_articles(cleaned_articles)
        metrics.update(db_metrics)
        
        logger.info("Saving cleaned articles to AWS.")
        bucket.upload_articles(upload_date_str,content=cleaned_articles)
        
        metrics["duration_ms"] = int((time.perf_counter() - started_at) * 1000)

        recorder.finish_stage(
            run_id,
            stage_name="ingest",
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
            stage_name="ingest",
            status="failed",
            metrics=metrics,
        )

        logger.exception("Ingestion stage failed.")

        raise

