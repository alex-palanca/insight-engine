from config import env_ini as env
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


from utils.hashing import generate_article_id


# ORM SETUP & SCHEMA DEFINITIONS
# Create a catalog class that tracks all our tables.
Base = declarative_base()

class Source(Base):
    """
    Represents the publisher of feeds (e.g., MIT Technology Review, TechCrunch).
    Normalized out of the articles table to maintain data integrity and efficiency.
    """
    __tablename__ = 'sources'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False) # Enforces that a source name is never duplicated
    category = Column(String, nullable=False)
    tier = Column(String, nullable=True) # Optional field for future use (e.g., premium vs free sources)
    region = Column(String, nullable=True) # Optional field for future use (e.g., US, EU, Asia)
    source_tags = Column(JSONB, nullable=True)
    url = Column(String, nullable=False)
    
    # It tells the ORM that when we query a Source, we can easily access its child articles via python list syntax.
    articles = relationship("Article", back_populates="source", cascade="all, delete-orphan")


class Event(Base):
    """
    Groups related articles into a unified historical cluster. 
    """
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now()) # Automatically stamps when the event was clustered

    articles = relationship("Article", back_populates="event")


class Article(Base):
    """
    Represents an individual collected piece of intelligence.
    Enforces uniqueness at the database engine layer via the 'link' URL column.
    """
    __tablename__ = 'articles'
    
    id = Column(Integer, primary_key=True)
    content_id = Column(PG_UUID(as_uuid=True), unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    link = Column(String, unique=True, nullable=False) # CRITICAL: Acts as our deduplication firewall
    published = Column(String, nullable=True)

    # BRONZE LAYER (Raw Data)
    article_tags = Column(JSONB, nullable=True)
    raw_summary = Column(Text, nullable=True)
    collected_at = Column(DateTime, nullable=False)

    # SILVER LAYER (AI Enriched Data)
    ai_summary = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)
    metrics = Column(JSONB, nullable=True)
    justification = Column(Text, nullable=True)
    article_read = Column(Boolean, default=False)
    enriched_at = Column(DateTime, nullable=True)
    
    # Foreign Keys.
    source_id = Column(Integer, ForeignKey('sources.id', ondelete="CASCADE"), nullable=False)
    source = relationship("Source", back_populates="articles")

    event_id = Column(Integer, ForeignKey('events.id', ondelete="SET NULL"), nullable=True)
    event = relationship("Event", back_populates="articles")


# DATABASE CLIENT MANAGER

