import logging
from datetime import datetime
import sys
from storage import db_service as db
from storage import storage_utils as storage
from intelligence import briefing_generator
from utils.prompt_loader import load_prompt


logger = logging.getLogger(__name__) 
today = datetime.now().strftime("%Y-%m-%d")

def assemble():
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
 
    logger.info("Assembling briefing prompt.")
    prompt, id_to_url = briefing_generator.build_prompt(
        prompt=load_prompt("daily_briefing.txt"),
        date=today,
        articles=articles,
        events=events,
        briefings=recent_briefings,
    )
    try:
        storage.upload_markdown(today, prompt)
        logger.info("Uploaded briefing prompt.")
    except Exception:
        logger.warning("Failed to archive the briefing prompt.", exc_info=True)

    try:
        storage.upload_id_to_url(today, id_to_url)
        logger.info("Uploaded id_to_url mapping.")
    except Exception:
        logger.warning("Failed to archive the id_to_url mapping.", exc_info=True)