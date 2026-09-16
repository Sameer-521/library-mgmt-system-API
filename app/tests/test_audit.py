import time

import pytest
from sqlalchemy import select
from starlette.requests import Request

from app.core.middleware import _build_audit_entry
from app.models import Audit, Event


async def _get_audits(test_session):
    result = await test_session.execute(select(Audit))
    return result.scalars().all()


@pytest.mark.anyio
async def test_successful_login_audited(client, mock_user, test_session):
    form_data = {"email": mock_user.email, "password": "mockuser123"}
    response = await client.post(f"{client.base_url}/auth/login", data=form_data)
    assert response.status_code == 200

    audits = await _get_audits(test_session)
    assert len(audits) == 1
    audit = audits[0]
    assert audit.event == Event.LOGIN_USER
    assert audit.success is True
    assert audit.actor_id == mock_user.user_uid
    assert isinstance(audit.details, dict)
    assert audit.details["is_staff"] is False
    assert "password" not in audit.details.get("form", {})


@pytest.mark.anyio
async def test_failed_login_audited(client, mock_admin, test_session):
    form_data = {"email": mock_admin.email, "password": "wrongpassword"}
    response = await client.post(f"{client.base_url}/auth/login", data=form_data)
    assert response.status_code == 401

    audits = await _get_audits(test_session)
    assert len(audits) == 1
    audit = audits[0]
    assert audit.event == Event.LOGIN_USER
    assert audit.success is False
    assert audit.actor_id == mock_admin.user_uid
    assert isinstance(audit.details, dict)
    assert audit.details["status_code"] == 401


@pytest.mark.anyio
async def test_unauthenticated_request_audited(client, test_session):
    response = await client.get(f"{client.base_url}/users")
    assert response.status_code == 401

    audits = await _get_audits(test_session)
    assert len(audits) == 1
    audit = audits[0]
    assert audit.event == Event.FETCH_USER
    assert audit.success is False
    assert audit.actor_id == "unauthenticated"
    assert isinstance(audit.details, dict)


def test_build_audit_entry_for_failure_path():
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "query_string": b"",
        "headers": [],
        "scheme": "http",
        "server": ("testserver", 80),
        "client": ("testclient", 1234),
    }
    request = Request(scope)
    entry = _build_audit_entry(
        request, time.time(), 500, {}, Event.UNIDENTIFIED_EVENT, None, None
    )
    assert entry["success"] is False
    assert entry["actor_id"] == "unauthenticated"
    assert entry["event"] == Event.UNIDENTIFIED_EVENT
    assert isinstance(entry["details"], dict)
    assert entry["details"]["status_code"] == 500
