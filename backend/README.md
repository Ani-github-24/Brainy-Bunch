# Brainy Bunch – Backend

FastAPI + SQLModel + SQLite backend for the Brainy Bunch study-pack generator.

## Prerequisites

- **Python 3.10+** (tested with 3.10.11)
- **Windows** (instructions below use PowerShell)

## Setup

```powershell
cd backend

# Create a virtual environment
py -3.10 -m venv .venv

# Activate it
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

## Seed the database

Inserts sample Class rows. Safe to run multiple times (idempotent).

```powershell
python seed.py
```

## Start the server

```powershell
uvicorn app.main:app --reload --port 8000
```

The API is then available at `http://127.0.0.1:8000`.
Interactive docs at `http://127.0.0.1:8000/docs`.

## API endpoints

| Method | Path                  | Description              |
| ------ | --------------------- | ------------------------ |
| GET    | `/health`             | Health check             |
| POST   | `/classes`            | Create a class           |
| GET    | `/classes`            | List all classes         |
| GET    | `/classes/{class_id}` | Get a class by ID        |
| POST   | `/sessions`           | Create a class session   |
| GET    | `/sessions`           | List all class sessions  |
| GET    | `/sessions/{id}`      | Get a class session by ID|

## Run tests

```powershell
python -m pytest tests/ -v
```
