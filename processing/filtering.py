import asyncio
import logging

from config.score_system import BatchFilterEvaluation
from intelligence.ai_client import async_evaluate_batch

BATCH_SIZE = 10
RATE_LIMIT_DELAY = 4.5  # 60 seconds / 15 requests = 4 seconds. We use 4.5 to be safe.
logger = logging.getLogger(__name__)

async def process_batch(
        batch: list[dict], 
        batch_id: int,
        prompt: str
) -> list[dict]:
    """Formats a batch into a prompt, calls an LLM model, and maps the scores back to the articles."""

    logger.info("Processing LLM batch %s.", batch_id)

    batch_prompt = ""
    for idx, article in enumerate(batch):
        batch_prompt += f"\n--- Article {idx} ---\n"
        batch_prompt += f"Title: {article.get('title')}\n"
        batch_prompt += f"Content: {article.get('summary')[:5000]}\n"

    evaluation_result, model_name, token_usage = await async_evaluate_batch(batch_prompt, prompt, BatchFilterEvaluation)

    logger.info(
        "Filter batch %s completed | model=%s | tokens=%s",
        batch_id,
        model_name,
        token_usage
    )

    if evaluation_result and isinstance(evaluation_result, BatchFilterEvaluation):
        for eval_data in evaluation_result.evaluations:
            idx = eval_data.article_index
            if 0 <= idx < len(batch):
                batch[idx]["decision"] = eval_data.decision
                batch[idx]["reason"] = eval_data.reason

    return batch


async def filter_articles_pipeline(
        articles: list[dict],
        prompt: str
) -> tuple[list[dict], list[dict]]:
    """The main filtering orchestrator function."""

    kept_articles: list[dict] = []
    dropped_articles: list[dict] = []
    
    for i in range(0, len(articles), BATCH_SIZE):
        batch = articles[i:i + BATCH_SIZE]
        batch_id = i // BATCH_SIZE + 1

        processed_batch = await process_batch(batch, batch_id, prompt)
    
        for article in processed_batch:
            if article.get("decision") == "drop":
                dropped_articles.append(article)
            else:
                if article.get("decision") != "keep":
                    logger.warning(
                        "Missing or invalid filter decision for %s; keeping article.",
                        article.get("link") or article.get("title"),
                    )
                    article["decision"] = "keep"
                    article["reason"] = (
                        "Kept because no valid filtering decision was returned."
                    )

                kept_articles.append(article)

        if i + BATCH_SIZE < len(articles):
            await asyncio.sleep(RATE_LIMIT_DELAY)

    logger.info(
        "Filtering complete: %s kept, %s dropped.",
        len(kept_articles),
        len(dropped_articles),
    )

    return kept_articles, dropped_articles