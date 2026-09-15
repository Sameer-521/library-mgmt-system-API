from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenResponse(Token):
    pass


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[str] = None


class TokenData(BaseModel):
    email: Optional[str] = None
