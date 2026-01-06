from fastapi import APIRouter, status, Depends, Query, Form, BackgroundTasks, Request
from app import services
from app.core.auth import get_current_staff_user, get_current_admin_user
from app.core.config import Settings
from app.core.database import get_session, AsyncSession
from typing import Annotated
from app.schemas.token import TokenResponse, Token
from app.schemas.user import UserCreate, UserLogin, UserListResponse
from app.models import User


users_router = APIRouter(prefix='/users')

@users_router.get('', response_model=UserListResponse)
async def get_all_non_staff_users(
    request: Request,
    staff_user_exc: tuple=Depends(get_current_staff_user),
    db: AsyncSession=Depends(get_session),
    ):
    
    staff_user, exc = staff_user_exc
    request.state.exceptions = exc
    users = await services.get_all_non_staff_users_service(request, db)
    return users

@users_router.post('/create-staff-user')
async def create_new_staff_user(
    request: Request,
    form_data: Annotated[UserCreate, Form()],
    admin_user_exc: tuple=Depends(get_current_admin_user),
    db: AsyncSession=Depends(get_session)
    ):
    admin_user, role, exc = admin_user_exc
    request.state.exceptions = exc

    data = form_data.model_dump()
    msg = await services.create_staff_user_service(request, db, data)
    return msg


@users_router.post('/sign-up', status_code=status.HTTP_201_CREATED)
async def create_new_user(
    request: Request,
    form_data: Annotated[UserCreate, Form()],
    db: AsyncSession=Depends(get_session)
    ):

    data = form_data.model_dump()
    request.state.actor = {'email': data['email']} #safety net

    msg = await services.create_user_service(request, db, form_data.model_dump())
    return msg

@users_router.post('/login', response_model=TokenResponse)
async def login_for_access_token(
    request: Request,
    form_data: Annotated[UserLogin, Form()],
    db: AsyncSession=Depends(get_session)
    ):

    data = form_data.model_dump()
    request.state.actor = {'email': data['email']} #safety net

    token = await services.login_user_service(request, db, form_data.model_dump()) 
    return token

@users_router.post('/admin/login', response_model=TokenResponse)
async def admin_login_for_access_token(
    request: Request,
    form_data: Annotated[UserLogin, Form()],
    db: AsyncSession=Depends(get_session)
    ):

    data = form_data.model_dump()
    request.state.actor = {'email': data['email']} #safety net

    token = await services.login_user_service(request, db, form_data.model_dump()) 
    return token

# Note: You can inject request object in dependency signature