"""FastAPI application – CRUD for Class & ClassSession, plus /health."""

from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select

from app.database import init_db, get_session
from app.models import Class, ClassCreate, ClassSession, ClassSessionCreate


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Brainy Bunch API", version="0.1.0", lifespan=lifespan)


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
