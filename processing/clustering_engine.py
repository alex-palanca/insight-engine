import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from datetime import datetime
from storage.db_service import Article, Event
import utils.text_utils as ut
from storage.db_service import NeonDatabaseService

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
        similarity_threshold: float = 0.40,
        max_df: float = 0.85,
        min_df: int = 2,) -> list[list[int]]:
    """
    Takes a flat list of strings (articles) and returns a list of clusters.
    Uses TF-IDF vectorization and cosine similarity to determine which articles are related enough to be grouped together.
    """
    
    if not texts:
        print("No content to cluster.")
        return []

    print(f"Clustering {len(texts)} entities...")



    # Vectorization: Convert text to TF-IDF matrix
    vectorizer = TfidfVectorizer(stop_words='english', 
        max_df=max_df, 
        min_df=min_df, 
        ngram_range=(1, 2),
        sublinear_tf=True
    )  
    
    try:
        tfidf_matrix = vectorizer.fit_transform(texts)
    except ValueError:
        # Happens if vocabulary is empty (e.g., all stop words or too few articles)
        print("Not enough meaningful text to cluster.")
        return []

    # Cosine Similarity Matrix: Returns an NxN matrix where matrix[i][j] is the similarity between article i and j
    sim_matrix = cosine_similarity(tfidf_matrix)

    # Graph Clustering: Build a graph where edges represent high similarity
    graph = nx.Graph()
    
    # Add all text entities as nodes
    for i in range(len(texts)):
        graph.add_node(i)
        
    # Draw edges between articles if similarity exceeds our threshold
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            if sim_matrix[i][j] >= similarity_threshold:
                graph.add_edge(i, j, weight=sim_matrix[i][j])

    # Extract Events (Connected Components)
    clusters = list(nx.connected_components(graph))
    return [list(cluster) for cluster in clusters if len(cluster) > 1]  # Only return clusters with more than one article
    
def events_clustering(score: int, **hyperparameters):
    """
    Main function to fetch unclustered articles, compute clusters, and create events in the database.
    """
    db_service = NeonDatabaseService()

    with db_service._SessionMarker() as session:
        try:

            # 1. Fetch unclustered articles
            articles = fetch_unclustered_articles(session, score)

            # 2. Extract texts and preserve structural mapping
            corpus = [f"{ut.normalize_text(article.title)} {ut.normalize_text(article.ai_summary or article.raw_summary)} {article.article_tags}" for article in articles]
            
            # 3. Call the pure math function
            clusters = compute_clusters(corpus, **hyperparameters)

            events_created = 0
            
            for cluster in clusters:
                # We only create an "Event" if 2 or more articles are talking about it.
                # Single articles remain unclustered
                if len(cluster) > 1:
                    # Create a new Event record
                    new_event = Event(
                        name="Pending AI Title and Summary", # The LLM will generate this later
                        created_at=datetime.now()
                    )
                    session.add(new_event)
                    session.flush() # Flushes to DB to get the new_event.id
                    
                    # Link the grouped articles to this new event
                    for idx in cluster:
                        articles[idx].event_id = new_event.id
                        
                    events_created += 1

            # 7. Commit transaction
            session.commit()
            print(f"Successfully created {events_created} events from {len(articles)} articles.")

        except Exception as e:
            session.rollback()
            print(f"Clustering coordination transaction failed! Rollback triggered: {e}")
            raise e