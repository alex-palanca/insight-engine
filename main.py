from config import env_ini, feed_loader # noqa: F401
import asyncio
import logging
import sys
import argparse
import ingestion.rss_collector as rss_collector
from processing import formatter, event_enrichment
from processing.enrichment import enrich_articles_pipeline
from intelligence import briefing_generator
from storage import storage_utils as storage
from storage import db_service as db
from datetime import datetime
from config.logging_config import setup_logging


today = datetime.now().strftime("%Y-%m-%d")
logger = logging.getLogger("isolate_pipeline")


def run_ingestion():
    logger.info("Loading feeds.")
    feeds = feed_loader.load_feeds()

    logger.info("Syncing sources from feeds.yaml.")
    db.sync_sources(feeds)

    logger.info("Starting article collection.")
    cleaned_articles = rss_collector.collect_articles(feeds,300,50)

    logger.info("Saving cleaned articles to Neon.")
    db.db_save_return(cleaned_articles)
    return cleaned_articles

def run_enrichment(articles):
    logger.info("Enriching and scoring articles.")
    enriched_articles = asyncio.run(enrich_articles_pipeline(articles))

    logger.info("Uploading enriched articles.")
    storage.save_articles(enriched_articles)
    logger.info("Saving enriched articles to Neon.")
    db.db_save_return(enriched_articles, stage="silver")

def events_processing():
    logger.info("Enriching events.")
    event_enrichment.run_event_enrichment()
    
def format():
    filtered_articles = db.db_save_return(stage="silver")
    logger.info("Formatting articles.")
    markdown = formatter.format_context(filtered_articles)
    logger.info("Uploading formatted document.")
    storage.upload_markdown(today,markdown)

    logger.info("Formatting stage complete.")

def run_synthesis():
    """
    Synthesizes the daily intelligence briefing from today's events and articles.
 
    Deliberately does NOT catch BriefingGenerationError: if synthesis fails on
    every model, this function must raise so the process exits non-zero and the
    scheduled workflow reports failure. Publishing an error notice as if it were
    a briefing would leave the pipeline silently broken for as long as nobody
    checks S3 by hand.
    """
    logger.info("Fetching today's events and articles.")
 
    db_service = db.NeonDatabaseService()
    events = db_service.get_delta_events(today)
 
    articles = db_service.get_articles_briefing(
        date=today,
        min_score=50,
    )
 
    if not articles and not events:
        logger.error("No articles or events available for %s. Nothing to synthesize.", today)
        sys.exit(1)
 
    logger.info("Assembled %d articles and %d events for synthesis.", len(articles), len(events))
 
    try:
        recent_briefings = storage.get_recent_briefings(limit=2)
        logger.info("Loaded %d recent briefing(s) for repetition checking.", len(recent_briefings))
    except Exception:
        logger.warning(
            "Could not load recent briefings; proceeding without repetition checking.",
            exc_info=True,
        )
        recent_briefings = []
 
    logger.info("Generating intelligence briefing.")
    briefing, prompt = briefing_generator.create_intelligence_briefing(
        date=today,
        articles=articles,
        events=events,
        briefings=recent_briefings,
    )
 
    try:
        storage.upload_markdown(today, prompt)
    except Exception:
        logger.warning("Failed to archive the briefing prompt.", exc_info=True)
 
    logger.info("Uploading intelligence briefing.")
    storage.upload_briefing(today, briefing)
    logger.info("Synthesis complete.")


def main():
    setup_logging()
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
        logger.info("Running ingestion stage.")
        articles = run_ingestion()
    
    if args.stage in ['enrich', 'enrichment','all']:
        logger.info("Running enrichment stage.")
        # Use articles from ingestion if available, otherwise fetch from database
        if articles is None:
            articles = db.db_save_return()
        if articles:
            run_enrichment(articles)
    
    if args.stage in ['events_processing', 'events','all']:
        logger.info("Running events processing stage.")
        events_processing()
    
    if args.stage in ['format', 'fmt','all']:
        logger.info("Running format stage.")
        format()
    
    if args.stage in ['synthesize', 'syn','all']:
        logger.info("Running synthesis stage.")
        run_synthesis()

if __name__ == "__main__":

    
    main()
