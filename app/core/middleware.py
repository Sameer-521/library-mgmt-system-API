import time
from collections.abc import Awaitable, Callable
from datetime import datetime
from logging import getLogger
from typing import Any
from urllib.parse import parse_qs

from fastapi import BackgroundTasks, Request
from jose.exceptions import ExpiredSignatureError, JWTError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response

from app.core.auth import decode_token
from app.core.database import AsyncSessionLocal
from app.models import Event, User
from app.services import create_audit_service

logger = getLogger(__name__)


audit_session_factory = AsyncSessionLocal


async def _bg_audit(entry: dict):
    async with audit_session_factory() as session:
        await create_audit_service(session, entry)


def actor_email(actor, claims):
    try:
        if isinstance(actor, User):
            return getattr(actor, "email", "unavailable")
        if isinstance(actor, dict):
            return actor.get("email", "unavailable")
        if isinstance(claims, dict):
            return claims.get("email", "unavailable")
    except Exception as e:
        logger.error(f"Error getting actor email: {e}")
    return "unavailable"


def actor_is_staff(actor, claims):
    try:
        if isinstance(actor, User):
            return getattr(actor, "is_staff", "unavailable")
        if isinstance(actor, dict):
            return actor.get("is_staff", "unavailable")
        if isinstance(claims, dict):
            return claims.get("is_staff", "unavailable")
    except Exception as e:
        logger.error(f"Error getting actor is_staff: {e}")
    return "unavailable"


def actor_id(actor, claims):
    try:
        if isinstance(actor, User):
            return str(getattr(actor, "user_uid", "unknown"))
        if isinstance(claims, dict) and claims.get("user_uid"):
            return str(claims["user_uid"])
        if isinstance(actor, dict) and actor.get("user_uid"):
            return str(actor["user_uid"])
    except Exception as e:
        logger.error(f"Error getting actor id: {e}")
    return "unauthenticated"


def get_actor_claims(token: str):
    try:
        payload = decode_token(token, False)
        email = payload.get("sub")
        user_uid = payload.get("user_uid")
        is_staff = payload.get("is_staff")
        return {
            "email": email,
            "user_uid": user_uid,
            "is_staff": is_staff,
        }
    except (ExpiredSignatureError, JWTError) as e:
        logger.error(f"Token decode error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected token error: {e}")
        return None


async def extract_form_data(request: Request) -> dict[str, Any]:
    """
    Safely extract form fields (urlencoded or multipart) from `request`
    without preventing downstream code (FastAPI/Dependencies) from reading
    the body. Returns a dict where repeated fields become lists and file
    uploads are returned as UploadFile instances.
    """
    # snapshot body
    body = await request.body()

    # restore mechanism so downstream can read the same body again
    async def _receive() -> dict:
        return {"type": "http.request", "body": body, "more_body": False}

    request._receive = _receive

    content_type = (request.headers.get("content-type") or "").lower()

    # application/x-www-form-urlencoded
    if "application/x-www-form-urlencoded" in content_type:
        decoded = body.decode("utf-8") if body else ""
        parsed = parse_qs(decoded, keep_blank_values=True)
        # convert single-item lists to scalars
        data: dict[str, Any] = {
            k: (v if len(v) > 1 else v[0]) for k, v in parsed.items()
        }
        return data

    # multipart/form-data (files supported) - parse with a temporary Starlette Request
    if "multipart/form-data" in content_type:
        # create a temporary Starlette request that reads from our saved body
        temp_scope = dict(request.scope)
        temp_req = StarletteRequest(temp_scope, _receive)
        form = await temp_req.form()
        data: dict[str, Any] = {}
        for key, val in form.multi_items():
            if key not in data:
                data[key] = val
            else:
                if not isinstance(data[key], list):
                    data[key] = [data[key]]
                data[key].append(val)
        return data

    # no form data or unsupported content-type
    return {}


