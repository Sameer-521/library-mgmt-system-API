from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Audit,
    BkCopySchedule,
    BkCopyStatus,
    Book,
    BookCopy,
    Loan,
    LoanStatus,
    User,
)


async def get_book_by_id(db: AsyncSession, book_id: int):
    book = await db.get(Book, book_id)
    return book


async def get_book_by_barcode(db: AsyncSession, barcode: str):
    stmt = select(Book).where(Book.library_barcode == barcode)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_book_by_isbn(db: AsyncSession, bk_isbn: str):
    stmt = select(Book).where(Book.isbn == bk_isbn)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_last_book_copy(db: AsyncSession, book: Book):
    stmt = (
        select(BookCopy)
        .order_by(desc(BookCopy.serial))
        .where(BookCopy.book_isbn == book.isbn)
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def get_bk_copy_by_barcode(db: AsyncSession, barcode: str):
    stmt = select(BookCopy).where(BookCopy.copy_barcode == barcode)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_reserved_bk_copy_by_barcode(db: AsyncSession, barcode: str):
    stmt = select(BookCopy).where(
        BookCopy.copy_barcode == barcode, BookCopy.status == "RESERVED"
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_active_schedule(db: AsyncSession, isbn: str, user_uid: str):
    stmt = (
        select(BkCopySchedule)
        .join(BookCopy, BkCopySchedule.bk_copy_barcode == BookCopy.copy_barcode)
        .where(
            BkCopySchedule.status == "ACTIVE",
            BkCopySchedule.user_uid == user_uid,
            BookCopy.book_isbn == isbn,
        )
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
    await db.flush()


async def get_user_active_loans(db: AsyncSession, user_uid: str):
    stmt = select(Loan).where(
        Loan.user_uid == user_uid, Loan.status == LoanStatus.ACTIVE
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def create_new_book(db: AsyncSession, book: Book):
    db.add(book)
    await db.flush()


async def add_book_copies(db: AsyncSession, copies: list[BookCopy]):
    db.add_all(copies)
    await db.flush()


async def update_book(
    db: AsyncSession,
    book: Book,
    update_data: dict,
):
    for key, value in update_data.items():
        setattr(book, key, value)
    await db.flush()


async def get_bk_copies_by_isbn(db: AsyncSession, isbn: str):
    stmt = select(BookCopy).where(BookCopy.book_isbn == isbn)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_book_copy(db: AsyncSession, isbn: str):
    stmt = select(BookCopy).where(
        BookCopy.book_isbn == isbn, BookCopy.status == "AVAILABLE"
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def get_book_copy_by_barcode(db: AsyncSession, copy_barcode_: str):
    stmt = select(BookCopy).where(BookCopy.copy_barcode == copy_barcode_)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_bk_copy(db: AsyncSession, book_copy: BookCopy, update_data: dict):
    for key, value in update_data.items():
        setattr(book_copy, key, value)
    await db.flush()
    await db.refresh(book_copy)
    return book_copy


async def update_loan(db: AsyncSession, loan: Loan, update_data: dict):
    for key, value in update_data.items():
        setattr(loan, key, value)
    await db.flush()
    await db.refresh(loan)
    return loan


async def get_user_by_email(db: AsyncSession, _email: str):
    stmt = select(User).where(User.email == _email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_new_user(db: AsyncSession, user: User):
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def create_loan(db: AsyncSession, loan: Loan):
    db.add(loan)
    await db.flush()
    await db.refresh(loan)
    return loan


async def get_all_non_staff_users(db: AsyncSession, role: str | None = None):
    if role == "staff":
        stmt = select(User).where(User.is_staff, ~User.is_superuser).order_by(User.id)
    else:
        stmt = select(User).where(~User.is_staff, ~User.is_superuser).order_by(User.id)
    return await apaginate(db, stmt)


async def get_all_books(db: AsyncSession):
    stmt = select(Book).order_by(Book.id)
    return await apaginate(db, stmt)


async def get_all_active_books(
    db: AsyncSession,
    title: str | None = None,
    author: str | None = None,
    isbn: str | None = None,
):
    stmt = select(Book).where(Book.is_active == True)
    if title:
        stmt = stmt.where(Book.title.ilike(f"%{title}%"))
    if author:
        stmt = stmt.where(Book.author.ilike(f"%{author}%"))
    if isbn:
        stmt = stmt.where(Book.isbn == isbn)
    stmt = stmt.order_by(Book.id)
    return await apaginate(db, stmt)


async def get_user_schedules(db: AsyncSession, user_uid: str):
    stmt = (
        select(BkCopySchedule, Book)
        .join(BookCopy, BkCopySchedule.bk_copy_barcode == BookCopy.copy_barcode)
        .join(Book, BookCopy.book_isbn == Book.isbn)
        .where(BkCopySchedule.user_uid == user_uid)
        .order_by(desc(BkCopySchedule.created_at))
    )
    result = await db.execute(stmt)
    return result.all()


async def get_all_active_loans(db: AsyncSession):
    stmt = (
        select(Loan, User, Book)
        .join(User, Loan.user_uid == User.user_uid)
        .join(BookCopy, Loan.bk_copy_barcode == BookCopy.copy_barcode)
        .join(Book, BookCopy.book_isbn == Book.isbn)
        .where(Loan.status == LoanStatus.ACTIVE)
        .order_by(Loan.id)
    )

    async def transform(rows):
        return [
            {
                "loan_id": loan.loan_id,
                "user_uid": loan.user_uid,
                "bk_copy_barcode": loan.bk_copy_barcode,
                "status": loan.status,
                "checked_out_at": loan.checked_out_at,
                "due_at": loan.due_at,
                "book_isbn": book.isbn,
                "book_title": book.title,
                "user_full_name": user.full_name,
                "user_email": user.email,
            }
            for loan, user, book in rows
        ]

    return await apaginate(db, stmt, transformer=transform)


async def get_loan_by_loan_id(db: AsyncSession, _loan_id: str):
    stmt = select(Loan).where(Loan.loan_id == _loan_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_default_superuser(db: AsyncSession, admin_user: User):
    db.add(admin_user)
    await db.flush()


async def update_user(
    db: AsyncSession,
    user: User,
    update_data: dict,
):
    for key, value in update_data.items():
        setattr(user, key, value)
    await db.flush()


async def get_default_superuser(db: AsyncSession, email: str):
    stmt = select(User).where(User.is_staff, User.is_superuser, User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_admin_by_uid_email(db: AsyncSession, email: str, admin_uid: str):
    stmt = select(User).where(
        User.is_staff,
        User.is_superuser,
        User.email == email,
        User.user_uid == admin_uid,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_uid_email(db: AsyncSession, email: str, uid: str):
    stmt = select(User).where(User.email == email, User.user_uid == uid)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int):
    user = await db.get(User, user_id)
    return user


async def get_user_by_uid(db: AsyncSession, user_uid: str):
    stmt = select(User).where(User.user_uid == user_uid)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_schedule(db: AsyncSession, schedule: BkCopySchedule):
    db.add(schedule)
    await db.flush()
    await db.refresh(schedule)
    return schedule


async def add_audit(db: AsyncSession, audit: Audit):
    db.add(audit)
    await db.flush()


async def get_bk_copies(
    db: AsyncSession,
    status: BkCopyStatus | None = None,
    isbn: str | None = None,
):
    stmt = (
        select(BookCopy, Book)
        .join(Book, BookCopy.book_isbn == Book.isbn)
        .order_by(BookCopy.copy_id)
    )
    if status:
        stmt = stmt.where(BookCopy.status == status)
    if isbn:
        stmt = stmt.where(BookCopy.book_isbn == isbn)

    async def transform(rows):
        return [
            {
                "copy_barcode": book_copy.copy_barcode,
                "book_isbn": book.isbn,
                "status": book_copy.status,
                "book_title": book.title,
            }
            for book_copy, book in rows
        ]

    return await apaginate(db, stmt, transformer=transform)


async def get_bk_copies_by_barcode(db: AsyncSession, barcodes: set[str]):
    stmt = select(BookCopy).where(BookCopy.copy_barcode.in_(barcodes))
    result = await db.execute(stmt)
    return result.scalars().all()


async def update_bk_copies_status(
    db: AsyncSession, bk_copies: list[BookCopy], update_data: list[dict]
):
    for i, data in enumerate(update_data):
        for key, value in data.items():
            setattr(bk_copies[i], key, value)
    await db.flush()
