# processing/enrichment.py
import asyncio
import aiohttp
import trafilatura
from intelligence.ai_client import async_evaluate_batch

BATCH_SIZE = 10
RATE_LIMIT_DELAY = 4.5 # 60 seconds / 15 requests = 4 seconds. We use 4.5 to be safe.

async def fetch_full_article(session: aiohttp.ClientSession, article: dict) -> dict:
    """Attempt to scrape the full article text. Fall back to RSS summary if it fails."""
    url = article.get("link")
    enriched_article = article.copy()
    
    try:
        async with session.get(url, timeout=8) as response:
            if response.status == 200:
                html = await response.text()
                extracted_text = trafilatura.extract(html)
                
                # Check for paywalls or overly short extractions
                if extracted_text and len(extracted_text.split()) > 200 and "subscribe to read" not in extracted_text.lower():
                    enriched_article['content_to_evaluate'] = extracted_text
                    return enriched_article
    except Exception:
        pass # Silently handle timeouts or connection errors
    
    # Fallback to RSS summary if scraping failed or hit a paywall
    enriched_article['content_to_evaluate'] = article.get("summary", "No content available.")
    return enriched_article

async def process_batch(batch: list[dict], batch_id: int) -> list[dict]:
    """Formats a batch into a prompt, calls the AI, and maps the scores back to the articles."""
    print(f"Processing LLM Batch {batch_id}...")
    
    # 1. Format the text for the LLM
    batch_prompt = ""
    for idx, article in enumerate(batch):
        batch_prompt += f"\n--- Article {idx} ---\n"
        batch_prompt += f"Title: {article.get('title')}\n"
        batch_prompt += f"Content: {article.get('content_to_evaluate')[:3000]}\n" # Cap at 3000 chars to save tokens
        
    # 2. Call Gemini
    evaluation_result = await async_evaluate_batch(batch_prompt)
    
    # 3. Map scores back to the original articles
    if evaluation_result and "evaluations" in evaluation_result:
        for eval_data in evaluation_result["evaluations"]:
            idx = eval_data.get("article_index")
            if 0 <= idx < len(batch):
                batch[idx]['score'] = eval_data.get("total_score", 0)
                batch[idx]['ai_summary'] = eval_data.get("ai_summary", "")
                batch[idx]['justification'] = eval_data.get("justification", "")
                batch[idx]['metrics'] = {
                    "immediacy": eval_data.get("immediacy", 0),
                    "scale": eval_data.get("scale", 0),
                    "permanence": eval_data.get("permanence", 0),
                    "reverberance": eval_data.get("reverberance", 0),
                    "novelty": eval_data.get("novelty", 0),
                }
    return batch

async def enrich_articles_pipeline(articles: list[dict]) -> list[dict]:
    """The main orchestrator function."""
    
    # Step 1: Concurrently scrape all articles using aiohttp
    print(f"Starting concurrent scraping of {len(articles)} articles...")
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_full_article(session, article) for article in articles]
        scraped_articles = await asyncio.gather(*tasks)
        
    # Step 2: Mini-batch the articles and rate-limit the LLM calls
    enriched_articles = []
    
    for i in range(0, len(scraped_articles), BATCH_SIZE):
        batch = scraped_articles[i:i + BATCH_SIZE]
        batch_id = i // BATCH_SIZE + 1
        
        processed_batch = await process_batch(batch, batch_id)
        enriched_articles.extend(processed_batch)
        
        # Rate Limiting: Sleep to avoid hitting the 15 RPM limit
        if i + BATCH_SIZE < len(scraped_articles):
            await asyncio.sleep(RATE_LIMIT_DELAY)
            
    # Step 3: Sort by score descending and filter out low-signal noise
    enriched_articles.sort(key=lambda x: x.get('score', 0), reverse=True)
    return enriched_articles