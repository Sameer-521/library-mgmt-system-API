import enum
import secrets
import string
from datetime import UTC, datetime, timedelta
from logging import Logger
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings

logger = Logger(__name__)

PROFILE_PIC_DIR = "profile-pics"
PROFILE_PIC_URL = "/users/me/profile-picture"

IMAGE_EXT_BY_MIME = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
}

IMAGE_MIME_BY_EXT = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}

UPLOAD_CHUNK_SIZE = 64 * 1024
IMAGE_SNIFF_LEN = 12


class FileTooLargeError(Exception):
    pass


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


def estimate_late_fine(due_at: datetime, *, now: datetime | None = None) -> int:
    now = now or datetime.now(UTC)
    if not safe_datetime_compare(now, due_at):
        return 0
    return settings.late_fee_per_day * (now.date() - due_at.date()).days


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


def sniff_image_mime(header: bytes) -> str | None:
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if header.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if (
        len(header) >= IMAGE_SNIFF_LEN
        and header[:4] == b"RIFF"
        and header[8:12] == b"WEBP"
    ):
        return "image/webp"
    return None


def save_file(uploaded_file: UploadFile, dst_path: str | Path, max_bytes: int) -> int:
    uploaded_file.file.seek(0)
    written = 0
    with open(dst_path, "wb") as buffer:
        while chunk := uploaded_file.file.read(UPLOAD_CHUNK_SIZE):
            written += len(chunk)
            if written > max_bytes:
                raise FileTooLargeError(f"upload exceeds limit of {max_bytes} bytes")
            buffer.write(chunk)
    return written


def remove_file(path: str | Path, base_dir: Path | None = None) -> None:
    try:
        file_path = Path(path)
        if base_dir is not None:
            resolved = file_path.resolve()
            if not resolved.is_relative_to(Path(base_dir).resolve()):
                logger.warning(f"Refusing to remove file outside base dir: {path}")
                return
        file_path.unlink(missing_ok=True)
    except OSError as e:
        logger.warning(f"Could not remove file {path}: {e}")
