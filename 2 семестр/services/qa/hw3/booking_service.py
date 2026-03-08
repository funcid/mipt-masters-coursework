from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4


def calc_price(base_price: float, discount: float, count: int) -> float:
    """Calculate total price for a booking."""
    if base_price < 0:
        raise ValueError("base_price must be >= 0")
    if count < 0:
        raise ValueError("count must be >= 0")
    if discount < 0 or discount > 100:
        raise ValueError("discount must be in range [0, 100]")

    total = base_price * count * (1 - discount / 100)
    return round(total, 2)


def _get_available_seats(event_id: int) -> int:
    """Stub for repository/API call."""
    seats_by_event = {1: 120, 2: 0, 3: 15}
    return seats_by_event.get(event_id, 0)


def check_availability(event_id: int, seats_requested: int) -> bool:
    """Return True when enough seats are available."""
    if event_id <= 0:
        raise ValueError("event_id must be > 0")
    if seats_requested <= 0:
        raise ValueError("seats_requested must be > 0")

    available = _get_available_seats(event_id)
    return available >= seats_requested


def _get_promo_data(promo_code: str) -> dict | None:
    """Stub for repository/API call."""
    now = datetime.now(timezone.utc)
    promo_map = {
        "PROMO10": {
            "is_active": True,
            "expires_at": now.replace(year=now.year + 1),
            "usage_limit": 100,
            "times_used": 10,
        }
    }
    return promo_map.get(promo_code)


def apply_promo_code(order_id: int, promo_code: str) -> bool:
    """Apply a promo code to an order when valid."""
    if order_id <= 0:
        raise ValueError("order_id must be > 0")
    if not promo_code or not promo_code.strip():
        raise ValueError("promo_code must not be empty")

    promo = _get_promo_data(promo_code.strip())
    if not promo:
        return False
    if not promo.get("is_active", False):
        return False

    expires_at = promo.get("expires_at")
    if expires_at and expires_at < datetime.now(timezone.utc):
        return False

    usage_limit = promo.get("usage_limit")
    times_used = promo.get("times_used", 0)
    if usage_limit is not None and times_used >= usage_limit:
        return False

    return True


def generate_booking_ref(user_id: int, event_id: int) -> str:
    """Generate booking reference in BOOK-<user>-<event>-<suffix> format."""
    if user_id <= 0:
        raise ValueError("user_id must be > 0")
    if event_id <= 0:
        raise ValueError("event_id must be > 0")

    suffix = uuid4().hex[:8].upper()
    return f"BOOK-{user_id}-{event_id}-{suffix}"


def _smtp_send(email: str, message: str) -> bool:
    """Stub SMTP sender."""
    return True


def send_notification_email(email: str, booking_details: dict) -> bool:
    """Send booking notification e-mail and handle SMTP errors."""
    if not email or "@" not in email:
        raise ValueError("invalid email")
    if not isinstance(booking_details, dict) or not booking_details:
        raise ValueError("booking_details must be a non-empty dict")

    message = (
        f"Booking #{booking_details.get('booking_id', 'n/a')} "
        f"for event {booking_details.get('event_id', 'n/a')}"
    )

    try:
        return bool(_smtp_send(email, message))
    except Exception:
        return False
