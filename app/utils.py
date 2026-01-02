import string
import secrets
from logging import Logger
from datetime import datetime, timezone, timedelta
from fastapi import Request

logger = Logger(__name__)

def safe_datetime_compare(dt1: datetime, dt2: datetime) -> bool:
    if dt1.tzinfo is None and dt2.tzinfo is not None:
        dt1 = dt1.replace(tzinfo=timezone.utc)
    elif dt1.tzinfo is not None and dt2.tzinfo is None:
        dt2 = dt2.replace(tzinfo=timezone.utc)
    return dt1 > dt2

def generate_book_copy_barcode(base_barcode, serial):
    try:
        str_serial = str(serial).zfill(3)
        return f'COPY-{base_barcode}-{str_serial}'
    except ValueError as e:
        logger.warning(f'ValueError: {e}')

def generate_barcode(serial: str | None = None):
    digits = string.digits
    serial = ''.join([secrets.choice(digits) for _ in range(7)])
    return f'BK-{serial}'

def generate_random_id():
    digits = string.digits
    letters = string.ascii_uppercase
    letter_part = ''.join([secrets.choice(letters) for _ in range(2)])
    num_part = ''.join([secrets.choice(digits) for _ in range(8)])
    return f'{letter_part}-{num_part}'

def generate_admin_id():
    id = generate_random_id()
    return f'ADMIN-{id}'

def generate_user_id():
    id = generate_random_id()
    return f'USER-{id}'

def generate_staff_id():
    id = generate_random_id()
    return f'STAFF-{id}'

def generate_library_cardnumber():
    id = generate_random_id()
    return f'LB-{id}'

def generate_loan_id():
    id = generate_random_id()
    return f'LN-{id}'

def generate_schedule_id():
    id = generate_random_id()
    return f'SC-{id}'

def default_loan_due_date():
    return datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0) + timedelta(days=7)

def reraise_exceptions(request: Request):
    if hasattr(request.state, 'exceptions'):
        exc: list | None = getattr(request.state, 'exceptions')
        if exc:
            raise exc[0]