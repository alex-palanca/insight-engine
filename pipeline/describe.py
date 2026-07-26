import logging
import storage.db_service as db
from processing.event_enrichment import describe_event_update, create_event_metadata, enrich_new_event_with_gemini, get_event_articles, get_new_unprocessed_events, update_event_with_gemini

logger = logging.getLogger(__name__) 
db_service = db.NeonDatabaseService()

async def describe():
    logger.info("Phase 1 - Describing change in delta events.")
    delta_events = db_service.fetch_pending_event_updates()
    logger.info("Updating %s developing events with newly attached articles.", len(delta_events))

    for update_id, payload in delta_events.items():
        event_id      = payload["event_id"]
        event_summary = payload["event_summary"]
        articles      = payload["articles"]

        metadata = await update_event_with_gemini(event_id, event_summary, articles)
        if metadata:
            describe_event_update(db_service, update_id, metadata)
        else:
            logger.warning("Failed to update event %s. Keeping previous metadata.", event_id)

    logger.info("Phase 2 - Describing new events.")

    events = get_new_unprocessed_events(db_service)
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
        else:
            logger.warning("Failed to enrich event %s. Skipping update.", event_id)