class NeonDatabaseService:
    """
    Handles connections, session lifecycles, schema initialization, and transactional batch writing.
    """
    def __init__(self, database_url: str = None):
        # Fall back to environment variable if connection string isn't explicitly passed
        self.db_url = database_url or env.get_env_var("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable or argument is missing.")
            
        # Initialization of the underlying database connection pool.
        self.engine = create_engine(
            self.db_url,
            pool_size=5,          # Maintain up to 5 permanent connections for rapid reuse
            max_overflow=10,      # Allow up to 10 bursting temporary connections under load
            pool_timeout=30       # Wait up to 30 seconds before throwing a connection timeout error
        )
        
        # Csessionmaker() configures a factory for creating individual transaction instances (Sessions).
        self._SessionMarker = sessionmaker(bind=self.engine, expire_on_commit=False)

    def initialize_schema(self):
        """
        Creates all tables defined in the Base metadata if they don't already exist.
        """
        Base.metadata.create_all(self.engine)

    def save_bronze_data(self, articles_data: list):
        """
        Takes a list of raw article dictionaries from rss_collector.py, extracts/upserts sources,
        and saves unique articles with optimal batch queries.
        
        Expected structure per item:
        {
           'title': '...', 'link': '...', 'published': '...', 
           'summary': '...', 'source': '...', 'category': '...', 'source_url': '...'
        }
        """
        if not articles_data:
            return

        # Open an isolated Unit of Work (Session).
        with self._SessionMarker() as session:
            try:
                for item in articles_data:
                    # 1. Manage Source Extraction & Verification
                    source_name = item.get('source', 'Unknown Source')
                    source_obj = session.query(Source).filter(Source.name == source_name).first()
                    
                    if not source_obj:
                        print(f"Source '{source_name}' not found in DB. Creating new source entry.")
                        source_obj = Source(
                            name=source_name,
                            category=item.get('category'),
                            source_tags=item.get('source_tags', []),
                            url=item.get('source_url')
                        )
                        session.add(source_obj)
                        session.flush()

                    # 2. Native PostgreSQL UPSERT Execution
                    article_link = item.get('link', '')
                    
                    # This returns a Python UUID object
                    deterministic_uuid = generate_article_id(article_link)

                    insert_op = insert(Article).values(
                        
                        content_id=deterministic_uuid,
                        title=item.get('title'),
                        link=item.get('link'),
                        published=item.get('published'),
                        article_tags=item.get('article_tags', []),
                        raw_summary=item.get('summary'),
                        source_id=source_obj.id,
                        collected_at=datetime.now()
                    )
                    
                    # This tells Neon to ignore the row entirely if the URL unique constraint triggers.
                    upsert_op = insert_op.on_conflict_do_nothing(index_elements=['link'])
                    
                    # Transmits the compiled SQL across the network wire to Neon
                    session.execute(upsert_op)

                # Pushes all accumulated structural operations to persistent storage simultaneously
                session.commit()
                print(f"Successfully processed batch of {len(articles_data)} articles to Neon DB.")
                
            except Exception as e:
                # If ANY query in the block fails, rollback returns the database state to zero technical debt
                session.rollback()
                print(f"Database batch operation failed! Executed full transaction rollback. Error: {e}")
                raise e
            
    def save_silver_data(self, articles_data: list):
        """
        Takes a list of raw article dictionaries from rss_collector.py, extracts/upserts sources,
        and saves unique articles with optimal batch queries.
        
        Expected structure per item:
        {
           'title': '...', 'link': '...', 'published': '...', 
           'summary': '...', 'source': '...', 'category': '...', 'source_url': '...'
        }
        """
        if not articles_data:
            return

        # Open an isolated Unit of Work (Session).
        with self._SessionMarker() as session:
            try:
                for item in articles_data:
                    # 1. Manage Source Extraction & Verification
                    source_name = item.get('source', 'Unknown Source')
                    source_obj = session.query(Source).filter(Source.name == source_name).first()
                    
                    if not source_obj:
                        source_obj = Source(
                            name=source_name,
                            category=item.get('category'),
                            url=item.get('source_url')
                        )
                        session.add(source_obj)
                        session.flush()

                    # 2. Native PostgreSQL UPSERT Execution
                    insert_op = insert(Article).values(
                        title=item.get('title'),
                        link=item.get('link'),
                        published=item.get('published'),
                        summary=item.get('summary'),
                        source_id=source_obj.id,
                        collected_at=datetime.now()
                    )
                    
                    # This tells Neon to ignore the row entirely if the URL unique constraint triggers.
                    upsert_op = insert_op.on_conflict_do_nothing(index_elements=['link'])
                    
                    # Transmits the compiled SQL across the network wire to Neon
                    session.execute(upsert_op)

                # Pushes all accumulated structural operations to persistent storage simultaneously
                session.commit()
                print(f"Successfully processed batch of {len(articles_data)} articles to Neon DB.")
                
            except Exception as e:
                # If ANY query in the block fails, rollback returns the database state to zero technical debt
                session.rollback()
                print(f"Database batch operation failed! Executed full transaction rollback. Error: {e}")
                raise e
            
# Service to use
def db_save(articles: list,stage: str = "bronze"):
    """
    Public-facing function to save a batch of articles to the database.
    Options : raw (bronze) or enriched (silver) data. Defaults to bronze.
    """
    try:
        db_service = NeonDatabaseService()
        db_service.initialize_schema()  # Ensure schema is ready before saving
        if stage == "bronze":
            db_service.save_bronze_data(articles)
        if stage == "silver":
            db_service.save_silver_data(articles)
    except Exception as e:
        print(f"Failed to save articles to the database: {e}")
        raise e