from datetime import timedelta, datetime, timezone
from fastapi import HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app import crud
from app.utils import (generate_book_copy_barcode, generate_staff_id,
                       reraise_exceptions, safe_datetime_compare)
from app.models import (BkCopySchedule, Book, BookCopy,
                        User, BkCopyStatus, Loan, ScheduleStatus, 
                        Audit, Event, LoanStatus)
from app.core.auth import authenticate_user, create_access_token, hash_password, authenticate_admin
from app.core.config import Settings
from typing import Optional
from logging import Logger

logger = Logger(__name__)

settings=Settings()

loan_eligibility_exception = HTTPException(
    status.HTTP_403_FORBIDDEN,
    detail='User is not eligble for anymore loans'
)

schd_eligibility_exception = HTTPException(
    status.HTTP_403_FORBIDDEN,
    detail='User is not eligble for anymore schedules'
)

book_not_found_exception = HTTPException(
    status.HTTP_404_NOT_FOUND,
    detail='Book not found'
)

user_not_found_exception = HTTPException(
    status.HTTP_404_NOT_FOUND,
    detail='User not found'
)

internal_error_exception = HTTPException(
    status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail='An internal error occured'
)

book_integrity_exception = HTTPException(
    status.HTTP_409_CONFLICT,
    detail='Book with this title or ISBN already exists'
)

user_integrity_exception = HTTPException(
    status.HTTP_409_CONFLICT,
    detail='User with this email already exists'
)

book_copy_integrity_exception = HTTPException(
    status.HTTP_409_CONFLICT,
    detail='Error creating book copies'
)

# tested
async def create_new_book_service(
        request: Request, 
        db: AsyncSession, 
        book_data: dict,
        ):
    try:
        reraise_exceptions(request)
        book = Book(**book_data)
        await crud.create_new_book(db, book)
        logger.info(f'New book created: {book_data['title']}')
    except IntegrityError as e:
        logger.warning(f'Integrity error creating book: {e}')
        raise book_integrity_exception
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f'DataBase error creating new book: {e}')
        await db.rollback()   
        raise internal_error_exception
    else:
        await db.commit()

# tested
async def get_book_by_isbn_service(
    request: Request,
    db: AsyncSession, 
    isbn: int
    ):
    try:
        reraise_exceptions(request)
        book = await crud.get_book_by_isbn(db, isbn)
        if not book:
            raise book_not_found_exception
        
        logger.info(f'Retrieved book: {book.library_barcode}')
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f'DataBase error retrieving book: {e}')
        await db.rollback()
        raise internal_error_exception
    else:
        return book

#tested  
async def update_book_service(
    request: Request,
    db: AsyncSession,
    update_data: dict,
    isbn: int,
    current_user: User
    ):
    try:
        reraise_exceptions(request)
        book = await crud.get_book_by_isbn(db, isbn)
        if not book:
            raise book_not_found_exception
        await crud.update_book(db, book, update_data)
        logger.info(f'Book-{book.library_barcode} updated')
    except IntegrityError as e:
        await db.rollback()
        logger.warning(f'Integrity error updating book: {e}')
        raise book_integrity_exception
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f'DataBase error updating book: {e}')
        await db.rollback()
        raise internal_error_exception
    else:
        await db.commit()
        request.state.msg = {'message': f'Book-{book.library_barcode} updated, fields updated: {list(update_data.keys())}'}
        return current_user

# tested
async def add_book_copies_service(
        request: Request,
        db: AsyncSession, 
        quantity: int, 
        isbn: int,
        ):
    try:
        reraise_exceptions(request)
        book_copies = []
        last_serial = 0
        book = await crud.get_book_by_isbn(db, isbn)
        if not book:
            raise book_not_found_exception
        book_lib_barcode = str(book.library_barcode)
        # get last bookcopy where isbn == book.isbn
        last_book_copy = await crud.get_last_book_copy(db, book)
        if last_book_copy:
            last_serial = last_book_copy.serial
        for i in range(quantity):
            bk_copy_serial = last_serial+1
            barcode = generate_book_copy_barcode(book_lib_barcode, bk_copy_serial)
            book_copy = BookCopy(book_isbn=isbn, serial=bk_copy_serial, copy_barcode=barcode)
            book_copies.append(book_copy)
            last_serial+=1
        await crud.add_book_copies(db, book_copies)
        logger.info(f'Created {quantity} copies of {isbn}')
    except IntegrityError as e:
        await db.rollback()
        logger.warning(f'Integrity error creating book copies: {e}')
        raise book_integrity_exception
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f'DataBase error adding book copies: {e}')
        await db.rollback()
        raise internal_error_exception
    else:
        await db.commit()
        msg = {
            'message': f'{quantity} copies of ISBN-{isbn} were created successfully'}
        request.state.msg = msg
        return msg

