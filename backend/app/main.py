"""FastAPI application – CRUD for Class & ClassSession, plus /health."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select, func, col

from app.database import init_db, get_session
from app.models import Class, ClassCreate, ClassSession, ClassSessionCreate, TranscriptChunk
from app.transcription import transcribe_audio

log = logging.getLogger(__name__)

CHUNK_DURATION_SEC = 25.0  # matches the frontend MediaRecorder timeslice


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Brainy Bunch API", version="0.1.0", lifespan=lifespan)

# Allow the static HTML page (served from the same origin or file://) to
# call the API without CORS issues during local development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the static frontend from backend/static/
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
STATIC_DIR.mkdir(exist_ok=True)


# ── Health ───────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


# ── Class CRUD ───────────────────────────────────────────────────────────

@app.post("/classes", response_model=Class, status_code=201)
def create_class(payload: ClassCreate, session: Session = Depends(get_session)):
    cls = Class.model_validate(payload)
    session.add(cls)
    session.commit()
    session.refresh(cls)
    return cls


@app.get("/classes", response_model=List[Class])
def list_classes(session: Session = Depends(get_session)):
    return session.exec(select(Class)).all()


@app.get("/classes/{class_id}", response_model=Class)
def get_class(class_id: int, session: Session = Depends(get_session)):
    cls = session.get(Class, class_id)
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    return cls


# ── ClassSession CRUD ────────────────────────────────────────────────────

@app.post("/sessions", response_model=ClassSession, status_code=201)
def create_session(payload: ClassSessionCreate, session: Session = Depends(get_session)):
    # Verify the parent class exists
    if not session.get(Class, payload.class_id):
        raise HTTPException(status_code=404, detail="Parent class not found")
    cs = ClassSession.model_validate(payload)
    session.add(cs)
    session.commit()
    session.refresh(cs)
    return cs


@app.get("/sessions", response_model=List[ClassSession])
def list_sessions(session: Session = Depends(get_session)):
    return session.exec(select(ClassSession)).all()


@app.get("/sessions/{session_id}", response_model=ClassSession)
def get_session_by_id(session_id: int, session: Session = Depends(get_session)):
    cs = session.get(ClassSession, session_id)
    if not cs:
        raise HTTPException(status_code=404, detail="Session not found")
    return cs


# ── Transcribe chunk ─────────────────────────────────────────────────────

@app.post("/sessions/{session_id}/transcribe-chunk")
def transcribe_chunk(
    session_id: int,
    audio: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    """Receive an audio chunk, transcribe it via Gemini, and store the result.

    - Skips insertion if the transcription is empty/silence.
    - Returns the transcription text (or empty string for silence).
    """
    # Verify session exists
    cs = session.get(ClassSession, session_id)
    if not cs:
        raise HTTPException(status_code=404, detail="ClassSession not found")

    # Read the uploaded audio bytes
    audio_bytes = audio.file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")

    # Determine the MIME type (browser sends webm/opus, fallback to webm)
    mime_type = audio.content_type or "audio/webm"

    # Call Gemini
    try:
        text = transcribe_audio(audio_bytes, mime_type=mime_type)
    except Exception as exc:
        log.exception("Gemini transcription failed for session %d", session_id)
        raise HTTPException(
            status_code=502,
            detail=f"Transcription failed: {exc}",
        )

    # If silence / near-empty, return without inserting a row
    if text is None:
        return {"session_id": session_id, "seq": None, "text": "", "silence": True}

    # Compute next seq number and timestamp range
    max_seq_result = session.exec(
        select(func.max(col(TranscriptChunk.seq))).where(
            TranscriptChunk.session_id == session_id
        )
    ).one()
    next_seq = (max_seq_result or 0) + 1

    start_ts = (next_seq - 1) * CHUNK_DURATION_SEC
    end_ts = next_seq * CHUNK_DURATION_SEC

    chunk = TranscriptChunk(
        session_id=session_id,
        seq=next_seq,
        start_ts_sec=start_ts,
        end_ts_sec=end_ts,
        text=text,
    )
    session.add(chunk)
    session.commit()
    session.refresh(chunk)

    return {
        "session_id": session_id,
        "seq": chunk.seq,
        "text": chunk.text,
        "start_ts_sec": chunk.start_ts_sec,
        "end_ts_sec": chunk.end_ts_sec,
        "silence": False,
    }


# Mount static files LAST so API routes take priority
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

