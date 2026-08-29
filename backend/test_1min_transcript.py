import requests
import json

# A ~1-minute transcript (about 130-150 words) about a single topic: the 4-stroke engine cycle.
# It genuinely has only a few key points: Intake, Compression, Power, Exhaust.
TRANSCRIPT = [
    {
        "seq": 1,
        "text": "Today we're going to cover the basic operation of a four-stroke internal combustion engine. This is the standard engine found in most gasoline-powered cars."
    },
    {
        "seq": 2,
        "text": "The cycle consists of four distinct strokes: intake, compression, power, and exhaust. Let's start with the first one, the intake stroke. During this phase, the piston moves down, creating a vacuum that draws a mixture of air and fuel into the cylinder through the open intake valve."
    },
    {
        "seq": 3,
        "text": "Next is the compression stroke. Both valves are closed, and the piston moves back up, squeezing the air-fuel mixture into a tight space, which makes it highly explosive. Then comes the power stroke, where the spark plug ignites the mixture, forcing the piston down. Finally, the exhaust stroke pushes the burned gases out the exhaust valve."
    }
]

def test_standalone(api_key):
    from google import genai
    from google.genai import types
    from app.studypack import StudyPackResponse

    client = genai.Client(api_key=api_key)
    
    combined_text = "\n".join([f"[Seq {c['seq']}]: {c['text']}" for c in TRANSCRIPT])
    prompt = (
        "You are an expert educational assistant. I will provide a transcript of a class session "
        "broken down into chunks with their sequence numbers. \n\n"
        "Generate a comprehensive study pack based ONLY on the provided transcript. Do not invent "
        "information outside of the transcript. "
        "For each glossary term, flashcard, and quiz question, you MUST accurately include the 'source_chunk_seq' "
        "which is the sequence number of the chunk that provided the information. \n"
        "For the bilingual_notes field, provide the exact same notes translated into Spanish.\n\n"
        f"Transcript:\n{combined_text}"
    )

    print("Sending to Gemini...")
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=StudyPackResponse,
        )
    )
    
    data = json.loads(response.text)
    
    print("\n--- Generated Flashcards ---")
    for f in data.get("flashcards", []):
        print(f"Q: {f['front']} | A: {f['back']} | Source: {f['source_chunk_seq']}")
        
    print("\n--- Generated Quiz Questions ---")
    for q in data.get("quiz", []):
        print(f"Q: {q['question']} | Source: {q['source_chunk_seq']}")

if __name__ == "__main__":
    import sys
    import os
    
    key = os.environ.get("GEMINI_API_KEY")
    if len(sys.argv) > 1:
        key = sys.argv[1]
        
    if not key:
        print("ERROR: No API key provided.")
        sys.exit(1)
        
    test_standalone(key)
