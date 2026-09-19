from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi_pagination import LimitOffsetPage

from app import services
from app.core.auth import get_current_admin_user, get_current_staff_user
from app.core.database import AsyncSession, get_session
from app.models import User
from app.schemas.user import UserCreate, UserResponse

users_router = APIRouter(prefix="/users", tags=["users"])


#
# decide to keep it or not later
@users_router.get("", response_model=LimitOffsetPage[UserResponse], tags=["staff"])
async def get_all_non_staff_users(
    request: Request,
    role: Annotated[Literal["staff"] | None, Query()] = None,
    staff_user: User = Depends(get_current_staff_user),
    db: AsyncSession = Depends(get_session),
):
    if role == "staff" and not staff_user.is_superuser:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Not enough privileges")
    return await services.get_all_non_staff_users_service(request, db, role)


@users_router.post("/create-staff-user", tags=["admin"])
async def create_new_staff_user(
    request: Request,
    form_data: Annotated[UserCreate, Form()],
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_session),
):
    data = form_data.model_dump()
    return await services.create_staff_user_service(request, db, data)


@users_router.post("/sign-up", status_code=status.HTTP_201_CREATED, tags=["public"])
async def create_new_user(
    request: Request,
    form_data: Annotated[UserCreate, Form()],
    db: AsyncSession = Depends(get_session),
):
    data = form_data.model_dump()
    request.state.actor = {"email": data["email"]}  # safety net

    return await services.create_user_service(request, db, form_data.model_dump())


# Note: You can inject request object in dependency signature
