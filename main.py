from config import env_ini, feed_loader # noqa: F401
import asyncio
import sys
import argparse
import ingestion.rss_collector as rss_collector
from processing import formatter, event_enrichment
from processing.enrichment import enrich_articles_pipeline
from intelligence import briefing_generator
from storage import storage_utils as storage
from storage import db_service as db
from datetime import datetime
from processing.clustering_engine import events_clustering


today = datetime.now().strftime("%Y-%m-%d")
neon = db.NeonDatabaseService()


def run_ingestion():
    print("Loading feeds...", flush=True)
    feeds = feed_loader.load_feeds()

    print("Starting article collection...", flush=True)
    cleaned_articles = rss_collector.collect_articles(feeds,200,50)

    print("Storing cleaned articles to neon...", flush=True)
    db.db_save_return(cleaned_articles)
    return cleaned_articles

def run_enrichment(articles):
    print("Enriching and scoring articles (Async Pipeline)...", flush=True)
    enriched_articles = asyncio.run(enrich_articles_pipeline(articles))

    print("Uploading enriched articles...", flush=True)
    storage.save_articles(enriched_articles)
    print("Storing enriched articles to neon...", flush=True)
    db.db_save_return(enriched_articles, stage="silver")

def events_processing():
    print("Resetting events...", flush=True)
    neon.reset_events()

    print("Identifying new events...", flush=True)
    events_clustering(score=50, similarity_threshold=0.45, max_df=0.8, min_df=2)

    print("Enriching events...", flush=True)
    event_enrichment.run_event_enrichment()
    
def format():
    filtered_articles = db.db_save_return(stage="silver")
    print("Formatting articles...", flush=True)
    markdown = formatter.format_context(filtered_articles)
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
        choices=['ingest','ing','enrich','enrichment','events_processing','events','format','fmt','synthesize','syn', 'all'], 
        nargs='?', 
        default='all',
        help="Pipeline stage to execute (default: all)"
    )
    args = parser.parse_args()

    articles = None
    
    if args.stage in ['ingest', 'ing','all']:
        print("Running ingestion stage...", flush=True)
        articles = run_ingestion()
    
    if args.stage in ['enrich', 'enrichment','all']:
        print("Running enrichment stage...", flush=True)
        # Use articles from ingestion if available, otherwise fetch from database
        if articles is None:
            articles = db.db_save_return()
        if articles:
            run_enrichment(articles)
    
    if args.stage in ['events_processing', 'events','all']:
        print("Running events processing stage...", flush=True)
        events_processing()
    
    if args.stage in ['format', 'fmt','all']:
        print("Running format stage...", flush=True)
        format()
    
    if args.stage in ['synthesize', 'syn','all']:
        print("Running synthesis stage...", flush=True)
        run_synthesis()

if __name__ == "__main__":

    
    main()