import pytest


@pytest.mark.anyio
async def test_book_creation(admin_auth_client, book_creation_data):
    form_data = book_creation_data
    response = await admin_auth_client.post(
        f"{admin_auth_client.base_url}/books", data=form_data
    )
    assert response.status_code == 201
    # confirm creation
    response = await admin_auth_client.post(
        f"{admin_auth_client.base_url}/books", data=form_data
    )
    assert response.status_code == 409


@pytest.mark.anyio
async def test_get_created_book(auth_client, mock_book):
    isbn = mock_book.isbn
    response = await auth_client.get(f"{auth_client.base_url}/books/fetch?isbn={isbn}")
    assert response.status_code == 200
    assert response.json()["isbn"] == isbn


@pytest.mark.anyio
async def test_update_book(admin_auth_client, mock_book):
    form_data = {"title": "Test Title"}
    isbn = mock_book.isbn
    response = await admin_auth_client.put(
        f"{admin_auth_client.base_url}/books/{isbn}", data=form_data
    )
    assert response.status_code == 204
    # confirm
    response_2 = await admin_auth_client.get(
        f"{admin_auth_client.base_url}/books/fetch?isbn={isbn}"
    )
    assert response_2.status_code == 200
    assert response_2.json()["title"] == form_data["title"]


@pytest.mark.anyio
async def test_add_book_copies(admin_auth_client, mock_book):
    form_data = {"isbn": mock_book.isbn, "quantity": 10}
    response = await admin_auth_client.post(
        f"{admin_auth_client.base_url}/books/generate-copies", data=form_data
    )
    assert response.status_code == 201
    assert (
        response.json()["message"]
        == f"{form_data['quantity']} copies of ISBN-{form_data['isbn']} were created successfully"
    )


@pytest.mark.anyio
async def test_loan_book_no_schedule(admin_auth_client, mock_book_copies, mock_user):
    isbn, _ = mock_book_copies
    form_data = {"user_uid": mock_user.user_uid, "isbn": isbn}
    response = await admin_auth_client.post(
        f"{admin_auth_client.base_url}/books/loan-book", data=form_data
    )
    assert response.status_code == 201
    assert not response.json()["was_scheduled"]
    # test none existent book
    form_data["isbn"] = "00001111"
    response_2 = await admin_auth_client.post(
        f"{admin_auth_client.base_url}/books/loan-book", data=form_data
    )
    assert response_2.status_code == 404


@pytest.mark.anyio
async def test_schedule_bk_copy(auth_client, mock_book_copies):
    isbn, _ = mock_book_copies
    response = await auth_client.post(
        f"{auth_client.base_url}/books/book-schedule/{isbn}"
    )
    assert response.status_code == 201
    assert response.json()["message"] == "Schedule has been successfuly created"


@pytest.mark.anyio
async def test_update_bk_copies(admin_auth_client, mock_book_copies):
    _, bk_copies = mock_book_copies

    barcodes = [bk.copy_barcode for bk in bk_copies]

    payload = {
        "book_copies": [{"copy_barcode": bc, "status": "AVAILABLE"} for bc in barcodes]
    }

    response = await admin_auth_client.patch(
        f"{admin_auth_client.base_url}/books/update-bk-copies-status", json=payload
    )

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["num_not_found"] == 0
