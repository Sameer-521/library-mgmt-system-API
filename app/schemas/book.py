from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, PositiveInt


class BookBase(BaseModel):
    title: str
    author: str
    available: bool = True
    location: str


class BookCreate(BookBase):
    isbn: str


class BookUpdate(BaseModel):
    title: str | None = None
    author: str | None = None
    available: bool | None = True
    location: str | None = None


class BookResponse(BookBase):
    id: PositiveInt
    isbn: str
    library_barcode: str
    created_at: datetime
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class BookCopyForm(BaseModel):
    isbn: str
    quantity: PositiveInt


class LoanForm(BaseModel):
    user_uid: str
    isbn: str


class LoanBase(BaseModel):
    loan_id: str
    user_uid: str
    bk_copy_barcode: str


class LoanCreate(LoanBase):
    pass


class LoanResponse(LoanBase):
    status: str
    checked_out_at: datetime
    due_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoanModel(BaseModel):
    pass


class LoanReturnForm(BaseModel):
    bk_copy_barcode: str
    loan_id: str


class BkCopyResponse(BaseModel):
    book_isbn: str
    copy_barcode: str
    status: str
    model_config = ConfigDict(from_attributes=True)


class BkCopyLoanResponse(BaseModel):
    loan: LoanResponse
    book_copy: BkCopyResponse
    was_scheduled: bool | None = False
    model_config = ConfigDict(from_attributes=True)


class BkCopyScheduleInfo(BaseModel):
    user_uid: str
    bk_copy_barcode: str
    schedule_id: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class FullScheduleInfo(BaseModel):
    message: str
    note: str
    schedule_info: BkCopyScheduleInfo
    model_config = ConfigDict(from_attributes=True)


class BkCopyUpdate(BaseModel):
    copy_barcode: str
    status: Literal["AVAILABLE", "LOST", "DAMAGED"]


class ListBkUpdate(BaseModel):
    book_copies: list[BkCopyUpdate]


class BkCopyUpdateResponse(BaseModel):
    message: str
    not_found_barcodes: list[str]
    num_not_found: int
    model_config = ConfigDict(from_attributes=True)
