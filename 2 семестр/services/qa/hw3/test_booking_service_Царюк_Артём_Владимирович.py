from datetime import datetime, timedelta, timezone
import re

import pytest

from booking_service import (
    apply_promo_code,
    calc_price,
    check_availability,
    generate_booking_ref,
    send_notification_email,
)


def test_calc_price_positive_regular_discount():
    assert calc_price(100.0, 10.0, 3) == 270.0


def test_calc_price_positive_zero_count():
    assert calc_price(250.0, 15.0, 0) == 0.0


def test_calc_price_negative_discount_raises():
    with pytest.raises(ValueError):
        calc_price(100.0, -5.0, 1)


def test_calc_price_negative_count_raises():
    with pytest.raises(ValueError):
        calc_price(100.0, 5.0, -1)


def test_check_availability_positive_enough_seats(monkeypatch):
    monkeypatch.setattr("booking_service._get_available_seats", lambda _: 10)
    assert check_availability(1, 5) is True


def test_check_availability_positive_exact_match(monkeypatch):
    monkeypatch.setattr("booking_service._get_available_seats", lambda _: 7)
    assert check_availability(10, 7) is True


def test_check_availability_negative_not_enough_seats(monkeypatch):
    monkeypatch.setattr("booking_service._get_available_seats", lambda _: 2)
    assert check_availability(1, 3) is False


def test_check_availability_negative_invalid_requested_raises():
    with pytest.raises(ValueError):
        check_availability(1, 0)


def test_apply_promo_code_positive_valid(monkeypatch):
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        "booking_service._get_promo_data",
        lambda _: {
            "is_active": True,
            "expires_at": now + timedelta(days=1),
            "usage_limit": 10,
            "times_used": 3,
        },
    )
    assert apply_promo_code(101, "PROMO10") is True


def test_apply_promo_code_positive_without_limit(monkeypatch):
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        "booking_service._get_promo_data",
        lambda _: {
            "is_active": True,
            "expires_at": now + timedelta(days=10),
            "usage_limit": None,
            "times_used": 10_000,
        },
    )
    assert apply_promo_code(202, "FREEFORM") is True


def test_apply_promo_code_negative_expired(monkeypatch):
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        "booking_service._get_promo_data",
        lambda _: {
            "is_active": True,
            "expires_at": now - timedelta(minutes=1),
            "usage_limit": 100,
            "times_used": 1,
        },
    )
    assert apply_promo_code(303, "OLD") is False


def test_apply_promo_code_negative_not_found(monkeypatch):
    monkeypatch.setattr("booking_service._get_promo_data", lambda _: None)
    assert apply_promo_code(404, "MISSING") is False


def test_generate_booking_ref_positive_format():
    value = generate_booking_ref(7, 42)
    assert re.fullmatch(r"BOOK-7-42-[0-9A-F]{8}", value)


def test_generate_booking_ref_positive_unique():
    first = generate_booking_ref(7, 42)
    second = generate_booking_ref(7, 42)
    assert first != second


def test_generate_booking_ref_negative_invalid_user_id():
    with pytest.raises(ValueError):
        generate_booking_ref(0, 42)


def test_generate_booking_ref_negative_invalid_event_id():
    with pytest.raises(ValueError):
        generate_booking_ref(7, -1)


def test_send_notification_email_positive_success(monkeypatch):
    calls = []

    def fake_send(email, message):
        calls.append((email, message))
        return True

    monkeypatch.setattr("booking_service._smtp_send", fake_send)
    result = send_notification_email(
        "user@example.com", {"booking_id": 11, "event_id": 99}
    )
    assert result is True
    assert calls and calls[0][0] == "user@example.com"


def test_send_notification_email_positive_truthy_result(monkeypatch):
    monkeypatch.setattr("booking_service._smtp_send", lambda *_: 1)
    assert send_notification_email("ok@mail.com", {"booking_id": 1, "event_id": 2}) is True


def test_send_notification_email_negative_invalid_email():
    with pytest.raises(ValueError):
        send_notification_email("broken-email", {"booking_id": 1, "event_id": 2})


def test_send_notification_email_negative_smtp_exception(monkeypatch):
    def broken_send(*_):
        raise RuntimeError("SMTP unavailable")

    monkeypatch.setattr("booking_service._smtp_send", broken_send)
    assert send_notification_email("user@example.com", {"booking_id": 1, "event_id": 2}) is False
