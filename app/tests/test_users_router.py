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


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 32


def upload_url(client) -> str:
    return f"{client.base_url}/users/me/profile-picture"


@pytest.mark.anyio
async def test_upload_profile_picture(auth_client, mock_user, upload_dir):
    response = await auth_client.post(
        upload_url(auth_client),
        files={"file": ("holiday photo.png", PNG_BYTES, "image/png")},
    )
    assert response.status_code == 200
    assert response.json()["profile_picture_url"] == "/users/me/profile-picture"

    saved = upload_dir / f"{mock_user.user_uid}.png"
    assert saved.is_file()
    assert saved.read_bytes() == PNG_BYTES


@pytest.mark.anyio
async def test_get_profile_picture_404_when_none(auth_client, upload_dir):
    response = await auth_client.get(upload_url(auth_client))
    assert response.status_code == 404


@pytest.mark.anyio
async def test_get_profile_picture_serves_file(auth_client, upload_dir):
    await auth_client.post(
        upload_url(auth_client),
        files={"file": ("a.png", PNG_BYTES, "image/png")},
    )
    response = await auth_client.get(upload_url(auth_client))
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == PNG_BYTES


@pytest.mark.anyio
async def test_upload_profile_picture_rejects_disallowed_type(auth_client, upload_dir):
    response = await auth_client.post(
        upload_url(auth_client),
        files={"file": ("notes.txt", b"just text", "text/plain")},
    )
    assert response.status_code == 422
    assert not any(upload_dir.iterdir())


@pytest.mark.anyio
async def test_upload_profile_picture_rejects_spoofed_content_type(
    auth_client, upload_dir
):
    # claims to be a png but the magic bytes say otherwise
    response = await auth_client.post(
        upload_url(auth_client),
        files={"file": ("evil.png", b"#!/bin/sh\nrm -rf /\n", "image/png")},
    )
    assert response.status_code == 422
    assert not any(upload_dir.iterdir())


@pytest.mark.anyio
async def test_upload_profile_picture_rejects_oversized(auth_client, upload_dir):
    big = PNG_BYTES + b"0" * (2 * 1024 * 1024)
    response = await auth_client.post(
        upload_url(auth_client),
        files={"file": ("big.png", big, "image/png")},
    )
    assert response.status_code == 413
    assert not any(upload_dir.iterdir())


@pytest.mark.anyio
async def test_upload_profile_picture_ignores_client_filename(
    auth_client, mock_user, upload_dir, tmp_path
):
    response = await auth_client.post(
        upload_url(auth_client),
        files={"file": ("../../escape.png", PNG_BYTES, "image/png")},
    )
    assert response.status_code == 200
    assert "../" not in response.json()["profile_picture_url"]
    assert (upload_dir / f"{mock_user.user_uid}.png").is_file()
    # nothing was written outside the profile-pics dir
    assert [p.name for p in tmp_path.iterdir()] == ["profile-pics"]


@pytest.mark.anyio
async def test_reupload_replaces_old_file(auth_client, mock_user, upload_dir):
    await auth_client.post(
        upload_url(auth_client),
        files={"file": ("first.png", PNG_BYTES, "image/png")},
    )
    response = await auth_client.post(
        upload_url(auth_client),
        files={"file": ("second.jpg", JPEG_BYTES, "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.json()["profile_picture_url"] == "/users/me/profile-picture"

    assert (upload_dir / f"{mock_user.user_uid}.jpg").is_file()
    assert not (upload_dir / f"{mock_user.user_uid}.png").exists()

    me = await auth_client.get(f"{auth_client.base_url}/users/me")
    assert me.json()["profile_picture_url"] == "/users/me/profile-picture"
