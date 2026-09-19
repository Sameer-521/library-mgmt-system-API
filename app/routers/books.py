from typing import Annotated

from fastapi import APIRouter, Body, Depends, Form, Query, Request, status
from fastapi_pagination import LimitOffsetPage
from starlette.status import HTTP_204_NO_CONTENT

from app import services
from app.core.auth import (
    get_current_active_user,
    get_current_admin_user,
    get_current_staff_user,
)
from app.core.database import AsyncSession, get_session
from app.models import BkCopyStatus, User
from app.schemas.book import (
    ActiveLoanItem,
    BkCopyItem,
    BkCopyLoanResponse,
    BkCopyScheduleInfo,
    BkCopyUpdateResponse,
    BookCopyForm,
    BookCreate,
    BookResponse,
    BookUpdate,
    FullScheduleInfo,
    ListBkUpdate,
    LoanForm,
    LoanResponse,
    LoanReturnForm,
)

books_router = APIRouter(prefix="/books", tags=["books"])


@books_router.get("", response_model=LimitOffsetPage[BookResponse], tags=["user"])
async def get_all_books(
    request: Request,
    title: Annotated[str | None, Query()] = None,
    author: Annotated[str | None, Query()] = None,
    isbn: Annotated[str | None, Query()] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
):
    return await services.get_all_books_service(request, db, title, author, isbn)


# tested
@books_router.get("/fetch", response_model=BookResponse, tags=["user"])
async def get_book_by_ISBN(
    request: Request,
    isbn: Annotated[str, Query()],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
):
    book = await services.get_book_by_isbn_service(request, db, isbn)
    return book


# tested
@books_router.post("", status_code=status.HTTP_201_CREATED, tags=["staff"])
async def create_book(
    request: Request,
    book_create: Annotated[BookCreate, Form()],
    staff_user: User = Depends(get_current_staff_user),
    db: AsyncSession = Depends(get_session),
):
    book_data = book_create.model_dump()
    await services.create_new_book_service(request, db, book_data)
    return {"message": "Created new book successully"}


# tested
@books_router.put("/{isbn}", status_code=status.HTTP_204_NO_CONTENT, tags=["staff"])
async def update_book(
    request: Request,
    isbn: str,
    update_data: Annotated[BookUpdate, Form()],
    staff_user: User = Depends(get_current_staff_user),
    db: AsyncSession = Depends(get_session),
):
    book_update_data = update_data.model_dump(exclude_unset=True)
    await services.update_book_service(request, db, book_update_data, isbn, staff_user)


# tested
@books_router.post(
    "/generate-copies", status_code=status.HTTP_201_CREATED, tags=["staff"]
)
async def add_book_copies(
    request: Request,
    add_copies_form: Annotated[BookCopyForm, Form()],
    staff_user: User = Depends(get_current_staff_user),
    db: AsyncSession = Depends(get_session),
):
    data = add_copies_form.model_dump()
    message = await services.add_book_copies_service(request=request, db=db, **data)
    return message


@books_router.delete("/{isbn}", status_code=HTTP_204_NO_CONTENT, tags=["admin"])
async def delete_book(
    request: Request,
    isbn: str,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_session),
):
    await services.soft_delete_book_by_isbn_service(request, db, isbn)


@books_router.post("/loan-return", tags=["staff"])
async def return_book_loan(
    request: Request,
    return_loan_form: Annotated[LoanReturnForm, Form()],
    staff_user: User = Depends(get_current_staff_user),
    db: AsyncSession = Depends(get_session),
):
    data = return_loan_form.model_dump()
    message = await services.return_book_loan_service(
        request, db, data["bk_copy_barcode"], data["loan_id"]
    )
    return message


# tested
@books_router.post(
    "/loan-book",
    response_model=BkCopyLoanResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["staff"],
)
async def loan_book(
    request: Request,
    form_data: Annotated[LoanForm, Form()],
    staff_user: User = Depends(get_current_staff_user),
    db: AsyncSession = Depends(get_session),
):
    data = form_data.model_dump()
    loan_info = await services.loan_book_service(request, db, **data)
    return loan_info


@books_router.post(
    "/schedule-book",
    response_model=FullScheduleInfo,
    status_code=status.HTTP_201_CREATED,
    tags=["user"],
)
async def schedule_book(
    request: Request,
    isbn: Annotated[str, Query()],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
):
    schedule_info = await services.schedule_book_copy_service(
        request, db, isbn, current_user
    )
    return schedule_info


@books_router.get(
    "/bk-copies", response_model=LimitOffsetPage[BkCopyItem], tags=["staff"]
)
async def get_bk_copies(
    request: Request,
    status: Annotated[BkCopyStatus | None, Query()] = None,
    isbn: Annotated[str | None, Query()] = None,
    staff_user: User = Depends(get_current_staff_user),
    db: AsyncSession = Depends(get_session),
):
    return await services.get_bk_copies_service(request, db, status, isbn)


@books_router.patch("/bk-copies", response_model=BkCopyUpdateResponse, tags=["staff"])
async def update_bk_copies(
    request: Request,
    data: ListBkUpdate = Body(),
    staff_user: User = Depends(get_current_staff_user),
    db: AsyncSession = Depends(get_session),
):
    parsed = data.model_dump()
    return await services.update_bk_copies_status(request, db, parsed["book_copies"])


@books_router.get(
    "/schedules/me", response_model=list[BkCopyScheduleInfo], tags=["user"]
)
async def get_user_schedules(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
):
    return await services.get_user_schedules_service(request, db, current_user.user_uid)


@books_router.get(
    "/loans/active", response_model=LimitOffsetPage[ActiveLoanItem], tags=["staff"]
)
async def get_active_loans(
    request: Request,
    staff_user: User = Depends(get_current_staff_user),
    db: AsyncSession = Depends(get_session),
):
    return await services.get_all_active_loans_service(request, db)


# fastapi depends should return a single value, you can unpack
# after
