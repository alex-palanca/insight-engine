# processing/enrichment.py
import asyncio
import logging

import aiohttp
import trafilatura

from config.score_system import BatchEvaluation
from intelligence.ai_client import async_evaluate_batch


BATCH_SIZE = 10
RATE_LIMIT_DELAY = 4.5  # 60 seconds / 15 requests = 4 seconds. We use 4.5 to be safe.
logger = logging.getLogger(__name__)


async def fetch_full_article(session: aiohttp.ClientSession, article: dict) -> dict:
    """Attempt to scrape the full article text. Fall back to RSS summary if it fails."""
    url = article.get("link")
    enriched_article = article.copy()

    try:
        async with session.get(url, timeout=8) as response:
            if response.status == 200:
                html = await response.text()
                extracted_text = trafilatura.extract(html)

                if extracted_text and len(extracted_text.split()) > 200 and "subscribe to read" not in extracted_text.lower():
                    enriched_article["content_to_evaluate"] = extracted_text
                    return enriched_article
    except Exception:
        logger.debug("Failed to scrape full article from %s.", url, exc_info=True)

    enriched_article["content_to_evaluate"] = article.get("summary", "No content available.")
    return enriched_article


async def process_batch(batch: list[dict], batch_id: int) -> list[dict]:
    """Formats a batch into a prompt, calls the AI, and maps the scores back to the articles."""
    logger.info("Processing LLM batch %s.", batch_id)

    for article in batch:
        article.setdefault("score", 0)
        article.setdefault("ai_summary", "")
        article.setdefault("justification", "")
        article.setdefault("metrics", {})

    batch_prompt = ""
    for idx, article in enumerate(batch):
        batch_prompt += f"\n--- Article {idx} ---\n"
        batch_prompt += f"Title: {article.get('title')}\n"
        batch_prompt += f"Content: {article.get('content_to_evaluate')[:3000]}\n"

    evaluation_result = await async_evaluate_batch(batch_prompt)

    if evaluation_result and isinstance(evaluation_result, BatchEvaluation):
        for eval_data in evaluation_result.evaluations:
            idx = eval_data.article_index
            if 0 <= idx < len(batch):
                batch[idx]["score"] = eval_data.total_score
                batch[idx]["ai_summary"] = eval_data.ai_summary
                batch[idx]["justification"] = eval_data.justification
                batch[idx]["metrics"] = {
                    "immediacy": eval_data.immediacy,
                    "scale": eval_data.scale,
                    "permanence": eval_data.permanence,
                    "reverberance": eval_data.reverberance,
                    "novelty": eval_data.novelty
                }
                batch[idx]["article_tags"] = eval_data.tags

    return batch


async def enrich_articles_pipeline(articles: list[dict]) -> list[dict]:
    """The main orchestrator function."""
    logger.info("Starting concurrent scraping for %s articles.", len(articles))
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_full_article(session, article) for article in articles]
        scraped_articles = await asyncio.gather(*tasks)

    enriched_articles = []

    for i in range(0, len(scraped_articles), BATCH_SIZE):
        batch = scraped_articles[i:i + BATCH_SIZE]
        batch_id = i // BATCH_SIZE + 1

        processed_batch = await process_batch(batch, batch_id)
        enriched_articles.extend(processed_batch)

        if i + BATCH_SIZE < len(scraped_articles):
            await asyncio.sleep(RATE_LIMIT_DELAY)

    enriched_articles.sort(key=lambda x: x.get("score", 0), reverse=True)
    return enriched_articles
