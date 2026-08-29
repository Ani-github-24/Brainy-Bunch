"""SQLModel data models for Brainy Bunch."""

from datetime import datetime, date
from typing import Optional

from sqlmodel import SQLModel, Field


# ── Table models (database) ─────────────────────────────────────────────


class Class(SQLModel, table=True):
    """A course / class that students attend."""

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    subject: str
    date: date
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ClassSession(SQLModel, table=True):
    """A single recording / live session within a Class."""

    id: Optional[int] = Field(default=None, primary_key=True)
    class_id: int = Field(foreign_key="class.id")
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    status: str = Field(default="pending")  # pending | recording | completed


class TranscriptChunk(SQLModel, table=True):
    """One chunk of transcribed audio tied to a session."""

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="classsession.id")
    seq: int
    start_ts_sec: float
    end_ts_sec: float
    text: str


class StudyPack(SQLModel, table=True):
    """AI-generated study material for a session."""

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="classsession.id")
    notes_md: Optional[str] = None
    glossary_json: Optional[str] = None
    flashcards_json: Optional[str] = None
    quiz_json: Optional[str] = None
    flowchart_mermaid: str | None = Field(default=None)
    generated_at: Optional[datetime] = None


class TranslationCache(SQLModel, table=True):
    session_id: int = Field(foreign_key="classsession.id", primary_key=True)
    lang: str = Field(primary_key=True)
    translated_md: str


# ── Request schemas (non-table, Pydantic validation runs on these) ───────
#
# SQLModel table=True classes skip Pydantic coercion in __init__, so an
# ISO-8601 string like "2026-01-01T10:00:00" stays a raw str instead of
# being parsed into a datetime.  These plain schemas guarantee proper
# type coercion before we construct the table model for the DB.


class ClassCreate(SQLModel):
    """Request body for creating a Class."""

    title: str
    subject: str
    date: date


class ClassSessionCreate(SQLModel):
    """Request body for creating a ClassSession."""

    class_id: int
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    status: str = "pending"

