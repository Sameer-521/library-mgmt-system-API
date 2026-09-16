import pytest


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
