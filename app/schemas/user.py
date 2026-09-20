from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    full_name: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=8, max_length=30, pattern=r"^[a-zA-Z0-9_@!]+$")


class UserLogin(UserBase):
    password: str  # = Field(pattern=r'^[a-zA-Z0-9_@!]*$')


class UserResponse(UserBase):
    user_uid: str
    full_name: str
    card_number: str
    is_active: bool
    # is_staff: bool
    # is_superuser: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(UserResponse):
    fine_balance: int
    profile_picture_url: str | None = None


class ProfilePicResponse(BaseModel):
    profile_picture_url: str
