"""AI study pack generation."""

import logging
import json
from pydantic import BaseModel, Field

from google import genai
from google.genai import types

from app.transcription import get_gemini_client, GEMINI_MODEL

log = logging.getLogger(__name__)

class GlossaryTerm(BaseModel):
    term: str = Field(description="The vocabulary term")
    definition: str = Field(description="The definition of the term")
    source_chunk_seq: int = Field(description="The seq number of the transcript chunk this term originated from")

class Flashcard(BaseModel):
    front: str = Field(description="The front side of the flashcard (question or prompt)")
    back: str = Field(description="The back side of the flashcard (answer)")
    source_chunk_seq: int = Field(description="The seq number of the transcript chunk this flashcard originated from")

class QuizQuestion(BaseModel):
    question: str = Field(description="The quiz question")
    options: list[str] = Field(description="Exactly 4 options for the multiple choice question")
    correct_index: int = Field(description="The 0-based index of the correct option")
    source_chunk_seq: int = Field(description="The seq number of the transcript chunk this question originated from")

class StudyPackResponse(BaseModel):
    notes: str = Field(description="Markdown formatted notes, organized by topic")
    glossary: list[GlossaryTerm] = Field(description="A list of glossary terms")
    flashcards: list[Flashcard] = Field(description="A list of flashcards")
    quiz: list[QuizQuestion] = Field(description="A list of quiz questions")
    flowchart: str = Field(description="A Mermaid flowchart string visualizing the concepts")


def generate_study_pack_content(transcript_chunks: list[dict]) -> tuple[dict, int, int]:
    """Send transcript chunks to Gemini and get a structured StudyPackResponse."""
    
    # Check if there is enough content
    combined_text = "\n".join([f"[Seq {c['seq']}]: {c['text']}" for c in transcript_chunks if c['text']])
    if len(combined_text.strip()) < 50:
        raise ValueError("Insufficient content for study pack generation")

    client = get_gemini_client()
    
    prompt = (
        "You are an expert educational assistant. I will provide a transcript of a class session "
        "broken down into chunks with their sequence numbers. \n\n"
        "Generate a comprehensive study pack based ONLY on the provided transcript. Do not invent "
        "information outside of the transcript. "
        "For each glossary term, flashcard, and quiz question, you MUST accurately include the 'source_chunk_seq' "
        "which is the sequence number of the chunk that provided the information. \n\n"
        f"Transcript:\n{combined_text}"
    )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=StudyPackResponse,
        )
    )

    try:
        pack_data = json.loads(response.text)
        
        # Safely extract token counts
        input_tokens = 0
        output_tokens = 0
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
            output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)
            
        return pack_data, input_tokens, output_tokens
    except json.JSONDecodeError as e:
        log.error("Failed to decode JSON from Gemini: %s", response.text)
        raise e

def translate_notes(notes_md: str, target_lang: str) -> str:
    """Translate markdown notes into the target language."""
    client = get_gemini_client()
    
    prompt = f"Translate the following educational notes into {target_lang}. Keep the Markdown formatting intact:\n\n{notes_md}"
    
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )
    
    return response.text
