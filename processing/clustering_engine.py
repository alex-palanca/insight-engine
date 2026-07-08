import logging
from datetime import datetime

import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

import utils.text_utils as ut
from storage.db_service import Article, Event, NeonDatabaseService


logger = logging.getLogger(__name__)


def fetch_unclustered_articles(session: Session, score: int):
    """
    Fetches articles that haven't been assigned to an event yet and have a score above the given threshold.
    """
    return session.query(Article).filter(
        Article.event_id == None,
        Article.score >= score
    ).all()


def compute_clusters(
        texts: list[str],
        similarity_threshold: float = 0.35,
        max_df: float = 0.85,
        min_df: int = 2,) -> list[list[int]]:
    """
    Takes a flat list of strings (articles) and returns a list of clusters.
    Uses TF-IDF vectorization and cosine similarity to determine which articles are related enough to be grouped together.
    """

    if not texts:
        logger.info("No content to cluster.")
        return []

    logger.info("Clustering %s entities.", len(texts))

    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_df=max_df,
        min_df=min_df,
        ngram_range=(1, 2),
        sublinear_tf=True
    )

    try:
        tfidf_matrix = vectorizer.fit_transform(texts)
    except ValueError:
        logger.info("Not enough meaningful text to cluster.")
        return []

    sim_matrix = cosine_similarity(tfidf_matrix)
    graph = nx.Graph()

    for index in range(len(texts)):
        graph.add_node(index)

    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            if sim_matrix[i][j] >= similarity_threshold:
                graph.add_edge(i, j, weight=sim_matrix[i][j])

    clusters = list(nx.algorithms.community.louvain_communities(graph, weight='weight', seed=42))
    return [list(cluster) for cluster in clusters if len(cluster) > 1]


def events_clustering(score: int, **hyperparameters):
    """
    Main function to fetch unclustered articles, compute clusters, and create events in the database.
    """
    db_service = NeonDatabaseService()

    with db_service._SessionMarker() as session:
        try:
            articles = fetch_unclustered_articles(session, score)
            corpus = [
                (
                    f"{ut.normalize_text(article.title)} "
                    f"{ut.normalize_text(article.ai_summary or article.raw_summary)} "
                    f"{' '.join(article.article_tags or [])}"
                )
                for article in articles
            ]

            clusters = compute_clusters(corpus, **hyperparameters)
            events_created = 0

            for cluster in clusters:
                if len(cluster) > 1:
                    new_event = Event(
                        name="Pending AI Title and Summary",
                        created_at=datetime.now()
                    )
                    session.add(new_event)
                    session.flush()

                    for idx in cluster:
                        articles[idx].event_id = new_event.id

                    events_created += 1

            session.commit()
            logger.info("Created %s events from %s articles.", events_created, len(articles))

        except Exception as exc:
            session.rollback()
            logger.exception("Clustering coordination failed. Transaction rolled back.")
            raise exc
