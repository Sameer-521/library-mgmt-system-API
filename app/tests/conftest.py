# ruff: noqa: E402
import os

import pytest
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from typing import List

load_dotenv()

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.auth import hash_password
from app.core.config import Settings
from app.core.database import Base, get_session
from app.main import app
from app.models import Book, User, BookCopy
from app.utils import generate_book_copy_barcode

settings = Settings()

mock_admin_email = os.getenv("MOCK_ADMIN_EMAIL")
mock_admin_password = os.getenv("MOCK_ADMIN_PASSWORD")

mock_user_email = os.getenv("MOCK_USER_EMAIL")
mock_user_password = os.getenv("MOCK_USER_PASSWORD")

BASE_URL = "http://127.0.0.1:8000"
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DB_URL, echo=True, future=True)

TestAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="function")
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest.fixture(scope="function")
async def test_session(setup_db):
    async with TestAsyncSessionLocal() as session:
        yield session


@pytest.fixture(scope="function")
async def client(test_session):
    async def override_get_session():
        yield test_session

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def mock_admin(test_session):
    if mock_admin_password:
        user_data = {
            "full_name": "Mock Admin",
            "email": mock_admin_email,
            "password": hash_password(mock_admin_password),
            "is_staff": True,
            "is_superuser": True,
        }
        admin_user = User(**user_data)
        test_session.add(admin_user)
        await test_session.flush()
        await test_session.refresh(admin_user)
        return admin_user


@pytest.fixture(scope="function")
async def mock_user(test_session):
    user_data = {
        "full_name": "Mock User2",
        "email": "mockuser2@gmail.com",
        "password": "mockuser123",
    }
    user = User(**user_data)
    test_session.add(user)
    await test_session.flush()
    await test_session.refresh(user)
    return user


@pytest.fixture(scope="function")
async def mock_book(test_session, book_creation_data):
    book = Book(**book_creation_data)
    test_session.add(book)
    await test_session.flush()
    await test_session.refresh(book)
    return book


# @pytest.fixture(scope="function")
# async def mock_schedule(
#     test_session, mock_user, mock_book_copies
# ) -> (BkCopySchedule, str):
#     isbn, bk_copies = mock_book_copies
#     schedule_data = {
#         "user_uid": mock_user.user_uid,
#         "bk_copy_barcode": bk_copy.copy_barcode,
#     }
#     schedule = BkCopySchedule(**schedule_data)
#     test_session.add(schedule)
#     await test_session.flush()
#     await test_session.refresh(schedule)
#     return schedule, isbn


@pytest.fixture(scope="function")
async def mock_book_copies(test_session, mock_book) -> (str, List[BookCopy]):
    """
    Adds `number_of_bk_copies`of mock book_copies and returns the original isbn used and a list of book copy instances
    """
    number_of_bk_copies = 5
    isbn = mock_book.isbn
    org_book_barcode = mock_book.library_barcode
    bk_copies = []
    refreshed_bk_copies = []
    last_serial = 0
    for i in range(number_of_bk_copies):
        bk_copy_serial = last_serial + 1
        cp_barcode = generate_book_copy_barcode(org_book_barcode, bk_copy_serial)
        book_copy = BookCopy(
            book_isbn=isbn, serial=bk_copy_serial, copy_barcode=cp_barcode
        )
        bk_copies.append(book_copy)
    test_session.add_all(bk_copies)
    await test_session.flush()
    for bk in bk_copies:
        await test_session.refresh(bk)
        refreshed_bk_copies.append(bk)
    return isbn, refreshed_bk_copies


@pytest.fixture(scope="function")
def book_creation_data():
    return {"title": "mock1", "author": "hitler", "location": "a3", "isbn": "11223344"}


@pytest.fixture(scope="function")
async def auth_client(client, mock_user) -> AsyncClient:
    form_data = {
        "email": "mockuser2@gmail.com",
        "password": "mockuser123",
    }
    response = await client.post(f"{BASE_URL}/users/login", data=form_data)
    data = response.json()
    token = data.get("access_token", None)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture(
    scope="function"
)  # doesnt need to create another admin, a default mock admin is always created for test purposes
async def admin_auth_client(client, mock_admin) -> AsyncClient:
    form_data = {"email": mock_admin_email, "password": mock_admin_password}
    response = await client.post(f"{BASE_URL}/users/login", data=form_data)
    data = response.json()
    token = data.get("access_token", None)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
