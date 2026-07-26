import logging
from processing import clustering_engine

logger = logging.getLogger(__name__)

def cluster(score = 30,**hyperparameters):

    logger.info("Phase 1 - Matching unclustered articles against open events.")
    clustering_engine.match_and_attach_articles(score, **hyperparameters)

    logger.info("Phase 2 - Clustering remaining unclustered articles into new events.")
    clustering_engine.events_clustering(score, **hyperparameters)