from email.policy import HTTP
from fastapi import HTTPException, status
import sqlalchemy
from app import crud
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.models import Book, BookCopy
from logging import Logger

logger = Logger(__name__)

book_not_found_exception = HTTPException(
    status.HTTP_404_NOT_FOUND,
    detail='Book not found'
)

internal_error_exception = HTTPException(
    status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail='An internal error occured'
)

book_integrity_exception = HTTPException(
    status.HTTP_409_CONFLICT,
    detail='Book with this title or ISBN already exists'
)

book_copy_integrity_exception = HTTPException(
    status.HTTP_409_CONFLICT,
    detail='Error creating book copies'
)

def generate_book_copy_barcode(base_barcode: str, serial: int):
    str_serial = str(serial).zfill(3)
    return f'COPY-{base_barcode}-{str_serial}'

async def create_new_book_service(db: AsyncSession, book_data: dict):
    try:
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

async def get_book_by_isbn_service(
        db: AsyncSession, 
        isbn: int):
    try:
        book = await crud.get_book_by_isbn(db, isbn)
        if not book:
            raise book_not_found_exception
        
        logger.info(f'Retrieved book: {book.library_barcode}')
        return book
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f'DataBase error retrieving book: {e}')
        await db.rollback()
        raise internal_error_exception
    
async def update_book_service(
        db: AsyncSession,
        update_data: dict,
        isbn: int):
    try:
        book = await crud.get_book_by_isbn(db, isbn)
        if not book:
            raise book_not_found_exception
        await crud.update_book(db, book, update_data, isbn)
        logger.info(f'Book-{book.library_barcode} updated')
    except IntegrityError as e:
        logger.warning(f'Integrity error updating book: {e}')
        raise book_integrity_exception
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f'DataBase error updating book: {e}')
        await db.rollback()
        raise internal_error_exception

async def add_book_copies_service(db: AsyncSession, quantity: int, isbn: int):
    try:
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
        return {'message': 'copies created successfully'}
    except IntegrityError as e:
        logger.warning(f'Integrity error creating book copies: {e}')
        raise book_integrity_exception
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f'DataBase error adding book copies: {e}')
        await db.rollback()
        raise internal_error_exception