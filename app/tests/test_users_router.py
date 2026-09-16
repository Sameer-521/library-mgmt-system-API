import pytest

from app.core.auth import hash_password
from app.models import User


@pytest.mark.anyio
async def test_signup(client):
    form_data = {
        "full_name": "Mock User",
        "email": "mock@gmail.com",
        "password": "12345678",
    }
    response = await client.post(f"{client.base_url}/users/sign-up", data=form_data)
    assert response.status_code == 201
    # confirm
    response = await client.post(f"{client.base_url}/users/sign-up", data=form_data)
    assert response.status_code == 409


@pytest.mark.anyio
async def test_get_users_pagination(admin_auth_client, test_session):
    for i in range(3):
        test_session.add(
            User(
                full_name=f"Pagination User {i}",
                email=f"pagination_user_{i}@example.com",
                password=hash_password("mockuser123"),
            )
        )
    await test_session.flush()

    response = await admin_auth_client.get(
        f"{admin_auth_client.base_url}/users?limit=2&offset=0"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert len(data["items"]) == 2

    response_2 = await admin_auth_client.get(
        f"{admin_auth_client.base_url}/users?limit=2&offset=2"
    )
    assert response_2.status_code == 200
    data_2 = response_2.json()
    assert data_2["offset"] == 2
    assert len(data_2["items"]) == 1
    first_page_ids = {u["id"] for u in data["items"]}
    second_page_ids = {u["id"] for u in data_2["items"]}
    assert first_page_ids.isdisjoint(second_page_ids)
