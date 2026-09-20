import os
from datetime import datetime, timedelta, UTC

import pytest
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("AUDIT_ENABLED", "true")

load_dotenv()

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core import middleware
from app.core.auth import hash_password
from app.core.config import settings
from app.core.database import Base, get_session
from app.main import app
from app.models import Book, User, BookCopy, Loan, BkCopyStatus
from app.utils import generate_book_copy_barcode

mock_admin_email = "mockadmin@example.com"
mock_admin_password = "imjustfortesting"

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

middleware.audit_session_factory = TestAsyncSessionLocal

user_data = {
    "full_name": "Mock User2",
    "email": "mockuser2@gmail.com",
    "password": "mockuser123",
}


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
    data = {**user_data, "password": hash_password(user_data["password"])}
    user = User(**data)
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


@pytest.fixture(scope="function")
async def mock_book_copies(test_session, mock_book) -> tuple[str, list[BookCopy]]:
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
        last_serial += 1
        bk_copies.append(book_copy)
    test_session.add_all(bk_copies)
    await test_session.flush()
    for bk in bk_copies:
        await test_session.refresh(bk)
        refreshed_bk_copies.append(bk)
    return isbn, refreshed_bk_copies


@pytest.fixture(scope="function")
async def mock_loan(test_session, mock_user, mock_book_copies) -> tuple[str, str]:
    isbn, mock_bks = mock_book_copies
    first_bk: BookCopy = mock_bks[0]
    update_bk_data = {"status": BkCopyStatus.BORROWED}
    for key, value in update_bk_data.items():
        setattr(first_bk, key, value)

    await test_session.flush()
    await test_session.refresh(first_bk)

    loan_data = {
        "user_uid": mock_user.user_uid,
        "bk_copy_barcode": first_bk.copy_barcode,
    }
    loan = Loan(**loan_data)
    test_session.add(loan)
    await test_session.flush()
    await test_session.refresh(loan)
    return loan.loan_id, loan.bk_copy_barcode


@pytest.fixture(scope="function")
async def overdue_loan(test_session, mock_user, mock_book_copies) -> tuple[str, str]:
    _, mock_bks = mock_book_copies
    first_bk: BookCopy = mock_bks[0]
    first_bk.status = BkCopyStatus.BORROWED

    await test_session.flush()
    await test_session.refresh(first_bk)

    loan = Loan(
        user_uid=mock_user.user_uid,
        bk_copy_barcode=first_bk.copy_barcode,
        due_at=datetime.now(UTC) - timedelta(days=3),  # now - 3 days
    )
    test_session.add(loan)
    await test_session.flush()
    await test_session.refresh(loan)
    return loan.loan_id, loan.bk_copy_barcode


@pytest.fixture(scope="function")
def book_creation_data():
    return {"title": "mock1", "author": "hitler", "location": "a3", "isbn": "11223344"}


@pytest.fixture(scope="function")
def upload_dir(tmp_path, monkeypatch):
    """
    Redirects profile-pic storage to a throwaway dir so tests never touch
    the real ./uploads tree.
    """
    pics_dir = tmp_path / "profile-pics"
    pics_dir.mkdir()
    monkeypatch.setattr(settings, "base_upload_path", str(tmp_path))
    return pics_dir


@pytest.fixture(scope="function")
async def auth_client(client, mock_user) -> AsyncClient:
    form_data = {
        "email": "mockuser2@gmail.com",
        "password": "mockuser123",
    }
    response = await client.post(f"{BASE_URL}/auth/login", data=form_data)
    data = response.json()
    token = data.get("access_token", None)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture(
    scope="function"
)  # doesnt need to create another admin, a default mock admin is always created for test purposes
async def admin_auth_client(client, mock_admin) -> AsyncClient:
    form_data = {"email": mock_admin_email, "password": mock_admin_password}
    response = await client.post(f"{BASE_URL}/auth/login", data=form_data)
    data = response.json()
    token = data.get("access_token", None)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
