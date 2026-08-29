from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
import os
from google import genai

from app.database import get_session
from app.models import ClassSession, TranscriptChunk, FlaggedQuestion, FlaggedQuestionCreate, ChatRequest

chat_router = APIRouter()

def get_gemini_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    return genai.Client(api_key=api_key)

@chat_router.post("/sessions/{session_id}/chat")
def ask_chat(session_id: int, payload: ChatRequest, session: Session = Depends(get_session)):
    cs = session.get(ClassSession, session_id)
    if not cs:
        raise HTTPException(status_code=404, detail="Session not found")
    
    chunks = session.exec(
        select(TranscriptChunk)
        .where(TranscriptChunk.session_id == session_id)
        .order_by(TranscriptChunk.seq)
    ).all()
    
    transcript_text = "\n".join([c.text for c in chunks if c.text])
    
    prompt = f"""
    You are an AI teaching assistant.
    Here is the transcript of the class so far:
    {transcript_text}
    
    The student asks: {payload.question}
    
    Please provide a helpful, concise answer based on the transcript if possible, or general knowledge if not explicitly covered.
    """
    
    client = get_gemini_client()
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt
    )
    
    return {"answer": response.text}

@chat_router.post("/sessions/{session_id}/flag-question")
def flag_question(session_id: int, payload: FlaggedQuestionCreate, session: Session = Depends(get_session)):
    cs = session.get(ClassSession, session_id)
    if not cs:
        raise HTTPException(status_code=404, detail="Session not found")
        
    fq = FlaggedQuestion(session_id=session_id, question_text=payload.question_text)
    session.add(fq)
    session.commit()
    session.refresh(fq)
    return fq

@chat_router.get("/sessions/{session_id}/flagged-questions", response_model=List[FlaggedQuestion])
def list_flagged_questions(session_id: int, session: Session = Depends(get_session)):
    fqs = session.exec(
        select(FlaggedQuestion)
        .where(FlaggedQuestion.session_id == session_id)
        .where(FlaggedQuestion.status == "open")
        .order_by(FlaggedQuestion.created_at)
    ).all()
    return fqs