# tested   
async def loan_book_service(
    request: Request,
    db: AsyncSession,
    isbn: int,
    user_uid: str
    ):
    created_loan = None
    updated_bk_copy = None
    try:
        user = await crud.get_user_by_uid(db, user_uid)
        if not user:
            raise user_not_found_exception
        bk_schedule_is_available = False # determines which return is used depending on if bk_schedule is None
        user_loans = await crud.get_user_active_loans(db, user.user_uid)
        if (len(user_loans) >= 3) or (user.fine_balance >= 10): # been a bit easy here
            raise loan_eligibility_exception
        
        bk_schedule = await crud.get_active_schedule(db, isbn, user.user_uid) # returns first record
        if bk_schedule:
            reserved_bk_copy = await crud.get_reserved_bk_copy_by_barcode(db, bk_schedule.bk_copy_barcode)
            if not reserved_bk_copy:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND,
                    detail='Scheduled book copy not found'
                )
            if reserved_bk_copy.status != BkCopyStatus.RESERVED:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    detail='Scheduled book copy is not available'
                )
            loan_data = {
            'user_uid': user.user_uid,
            'bk_copy_barcode': reserved_bk_copy.copy_barcode
            }
            loan = Loan(**loan_data)
            created_loan = await crud.create_loan(db, loan)
            updated_bk_copy = await crud.update_bk_copy(
                db, reserved_bk_copy, {'status': BkCopyStatus.BORROWED})
            await crud.update_bk_schedule(db, bk_schedule, {'status': ScheduleStatus.CONSUMED})
            logger.info('Retrieved scheduled book copy')
            bk_schedule_is_available = True
        
        if not bk_schedule_is_available:
            book_copy = await crud.get_book_copy(db, isbn)
            if not book_copy:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND,
                    detail=f'There are no available copies of ISBN-{isbn} currently and user does not have any active schedules'
                )
            loan_data = {
                'user_uid': user.user_uid,
                'bk_copy_barcode': book_copy.copy_barcode
            }

            loan = Loan(**loan_data)
            created_loan = await crud.create_loan(db, loan)
            updated_bk_copy = await crud.update_bk_copy(
                db, book_copy, {'status': BkCopyStatus.BORROWED})

            logger.info('Retrieved book copy')
    except IntegrityError as e:
        logger.warning(f'Integrity error fetching book_copy: {e}')
        await db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail='Loan with this id already exists'
        )
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f'DataBase error fetching book_copy: {e}')
        await db.rollback()
        raise internal_error_exception
    else:
        await db.commit()
        if bk_schedule_is_available:
            return {
                'loan': created_loan,
                'book_copy': updated_bk_copy, 
                'was_scheduled': True}
        return {'loan': created_loan, 
                'book_copy': updated_bk_copy,
                'was_scheduled': False}

# tested 
async def create_user_service(
    request: Request,
    db: AsyncSession,
    user_data: dict,
    ):
    try:
        #reraise_exceptions(request)
        data = user_data.copy()
        data['password'] = hash_password(data['password'])
        user = await crud.create_new_user(db, User(**data))
        request.state.actor = user
        logger.info('Created new user successfully')
        
    except IntegrityError as e:
        logger.warning(f'Integrity error creating new user: {e}')
        raise user_integrity_exception
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f'DataBase error creating user: {e}')
        await db.rollback()
        raise internal_error_exception # update exceptions
    else:
        await db.commit()
        return {'message': 'User created successfully',
                'user_uid': user.user_uid}

# tested  
async def login_user_service(
    request: Request,
    db: AsyncSession,
    user_data: dict,
    is_admin: Optional[bool] = False
    ):
    try:
        token = None
        ACCESS_TOKEN_EXPIRE_MINUTES = timedelta(minutes=settings.access_token_expire_minutes)
        if is_admin:
            user, exc = await authenticate_admin(user_data, db)
        else:
            user, exc = await authenticate_user(user_data, db)
        request.state.actor = user
        if exc:
            raise exc[0]
        if user:
            data = {'sub': user.email, 'user_uid': user.user_uid, 'is_staff': user.is_staff}
            token = create_access_token(data, ACCESS_TOKEN_EXPIRE_MINUTES) 
    except HTTPException:
        await db.rollback()
        raise
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f'DataBase error reading user: {e}')
        raise internal_error_exception
    else:
        await db.commit()
        return {'access_token': token, 'token_type': 'bearer'}
    
async def get_all_non_staff_users_service(
    request: Request,
    db: AsyncSession,
    ):
    try:
        reraise_exceptions(request)
        users = await crud.get_all_non_staff_users(db)
        return users
    except HTTPException:
        await db.rollback()
        raise
    except SQLAlchemyError as e:
        await db.rollback() # is rollback even necessary here?
        logger.error(f'DataBase error fetching users: {e}')
        raise internal_error_exception

