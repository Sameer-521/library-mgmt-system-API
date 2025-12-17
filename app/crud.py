from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Book, BookCopy, User, Loan, BkCopySchedule
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
    return result.scalars().first()

async def get_bk_copy_by_barcode(db: AsyncSession, barcode: str):
    stmt = select(BookCopy).where(BookCopy.copy_barcode == barcode)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_active_schedule(db: AsyncSession, isbn: int, user_id: int):
    stmt = select(BkCopySchedule).join(
        BookCopy, 
        BkCopySchedule.bk_copy_barcode == BookCopy.copy_barcode).where(
        BkCopySchedule.status == 'ACTIVE',
        BkCopySchedule.user_id == user_id,
        BookCopy.book_isbn == isbn
        )
    result = await db.execute(stmt)
    return result.scalars().first()

async def update_bk_schedule(
        db: AsyncSession, 
        bk_copy_schedule: BkCopySchedule, 
        update_data: dict,
        ):
    for key, value in update_data.items():
        setattr(bk_copy_schedule, key, value)
    await db.commit()

async def get_user_active_loans(db: AsyncSession, user_id):
    stmt = select(Loan).where(Loan.user_id == user_id, Loan.status == 'ACTIVE')
    result = await db.execute(stmt)
    return result.scalars().all()

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
        ):
    for key, value in update_data.items():
        setattr(book, key, value)
    await db.commit()

async def get_book_copy(
        db: AsyncSession,
        isbn: int
        ):
    stmt = select(BookCopy).where(BookCopy.book_isbn == isbn, BookCopy.status == "AVAILABLE")
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_book_copy_by_barcode(
        db: AsyncSession,
        copy_barcode_: str
        ):
    stmt = select(BookCopy).where(BookCopy.copy_barcode == copy_barcode_)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def update_bk_copy(
        db: AsyncSession, 
        book_copy: BookCopy, 
        update_data: dict
        ):
    for key, value in update_data.items():
        setattr(book_copy, key, value)
    await db.commit()
    await db.refresh(book_copy)
    return book_copy

async def update_loan(
        db: AsyncSession, 
        loan: Loan, 
        update_data: dict
        ):
    for key, value in update_data.items():
        setattr(loan, key, value)
    await db.commit()
    await db.refresh(loan)
    return loan

async def get_user_by_email(db: AsyncSession, _email: str):
    stmt = select(User).where(User.email == _email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_new_user(db: AsyncSession, user: User):
    db.add(user)
    await db.commit()

async def create_loan(db: AsyncSession, loan: Loan):
    db.add(loan)
    await db.commit()
    await db.refresh(loan)
    return loan

async def get_all_non_staff_users(db: AsyncSession):
    stmt = select(User).where(User.is_staff==False, User.is_superuser==False)
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_loan_by_id(
        db:AsyncSession,
        _loan_id: str
        ):
    stmt = select(Loan).where(Loan.loan_id == _loan_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_default_superuser(db: AsyncSession, admin_user: User):
    db.add(admin_user)
    await db.commit()

async def update_user(
        db: AsyncSession, 
        user: User, 
        update_data: dict,
        ):
    for key, value in update_data.items():
        setattr(user, key, value)
    await db.commit()

async def get_default_superuser(db: AsyncSession, email: str):
    stmt = select(User).where(User.is_staff==True, User.is_superuser==True, User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_user_by_id(db: AsyncSession, user_id):
    user = await db.get(User, user_id)
    return user

async def create_schedule(db: AsyncSession, schedule: BkCopySchedule):
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule