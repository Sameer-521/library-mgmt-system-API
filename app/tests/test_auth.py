import pytest


@pytest.mark.anyio
async def test_protected_route_requires_token(client):
    response = await client.get(f"{client.base_url}/books/fetch?isbn=11223344")
    assert response.status_code == 401


@pytest.mark.anyio
async def test_invalid_token_rejected(client):
    client.headers.update({"Authorization": "Bearer not-a-real-token"})
    response = await client.get(f"{client.base_url}/books/fetch?isbn=11223344")
    assert response.status_code == 401


@pytest.mark.anyio
async def test_non_staff_forbidden_on_staff_route(auth_client, book_creation_data):
    response = await auth_client.post(
        f"{auth_client.base_url}/books", data=book_creation_data
    )
    assert response.status_code == 403
