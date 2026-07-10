import asyncio
import json
import logging
from typing import Optional

import config.env_ini as env
from google import genai
from google.genai import types
from google.genai.errors import APIError
from pydantic import BaseModel

from models.event_metadata import EventCreate, EventUpdate as EventUpdatePayload, EVENT_CREATE_PROMPT, EVENT_UPDATE_PROMPT
from processing import clustering_engine
from storage.db_service import NeonDatabaseService

RATE_LIMIT_DELAY = 4.5  # 60 seconds / 15 requests = 4 seconds. We use 4.5 to be safe.
logger = logging.getLogger(__name__)

key = env.get_env_var("GOOGLE_API_KEY")
if not key:
    raise ValueError("GOOGLE_API_KEY is not set in environment variables.")

client = genai.Client(api_key=key)

FALLBACK_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-3-flash"
]

def format_articles_context(articles: list) -> str:
    """
    Formats a list of article dictionaries into a readable context string for Gemini.
    """
    if not articles:
        return "No articles found for this event."

    context_lines = []
    for index, article in enumerate(articles, 1):
        context_lines.append(f"Article {index}:")
        context_lines.append(f"  Title: {article.get('title', 'Unknown')}")
        context_lines.append(f"  Source: {article.get('source', 'Unknown')}")
        context_lines.append(f"  Published: {article.get('published', 'Unknown')}")
        context_lines.append(f"  Score: {article.get('score', 'N/A')}")
        context_lines.append(f"  Summary: {article.get('ai_summary', article.get('raw_summary', 'No summary available'))}")
        context_lines.append(f"  Tags: {', '.join(article.get('article_tags', []))}")
        context_lines.append("")

    return "\n".join(context_lines)


async def enrich_new_event_with_gemini(event_id: int, articles: list) -> Optional[EventCreate]:
    """
    Sends a brand-new event's articles to Gemini to generate its canonical representation,
    using new_event.txt.
    """
    if not articles:
        logger.warning("Event %s has no articles. Skipping enrichment.", event_id)
        return None

    contents = f"# Articles\n\n{format_articles_context(articles)}"

    return await _generate_structured_content(event_id, EVENT_CREATE_PROMPT, contents, EventCreate)


async def update_event_with_gemini(event_id: int, existing_summary: str, articles: list) -> Optional[EventUpdatePayload]:
    """
    Sends an open event's existing summary plus newly attached articles to Gemini to determine
    whether the canonical representation needs to change, using update_event.txt.
    """
    if not articles:
        logger.warning("Event %s has no newly attached articles. Skipping update.", event_id)
        return None

    contents = (
        f"# Existing Event Summary\n\n{existing_summary or 'No summary yet.'}\n\n"
        f"# New Articles\n\n{format_articles_context(articles)}"
    )

    return await _generate_structured_content(event_id, EVENT_UPDATE_PROMPT, contents, EventUpdatePayload)


async def _generate_structured_content(event_id: int, system_instruction: str, contents: str, response_schema: type[BaseModel]) -> Optional[BaseModel]:
    """
    Sends a system instruction plus dynamic contents to Gemini and parses the response into the
    given schema. Includes automatic fallback to backup models on 503 errors.
    """
    for model_name in FALLBACK_MODELS:
        try:
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    temperature=0.1
                ),
            )

            result_dict = json.loads(response.text)
            await asyncio.sleep(RATE_LIMIT_DELAY)
            return response_schema(**result_dict)

        except APIError as api_err:
            if api_err.code == 503:
                logger.warning(
                    "Model %s is overloaded (503) while enriching event %s. Trying fallback.",
                    model_name,
                    event_id,
                )

                await asyncio.sleep(RATE_LIMIT_DELAY)
                continue

            logger.error(
                "Google API error on model %s while enriching event %s (%s): %s",
                model_name,
                event_id,
                api_err.code,
                api_err.message,
            )
            return None

        except Exception:
            logger.exception("Unexpected event enrichment failure on model %s for event %s.", model_name, event_id)
            return None

    logger.error("All fallback models were exhausted for event %s. Skipping enrichment.", event_id)
    return None


def get_event_articles(db_service: NeonDatabaseService, event_id: int) -> list:
    """
    Retrieves all articles associated with a specific event from the database.
    """
    from storage.db_service import Article

    with db_service._SessionMarker() as session:
        try:
            articles = session.query(Article).filter(Article.event_id == event_id).all()

            articles_data = []
            for article in articles:
                articles_data.append({
                    "title": article.title,
                    "link": article.link,
                    "published": article.published.isoformat() if article.published else "Unknown",
                    "source": article.source.name if article.source else "Unknown",
                    "category": article.source.category if article.source else "Unknown",
                    "raw_summary": article.raw_summary,
                    "ai_summary": article.ai_summary,
                    "score": article.score,
                    "article_tags": article.article_tags or []
                })

            return articles_data

        except Exception:
            logger.exception("Failed to retrieve articles for event %s.", event_id)
            return []


