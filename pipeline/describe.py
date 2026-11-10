import logging

from processing.event_enrichment import (
    create_event_metadata,
    describe_event_update,
    enrich_new_event_with_gemini,
    get_event_articles,
    get_new_unprocessed_events,
    update_event_with_gemini,
)
from storage.db_service import get_db_service

logger = logging.getLogger(__name__) 


async def describe():
    """ Describe events in the database using Gemini and update their metadata."""
    db_service = get_db_service()
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