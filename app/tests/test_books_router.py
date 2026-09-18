from datetime import UTC, datetime, timedelta

import pytest

from app.models import BkCopySchedule, BkCopyStatus, Book, BookCopy, Loan, LoanStatus


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
async def test_get_books_pagination(auth_client, test_session):
    for i in range(3):
        test_session.add(
            Book(
                title=f"Pagination Book {i}",
                author="Pagination Author",
                location="P1",
                isbn=f"pagination-isbn-{i}",
            )
        )
    await test_session.flush()

    response = await auth_client.get(f"{auth_client.base_url}/books?limit=2&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert len(data["items"]) == 2

    response_2 = await auth_client.get(f"{auth_client.base_url}/books?limit=2&offset=2")
    assert response_2.status_code == 200
    data_2 = response_2.json()
    assert data_2["offset"] == 2
    assert len(data_2["items"]) == 1
    first_page_ids = {b["id"] for b in data["items"]}
    second_page_ids = {b["id"] for b in data_2["items"]}
    assert first_page_ids.isdisjoint(second_page_ids)


@pytest.mark.anyio
async def test_get_books_filtering(auth_client, test_session):
    test_session.add_all(
        [
            Book(
                title="Clean Code",
                author="Robert Martin",
                location="F1",
                isbn="filter-clean",
            ),
            Book(
                title="The Pragmatic Programmer",
                author="Andrew Hunt",
                location="F1",
                isbn="filter-prag",
            ),
            Book(
                title="Clean Architecture",
                author="Robert Martin",
                location="F1",
                isbn="filter-arch",
            ),
        ]
    )
    await test_session.flush()

    by_title = await auth_client.get(f"{auth_client.base_url}/books?title=Clean")
    assert by_title.status_code == 200
    data = by_title.json()
    assert data["total"] == 2
    assert {book["isbn"] for book in data["items"]} == {"filter-clean", "filter-arch"}

    by_author = await auth_client.get(f"{auth_client.base_url}/books?author=Andrew")
    assert by_author.status_code == 200
    data = by_author.json()
    assert data["total"] == 1
    assert data["items"][0]["isbn"] == "filter-prag"

    by_isbn = await auth_client.get(f"{auth_client.base_url}/books?isbn=filter-prag")
    assert by_isbn.status_code == 200
    data = by_isbn.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "The Pragmatic Programmer"

    combined = await auth_client.get(
        f"{auth_client.base_url}/books?author=Robert&title=Architecture"
    )
    assert combined.status_code == 200
    data = combined.json()
    assert data["total"] == 1
    assert data["items"][0]["isbn"] == "filter-arch"


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
        f"{auth_client.base_url}/books/schedule-book?isbn={isbn}"
    )
    assert response.status_code == 201
    assert response.json()["message"] == "Schedule has been successfuly created"


