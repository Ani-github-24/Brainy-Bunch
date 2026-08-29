from app.database import engine
from sqlmodel import Session, select
from app.models import StudyPack, TranscriptChunk
import json
from datetime import datetime

mock_glossary = [
    {
        "term": "Four-stroke engine",
        "definition": "An internal combustion engine that utilizes four distinct strokes (intake, compression, power, exhaust) to complete one operating cycle.",
        "source_chunk_seq": 1
    }
]

mock_flashcards = [
    {
        "front": "What happens during the intake stroke?",
        "back": "The piston moves down, drawing a mixture of air and fuel into the cylinder.",
        "source_chunk_seq": 2
    }
]

mock_quiz = [
    {
        "question": "Which stroke ignites the air-fuel mixture?",
        "options": ["Intake", "Compression", "Power", "Exhaust"],
        "correct_index": 2,
        "source_chunk_seq": 3
    }
]

mock_notes = "# Engine Operation\nThe four-stroke engine is standard in most cars.\n\n## The Strokes\n1. Intake\n2. Compression\n3. Power\n4. Exhaust"
mock_bilingual = "# Operación del Motor\nEl motor de cuatro tiempos es estándar en la mayoría de los autos.\n\n## Los Tiempos\n1. Admisión\n2. Compresión\n3. Potencia\n4. Escape"

mock_mermaid = "graph TD;\n    A[Intake] --> B[Compression];\n    B --> C[Power];\n    C --> D[Exhaust];"

with Session(engine) as session:
    sp = StudyPack(
        session_id=3,
        notes_md=mock_notes,
        glossary_json=json.dumps(mock_glossary),
        flashcards_json=json.dumps(mock_flashcards),
        quiz_json=json.dumps(mock_quiz),
        flowchart_mermaid=mock_mermaid,
        bilingual_notes_md=mock_bilingual,
        generated_at=datetime.utcnow()
    )
    session.add(sp)
    
    # Also seed transcript chunks for session 3 so source indicator works
    # Delete existing chunks for session 3 to be safe
    existing_chunks = session.exec(select(TranscriptChunk).where(TranscriptChunk.session_id == 3)).all()
    for c in existing_chunks:
        session.delete(c)
        
    c1 = TranscriptChunk(session_id=3, seq=1, text="The four-stroke engine works.", start_ts_sec=0, end_ts_sec=10)
    c2 = TranscriptChunk(session_id=3, seq=2, text="Intake happens first.", start_ts_sec=10, end_ts_sec=20)
    c3 = TranscriptChunk(session_id=3, seq=3, text="Power happens third.", start_ts_sec=20, end_ts_sec=30)
    
    session.add(c1)
    session.add(c2)
    session.add(c3)
    
    session.commit()
    print("Mock StudyPack and Transcript chunks inserted for session 3.")
