"""Gemini-based audio transcription service."""

import logging
import os

from google import genai
from google.genai import types

log = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-3.6-flash"

TRANSCRIBE_PROMPT = (
    "Transcribe the following audio exactly. "
    "Output only the spoken words, no commentary, no formatting, no timestamps. "
    "If the audio is silent or contains no speech, respond with exactly: [SILENCE]"
)


def get_gemini_client() -> genai.Client:
    """Create a Gemini client from the environment API key.

    Raises RuntimeError if neither GEMINI_API_KEY nor GOOGLE_API_KEY is set.
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY (or GOOGLE_API_KEY) environment variable is not set. "
            "Get a key from https://aistudio.google.com/apikey and set it with: "
            "$env:GEMINI_API_KEY = 'your-key-here'"
        )
    return genai.Client(api_key=api_key)


def transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/webm") -> str | None:
    """Send audio bytes to Gemini and return the transcription text.

    Returns None if the audio is silence / near-empty.
    Raises on API failure so the caller can handle it.
    """
    client = get_gemini_client()

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            TRANSCRIBE_PROMPT,
            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
        ],
    )

    text = (response.text or "").strip()

    # Treat silence / near-empty transcriptions as "nothing to store"
    if not text or text == "[SILENCE]" or len(text) < 3:
        log.info("Chunk transcribed to silence / near-empty, skipping.")
        return None

    return text
