import pytest

from app.core.auth import decode_token


@pytest.mark.anyio
async def test_user_login_returns_user_token(client, mock_user):
    form_data = {"email": mock_user.email, "password": "mockuser123"}
    response = await client.post(f"{client.base_url}/auth/login", data=form_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    assert decode_token(token)["role"] == "user"


@pytest.mark.anyio
async def test_admin_login_returns_admin_token(client, mock_admin):
    form_data = {"email": mock_admin.email, "password": "imjustfortesting"}
    response = await client.post(f"{client.base_url}/auth/login", data=form_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    assert decode_token(token)["role"] == "admin"