@pytest.mark.anyio
async def test_schedule_bk_copy_unknown_isbn_404(auth_client):
    response = await auth_client.post(
        f"{auth_client.base_url}/books/schedule-book?isbn=0000000000"
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_schedule_bk_copy_no_copies_400(auth_client, mock_book):
    response = await auth_client.post(
        f"{auth_client.base_url}/books/schedule-book?isbn={mock_book.isbn}"
    )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "NO_COPIES_AVAILABLE"
    assert detail["message"] == "No available copies"


@pytest.mark.anyio
async def test_book_response_includes_available_copies(
    auth_client, mock_book_copies, test_session
):
    isbn, bk_copies = mock_book_copies
    bk_copies[0].status = BkCopyStatus.BORROWED
    await test_session.flush()
    test_session.expire_all()

    response = await auth_client.get(f"{auth_client.base_url}/books/fetch?isbn={isbn}")
    assert response.status_code == 200
    assert response.json()["available_copies"] == 4

    list_response = await auth_client.get(f"{auth_client.base_url}/books?isbn={isbn}")
    assert list_response.status_code == 200
    assert list_response.json()["items"][0]["available_copies"] == 4


@pytest.mark.anyio
async def test_copy_status_changes_reflect_in_count(
    auth_client, mock_book_copies, test_session
):
    isbn, _ = mock_book_copies
    damaged = BookCopy(
        book_isbn=isbn,
        serial=99,
        copy_barcode="COPY-DAMAGED-99",
        status=BkCopyStatus.DAMAGED,
    )
    test_session.add(damaged)
    await test_session.flush()
    test_session.expire_all()

    response = await auth_client.get(f"{auth_client.base_url}/books/fetch?isbn={isbn}")
    assert response.status_code == 200
    assert response.json()["available_copies"] == 5


@pytest.mark.anyio
async def test_update_bk_copies(admin_auth_client, mock_book_copies):
    _, bk_copies = mock_book_copies

    barcodes = [bk.copy_barcode for bk in bk_copies]

    payload = {
        "book_copies": [{"copy_barcode": bc, "status": "AVAILABLE"} for bc in barcodes]
    }

    response = await admin_auth_client.patch(
        f"{admin_auth_client.base_url}/books/bk-copies", json=payload
    )

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["num_not_found"] == 0


@pytest.mark.anyio
async def test_return_book(admin_auth_client, mock_loan):
    loan_id, barcode = mock_loan
    form_data = {"bk_copy_barcode": barcode, "loan_id": loan_id}
    response = await admin_auth_client.post(
        f"{admin_auth_client.base_url}/books/loan-return", data=form_data
    )
    print(response.json())
    assert response.status_code == 200
    assert response.json()["message"] == "User loan cleared, awaiting staff inspection"
    # confirm
    response = await admin_auth_client.post(
        f"{admin_auth_client.base_url}/books/loan-return", data=form_data
    )
    assert response.status_code == 409


@pytest.mark.anyio
async def test_inspection_flow(
    admin_auth_client, mock_loan, mock_book_copies, test_session
):
    loan_id, barcode = mock_loan
    _, bk_copies = mock_book_copies
    book_copy = bk_copies[0]

    form_data = {"bk_copy_barcode": barcode, "loan_id": loan_id}
    response = await admin_auth_client.post(
        f"{admin_auth_client.base_url}/books/loan-return", data=form_data
    )
    assert response.status_code == 200
    await test_session.refresh(book_copy)
    assert book_copy.status == BkCopyStatus.IN_CHECK

    payload = {"book_copies": [{"copy_barcode": barcode, "status": "AVAILABLE"}]}
    response_2 = await admin_auth_client.patch(
        f"{admin_auth_client.base_url}/books/bk-copies", json=payload
    )
    assert response_2.status_code == 200
    await test_session.refresh(book_copy)
    assert book_copy.status == BkCopyStatus.AVAILABLE


@pytest.mark.anyio
async def test_return_overdue_book(admin_auth_client, overdue_loan):
    loan_id, barcode = overdue_loan
    form_data = {"bk_copy_barcode": barcode, "loan_id": loan_id}
    response = await admin_auth_client.post(
        f"{admin_auth_client.base_url}/books/loan-return", data=form_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "User loan cleared, you have also been fined for delay"
    assert data["fine"] == "300"


@pytest.mark.anyio
async def test_soft_delete_book(
    admin_auth_client, mock_book, mock_book_copies, test_session
):
    isbn, _ = mock_book_copies
    response = await admin_auth_client.delete(
        f"{admin_auth_client.base_url}/books/{isbn}"
    )
    assert response.status_code == 204

    await test_session.refresh(mock_book)
    assert mock_book.is_active is False

    # unknown book
    response_2 = await admin_auth_client.delete(
        f"{admin_auth_client.base_url}/books/99999999"
    )
    assert response_2.status_code == 404


@pytest.mark.anyio
async def test_soft_delete_book_with_active_copy(
    admin_auth_client, mock_book, mock_loan
):
    isbn = mock_book.isbn
    response = await admin_auth_client.delete(
        f"{admin_auth_client.base_url}/books/{isbn}"
    )
    assert response.status_code == 409


@pytest.mark.anyio
async def test_inactive_book_hidden_and_unfetchable(
    auth_client, test_session, mock_book
):
    inactive_book = Book(
        title="Inactive Book",
        author="Inactive Author",
        location="P2",
        isbn="inactive-isbn-1",
        is_active=False,
    )
    test_session.add(inactive_book)
    await test_session.flush()

    response = await auth_client.get(f"{auth_client.base_url}/books?limit=10&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert {book["isbn"] for book in data["items"]} == {mock_book.isbn}

    response_2 = await auth_client.get(
        f"{auth_client.base_url}/books/fetch?isbn={inactive_book.isbn}"
    )
    assert response_2.status_code == 404


@pytest.mark.anyio
async def test_get_my_schedules(auth_client, mock_user, mock_book_copies):
    isbn, bk_copies = mock_book_copies
    schedule_response = await auth_client.post(
        f"{auth_client.base_url}/books/schedule-book?isbn={isbn}"
    )
    assert schedule_response.status_code == 201
    schedule_id = schedule_response.json()["schedule_info"]["schedule_id"]

    response = await auth_client.get(f"{auth_client.base_url}/books/schedules/me")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["schedule_id"] == schedule_id
    assert data[0]["user_uid"] == mock_user.user_uid
    assert data[0]["bk_copy_barcode"] == bk_copies[0].copy_barcode
    assert data[0]["status"] == "active"


@pytest.mark.anyio
async def test_get_my_schedules_requires_token(client):
    response = await client.get(f"{client.base_url}/books/schedules/me")
    assert response.status_code == 401


@pytest.mark.anyio
async def test_get_my_schedules_inactive_user(auth_client, mock_user, test_session):
    mock_user.is_active = False
    await test_session.flush()

    response = await auth_client.get(f"{auth_client.base_url}/books/schedules/me")
    assert response.status_code == 400


@pytest.mark.anyio
async def test_get_my_schedules_newest_first(
    auth_client, mock_user, mock_book_copies, test_session
):
    _, bk_copies = mock_book_copies
    base = datetime(2026, 1, 1, tzinfo=UTC)
    test_session.add_all(
        [
            BkCopySchedule(
                user_uid=mock_user.user_uid,
                bk_copy_barcode=bk_copies[i].copy_barcode,
                created_at=base + timedelta(minutes=i),
            )
            for i in range(3)
        ]
    )
    await test_session.flush()

    response = await auth_client.get(f"{auth_client.base_url}/books/schedules/me")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert [schedule["bk_copy_barcode"] for schedule in data] == [
        bk_copies[2].copy_barcode,
        bk_copies[1].copy_barcode,
        bk_copies[0].copy_barcode,
    ]


@pytest.mark.anyio
async def test_get_active_loans(
    admin_auth_client, mock_user, mock_loan, mock_book_copies, test_session
):
    loan_id, _ = mock_loan
    _, bk_copies = mock_book_copies
    returned_copy = bk_copies[1]
    returned_copy.status = BkCopyStatus.BORROWED
    test_session.add(
        Loan(
            user_uid=mock_user.user_uid,
            bk_copy_barcode=returned_copy.copy_barcode,
            status=LoanStatus.RETURNED,
        )
    )
    await test_session.flush()

    response = await admin_auth_client.get(
        f"{admin_auth_client.base_url}/books/loans/active?limit=10&offset=0"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["loan_id"] == loan_id
    assert data["limit"] == 10
    assert data["offset"] == 0


@pytest.mark.anyio
async def test_get_active_loans_requires_token(client):
    response = await client.get(f"{client.base_url}/books/loans/active")
    assert response.status_code == 401


@pytest.mark.anyio
async def test_get_active_loans_requires_staff(auth_client):
    response = await auth_client.get(f"{auth_client.base_url}/books/loans/active")
    assert response.status_code == 403
