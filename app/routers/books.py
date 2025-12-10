from fastapi import APIRouter, status, Depends, Query, Form
from app.schemas import BookCreate, BookResponse, BookUpdate, BookCopyForm
from app import services
from app.database import get_session, AsyncSession
from typing import Annotated

books_router = APIRouter(prefix='/books')

@books_router.get('')
async def get_all_books():
    return {'books': []}

@books_router.get('/', response_model=BookResponse)
async def get_book_by_ISBN(
    isbn: Annotated[int, Query()], #search whether you need a '/' for query params
    db: AsyncSession=Depends(get_session)
    ):
    book = await services.get_book_by_isbn_service(db, isbn)
    return book

@books_router.post('', status_code=status.HTTP_201_CREATED)
async def create_book(
    book_create: Annotated[BookCreate, Form()],
    db: AsyncSession=Depends(get_session)
    ):
    book_data = book_create.model_dump()
    await services.create_new_book_service(db, book_data)
    return {'message': 'Created new book successully'}

@books_router.put('/{isbn}', status_code=status.HTTP_204_NO_CONTENT)
async def update_book(
    isbn: int,
    update_data: Annotated[BookUpdate, Form()],
    db: AsyncSession=Depends(get_session)
    ):
    book_update_data = update_data.model_dump(exclude_unset=True)
    await services.update_book_service(db, book_update_data, isbn)

@books_router.post('/generate-copies', status_code=status.HTTP_201_CREATED)
async def add_book_copies(
    add_copies_form: Annotated[BookCopyForm, Form()],
    db: AsyncSession=Depends(get_session)
    ):
    data = add_copies_form.model_dump()
    message = await services.add_book_copies_service(db, **data)
    return message

@books_router.delete('/')
async def delete_book():
    pass
