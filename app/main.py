from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi_pagination import add_pagination

from app.core.auth import create_superuser
from app.core.config import settings
from app.core.database import AsyncSessionLocal, Base, engine
from app.core.middleware import AuditMiddleware
from app.routers import auth, books, users
from app.seed import seed_books


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        if not settings.test_mode:
            await create_superuser(session)
        if settings.seed_books:
            await seed_books(session)
    yield
    await engine.dispose()


app = FastAPI(
    lifespan=lifespan,
    openapi_tags=[
        {"name": "auth", "description": "Token issuance / login"},
        {"name": "books", "description": "Book, copy and loan operations"},
        {"name": "users", "description": "User management"},
        {"name": "public", "description": "No authentication required"},
        {"name": "user", "description": "Requires an active user token"},
        {"name": "staff", "description": "Requires a staff token"},
        {"name": "admin", "description": "Requires an admin token"},
    ],
)

audit_enabled = settings.audit_enabled
if audit_enabled is None:
    audit_enabled = not settings.test_mode
if audit_enabled:
    app.add_middleware(AuditMiddleware)

app.include_router(auth.auth_router)
app.include_router(books.books_router)
app.include_router(users.users_router)

add_pagination(app)

_original_openapi = app.openapi


def custom_openapi():
    # avoids regenerating/caching conflicts
    if app.openapi_schema:
        return app.openapi_schema
    schema = _original_openapi()
    schema["components"]["securitySchemes"]["OAuth2PasswordBearer"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi


@app.get("/")
async def root():
    return {"message": "This is the root page"}


# TODO:

# Write tests: ongoing
# add view schedules and active loans endpoint
# Add maintenance utilities
# Implement soft delete functionality or just a seperate endpoint for it
