from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request

from app import services
from app.core.database import AsyncSession, get_session
from app.schemas.token import TokenResponse
from app.schemas.user import UserLogin

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/login", response_model=TokenResponse, tags=["public"])
async def login_for_access_token(
    request: Request,
    form_data: Annotated[UserLogin, Form()],
    db: AsyncSession = Depends(get_session),
):
    data = form_data.model_dump()
    request.state.actor = {"email": data["email"]}  # safety net

    token = await services.login_user_service(request, db, data)
    return token
