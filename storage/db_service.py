import logging
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, create_engine, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from config import env_ini as env
from utils.hashing import generate_article_id
from utils.text_utils import normalize_text, normalize_url


logger = logging.getLogger(__name__)

Base = declarative_base()


class Source(Base):
    """
    Represents the publisher of feeds (e.g., MIT Technology Review, TechCrunch).
    Normalized out of the articles table to maintain data integrity and efficiency.
    """
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    category = Column(String, nullable=False)
    tier = Column(String, nullable=True)
    region = Column(String, nullable=True)
    source_tags = Column(JSONB, nullable=True)
    url = Column(String, nullable=False)

    articles = relationship("Article", back_populates="source", cascade="all, delete-orphan")


class Event(Base):
    """
    Groups related articles into a unified historical cluster.
    """
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    summary = Column(Text, nullable=True)

    status = Column(String, nullable=False, default="open", index=True)
    merged_into_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    event_type = Column(String, nullable=True)
    entities = Column(JSONB, nullable=True)
    domains = Column(JSONB, nullable=True)
    first_seen_at = Column(DateTime, nullable=False, default=datetime.now)
    last_updated_at = Column(DateTime, nullable=False, default=datetime.now, index=True)
    closed_at = Column(DateTime, nullable=True)
    article_count = Column(Integer, nullable=False, default=1)
    source_count = Column(Integer, nullable=False, default=1)

    articles = relationship("Article", back_populates="event")
    updates = relationship("EventUpdate", back_populates="event", cascade="all, delete-orphan")
    merged_into = relationship("Event", remote_side=[id])


class EventUpdate(Base):
    """
    Append-only delta log recording the history of changes to an Event.
    """
    __tablename__ = "event_updates"

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    update_type = Column(String, nullable=False)
    delta_text = Column(Text, nullable=True)
    material_change = Column(Boolean, nullable=False, default=False)
    article_ids = Column(JSONB, nullable=True)

    event = relationship("Event", back_populates="updates")


class Article(Base):
    """
    Represents an individual collected piece of intelligence.
    Enforces uniqueness at the database engine layer via the 'link' URL column.
    """
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    content_id = Column(PG_UUID(as_uuid=True), unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    link = Column(String, unique=True, nullable=False)
    published = Column(DateTime, nullable=True)

    article_tags = Column(JSONB, nullable=True)
    raw_summary = Column(Text, nullable=True)
    collected_at = Column(DateTime, nullable=False)

    ai_summary = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)
    metrics = Column(JSONB, nullable=True)
    justification = Column(Text, nullable=True)
    article_read = Column(Boolean, default=False)
    enriched_at = Column(DateTime, nullable=True)

    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    source = relationship("Source", back_populates="articles")

    event_id = Column(Integer, ForeignKey("events.id", ondelete="SET NULL"), nullable=True)
    event = relationship("Event", back_populates="articles")
    attached_at = Column(DateTime, nullable=True)


