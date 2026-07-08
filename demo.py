# scripts/backfill_tags.py
"""
ONE-OFF, DISPOSABLE SCRIPT -- delete after use.

Generates AI tags for historical articles with fewer than --min-tags tags
(default 3) -- covers both untagged articles and ones with a sparse 1-2
tag set that isn't useful for clustering. Fully self-contained: its own
prompt, schema, Gemini calling logic, and DB queries, so it doesn't
require any changes to storage/db_service.py or any other application file.

The only things reused from the app are the Article ORM model and the
DB engine/connection-pool setup already defined in storage.db_service --
reusing those avoids duplicating the table schema in a second place
(a real correctness risk) and avoids reinventing connection pooling.
Everything else needed for the backfill itself lives in this one file.

Safe to re-run: each run only fetches articles still under the threshold,
so a partial failure just means running it again picks up where it left off.

Usage:
    python -m scripts.backfill_tags
    python -m scripts.backfill_tags --limit 20        # test on a small batch first
    python -m scripts.backfill_tags --min-tags 2       # only reprocess 0-1 tag articles
"""
import argparse
import asyncio
import json

from google import genai
from google.genai import types
from google.genai.errors import APIError
from pydantic import BaseModel, Field
from sqlalchemy.orm import sessionmaker

import config.env_ini as env
from storage.db_service import NeonDatabaseService, Article

# --- Config -----------------------------------------------------------

BATCH_SIZE = 10
RATE_LIMIT_DELAY = 4.5  # matches processing/enrichment.py -- same Gemini free-tier RPM budget

FALLBACK_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-3-flash",
]

TAG_PROMPT = """
You are tagging a batch of news articles for a clustering system. For each
article, extract 3-6 lowercase, underscore-separated tags identifying the
specific named entities, organizations, people, places, or concrete topics
in the article (e.g. "nato", "ukraine", "interest_rates").

Base tags only on the article's own content. Prefer specific named entities
over general terms. Do NOT include: publication section names ("opinion",
"breaking"), author names, promotional terms ("subscribe", "sponsored"), or
broad category words already implied by context ("news", "update",
"technology"). If in doubt, prefer a specific entity over a general term.
"""

# --- Schema -------------------------------------------------------------

class ArticleTags(BaseModel):
    article_index: int = Field(description="Zero-based index of the article in the input batch.")
    tags: list[str] = Field(description="3-6 lowercase, underscore-separated tags.")

class BatchTags(BaseModel):
    evaluations: list[ArticleTags] = Field(description="One tag set per article, in input order.")

# --- DB access, inlined -- no changes to storage/db_service.py needed ---

db_service = NeonDatabaseService()
Session = sessionmaker(bind=db_service.engine)


def get_articles_needing_tags(min_tags: int = 3, limit: int = None) -> list[dict]:
    """
    Fetches articles with fewer than `min_tags` tags -- covers NULL, empty
    list, and lists that are present but too sparse to be useful for
    clustering. Filtered in Python rather than SQL since JSONB array-length
    comparisons are dialect-fiddly and this is a one-off query, not a hot path.
    """
    with Session() as session:
        query = session.query(Article).filter(Article.link.isnot(None))
        if limit:
            query = query.limit(limit * 3)  # over-fetch since we filter in Python next

        candidates = [a for a in query.all() if len(a.article_tags or []) < min_tags]
        if limit:
            candidates = candidates[:limit]

        articles_data = [{
            "link": a.link,
            "title": a.title,
            "content_to_evaluate": a.ai_summary or a.raw_summary or "",
        } for a in candidates]

        print(f"Found {len(articles_data)} articles with fewer than {min_tags} tags.")
        return articles_data


