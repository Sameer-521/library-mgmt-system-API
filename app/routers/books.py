from fastapi import APIRouter, status, Depends, Query, Form, Request, Body
from app.schemas.book import (BookCreate, BookResponse,
                               BookUpdate, BookCopyForm, 
                               BkCopyLoanResponse, LoanReturnForm,
                               FullScheduleInfo, LoanForm, ListBkUpdate, BkCopyUpdateResponse)
from app import services
from app.core.database import get_session, AsyncSession
from app.core.auth import get_current_active_user, get_current_staff_user
from app.models import User
from typing import Annotated

books_router = APIRouter(prefix='/books')

@books_router.get('')
async def get_all_books(request: Request):
    return {'books': []}

# tested
@books_router.get('/fetch', response_model=BookResponse)
async def get_book_by_ISBN(
    request: Request,
    isbn: Annotated[int, Query()],
    user_role_exc: tuple=Depends(get_current_active_user),
    db: AsyncSession=Depends(get_session), 
    ):

    current_user, role, exc = user_role_exc
    request.state.exceptions = exc
    book = await services.get_book_by_isbn_service(request, db, isbn)
    return book

# tested
@books_router.post('', status_code=status.HTTP_201_CREATED)
async def create_book(
    request: Request,
    book_create: Annotated[BookCreate, Form()],
    staff_user_exc: tuple=Depends(get_current_staff_user),
    db: AsyncSession=Depends(get_session),
    ):

    staff_user, role, exc = staff_user_exc
    request.state.exceptions = exc
    book_data = book_create.model_dump()
    await services.create_new_book_service(request, db, book_data)
    return {'message': 'Created new book successully'}

# tested
@books_router.put('/{isbn}', status_code=status.HTTP_204_NO_CONTENT)
async def update_book(
    request: Request,
    isbn: int,
    update_data: Annotated[BookUpdate, Form()],
    staff_user_exc: tuple=Depends(get_current_staff_user),
    db: AsyncSession=Depends(get_session),
    ):

    staff_user, role, exc = staff_user_exc
    request.state.exceptions = exc
    book_update_data = update_data.model_dump(exclude_unset=True)
    await services.update_book_service(request, db, book_update_data, isbn, staff_user)

# tested
@books_router.post('/generate-copies', status_code=status.HTTP_201_CREATED)
async def add_book_copies(
    request: Request,
    add_copies_form: Annotated[BookCopyForm, Form()],
    staff_user_exc: tuple=Depends(get_current_staff_user),
    db: AsyncSession=Depends(get_session),
    ):

    staff_user, role, exc = staff_user_exc
    request.state.exceptions = exc
    data = add_copies_form.model_dump()
    message = await services.add_book_copies_service(
        request=request, db=db, **data)
    return message

@books_router.delete('/')
async def delete_book(request: Request):
    pass

@books_router.post('/loan-return')
async def return_book_loan(
    request: Request,
    return_loan_form: Annotated[LoanReturnForm, Form()],
    staff_user_exc: tuple=Depends(get_current_staff_user),
    db: AsyncSession=Depends(get_session),
    ):

    staff_user, role, exc = staff_user_exc
    request.state.exceptions = exc
    data = return_loan_form.model_dump()
    message = await services.return_book_loan_service(
        request, db, data['bk_copy_barcode'], data['loan_id'])
    return message

# tested
@books_router.post('/loan-book', response_model=BkCopyLoanResponse) # update to staff dep.
async def loan_book(
    request: Request,
    form_data: Annotated[LoanForm, Form()],
    staff_user_exc: tuple=Depends(get_current_staff_user),
    db: AsyncSession=Depends(get_session),
    ):

    staff_user, role, exc = staff_user_exc
    request.state.exceptions = exc
    data = form_data.model_dump()
    loan_info = await services.loan_book_service(request, db, **data)
    return loan_info

@books_router.post('/book-schedule/{isbn}', 
response_model=FullScheduleInfo, status_code=status.HTTP_201_CREATED)
async def schedule_book(
    request: Request,
    isbn: int,
    user_role_exc: tuple=Depends(get_current_active_user),
    db: AsyncSession=Depends(get_session),
    ):

    current_user, role, exc = user_role_exc
    request.state.exceptions = exc
    schedule_info = await services.schedule_book_copy_service(
        request, db, isbn, current_user)
    return schedule_info

@books_router.patch('/update-bk-copies-status', response_model=BkCopyUpdateResponse)
async def update_bk_copies(
    request: Request,
    data: ListBkUpdate = Body(),
    staff_user_exc: tuple=Depends(get_current_staff_user),
    db: AsyncSession=Depends(get_session)
    ):

    staff_user, role, exc = staff_user_exc
    request.state.exceptions = exc

    parsed = data.model_dump()
    return await services.update_bk_copies_status(
        request, db, parsed['book_copies'])

# fastapi depends should return a single value, you can unpack 
# after