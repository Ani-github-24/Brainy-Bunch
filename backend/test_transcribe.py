"""Standalone test: send audio.mp3 to Gemini for transcription.

Verifies that the transcription path works before wiring it into
the FastAPI endpoint.  Uses the same SDK calls the endpoint will use.
"""

import os
import sys

from google import genai
from google.genai import types

API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
if not API_KEY:
    print("ERROR: Set GEMINI_API_KEY or GOOGLE_API_KEY env var first.")
    sys.exit(1)

AUDIO_PATH = os.path.join(os.path.dirname(__file__), "..", "audio.mp3")

print(f"Reading audio from: {os.path.abspath(AUDIO_PATH)}")
with open(AUDIO_PATH, "rb") as f:
    audio_bytes = f.read()
print(f"Audio size: {len(audio_bytes)} bytes")

client = genai.Client(api_key=API_KEY)

print("Sending to Gemini (gemini-3.6-flash) for transcription...")
response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=[
        "Transcribe the following audio exactly. Output only the spoken words, "
        "no commentary, no formatting, no timestamps.",
        types.Part.from_bytes(data=audio_bytes, mime_type="audio/mpeg"),
    ],
)

print("\n--- Transcription result ---")
print(response.text)
print("--- end ---")