def update_article_tags(tag_updates: list[dict]):
    """Writes backfilled tags to existing articles, keyed by link."""
    if not tag_updates:
        return

    with Session() as session:
        try:
            for item in tag_updates:
                article = session.query(Article).filter_by(link=item["link"]).first()
                if article:
                    article.article_tags = item["article_tags"]
                else:
                    print(f"Warning: Article with link '{item['link']}' not found. Skipping tag update.")

            session.commit()
            print(f"Successfully backfilled tags for {len(tag_updates)} articles.")

        except Exception as e:
            session.rollback()
            print(f"Tag backfill batch failed! Executed full transaction rollback. Error: {e}")
            raise e

# --- Gemini call, with the same fallback pattern as the main pipeline ---

key = env.get_env_var("GOOGLE_API_KEY")
if not key:
    raise ValueError("GOOGLE_API_KEY is not set in the environment variables.")

client = genai.Client(api_key=key)


async def generate_tags_batch(batch_text: str) -> dict | None:
    for model_name in FALLBACK_MODELS:
        try:
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=batch_text,
                config=types.GenerateContentConfig(
                    system_instruction=TAG_PROMPT,
                    response_mime_type="application/json",
                    response_schema=BatchTags,
                    temperature=0.1,
                ),
            )
            return json.loads(response.text)

        except APIError as api_err:
            if api_err.code == 503:
                print(f"⚠️ Model {model_name} is overloaded (503). Attempting fallback...")
                await asyncio.sleep(0.5)
                continue
            else:
                print(f"❌ Critical Google API Error ({api_err.code}): {api_err.message}")
                break

        except Exception as e:
            print(f"💥 Unexpected system failure on model {model_name}: {e}")
            break

    print("🚨 All fallback models exhausted. Batch skipped -- will retry on next run.")
    return None


async def process_batch(batch: list[dict], batch_id: int) -> list[dict]:
    print(f"Tagging batch {batch_id} ({len(batch)} articles)...")

    batch_prompt = ""
    for idx, article in enumerate(batch):
        batch_prompt += f"\n--- Article {idx} ---\n"
        batch_prompt += f"Title: {article.get('title')}\n"
        batch_prompt += f"Content: {article.get('content_to_evaluate')[:3000]}\n"

    result = await generate_tags_batch(batch_prompt)

    updates = []
    if result and "evaluations" in result:
        for eval_data in result["evaluations"]:
            idx = eval_data.get("article_index")
            if idx is not None and 0 <= idx < len(batch):
                raw_tags = eval_data.get("tags", [])
                normalized = [t.lower().strip().replace(" ", "_") for t in raw_tags if t]
                updates.append({"link": batch[idx]["link"], "article_tags": normalized})
            else:
                print(f"  Warning: batch {batch_id} returned an out-of-range article_index, skipping one entry.")

    return updates

# --- Orchestration --------------------------------------------------------

async def run(min_tags: int = 3, limit: int = None):
    articles = get_articles_needing_tags(min_tags=min_tags, limit=limit)

    if not articles:
        print(f"No articles with fewer than {min_tags} tags. Nothing to do.")
        return

    total_updated = 0
    for i in range(0, len(articles), BATCH_SIZE):
        batch = articles[i:i + BATCH_SIZE]
        batch_id = i // BATCH_SIZE + 1

        updates = await process_batch(batch, batch_id)
        if updates:
            update_article_tags(updates)
            total_updated += len(updates)
            print(f"  Committed {len(updates)} tag updates from batch {batch_id}.")

        if i + BATCH_SIZE < len(articles):
            await asyncio.sleep(RATE_LIMIT_DELAY)

    print(f"Done. Backfilled tags for {total_updated}/{len(articles)} articles this run.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill AI-generated tags for under-tagged articles.")
    parser.add_argument("--limit", type=int, default=None, help="Cap the number of articles processed this run.")
    parser.add_argument("--min-tags", type=int, default=3, help="Reprocess any article with fewer than this many tags (default: 3).")
    args = parser.parse_args()

    asyncio.run(run(min_tags=args.min_tags, limit=args.limit))