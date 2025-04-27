from sqlmodel import create_engine, SQLModel, Session
from app.config import DATABASE_URL
# Database URL is loaded from environment (Railway DATABASE_URL) or local SQLite fallback
# NOTE: Removed fallback assignment; using config.DATABASE_URL

# Create the SQLModel engine
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    """
    Create database tables.
    """
    SQLModel.metadata.create_all(engine)

def get_session():
    """
    Provide a transactional scope around a series of operations.
    """
    with Session(engine) as session:
        yield session