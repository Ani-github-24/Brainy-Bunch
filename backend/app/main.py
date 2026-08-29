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
from app.models import Class, ClassCreate, ClassSession, ClassSessionCreate, TranscriptChunk, StudyPack, ManualNoteCreate
from app.transcription import transcribe_audio
from app.studypack import generate_study_pack_content
from app.feature_chat import chat_router
from fastapi.responses import HTMLResponse

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
def list_sessions(class_id: int = None, session: Session = Depends(get_session)):
    query = select(ClassSession)
    if class_id is not None:
        query = query.where(ClassSession.class_id == class_id)
    # Order by started_at desc nulls last, then id desc
    query = query.order_by(
        col(ClassSession.started_at).desc().nulls_last(),
        col(ClassSession.id).desc()
    )
    return session.exec(query).all()


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


@app.post("/sessions/{session_id}/manual-note")
def create_manual_note(
    session_id: int,
    payload: ManualNoteCreate,
    session: Session = Depends(get_session),
):
    """Receive a manual note and store it as a TranscriptChunk."""
    # Verify session exists
    cs = session.get(ClassSession, session_id)
    if not cs:
        raise HTTPException(status_code=404, detail="ClassSession not found")
        
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Note cannot be empty")

    # Compute next seq number and timestamp range
    max_seq_result = session.exec(
        select(func.max(col(TranscriptChunk.seq))).where(
            TranscriptChunk.session_id == session_id
        )
    ).one()
    next_seq = (max_seq_result or 0) + 1

    # Keep timestamps consistent with sequence progression
    start_ts = (next_seq - 1) * CHUNK_DURATION_SEC
    end_ts = next_seq * CHUNK_DURATION_SEC

    chunk = TranscriptChunk(
        session_id=session_id,
        seq=next_seq,
        start_ts_sec=start_ts,
        end_ts_sec=end_ts,
        text=text,
        source="manual"
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
        "source": chunk.source
    }


@app.get("/sessions/{session_id}/transcript", response_model=List[TranscriptChunk])
def get_transcript(session_id: int, session: Session = Depends(get_session)):
    chunks = session.exec(
        select(TranscriptChunk)
        .where(TranscriptChunk.session_id == session_id)
        .order_by(TranscriptChunk.seq)
    ).all()
    return chunks


# ── Study Pack ───────────────────────────────────────────────────────────

@app.post("/sessions/{session_id}/generate-study-pack", response_model=StudyPack)
def generate_study_pack(session_id: int, session: Session = Depends(get_session)):
    cs = session.get(ClassSession, session_id)
    if not cs:
        raise HTTPException(status_code=404, detail="Session not found")

    # Pull all TranscriptChunk rows for the session, ordered by seq.
    chunks = session.exec(
        select(TranscriptChunk)
        .where(TranscriptChunk.session_id == session_id)
        .order_by(TranscriptChunk.seq)
    ).all()

    chunk_dicts = [{"seq": c.seq, "text": c.text} for c in chunks]
    
    try:
        pack_data, input_tokens, output_tokens = generate_study_pack_content(chunk_dicts)
    except ValueError as e:
        if "Insufficient content" in str(e):
            raise HTTPException(status_code=400, detail="insufficient content")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        log.exception("Study pack generation failed for session %d", session_id)
        raise HTTPException(status_code=502, detail=f"Generation failed: {e}")

    # Store the result as a StudyPack row
    # Delete existing if any (optional, but good for regeneration)
    existing_pack = session.exec(
        select(StudyPack).where(StudyPack.session_id == session_id)
    ).first()
    
    if existing_pack:
        session.delete(existing_pack)

    import json
    new_pack = StudyPack(
        session_id=session_id,
        notes_md=pack_data.get("notes"),
        glossary_json=json.dumps(pack_data.get("glossary", [])),
        flashcards_json=json.dumps(pack_data.get("flashcards", [])),
        quiz_json=json.dumps(pack_data.get("quiz", [])),
        flowchart_mermaid=pack_data.get("flowchart"),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        generated_at=func.now()
    )
    
    session.add(new_pack)
    session.commit()
    session.refresh(new_pack)
    
    return new_pack


@app.get("/sessions/{session_id}/study-pack", response_model=StudyPack)
def get_study_pack(session_id: int, session: Session = Depends(get_session)):
    pack = session.exec(
        select(StudyPack).where(StudyPack.session_id == session_id)
    ).first()
    
    if not pack:
        raise HTTPException(status_code=404, detail="Study pack not found")
        
    return pack

@app.post("/sessions/{session_id}/translate")
def translate_study_pack(session_id: int, lang: str, session: Session = Depends(get_session)):
    from app.models import TranslationCache
    from app.studypack import translate_notes

    # Verify session and study pack exist
    pack = session.exec(
        select(StudyPack).where(StudyPack.session_id == session_id)
    ).first()
    
    if not pack or not pack.notes_md:
        raise HTTPException(status_code=404, detail="Study pack notes not found for this session")

    # Check cache
    cached = session.exec(
        select(TranslationCache).where(
            TranslationCache.session_id == session_id,
            TranslationCache.lang == lang
        )
    ).first()

    if cached:
        return {"translated_md": cached.translated_md}

    # Not cached, hit Gemini
    try:
        translated_md = translate_notes(pack.notes_md, lang)
    except Exception as e:
        log.exception("Translation failed for session %d, lang %s", session_id, lang)
        raise HTTPException(status_code=502, detail=f"Translation failed: {e}")

    # Save to cache
    new_cache = TranslationCache(
        session_id=session_id,
        lang=lang,
        translated_md=translated_md
    )
    session.add(new_cache)
    session.commit()

    return {"translated_md": translated_md}

app.include_router(chat_router)

@app.get("/record.html")
def get_record_html():
    content = (STATIC_DIR / "record.html").read_text()
    injection = "<script src='/chat_panel.js'></script></body>"
    content = content.replace("</body>", injection)
    return HTMLResponse(content)

# Mount static files LAST so API routes take priority
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

