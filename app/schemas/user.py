from pydantic import BaseModel, PositiveInt, ConfigDict, EmailStr, Field
from datetime import datetime
from typing import Optional, List

class UserBase(BaseModel):
    email: EmailStr
    
class UserCreate(UserBase):
    full_name: str = Field(min_length=3, max_length=30)
    password: str = Field(
        min_length=8, 
        max_length=30, 
        pattern=r'^[a-zA-Z0-9_@!]+$'
        )
    
class UserLogin(UserBase):
    password: str #= Field(pattern=r'^[a-zA-Z0-9_@!]*$')

class AdminLogin(UserBase):
    password: str
    admin_uid: str = Field(pattern=r'^ADMIN-[\w-]+')

class UserResponse(UserBase):
    id: PositiveInt
    card_number: str
    is_active: bool
    is_staff: bool
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class UserListResponse(UserBase):
    users: List[UserResponse]

    model_config = ConfigDict(from_attributes=True)