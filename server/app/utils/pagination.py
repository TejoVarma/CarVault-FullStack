import base64
import binascii
import json
from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status

# A real cursor is ~100 characters; anything much longer is not one of ours.
MAX_CURSOR_LENGTH = 200


def encode_cursor(created_at: datetime, car_id: UUID) -> str:
    raw = json.dumps({"t": created_at.isoformat(), "id": str(car_id)})
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def decode_cursor(cursor: str) -> tuple[datetime, UUID]:
    invalid = HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid cursor")
    if len(cursor) > MAX_CURSOR_LENGTH:
        raise invalid
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
    except (binascii.Error, ValueError):
        raise invalid from None
    if not isinstance(data, dict) or not isinstance(data.get("t"), str) or not isinstance(data.get("id"), str):
        raise invalid
    try:
        return datetime.fromisoformat(data["t"]), UUID(data["id"])
    except ValueError:
        raise invalid from None
