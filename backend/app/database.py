"""Database engine, session management, and initialisation."""

import os
import shutil
from sqlmodel import SQLModel, Session, create_engine

# On Vercel, the filesystem is read-only except for /tmp.
if os.getenv("VERCEL"):
    tmp_db = "/tmp/brainy_bunch.db"
    local_db = "./brainy_bunch.db"
    
    # Copy the bundled test data to /tmp on cold start if it exists
    if not os.path.exists(tmp_db) and os.path.exists(local_db):
        shutil.copy2(local_db, tmp_db)
        
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{tmp_db}")
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
