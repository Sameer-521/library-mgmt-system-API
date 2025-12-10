from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Book, BookCopy
from typing import List

async def get_book_by_id(db: AsyncSession, book_id: int):
    book = await db.get(Book, book_id)
    return book

async def get_book_by_barcode(db: AsyncSession, barcode: str):
    stmt = select(Book).where(Book.library_barcode == barcode)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_book_by_isbn(db: AsyncSession, bk_isbn: int):
    stmt = select(Book).where(Book.isbn == bk_isbn)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_last_book_copy(db: AsyncSession, book: Book):
    stmt = select(BookCopy).order_by(desc(BookCopy.serial)).where(BookCopy.book_isbn == book.isbn)
    result = await db.execute(stmt)
    return result.first()

async def create_new_book(db: AsyncSession, book: Book):
    db.add(book)
    await db.commit()

async def add_book_copies(db: AsyncSession, copies: List[BookCopy]):
    db.add_all(copies)
    await db.commit()

async def update_book(
        db: AsyncSession, 
        book: Book, 
        update_data: dict, 
        book_id: int
        ):
    for key, value in update_data.items():
        setattr(book, key, value)
    await db.commit()

# can i interact with the result returned from first() just like scalar_one_or_none()?
# yes, first() returns a Row object or None, you can access the columns using indexing or attribute access.