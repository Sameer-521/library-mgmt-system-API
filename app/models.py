import string, secrets, enum
from app.core.database import Base
from app.utils import (generate_barcode, generate_library_cardnumber, 
                       generate_loan_id, generate_schedule_id, 
                       default_loan_due_date, generate_user_id)
from sqlalchemy import (String, Integer, DateTime, 
                        Boolean, func, ForeignKey,
                        JSON, Enum)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime

class LoanStatus(enum.Enum):
    ACTIVE = 'active'
    RETURNED = 'returned'
    RETURNED_LATE = 'returned_late'

class Event(enum.Enum):
    CHECKOUT = 'checkout'
    CREATE_BOOK = 'create_book'
    CREATE_BK_COPIES = 'create_bk_copies'
    CREATE_USER = 'create_user'
    FETCH_BOOK = 'fecth_book'
    FETCH_USER = 'fetch_user'
    LOGIN_ADMIN_USER = 'login_admin_user'
    LOGIN_USER = 'login_user'
    RETURN_BOOK = 'return_book'
    SCHEDULE_BOOK = 'schedule_book'
    UPDATE_BOOK = 'update_book'
    UNIDENTIFIED_EVENT = 'unidentified_event' # safety net
    REJECTED_EVENT = 'rejected_event'

class BkCopyStatus(enum.Enum):
    AVAILABLE = 'available'
    LOST = 'lost'
    BORROWED = 'borrowed'
    IN_CHECK = 'in-check'
    RESERVED = 'reserved'

class ScheduleStatus(enum.Enum):
    ACTIVE = 'active'
    CONSUMED = 'consumed'
    EXPIRED = 'expired'
    
class Book(Base):
    __tablename__ = 'books'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    author: Mapped[str] = mapped_column(String(100), nullable=False)
    isbn: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    library_barcode: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, default=generate_barcode)
    available: Mapped[bool] = mapped_column(Boolean, default=True)
    location: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True, onupdate=func.now())

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_uid: Mapped[str] = mapped_column(String(50), unique=True, default=generate_user_id)
    full_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String, nullable=False)
    card_number: Mapped[str] = mapped_column(String(50), unique=True, default=generate_library_cardnumber)
    fine_balance: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    loans = relationship('Loan', back_populates='user')

class Loan(Base):
    __tablename__ = 'loans'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    loan_id: Mapped[str] = mapped_column(String(50), unique=True,default=generate_loan_id)
    user_uid: Mapped[int] = mapped_column(String, ForeignKey('users.user_uid'))
    bk_copy_barcode: Mapped[str] = mapped_column(String, ForeignKey('book_copies.copy_barcode'), index=True)
    status: Mapped[enum.Enum] = mapped_column(Enum(LoanStatus), default=LoanStatus.ACTIVE)
    checked_out_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=default_loan_due_date)
    returned_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    user = relationship('User', back_populates='loans')

class BookCopy(Base):
    __tablename__ = 'book_copies'

    copy_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    book_isbn: Mapped[str] = mapped_column(String(50), ForeignKey('books.isbn'), nullable=False, index=True)
    serial: Mapped[int] = mapped_column(Integer, nullable=False)
    copy_barcode: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[enum.Enum] = mapped_column(Enum(BkCopyStatus), default=BkCopyStatus.AVAILABLE)

    schedule = relationship('BkCopySchedule', back_populates='bk_copy')

class BkCopySchedule(Base):
    __tablename__ = 'bk_copy_schedules'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_uid: Mapped[int] = mapped_column(Integer, ForeignKey('users.user_uid'), nullable=False)
    bk_copy_barcode: Mapped[str] = mapped_column(String(50), ForeignKey('book_copies.copy_barcode'), nullable=False)
    schedule_id: Mapped[str] = mapped_column(String(50), nullable=False, default=generate_schedule_id)
    status: Mapped[enum.Enum] = mapped_column(Enum(ScheduleStatus), default=ScheduleStatus.ACTIVE, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
                                                 server_default=func.now())
    
    bk_copy = relationship('BookCopy', back_populates='schedule')

class Audit(Base):
    __tablename__ = 'audit'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_id: Mapped[str] = mapped_column(String(50), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    event: Mapped[enum.Enum] = mapped_column(Enum(Event), nullable=False)
    details: Mapped[JSON] = mapped_column(JSON, nullable=False)
    audited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
