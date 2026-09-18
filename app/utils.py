import enum
import secrets
import string
from datetime import UTC, datetime, timedelta
from logging import Logger

logger = Logger(__name__)


class BkCopyStatus(enum.Enum):
    AVAILABLE = "available"
    LOST = "lost"
    DAMAGED = "damaged"
    BORROWED = "borrowed"
    IN_CHECK = "in-check"
    RESERVED = "reserved"


def safe_datetime_compare(dt1: datetime, dt2: datetime) -> bool:
    if dt1.tzinfo is None and dt2.tzinfo is not None:
        dt1 = dt1.replace(tzinfo=UTC)
    elif dt1.tzinfo is not None and dt2.tzinfo is None:
        dt2 = dt2.replace(tzinfo=UTC)
    return dt1 > dt2


def generate_book_copy_barcode(base_barcode, serial):
    try:
        str_serial = str(serial).zfill(3)
        return f"COPY-{base_barcode}-{str_serial}"
    except ValueError as e:
        logger.warning(f"ValueError: {e}")


def generate_barcode(serial: str | None = None):
    digits = string.digits
    serial = "".join([secrets.choice(digits) for _ in range(7)])
    return f"BK-{serial}"


def generate_random_id():
    digits = string.digits
    letters = string.ascii_uppercase
    letter_part = "".join([secrets.choice(letters) for _ in range(2)])
    num_part = "".join([secrets.choice(digits) for _ in range(8)])
    return f"{letter_part}-{num_part}"


def generate_admin_id():
    id = generate_random_id()
    return f"ADMIN-{id}"


def generate_user_id():
    id = generate_random_id()
    return f"USER-{id}"


def generate_staff_id():
    id = generate_random_id()
    return f"STAFF-{id}"


def generate_library_cardnumber():
    id = generate_random_id()
    return f"LB-{id}"


def generate_loan_id():
    id = generate_random_id()
    return f"LN-{id}"


def generate_schedule_id():
    id = generate_random_id()
    return f"SC-{id}"


def default_loan_due_date():
    return datetime.now(UTC) + timedelta(days=7)
