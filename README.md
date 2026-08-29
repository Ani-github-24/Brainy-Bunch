# Brainy Bunch

Brainy Bunch is an AI-powered educational application that records live class sessions, transcribes them in near real-time, and automatically generates comprehensive, interactive study materials. 

## Features

### Built
- **Live Audio Transcription**: Chunks audio directly from the browser and transcribes it using Gemini. 
- **Study Pack Generation**: Generates structured study materials directly from the transcript, including:
  - Markdown Notes
  - Glossary (with source citations)
  - Flashcards (with source citations)
  - Multiple Choice Quizzes (with source citations)
  - Mermaid.js Flowcharts
- **Live AI Assistant**: A chat panel available during recording that allows students to ask questions against the running transcript. 
- **Flagged Questions for Teachers**: Students can flag questions they couldn't get answered by the AI. Teachers can view these in a dashboard that polls for new questions.
- **Multilingual Notes**: Automatically translates the generated markdown notes into multiple languages (Tamil, Telugu, Malayalam, Hindi, Spanish) using Gemini.
- **PII Scrubbing**: Automatically detects and redacts emails and phone numbers from the transcript before storing them.
- **Manual Notes**: Students can type manual notes during the live recording which are interleaved into the transcript chunks.

### Planned (Not Yet Built)
- **Authentication & Authorization**: Currently, the application has no login system. 
- **Rate Limiting**: To prevent API abuse, rate-limiting on Gemini endpoints needs to be implemented.
- **Calendar OAuth**: Planned integration to automatically sync class schedules.
- **Live Audio in Teacher View**: Real-time audio streaming to the teacher dashboard is planned but not yet built.

## Tech Stack
- **Backend**: FastAPI (Python), SQLModel (SQLite)
- **Frontend**: Vanilla HTML/JS/CSS, Marked.js (Markdown), Mermaid.js (Flowcharts)
- **AI/LLMs**: Google GenAI SDK (`gemini-3.6-flash` for transcription & study packs, `gemini-3.1-flash-lite` for live chat).

## Setup & Run Instructions
1. Ensure Python 3.10+ is installed.
2. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```
3. Create a virtual environment and activate it:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Set your Gemini API key:
   ```bash
   export GEMINI_API_KEY="your-api-key" # On Windows: $env:GEMINI_API_KEY="your-api-key"
   ```
6. Run the database migration to create the tables:
   ```bash
   python migrate.py
   ```
7. Start the FastAPI server:
   ```bash
   fastapi dev app/main.py
   ```
8. Open your browser and navigate to `http://localhost:8000/`.

## Presentation Material
See [ppt-content.md](ppt-content.md) for a detailed presentation outline of the architecture, design, and value proposition.
