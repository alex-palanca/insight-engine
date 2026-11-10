import logging

from processing import clustering_engine
from storage.db_service import get_db_service

logger = logging.getLogger(__name__)

def cluster(
        score = 30,
        **hyperparameters
):
    """Cluster articles into events and link them to existing events in the database."""
    db_service = get_db_service()

    logger.info("Phase 1 - Matching unclustered articles against open events.")
    clustering_engine.match_and_attach_articles(score, **hyperparameters)

    logger.info("Intermediate Phase - Updating opened events state")
    db_service.update_stale_events_status()

    logger.info("Phase 2 - Clustering remaining unclustered articles into new events.")
    clustering_engine.events_clustering(score, **hyperparameters)