def get_all_events(db_service: NeonDatabaseService) -> list:
    """
    Retrieves all events from the database that don't have metadata yet.
    """
    from storage.db_service import Event

    with db_service._SessionMarker() as session:
        try:
            events = session.query(Event).filter(Event.summary == None).all()

            event_data = []
            for event in events:
                event_data.append({
                    "id": event.id,
                    "name": event.name,
                    "first_seen_at": event.first_seen_at
                })

            return event_data

        except Exception:
            logger.exception("Failed to retrieve unenriched events.")
            return []


def get_event(db_service: NeonDatabaseService, event_id: int) -> Optional[dict]:
    """
    Retrieves a single event record from the database.
    """
    from storage.db_service import Event

    with db_service._SessionMarker() as session:
        try:
            event = session.query(Event).filter(Event.id == event_id).first()

            if not event:
                return None

            return {
                "id": event.id,
                "name": event.name,
                "summary": event.summary,
            }

        except Exception:
            logger.exception("Failed to retrieve event %s.", event_id)
            return None


def create_event_metadata(db_service: NeonDatabaseService, event_id: int, metadata: EventCreate) -> bool:
    """
    Fills in a brand-new event record with its AI-generated canonical representation.
    """
    from storage.db_service import Event

    with db_service._SessionMarker() as session:
        try:
            event = session.query(Event).filter(Event.id == event_id).first()

            if not event:
                logger.warning("Event %s was not found in the database.", event_id)
                return False

            payload = metadata.model_dump(mode="json")
            event.name = payload["title"]
            event.summary = payload["summary"]
            event.event_type = payload["event_type"]
            event.entities = payload["entities"]
            event.domains = payload["domains"]

            session.commit()
            logger.info("Created metadata for event %s.", event_id)
            return True

        except Exception:
            session.rollback()
            logger.exception("Failed to create metadata for event %s.", event_id)
            return False


def apply_event_update(db_service: NeonDatabaseService, event_id: int, metadata: EventUpdatePayload, article_ids: list) -> bool:
    """
    Applies an AI-judged event update: revises the summary only if the change is material, and
    always records the delta as an append-only EventUpdate log entry.
    """
    from storage.db_service import Event
    from storage.db_service import EventUpdate as EventUpdateRecord

    with db_service._SessionMarker() as session:
        try:
            event = session.query(Event).filter(Event.id == event_id).first()

            if not event:
                logger.warning("Event %s was not found in the database.", event_id)
                return False

            if metadata.material_change:
                event.summary = metadata.revised_summary

            session.add(EventUpdateRecord(
                event_id=event_id,
                update_type="article_match",
                delta_text=metadata.delta_text,
                material_change=metadata.material_change,
                article_ids=article_ids,
            ))

            session.commit()
            logger.info(
                "Recorded event update for %s (material_change=%s).",
                event_id, metadata.material_change,
            )
            return True

        except Exception:
            session.rollback()
            logger.exception("Failed to apply update for event %s.", event_id)
            return False


async def update_open_events_pipeline(score: int = 30, **hyperparameters):
    """
    Phase 1: matches unclustered articles against currently open events (skipped entirely if
    there are none), attaches the matched articles to their event, and asks Gemini whether the
    event's canonical representation needs to change given the new information (update_event.txt).
    """
    db_service = NeonDatabaseService()

    logger.info("Matching unclustered articles against open events.")
    touched_events = clustering_engine.match_and_attach_articles(score, **hyperparameters)

    if not touched_events:
        logger.info("No open events matched new articles. Skipping event updates.")
        return

    logger.info("Updating %s open events with newly attached articles.", len(touched_events))

    for event_id, articles in touched_events.items():
        existing_event = get_event(db_service, event_id)
        if not existing_event:
            logger.warning("Event %s was not found. Skipping update.", event_id)
            continue

        metadata = await update_event_with_gemini(event_id, existing_event["summary"], articles)

        if metadata:
            article_ids = [article["id"] for article in articles]
            apply_event_update(db_service, event_id, metadata, article_ids)
        else:
            logger.warning("Failed to update event %s. Keeping previous metadata.", event_id)


async def create_new_events_pipeline(score: int = 30, **hyperparameters):
    """
    Phase 2: clusters remaining unclustered articles into brand-new events, then fills in each
    new event's canonical representation with Gemini (new_event.txt).
    """
    db_service = NeonDatabaseService()

    logger.info("Clustering remaining unclustered articles into new events.")
    clustering_engine.events_clustering(score, **hyperparameters)

    events = get_all_events(db_service)
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


async def enrich_events_pipeline(score: int = 30, **hyperparameters):
    """
    Main orchestration function, run sequentially:
    1. Match articles to open events and update them (update_event.txt).
    2. Cluster whatever is left into new events and enrich them (new_event.txt).
    """
    logger.info("Phase 1: matching articles to open events.")
    await update_open_events_pipeline(score, **hyperparameters)

    logger.info("Phase 2: clustering remaining articles into new events.")
    await create_new_events_pipeline(score, **hyperparameters)

    logger.info("Event enrichment pipeline complete.")


def run_event_enrichment():
    """
    Wrapper to run the async event enrichment pipeline.
    """
    asyncio.run(enrich_events_pipeline(similarity_threshold=0.375, max_df=0.85, min_df=2))
