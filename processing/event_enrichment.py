import asyncio
import json
import logging
from typing import Optional

from utils import prompt_loader
import config.env_ini as env
from google import genai
from google.genai import types
from google.genai.errors import APIError

from models.event_metadata import EventMetadata
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


async def enrich_event_with_gemini(event_id: int, articles: list) -> Optional[EventMetadata]:
    """
    Sends event articles to Gemini for analysis and returns EventMetadata.
    Includes automatic fallback to backup models on 503 errors.
    """
    if not articles:
        logger.warning("Event %s has no articles. Skipping enrichment.", event_id)
        return None

    prompt_template = prompt_loader.load_prompt("event_enrichment.txt")
    articles_context = format_articles_context(articles)
    full_prompt = prompt_template.replace("{articles_context}", articles_context)

    for model_name in FALLBACK_MODELS:
        try:
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=EventMetadata,
                    temperature=0.1
                ),
            )

            metadata_dict = json.loads(response.text)
            await asyncio.sleep(RATE_LIMIT_DELAY)
            return EventMetadata(**metadata_dict)

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
                    "created_at": event.created_at
                })

            return event_data

        except Exception:
            logger.exception("Failed to retrieve unenriched events.")
            return []


def update_event_metadata(db_service: NeonDatabaseService, event_id: int, metadata: EventMetadata) -> bool:
    """
    Updates an event record with enriched metadata from Gemini.
    """
    from storage.db_service import Event

    with db_service._SessionMarker() as session:
        try:
            event = session.query(Event).filter(Event.id == event_id).first()

            if not event:
                logger.warning("Event %s was not found in the database.", event_id)
                return False

            event.name = metadata.title
            event.summary = metadata.summary
            event.tags = metadata.tags
            event.importance = metadata.importance
            event.category = metadata.category

            session.commit()
            logger.info("Updated event %s with generated metadata.", event_id)
            return True

        except Exception:
            session.rollback()
            logger.exception("Failed to update event %s.", event_id)
            return False


async def enrich_events_pipeline():
    """
    Main orchestration function that:
    1. Fetches all unenriched events
    2. For each event, retrieves its articles
    3. Sends articles to Gemini for analysis
    4. Updates the event with enriched metadata
    """
    db_service = NeonDatabaseService()

    logger.info("Fetching unenriched events from the database.")
    events = get_all_events(db_service)

    if not events:
        logger.info("No unenriched events found. Skipping event enrichment.")
        return

    logger.info("Found %s events to enrich.", len(events))

    for event_data in events:
        event_id = event_data["id"]
        logger.info("Enriching event %s: %s", event_id, event_data["name"])

        articles = get_event_articles(db_service, event_id)
        logger.info("Retrieved %s articles for event %s.", len(articles), event_id)

        metadata = await enrich_event_with_gemini(event_id, articles)

        if metadata:
            update_event_metadata(db_service, event_id, metadata)
        else:
            logger.warning("Failed to enrich event %s. Skipping update.", event_id)

    logger.info("Event enrichment pipeline complete.")


def run_event_enrichment():
    """
    Wrapper to run the async event enrichment pipeline.
    """
    asyncio.run(enrich_events_pipeline())
