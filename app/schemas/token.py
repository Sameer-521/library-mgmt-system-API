
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenResponse(Token):
    pass


class TokenPayload(BaseModel):
    sub: str | None = None
    exp: str | None = None


class TokenData(BaseModel):
    email: str | None = None
