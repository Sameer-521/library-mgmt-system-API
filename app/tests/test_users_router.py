import pytest

@pytest.mark.anyio
async def test_signup(client):
    form_data = {
        'full_name': 'Mock User',
        'email': 'mock@gmail.com',
        'password': '12345678'
    }
    response = await client.post(f'{client.base_url}/users/sign-up', data=form_data)
    assert response.status_code == 201
    #confirm
    response = await client.post(f'{client.base_url}/users/sign-up', data=form_data)
    assert response.status_code == 409

@pytest.mark.anyio
async def test_login(client, mock_user):

    form_data = {
        'email': mock_user.email,
        'password': 'mockuser123' # cant use password tied to db user, its hashed
    }
    response = await client.post(f'{client.base_url}/users/login', data=form_data)
    assert response.status_code == 200
    data = response.json()
    token = data['access_token']
    assert isinstance(token, str)