from fastapi import FastAPI
from app.core.config import Settings
from contextlib import asynccontextmanager
from app.core.middleware import AuditMiddleware
from app.routers import books, users
from app.core.database import engine, Base, AsyncSessionLocal
from app.core.auth import create_superuser

settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        if not settings.test_mode:
            await create_superuser(session)         
    yield
    await engine.dispose()
    
app = FastAPI(lifespan=lifespan)

if not settings.test_mode:
    app.add_middleware(AuditMiddleware)

app.include_router(books.books_router)
app.include_router(users.users_router)

@app.get('/')
async def root():
    return {'message': 'This is the root page'}

# TODO:

# Write tests: ongoing
# add view schedules and active loans endpoint
# Add maintenance utilities
# Implement soft delete functionality or just a seperate endpoint for it