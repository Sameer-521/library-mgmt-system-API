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
    first_page_ids = {u["user_uid"] for u in data["items"]}
    second_page_ids = {u["user_uid"] for u in data_2["items"]}
    assert first_page_ids.isdisjoint(second_page_ids)


@pytest.mark.anyio
async def test_get_users_includes_full_name(admin_auth_client, mock_user):
    response = await admin_auth_client.get(f"{admin_auth_client.base_url}/users")
    assert response.status_code == 200
    items = response.json()["items"]
    assert items[0]["full_name"] == mock_user.full_name


@pytest.mark.anyio
async def test_get_users_staff_role(admin_auth_client, mock_user, test_session):
    staff_user = User(
        full_name="Staff Member",
        email="staffmember@example.com",
        password=hash_password("mockuser123"),
        is_staff=True,
        is_superuser=False,
    )
    test_session.add(staff_user)
    await test_session.flush()
    await test_session.refresh(staff_user)

    # staff-only listing for admin
    response = await admin_auth_client.get(
        f"{admin_auth_client.base_url}/users?role=staff&limit=10&offset=0"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    item = data["items"][0]
    assert item["user_uid"] == staff_user.user_uid
    assert item["full_name"] == "Staff Member"

    # default listing excludes staff
    response_2 = await admin_auth_client.get(
        f"{admin_auth_client.base_url}/users?limit=10&offset=0"
    )
    assert response_2.status_code == 200
    assert {u["user_uid"] for u in response_2.json()["items"]} == {mock_user.user_uid}


@pytest.mark.anyio
async def test_get_users_staff_role_requires_admin(auth_client):
    response = await auth_client.get(f"{auth_client.base_url}/users?role=staff")
    assert response.status_code == 403


@pytest.mark.anyio
async def test_get_my_profile(auth_client, mock_user):
    response = await auth_client.get(f"{auth_client.base_url}/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["user_uid"] == mock_user.user_uid
    assert data["email"] == mock_user.email
    assert data["full_name"] == mock_user.full_name
    assert data["card_number"] == mock_user.card_number
    assert data["is_active"] is True
    assert "created_at" in data
    assert data["fine_balance"] == 0


@pytest.mark.anyio
async def test_get_my_profile_fine_balance(auth_client, mock_user, test_session):
    mock_user.fine_balance = 300
    await test_session.flush()

    response = await auth_client.get(f"{auth_client.base_url}/users/me")
    assert response.status_code == 200
    assert response.json()["fine_balance"] == 300


@pytest.mark.anyio
async def test_get_my_profile_requires_token(client):
    response = await client.get(f"{client.base_url}/users/me")
    assert response.status_code == 401
