import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app

async def test_add_book_copies():
    pass

# how do i create a mock form for testing  an endpoint that accepts form data
@pytest.mark.asyncio
async def test_add_book_copies_endpoint(async_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # First, create a new book to add copies to
        book_data = {
            "title": "Test Book",
            "author": "Test Author",
            "isbn": 1234567890,
            "library_barcode": "LB123456"
        }
        response = await ac.post("/books", json=book_data)
        assert response.status_code == 201
        created_book = response.json()
        isbn = created_book["isbn"]

        # Now, add copies to the created book
        add_copies_data = {
            "quantity": 5,
            "isbn": isbn
        }
        response = await ac.post("/books/add_copies/", json=add_copies_data)
        assert response.status_code == 201
        assert response.json() == {"message": "5 copies added successfully."}