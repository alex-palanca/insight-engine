from datetime import datetime
from sqlalchemy import func
from storage.db_service import NeonDatabaseService, Article
from processing.clustering_engine import compute_clusters
import utils.text_utils as ut

# ==========================================================
# TUNING PARAMETERS
# ==========================================================

SCORE = 60

SIMILARITY_THRESHOLD = 0.42
MAX_DF = 0.85
MIN_DF = 2

# ==========================================================

today = datetime.now().date()

db = NeonDatabaseService()

with db._SessionMarker() as session:

    articles = (
        session.query(Article)
        .filter(
            func.date(Article.collected_at) == today,
            Article.event_id == None,
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

    print("=" * 80)
    print(
        f"Threshold={SIMILARITY_THRESHOLD} | "
        f"max_df={MAX_DF} | "
        f"min_df={MIN_DF}"
    )
    print("=" * 80)

    for event_number, cluster in enumerate(clusters, start=1):

        print(f"\nEVENT {event_number} ({len(cluster)} articles)")
        print("-" * 60)

        for idx in cluster:
            clustered.add(idx)

            print(f"• {articles[idx].title}")

            if articles[idx].article_tags:
                print(f"    Tags: {', '.join(articles[idx].article_tags)}")

    print("\n" + "=" * 80)

    print(f"Articles: {len(articles)}")
    print(f"Events: {len(clusters)}")
    print(f"Clustered articles: {len(clustered)}")
    print(f"Singletons: {len(articles)-len(clustered)}")

    print("=" * 80)