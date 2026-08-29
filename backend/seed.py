"""Seed the database with sample Class rows (idempotent)."""

from datetime import date

from sqlmodel import Session, select

from app.database import engine, init_db
from app.models import Class

SAMPLE_CLASSES = [
    Class(title="Intro to Algebra", subject="Mathematics", date=date(2026, 9, 1)),
    Class(title="Organic Chemistry 101", subject="Chemistry", date=date(2026, 9, 2)),
    Class(title="World History: Ancient Civilizations", subject="History", date=date(2026, 9, 3)),
]


def seed():
    init_db()
    with Session(engine) as session:
        for sample in SAMPLE_CLASSES:
            existing = session.exec(
                select(Class).where(Class.title == sample.title)
            ).first()
            if existing:
                print(f"  [skip] Already exists: {sample.title}")
            else:
                session.add(sample)
                session.commit()
                print(f"  [+] Inserted: {sample.title}")


if __name__ == "__main__":
    print("Seeding database...")
    seed()
    print("Done.")
