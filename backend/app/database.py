"""Database engine, session management, and initialisation."""

from sqlmodel import SQLModel, Session, create_engine

DATABASE_URL = "sqlite:///./brainy_bunch.db"

engine = create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
    """Create all tables if they don't already exist."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency that yields a database session."""
    with Session(engine) as session:
        yield session