_EVENT_RULES: tuple[tuple[str, str, bool, Event], ...] = (
    # (method, path, is_prefix, event)
    ("GET", "/", False, Event.ROOT),
    ("POST", "/auth/login", False, Event.LOGIN_USER),
    # books - static paths before dynamic/prefix rules
    ("POST", "/books/loan-return", False, Event.RETURN_BOOK),
    ("POST", "/books/loan-book", False, Event.CHECKOUT),
    ("POST", "/books/generate-copies", False, Event.CREATE_BK_COPIES),
    ("POST", "/books/schedule-book", False, Event.SCHEDULE_BOOK),
    ("GET", "/books/fetch", False, Event.FETCH_BOOK),
    ("GET", "/books/schedules/me", False, Event.FETCH_USER_SCHEDULES),
    ("GET", "/books/loans/active", False, Event.FETCH_ACTIVE_LOANS),
    ("PATCH", "/books/bk-copies", False, Event.UPDATE_BOOK_COPIES),
    ("GET", "/books", False, Event.FETCH_BOOKS),
    ("POST", "/books", False, Event.CREATE_BOOK),
    ("PUT", "/books/", True, Event.UPDATE_BOOK),
    ("DELETE", "/books/", True, Event.DELETE_BOOK),
    # users
    ("GET", "/users", False, Event.FETCH_USER),
    ("POST", "/users/sign-up", False, Event.CREATE_USER),
    ("POST", "/users/create-staff-user", False, Event.CREATE_STAFF_USER),
)


def detect_event_from_request(request: Request) -> Event:
    path = request.url.path.lower().rstrip("/") or "/"
    method = request.method.upper()

    for rule_method, rule_path, is_prefix, event in _EVENT_RULES:
        if method != rule_method:
            continue
        if path == rule_path or (is_prefix and path.startswith(rule_path)):
            return event

    return Event.UNIDENTIFIED_EVENT


def _build_audit_entry(
    request: Request,
    start_time: float,
    status_code: int,
    form_data: dict[str, Any],
    event_type: Event,
    actor: Any,
    claims: Any,
) -> dict:
    extra_details = {
        "timestamp": datetime.now().isoformat(),
        "request_url": f"{request.url}",
        "actor_email": actor_email(actor, claims),
        "is_staff": actor_is_staff(actor, claims),
        "latency": f"{round((time.time() - start_time) * 1000, 2)} ms",
        "status_code": status_code,
    }

    if hasattr(request.state, "msg"):
        msg: dict = getattr(request.state, "msg", {})
        extra_details.update({"msg": msg.get("message", None)})

    if form_data:
        extra_details.update({"form": form_data})

    return {
        "actor_id": actor_id(actor, claims),
        "success": status_code < 400,
        "event": event_type,
        "details": extra_details,
    }


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start_time = time.time()
        token = None
        claims = None
        event_type = detect_event_from_request(request)

        form_data = await extract_form_data(request)
        if "password" in form_data.keys():
            del form_data["password"]

        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]

        if token:
            claims = get_actor_claims(token)

        try:
            response = await call_next(request)
        except Exception:
            actor = getattr(request.state, "actor", None)
            audit_entry = _build_audit_entry(
                request, start_time, 500, form_data, event_type, actor, claims
            )
            await _bg_audit(audit_entry)
            raise

        if event_type == Event.UNIDENTIFIED_EVENT:
            logger.warning("Unidentified event detected")

        actor = getattr(request.state, "actor", None)
        audit_entry = _build_audit_entry(
            request,
            start_time,
            response.status_code,
            form_data,
            event_type,
            actor,
            claims,
        )

        tasks = response.background
        if not isinstance(tasks, BackgroundTasks):
            tasks = BackgroundTasks()
            response.background = tasks
        tasks.add_task(_bg_audit, audit_entry)
        return response

    # avoid calling get_session() in middleware
    # instead use a function that safely opens / closes, a db session and does the functionality
    # add that function to the background tasks instead
