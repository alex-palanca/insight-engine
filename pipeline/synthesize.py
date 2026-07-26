import logging
from datetime import datetime
from storage import storage_utils as storage
from intelligence import briefing_generator


logger = logging.getLogger(__name__) 
today = datetime.now().strftime("%Y-%m-%d")

def synthesize():
    logger.info("Synthesizing briefing.")

    prompt = storage.obtain_markdown(today)
    id_to_url = storage.download_id_to_url(today)

    briefing = briefing_generator.generate_briefing(prompt, id_to_url, temperature=0.35)

    try:
        storage.upload_briefing(today,briefing)
    except Exception:
        logger.warning("Failed to upload briefing", exc_info=True)