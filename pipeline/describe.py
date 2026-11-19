import asyncio
import logging
import time

from processing.event_enrichment import (
    create_event_metadata,
    describe_event_update,
    enrich_new_event_with_gemini,
    get_event_articles,
    get_new_unprocessed_events,
    update_event_with_gemini,
)
from storage.db_service import get_db_service
from telemetry.recorder import TelemetryRecorder

logger = logging.getLogger(__name__) 


async def _describe_async(
        run_id: str,
        recorder: TelemetryRecorder
):
    """ Describe events in the database using Gemini and update their metadata."""
    run_id = recorder.get_or_create_current_run_id()

    metrics: dict = {"duration_ms": 0}
    started_at = time.perf_counter()

    recorder.start_stage(run_id, "describe")

    try:

        db_service = get_db_service()
        
        logger.info("Phase 1 - Describing change in delta events.")
        delta_events = db_service.fetch_pending_event_updates()
        metrics["delta_events"] = len(delta_events)
        logger.info("Updating %s developing events with newly attached articles.", len(delta_events))
        #"""
        for update_id, payload in delta_events.items():
            event_id      = payload["event_id"]
            event_summary = payload["event_summary"]
            articles      = payload["articles"]

            metadata = await update_event_with_gemini(event_id, event_summary, articles)
            if metadata:
                describe_event_update(db_service, update_id, metadata)
                metrics["updated_delta_events_descriptions"] = metrics.get("updated_delta_events_descriptions", 0) + 1
            else:
                logger.warning("Failed to update event %s. Keeping previous metadata.", event_id)
                metrics["failed_delta_event_updates"] = metrics.get("failed_delta_event_updates", 0) + 1

        logger.info("Phase 2 - Describing new events.")

        events = get_new_unprocessed_events(db_service)
        metrics["new_events"] = len(events)
        if not events:
            logger.info("No new events to enrich.")
            return

        logger.info("Found %s new events to enrich.", len(events))

        for event_data in events:
            event_id = event_data["id"]
            logger.info("Enriching event %s: %s", event_id, event_data["name"])

            articles = get_event_articles(db_service, event_id)
            logger.info("Retrieved %s articles for event %s.", len(articles), event_id)

            metadata = await enrich_new_event_with_gemini(event_id, articles)

            if metadata:
                create_event_metadata(db_service, event_id, metadata)
                metrics["enriched_new_events"] = metrics.get("enriched_new_events", 0) + 1
            else:
                logger.warning("Failed to enrich event %s. Skipping update.", event_id)
                metrics["failed_new_event_enrichments"] = metrics.get("failed_new_event_enrichments", 0) + 1
        #"""
        metrics["duration_ms"] = int((time.perf_counter() - started_at) * 1000)
        recorder.finish_stage(  
            run_id,
                "describe",
                status="success",
                metrics=metrics,
            )

    except Exception as exc:
        metrics["duration_ms"] = int((time.perf_counter() - started_at) * 1000)
        metrics["error_type"] = type(exc).__name__

        recorder.finish_stage(
            run_id,
            "describe",
            status="failed",
            metrics=metrics,
        )
        logger.exception("Describe stage failed.")

def describe(
        run_id: str,
        recorder: TelemetryRecorder
) -> dict:
    """Run event description and enrichment asynchronously."""
    asyncio.run(_describe_async(run_id, recorder))