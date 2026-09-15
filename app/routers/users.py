from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, status

from app import services
from app.core.auth import get_current_admin_user, get_current_staff_user
from app.core.database import AsyncSession, get_session
from app.models import User
from app.schemas.token import TokenResponse
from app.schemas.user import UserCreate, UserListResponse, UserLogin, UserResponse

users_router = APIRouter(prefix="/users")


#
# decide to keep it or not later
@users_router.get("", response_model=UserListResponse)
async def get_all_non_staff_users(
    request: Request,
    staff_user: User = Depends(get_current_staff_user),
    db: AsyncSession = Depends(get_session),
):
    users = await services.get_all_non_staff_users_service(request, db)
    return UserListResponse(users=[UserResponse.model_validate(u) for u in users])


@users_router.post("/create-staff-user")
async def create_new_staff_user(
    request: Request,
    form_data: Annotated[UserCreate, Form()],
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_session),
):
    data = form_data.model_dump()
    msg = await services.create_staff_user_service(request, db, data)
    return msg


@users_router.post("/sign-up", status_code=status.HTTP_201_CREATED)
async def create_new_user(
    request: Request,
    form_data: Annotated[UserCreate, Form()],
    db: AsyncSession = Depends(get_session),
):
    data = form_data.model_dump()
    request.state.actor = {"email": data["email"]}  # safety net

    msg = await services.create_user_service(request, db, form_data.model_dump())
    return msg


@users_router.post("/login", response_model=TokenResponse)
async def login_for_access_token(
    request: Request,
    form_data: Annotated[UserLogin, Form()],
    db: AsyncSession = Depends(get_session),
):
    data = form_data.model_dump()
    request.state.actor = {"email": data["email"]}  # safety net

    token = await services.login_user_service(request, db, form_data.model_dump())
    return token


@users_router.post("/admin/login", response_model=TokenResponse)
async def admin_login_for_access_token(
    request: Request,
    form_data: Annotated[UserLogin, Form()],
    db: AsyncSession = Depends(get_session),
):
    data = form_data.model_dump()
    request.state.actor = {"email": data["email"]}  # safety net

    token = await services.login_user_service(request, db, form_data.model_dump())
    return token


# Note: You can inject request object in dependency signature
