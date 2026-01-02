import time, json
from typing import Any, Dict
from fastapi import Request
from urllib.parse import parse_qs
from starlette.requests import Request as StarletteRequest
from jwt.exceptions import InvalidSignatureError
from jose.exceptions import JWTError
from datetime import datetime
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, BackgroundTasks, status
from fastapi.responses import JSONResponse
from typing import Any, Callable, Awaitable
from starlette.responses import Response
from app.services import create_audit_service
from app.core.database import AsyncSessionLocal
from app.core.auth import decode_token
from app.models import User, Event
from logging import getLogger

logger = getLogger(__name__)

async def _bg_audit(entry: dict):
    async with AsyncSessionLocal() as session:
        await create_audit_service(session, entry)

def actor_email(actor, claims):
    try:
        if isinstance(actor, User):
            return getattr(actor, 'email', 'unavailable')
        if isinstance(actor, dict):
            return actor.get('email', 'unavailable')
        if isinstance(claims, dict):
            return claims.get('email', 'unavailable')
    except Exception as e:
        logger.error(f'Error getting actor email: {e}')
    return 'unavailable'

def actor_is_staff(actor, claims):
    try:
        if isinstance(actor, User):
            return getattr(actor, 'is_staff', 'unavailable')
        if isinstance(actor, dict):
            return actor.get('is_staff', 'unavailable')
        if isinstance(claims, dict):
            return claims.get('is_staff', 'unavailable')
    except Exception as e:
        logger.error(f'Error getting actor is_staff: {e}')
    return 'unavailable'

def actor_id(actor, claims):
    try:
        if isinstance(actor, User):
            return getattr(actor, 'user_uid', -401)
        if isinstance(claims, dict):
            return claims.get('user_uid', -1)
        if isinstance(actor, dict):
            return actor.get('user_uid', -401)
    except Exception as e:
        logger.error(f'Error getting actor is_staff: {e}')
    return -1

def get_actor_claims(token: str):
    try:
        payload = decode_token(token, False)
        email = payload.get('sub')
        user_uid = payload.get('user_uid')
        is_staff = payload.get('is_staff')
        return {
            'email': email, 
            'user_uid': user_uid,
            'is_staff': is_staff,
            }
    except (InvalidSignatureError, JWTError) as e:
        logger.error(f'Token decode error: {e}')
        return None
    except Exception as e:
        logger.error(f'Unexpected token error: {e}')
        return None
    
async def extract_form_data(request: Request) -> Dict[str, Any]:
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
        data: Dict[str, Any] = {
            k: (v if len(v) > 1 else v[0]) for k, v in parsed.items()
        }
        return data

    # multipart/form-data (files supported) - parse with a temporary Starlette Request
    if "multipart/form-data" in content_type:
        # create a temporary Starlette request that reads from our saved body
        temp_scope = dict(request.scope)
        temp_req = StarletteRequest(temp_scope, _receive)
        form = await temp_req.form()
        data: Dict[str, Any] = {}
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

def detect_event_from_request(request: Request) -> Event:
    path = request.url.path.lower()
    method = request.method.upper()

    # Book-related
    if path.startswith("/books/loan-return") and method == "POST":
        return Event.RETURN_BOOK
    if path.startswith("/books/loan") and method == "POST":
        return Event.CHECKOUT
    if path.startswith("/books/generate-copies") and method == "POST":
        return Event.CREATE_BK_COPIES
    if path.startswith("/books/book-schedule") and method == "POST":
        return Event.SCHEDULE_BOOK
    if path == "/books" and method == "POST":
        return Event.CREATE_BOOK
    if path.startswith("/books/") and method == "PUT":
        return Event.UPDATE_BOOK
    if path.startswith("/books/fetch") and method == "GET":
        return Event.FETCH_BOOK

    # User-related
    if path.startswith("/users/sign-up") and method == "POST":
        return Event.CREATE_USER
    if path.startswith("/users/login") and method == "POST":
        return Event.LOGIN_USER
    if path.startswith("/users/admin-login") and method == "POST":
        return Event.LOGIN_ADMIN_USER
    if path == "/users" and method == "GET":
        return Event.FETCH_USER

    return Event.UNIDENTIFIED_EVENT
    
class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        start_time = time.time()
        token = None
        actor = None
        claims = None
        event_type = detect_event_from_request(request)

        form_data = await extract_form_data(request)
        if 'password' in form_data.keys():
            del form_data['password']

        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]
        
        if token:
            claims = get_actor_claims(token)
            
        response = await call_next(request)

        if hasattr(request.state, 'actor'):
            actor = getattr(request.state, 'actor', None)
        
        response.background = BackgroundTasks()

        if event_type == Event.UNIDENTIFIED_EVENT:
            logger.warning(f'Unidentified event detected')

        success = response.status_code < 400
        
        extra_details = {
            'timestamp': datetime.now().isoformat(),
            'request_url': f'{request.url}',
            'actor_email': actor_email(actor, claims),
            'is_staff': actor_is_staff(actor, claims),
            'latency': f'{round((time.time() - start_time) * 1000, 2)} ms',
            'status_code': response.status_code
        }

        if hasattr(request.state, 'msg'):
            msg: dict = getattr(request.state, 'msg', {})
            extra_details.update({'msg': msg.get('message', None)})

        if form_data:
            extra_details.update({'form': form_data})

        audit_entry = {
            'actor_id': actor_id(actor, claims),
            'success': success,
            'event': event_type,
            'details': json.dumps(extra_details)
        }

        if response.background is None:
            tasks = BackgroundTasks()
            tasks.add_task(_bg_audit, audit_entry)
            response.background = tasks
        else:
            response.background.add_task(_bg_audit, audit_entry)
        return response

    
    # avoid calling get_session() in middleware
    # instead use a function that safely opens / closes, a db session and does the functionality
    # add that function to the background tasks instead