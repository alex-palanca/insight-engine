import logging
from datetime import datetime, timedelta
from sqlalchemy import func
import utils.text_utils as ut
from config.logging_config import setup_logging
from processing.clustering_engine import compute_clusters
from storage.db_service import Article, NeonDatabaseService


setup_logging()
logger = logging.getLogger(__name__)

SCORE = 50
SIMILARITY_THRESHOLD = 0.375
MAX_DF = 0.85
MIN_DF = 2

today = datetime.now().date()
yesterday = today - timedelta(days=1)
db = NeonDatabaseService()

with db._SessionMarker() as session:
    articles = (
        session.query(Article)
        .filter(
            func.date(Article.collected_at) == today,
            Article.score >= SCORE,
        )
        .all()
    )

    corpus = [
        (
            f"{ut.normalize_text(article.title)} "
            f"{ut.normalize_text(article.ai_summary or article.raw_summary)} "
            f"{' '.join(article.article_tags or [])}"
        )
        for article in articles
    ]

    clusters = compute_clusters(
        corpus,
        similarity_threshold=SIMILARITY_THRESHOLD,
        max_df=MAX_DF,
        min_df=MIN_DF,
    )

    clustered = set()

    logger.info("%s", "=" * 80)
    logger.info(
        "Threshold=%s | max_df=%s | min_df=%s",
        SIMILARITY_THRESHOLD,
        MAX_DF,
        MIN_DF,
    )
    logger.info("%s", "=" * 80)

    for event_number, cluster in enumerate(clusters, start=1):
        logger.info("EVENT %s (%s articles)", event_number, len(cluster))
        logger.info("%s", "-" * 60)

        for idx in cluster:
            clustered.add(idx)
            logger.info(" - %s", articles[idx].title)

            if articles[idx].article_tags:
                logger.info("   Tags: %s", ", ".join(articles[idx].article_tags))

    logger.info("%s", "=" * 80)
    logger.info("Articles: %s", len(articles))
    logger.info("Events: %s", len(clusters))
    logger.info("Clustered articles: %s", len(clustered))
    logger.info("Singletons: %s", len(articles) - len(clustered))
    logger.info("%s", "=" * 80)
