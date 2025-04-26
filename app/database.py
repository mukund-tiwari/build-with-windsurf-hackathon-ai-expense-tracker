from sqlmodel import create_engine, SQLModel, Session
from pathlib import Path

# Database URL, here using SQLite in the project directory
DATABASE_URL = f"sqlite:///{Path(__file__).parent.parent / 'expenses.db'}"

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