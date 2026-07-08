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


def fetch_open_events(session: Session):
    """
    Fetches all events that are still open and can receive newly matched articles.
    """
    return session.query(Event).filter(Event.status == "open").all()


def build_event_text(event: Event) -> str:
    """
    Builds a normalized text representation of an event for similarity comparison against articles.
    """
    return (
        f"{ut.normalize_text(event.name)} "
        f"{ut.normalize_text(event.summary or '')} "
        f"{' '.join(event.tags or [])}"
    )


def build_article_text(article: Article) -> str:
    """
    Builds a normalized text representation of an article for clustering/matching.
    """
    return (
        f"{ut.normalize_text(article.title)} "
        f"{ut.normalize_text(article.ai_summary or article.raw_summary)} "
        f"{' '.join(article.article_tags or [])}"
    )


def compute_clusters(
        texts: list[str],
        similarity_threshold: float = 0.375,
        max_df: float = 0.75,
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


def match_articles_to_events(
        event_texts: list[str],
        article_texts: list[str],
        similarity_threshold: float = 0.375,
        max_df: float = 0.75,
        min_df: int = 2,) -> dict[int, list[int]]:
    """
    Compares unclustered article text against open event text using TF-IDF cosine similarity.
    Returns a mapping of event index -> list of article indices whose best-matching event is
    that event, above the similarity threshold.
    """
    if not event_texts or not article_texts:
        return {}

    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_df=max_df,
        min_df=min_df,
        ngram_range=(1, 2),
        sublinear_tf=True
    )

    try:
        tfidf_matrix = vectorizer.fit_transform(event_texts + article_texts)
    except ValueError:
        logger.info("Not enough meaningful text to match articles against open events.")
        return {}

    event_count = len(event_texts)
    sim_matrix = cosine_similarity(tfidf_matrix[event_count:], tfidf_matrix[:event_count])

    matches: dict[int, list[int]] = {}
    for article_idx, similarities in enumerate(sim_matrix):
        best_event_idx = int(similarities.argmax())
        if similarities[best_event_idx] >= similarity_threshold:
            matches.setdefault(best_event_idx, []).append(article_idx)

    return matches


def match_and_attach_articles(score: int, **hyperparameters) -> dict:
    """
    Matches unclustered articles against currently open events and attaches the matched
    articles to their event. Skips entirely if there are no open events.
    Returns a mapping of event_id -> list of newly attached article dicts, for downstream
    AI-driven event updates.
    """
    db_service = NeonDatabaseService()
    touched_events: dict = {}

    with db_service._SessionMarker() as session:
        try:
            open_events = fetch_open_events(session)
            if not open_events:
                logger.info("No open events found. Skipping article-to-event matching.")
                return {}

            articles = fetch_unclustered_articles(session, score)
            if not articles:
                logger.info("No unclustered articles found to match against open events.")
                return {}

            event_texts = [build_event_text(event) for event in open_events]
            article_texts = [build_article_text(article) for article in articles]

            matches = match_articles_to_events(event_texts, article_texts, **hyperparameters)
            now = datetime.now()

            for event_idx, article_indices in matches.items():
                event = open_events[event_idx]
                matched_articles = [articles[idx] for idx in article_indices]

                for article in matched_articles:
                    article.event_id = event.id
                    article.attached_at = now

                event.last_updated_at = now

                touched_events[event.id] = [
                    {
                        "id": article.id,
                        "title": article.title,
                        "link": article.link,
                        "published": article.published.isoformat() if article.published else "Unknown",
                        "source": article.source.name if article.source else "Unknown",
                        "category": article.source.category if article.source else "Unknown",
                        "raw_summary": article.raw_summary,
                        "ai_summary": article.ai_summary,
                        "score": article.score,
                        "article_tags": article.article_tags or [],
                    }
                    for article in matched_articles
                ]

            session.commit()
            logger.info(
                "Matched %s articles to %s open events.",
                sum(len(articles) for articles in touched_events.values()),
                len(touched_events),
            )
            return touched_events

        except Exception as exc:
            session.rollback()
            logger.exception("Article-to-event matching failed. Transaction rolled back.")
            raise exc


def events_clustering(score: int, **hyperparameters):
    """
    Main function to fetch unclustered articles, compute clusters, and create events in the database.
    """
    db_service = NeonDatabaseService()

    with db_service._SessionMarker() as session:
        try:
            articles = fetch_unclustered_articles(session, score)
            corpus = [build_article_text(article) for article in articles]

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
