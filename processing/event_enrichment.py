import asyncio
import json
from typing import Optional
import config.env_ini as env
from google import genai
from google.genai import types
from google.genai.errors import APIError
from models.event_metadata import EventMetadata
from storage.db_service import NeonDatabaseService
from pathlib import Path


# Initialize Gemini client
key = env.get_env_var("GOOGLE_API_KEY")
if not key:
    raise ValueError("GOOGLE_API_KEY is not set in environment variables.")

client = genai.Client(api_key=key)

# Fallback models in case of 503 errors
FALLBACK_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-3-flash"
]


def load_event_enrichment_prompt() -> str:
    """
    Loads the event enrichment prompt template from the prompts directory.
    """
    prompt_path = Path(__file__).parent.parent / "prompts" / "event_enrichment.txt"
    with open(prompt_path, 'r') as f:
        return f.read()


def format_articles_context(articles: list) -> str:
    """
    Formats a list of article dictionaries into a readable context string for Gemini.
    """
    if not articles:
        return "No articles found for this event."
    
    context_lines = []
    for i, article in enumerate(articles, 1):
        context_lines.append(f"Article {i}:")
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
        print(f"⚠️  Event {event_id} has no articles. Skipping enrichment.")
        return None
    
    prompt_template = load_event_enrichment_prompt()
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
            
            # Parse the JSON response into EventMetadata
            metadata_dict = json.loads(response.text)
            return EventMetadata(**metadata_dict)
            
        except APIError as api_err:
            if api_err.code == 503:
                print(f"⚠️  Model {model_name} is overloaded (503). Attempting fallback...")
                await asyncio.sleep(0.5)
                continue
        
        except Exception as e:
            print(f"💥 Unexpected error on model {model_name}: {e}")
            return None
    
    print(f"🚨 All fallback models exhausted for event {event_id}. Skipping enrichment.")
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
        
        except Exception as e:
            print(f"Failed to retrieve articles for event {event_id}: {e}")
            return []


def get_all_events(db_service: NeonDatabaseService) -> list:
    """
    Retrieves all events from the database that don't have metadata yet.
    """
    from storage.db_service import Event
    
    with db_service._SessionMarker() as session:
        try:
            # Query events where summary is None (not yet enriched)
            events = session.query(Event).filter(Event.summary == None).all()
            
            event_data = []
            for event in events:
                event_data.append({
                    "id": event.id,
                    "name": event.name,
                    "created_at": event.created_at
                })
            
            return event_data
        
        except Exception as e:
            print(f"Failed to retrieve events: {e}")
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
                print(f"Event {event_id} not found in database.")
                return False
            
            event.name = metadata.title
            event.summary = metadata.summary
            event.tags = metadata.tags
            event.importance = metadata.importance
            event.category = metadata.category
            
            session.commit()
            print(f"✓ Event {event_id} updated with metadata.")
            return True
        
        except Exception as e:
            session.rollback()
            print(f"Failed to update event {event_id}: {e}")
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
    
    print("Fetching unenriched events from database...", flush=True)
    events = get_all_events(db_service)
    
    if not events:
        print("No unenriched events found. Skipping event enrichment.", flush=True)
        return
    
    print(f"Found {len(events)} events to enrich.", flush=True)
    
    for event_data in events:
        event_id = event_data["id"]
        print(f"\nEnriching event {event_id}: '{event_data['name']}'...", flush=True)
        
        # Retrieve all articles for this event
        articles = get_event_articles(db_service, event_id)
        print(f"  Retrieved {len(articles)} articles for this event.", flush=True)
        
        # Send to Gemini for enrichment
        metadata = await enrich_event_with_gemini(event_id, articles)
        
        if metadata:
            # Update the event with enriched metadata
            update_event_metadata(db_service, event_id, metadata)
        else:
            print(f"  Failed to enrich event {event_id}. Skipping update.", flush=True)
    
    print("\nEvent enrichment pipeline complete.", flush=True)


# Public interface function for integration with main pipeline
def run_event_enrichment():
    """
    Wrapper to run the async event enrichment pipeline.
    """
    asyncio.run(enrich_events_pipeline())
