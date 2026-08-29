import logging
from sqlmodel import SQLModel
from app.database import engine
import app.models

logging.basicConfig(level=logging.INFO)

def migrate():
    SQLModel.metadata.create_all(engine)
    print("Database tables updated successfully.")

if __name__ == "__main__":
    migrate()