class NeonDatabaseService:
    """
    Handles connections, session lifecycles, schema initialization, and transactional batch writing.
    """
    def __init__(self):
        self.db_url = env.get_env_var("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable or argument is missing.")

        self.engine = create_engine(
            self.db_url,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30
        )

        self._SessionMarker = sessionmaker(bind=self.engine, expire_on_commit=False)

    def initialize_schema(self):
        """
        Creates all tables defined in the Base metadata if they don't already exist.
        """
        Base.metadata.create_all(self.engine)

    def reset_events(self):
        """
        Deletes all events and removes event assignments from articles.
        Intended for rebuilding events from scratch.
        """
        with self._SessionMarker() as session:
            try:
                session.query(Article).update(
                    {Article.event_id: None}
                )
                session.query(Event).delete()
                session.commit()
                logger.info("Events successfully reset.")

            except Exception:
                session.rollback()
                raise

    def sync_sources_from_feeds(self, feeds: dict) -> None:
        """
        Upserts the sources table from feeds.yaml: creates any source not yet in the DB,
        and updates category/tier/region/source_tags/url on existing sources whose
        feeds.yaml entry has changed since, preserving the source's id.
        """
        with self._SessionMarker() as session:
            try:
                created = 0
                updated = 0

                for category, category_feeds in feeds.items():
                    for feed_info in category_feeds:
                        name = feed_info["name"]
                        fields = {
                            "category": category,
                            "tier": str(feed_info["tier"]) if feed_info.get("tier") is not None else None,
                            "region": feed_info.get("region"),
                            "source_tags": feed_info.get("source_tags", []),
                            "url": feed_info["url"],
                        }

                        source_obj = session.query(Source).filter(Source.name == name).first()

                        if not source_obj:
                            session.add(Source(name=name, **fields))
                            created += 1
                            continue

                        if any(getattr(source_obj, field) != value for field, value in fields.items()):
                            for field, value in fields.items():
                                setattr(source_obj, field, value)
                            updated += 1

                session.commit()
                logger.info("Synced sources from feeds.yaml: %s created, %s updated.", created, updated)

            except Exception:
                session.rollback()
                logger.exception("Failed to sync sources from feeds.yaml.")
                raise

    def save_bronze_data(self, articles_data: list):
        """
        Takes a list of raw article dictionaries from rss_collector.py, extracts/upserts sources,
        and saves unique articles with optimal batch queries.
        """
        if not articles_data:
            return

        with self._SessionMarker() as session:
            try:
                for item in articles_data:
                    source_name = item.get("source", "Unknown Source")
                    source_obj = session.query(Source).filter(Source.name == source_name).first()

                    if not source_obj:
                        logger.info("Source '%s' not found in DB. Creating a new source entry.", source_name)
                        source_obj = Source(
                            name=source_name,
                            category=item.get("category"),
                            source_tags=item.get("source_tags", []),
                            url=item.get("source_url")
                        )
                        session.add(source_obj)
                        session.flush()

                    article_title = normalize_text(item.get("title", ""))
                    article_link = normalize_url(item.get("link", ""))
                    deterministic_uuid = generate_article_id(article_title, article_link)

                    insert_op = insert(Article).values(
                        content_id=deterministic_uuid,
                        title=article_title,
                        link=article_link,
                        published=datetime.fromisoformat(item.get("published")),
                        article_tags=item.get("article_tags", []),
                        raw_summary=item.get("summary"),
                        source_id=source_obj.id,
                        collected_at=datetime.now()
                    )

                    upsert_op = insert_op.on_conflict_do_nothing()
                    session.execute(upsert_op)

                session.commit()
                logger.info("Processed %s bronze articles to Neon.", len(articles_data))

            except Exception as exc:
                session.rollback()
                logger.exception("Bronze batch operation failed. Transaction rolled back.")
                raise exc

    def save_silver_data(self, enriched_articles: list):
        """
        Takes a list of AI-enriched article dictionaries and updates the existing
        Bronze records in the database with their new Silver metrics.
        """
        if not enriched_articles:
            return

        with self._SessionMarker() as session:
            try:
                for item in enriched_articles:
                    article_title = normalize_text(item.get("title", ""))
                    article_link = normalize_url(item["link"])
                    deterministic_uuid = generate_article_id(article_title, article_link)

                    article = (
                        session.query(Article)
                        .filter_by(content_id=deterministic_uuid)
                        .first()
                    )

                    if article:
                        article.ai_summary = item.get("ai_summary", article.ai_summary)
                        article.score = item.get("score", article.score)
                        article.metrics = item.get("metrics", article.metrics)
                        article.justification = item.get("justification", article.justification)
                        existing_tags = getattr(article, "article_tags", None)
                        article.article_tags = item.get("article_tags", existing_tags)
                        article.enriched_at = datetime.now()
                    else:
                        logger.warning(
                            "Article with link '%s' was not found in DB. Skipping silver update.",
                            item["link"],
                        )

                session.commit()
                logger.info("Synchronized %s silver articles to Neon.", len(enriched_articles))

            except Exception as exc:
                session.rollback()
                logger.exception("Silver batch operation failed. Transaction rolled back.")
                raise exc

    def get_articles(self, stage: str = "bronze", min_score: int = 0) -> list:
        """
        Retrieves today's articles from the database and maps them back into
        the dictionary format expected by the markdown report generator.
        """
        with self._SessionMarker() as session:
            try:
                today = datetime.now().date()
                articles_data = []

                if stage == "silver":
                    query_results = session.query(Article).join(Source).filter(
                        func.date(Article.collected_at) == today,
                        Article.score >= min_score
                    ).order_by(Article.score.desc()).all()

                    for db_article in query_results:
                        articles_data.append({
                            "title": db_article.title,
                            "link": db_article.link,
                            "published": db_article.published.isoformat() if db_article.published else "Unknown",
                            "source": db_article.source.name,
                            "category": db_article.source.category,
                            "ai_summary": db_article.ai_summary,
                            "score": db_article.score,
                            "metrics": db_article.metrics,
                            "justification": db_article.justification,
                            "article_tags": db_article.article_tags,
                        })

                if stage == "bronze":
                    query_results = session.query(Article).join(Source).filter(
                        func.date(Article.collected_at) == today,
                    ).order_by(Article.published.desc()).all()

                    for db_article in query_results:
                        articles_data.append({
                            "title": db_article.title,
                            "link": db_article.link,
                            "published": db_article.published.isoformat() if db_article.published else "Unknown",
                            "source": db_article.source.name,
                            "category": db_article.source.category,
                            "summary": db_article.raw_summary
                        })

                logger.info("Retrieved %s articles from the database for stage '%s'.", len(articles_data), stage)
                return articles_data

            except Exception as exc:
                logger.exception("Failed to retrieve articles for stage '%s'.", stage)
                raise exc


def sync_sources(feeds: dict) -> None:
    """
    Public-facing function to upsert the sources table from a loaded feeds.yaml dict.
    """
    try:
        db_service = NeonDatabaseService()
        db_service.sync_sources_from_feeds(feeds)
    except Exception:
        logger.exception("Failed to sync sources from feeds.")
        raise


def db_save_return(articles: list = None, stage: str = "bronze"):
    """
    Public-facing function to save a batch of articles to the database.
    Options : raw (bronze) or enriched (silver) data. Defaults to bronze.
    """
    try:
        db_service = NeonDatabaseService()
        if stage == "bronze":
            if articles:
                db_service.save_bronze_data(articles)
            return db_service.get_articles()
        if stage == "silver":
            if articles:
                db_service.save_silver_data(articles)
            return db_service.get_articles("silver", 50)
    except Exception as exc:
        logger.exception("Failed to save articles to the database for stage '%s'.", stage)
        raise exc
