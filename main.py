from config import env_ini, feed_loader # noqa: F401
import asyncio
import sys
import argparse
import ingestion.rss_collector as rss_collector
from processing import formatter
from processing.enrichment import enrich_articles_pipeline
from intelligence import briefing_generator
from storage import storage_utils as storage
from datetime import datetime


today = datetime.now().strftime("%Y-%m-%d")

def run_ingestion():
    print("Loading feeds...", flush=True)
    feeds = feed_loader.load_feeds()

    print("Starting article collection...", flush=True)
    cleaned_articles = rss_collector.collect_articles(feeds,200,50)

    print("Enriching and scoring articles (Async Pipeline)...", flush=True)
    enriched_articles = asyncio.run(enrich_articles_pipeline(cleaned_articles))
    print("Uploading enriched articles...", flush=True)
    storage.save_articles(enriched_articles)
    
    print("Formatting articles...", flush=True)
    markdown = formatter.format_context(enriched_articles)
    print("Uploading formatted document...", flush=True)
    storage.upload_markdown(today,markdown)

    print("Ingestion complete.", flush=True)

def run_synthesis():
    try:
        print("Obtaining markdown report...", flush=True)
        markdown = storage.obtain_markdown(today)
    except FileNotFoundError:
        print("Error: Could not find the formatted for today", flush=True)
        print("Did you run the ingestion stage first?")
        sys.exit(1)
        
    if markdown:
        print("Generating Intelligence Briefing...", flush=True)
        briefing = briefing_generator.create_intelligence_briefing(markdown)
        print(briefing)
        print("Uploading Intelligence briefing...", flush=True)
        storage.upload_briefing(today,briefing)
        print("Synthesis complete.", flush=True)
    else:
        print("Error: Could not obtain the formatted articles", flush=True)


def main():
    parser = argparse.ArgumentParser(description="ISOLATE Intelligence Pipeline")
    parser.add_argument(
        'stage', 
        choices=['ingest','ing','synthesize','syn', 'all'], 
        nargs='?', 
        default='all',
        help="Pipeline stage to execute (default: all)"
    )
    args = parser.parse_args()

    if args.stage in ['ingest', 'ing','all']:
        print("Running ingestion stage...", flush=True)
        run_ingestion()
    
    if args.stage in ['synthesize', 'syn','all']:
        print("Running synthesis stage...", flush=True)
        run_synthesis()

if __name__ == "__main__":

    main()