async def return_book_loan_service(
    request: Request,
    db: AsyncSession,
    bk_copy_barcode_: str,
    loan_id: str,
    ):
    try:
        reraise_exceptions(request)
        fined: bool = False
        fine_fee: int = 0
        days_deltas: int = 0
        loan = await crud.get_loan_by_id(db, loan_id)
        if not loan:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail='Loan not found'
            )
        
        # I'll fix this later
        if bk_copy_barcode_ != loan.bk_copy_barcode:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail='Book-copy-barcode not the same as stated by loan'
            )
        
        book_returned = await crud.get_book_copy_by_barcode(db, bk_copy_barcode_)
        if not book_returned:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail='Book copy not found'
            )
        if book_returned.status != BkCopyStatus.BORROWED:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail='This book copy is not currently on loan'
            )
        updated_bk_copy = await crud.update_bk_copy(
            db, book_returned, {'status': BkCopyStatus.IN_CHECK})
        
        returned_at = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0) # + timedelta(days=14)
        loan_status = LoanStatus.RETURNED
        if safe_datetime_compare(returned_at, loan.due_at): # overdue
            loan_status = LoanStatus.RETURNED_LATE
            days_deltas = (returned_at.date() - loan.due_at.date()).days
            fine = 100 * days_deltas
            fine_fee = fine
            fined = True
            user = await crud.get_user_by_id(db, loan.user_id)
            if not user:
                raise user_not_found_exception
            updated_fine = fine + user.fine_balance
            await crud.update_user(db, user, update_data={'fine_balance': updated_fine})

        loan_data = {
            'status': loan_status,
            'returned_at': returned_at
            }
        await crud.update_loan(db, loan, loan_data) 
    except HTTPException:
        await db.rollback()
        raise
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f'DataBase error clearing loan: {e}')
        raise internal_error_exception
    else:
        await db.commit()
        return {
            'message': 'User loan cleared, you have also been fined for delay',
            'delay time': f'{days_deltas} days',
            'fine': f'{fine_fee}'
            } if fined else {
                'message': 'User loan cleared, awaiting staff inspection'}

# tested    
async def schedule_book_copy_service(
    request: Request,
    db: AsyncSession,
    isbn: int,
    current_user: User
    ):
    try:
        reraise_exceptions(request)
        user_loans = await crud.get_user_active_loans(db, current_user.user_uid)
        if (len(user_loans) >= 3) or (current_user.fine_balance >= 10):
            raise schd_eligibility_exception
        
        book_copy = await crud.get_book_copy(db, isbn)
        if not book_copy:
            raise book_not_found_exception
        
        await crud.update_bk_copy(db, book_copy, update_data={'status': BkCopyStatus.RESERVED})
        schedule_data = {
            'user_uid': current_user.user_uid,
            'bk_copy_barcode': book_copy.copy_barcode
        }
        schedule = await crud.create_schedule(db, BkCopySchedule(**schedule_data))
    except IntegrityError as e:
        await db.rollback()
        logger.warning(f'Integrity error creating schedule: {e}')
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail='Integrity error creating schedule'
        )
    except HTTPException:
        await db.rollback()
        raise
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f'DataBase error creating book copy schedule: {e}')
        raise internal_error_exception
    else:
        await db.commit()
        return {
            'message': 'Schedule has been successfuly created',
            'note': 'All schedules that have\'nt been consumed will be cleared by 6pm',
            'schedule_info': schedule
        }

async def create_audit_service(
        db: AsyncSession,
        details: dict
    ):
    try:
        audit = Audit(**details)
        await crud.add_audit(db, audit)
    except HTTPException:
        await db.rollback()
        raise
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f'DataBase error creating audit: {e}')
        raise internal_error_exception
    else:
        await db.commit()

async def create_staff_user_service(
    request: Request,
    db: AsyncSession,
    user_data: dict,
    ):
    try:
        reraise_exceptions(request)
        data = user_data.copy()
        data['password'] = hash_password(data['password'])
        data['user_uid'] = generate_staff_id()
        user = await crud.create_new_user(db, User(**data))
        logger.info('Created new staff user successfully')
        
    except IntegrityError as e:
        logger.warning(f'Integrity error creating new staff user: {e}')
        raise user_integrity_exception
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f'DataBase error creating staff user: {e}')
        await db.rollback()
        raise internal_error_exception # update exceptions
    else:
        await db.commit()
        msg = {'message': 'Staff user created successfully',
                'user_uid': user.user_uid}
        request.state.msg = msg
        return msg