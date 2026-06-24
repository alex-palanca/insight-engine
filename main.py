import os
from dotenv import load_dotenv
load_dotenv()

import asyncio
import ingestion.rss_collector as rss_collector
from processing import formatter
from processing.enrichment import enrich_articles_pipeline
from intelligence import briefing_generator
from storage import storage_utils as storage
import config
from datetime import datetime


today = datetime.now().strftime(
        "%Y-%m-%d"
    )

def main():
    feeds = config.feed_loader.load_feeds()

    print("Starting article collection...")
    cleaned_articles = rss_collector.collect_articles(feeds,200,50)

    print("Enriching and scoring articles (Async Pipeline)...")
    enriched_articles = asyncio.run(enrich_articles_pipeline(cleaned_articles))

    storage.save_articles(enriched_articles)
    
    print("Formatting articles...")
    markdown = formatter.format_context(enriched_articles)

    print("Generating IB report...")
    briefing = briefing_generator.create_intelligence_briefing(markdown)
    print("Saving Intelligence Briefing...")
    storage.upload_briefing(today,briefing)

    print("Finished successfully.")

if __name__ == "__main__":

    main()