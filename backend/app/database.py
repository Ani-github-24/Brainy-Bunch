"""Database engine, session management, and initialisation."""

import os
from sqlmodel import SQLModel, Session, create_engine

# On Vercel, the filesystem is read-only except for /tmp.
if os.getenv("VERCEL"):
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////tmp/brainy_bunch.db")
else:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./brainy_bunch.db")

engine = create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
    """Create all tables if they don't already exist."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency that yields a database session."""
    with Session(engine) as session:
        yield session
