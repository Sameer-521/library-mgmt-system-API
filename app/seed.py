import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Book

logger = logging.getLogger(__name__)

SEED_BOOKS: list[dict] = [
    {
        "title": "The Pragmatic Programmer",
        "author": "Andrew Hunt & David Thomas",
        "isbn": "9780135957059",
        "location": "A1",
    },
    {
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "isbn": "9780132350884",
        "location": "A2",
    },
    {
        "title": "The Rust Programming Language",
        "author": "Steve Klabnik & Carol Nichols",
        "isbn": "9781718500440",
        "location": "B1",
    },
]


async def seed_books(db: AsyncSession) -> None:
    existing = await db.execute(select(Book.id).limit(1))
    if existing.first() is not None:
        logger.info("Books already present, skipping seed")
        return

    db.add_all([Book(**data) for data in SEED_BOOKS])
    await db.commit()
    logger.info("Seeded %d books", len(SEED_BOOKS))
