from pydantic import BaseModel, PositiveInt
from datetime import datetime
from typing import Optional

class BookBase(BaseModel):
    title: str
    author: str
    available: bool = True
    location: str

class BookCreate(BookBase):
    isbn: int

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    available: Optional[bool] = True
    location: Optional[str] = None

class BookResponse(BookBase):
    id: int
    isbn: int
    library_barcode: str
    created_at: datetime
    updated_at: Optional[datetime] = None

class BookCopyForm(BaseModel):
    isbn: PositiveInt
    quantity: PositiveInt