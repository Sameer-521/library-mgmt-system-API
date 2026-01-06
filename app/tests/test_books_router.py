import pytest

@pytest.mark.anyio
async def test_book_creation(admin_auth_client, book_creation_data):
    form_data = book_creation_data
    response = await admin_auth_client.post(
        f'{admin_auth_client.base_url}/books', data=form_data)
    assert response.status_code == 201
    # confirm creation
    response = await admin_auth_client.post(
        f'{admin_auth_client.base_url}/books', data=form_data)
    assert response.status_code == 409

@pytest.mark.anyio
async def test_get_created_book(auth_client, mock_book):
    isbn = mock_book.isbn
    response = await auth_client.get(f'{auth_client.base_url}/books/fetch?isbn={isbn}')
    assert response.status_code == 200
    assert response.json()['isbn'] == isbn
