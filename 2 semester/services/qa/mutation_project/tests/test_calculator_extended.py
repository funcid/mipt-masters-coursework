from datetime import datetime

import pytest

from billing.calculator import (
    apply_dynamic_tax,
    apply_loyalty_discount,
    bulk_discount,
    cap_price,
    compute_bulk_total,
    compute_refund,
    is_weekend_rate,
    loyalty_points_earned,
    parse_iso_date,
    round_money,
    split_payment,
    tax_breakdown,
    validate_coupon,
    validate_tax_number,
)

PARTS_POSITIVE_MSG = "parts must be > 0"
PERCENTAGE_RANGE_MSG = "percentage 0..1"


def test_validate_coupon_positive_valid():
    assert validate_coupon("SPORT10") is True


def test_validate_coupon_positive_lowercase():
    assert validate_coupon("newuser5") is True


def test_validate_coupon_positive_blackfriday():
    assert validate_coupon("BLACKFRIDAY") is True


def test_validate_coupon_negative_invalid():
    assert validate_coupon("FAKE") is False


def test_split_payment_positive_single_part():
    assert split_payment(10.0, 1) == [10.0]


def test_split_payment_positive_even_split():
    assert split_payment(9.0, 3) == [3.0, 3.0, 3.0]


def test_split_payment_positive_rounding_remainder():
    amounts = split_payment(10.0, 3)
    assert amounts == [3.33, 3.33, 3.34]
    assert amounts[0] == 3.33
    assert amounts[1] == 3.33
    assert amounts[2] == 3.34
    assert sum(amounts) == 10.0


@pytest.mark.parametrize("parts", [0, -1])
def test_split_payment_negative_invalid_parts(parts):
    with pytest.raises(ValueError) as exc_info:
        split_payment(10.0, parts)
    assert str(exc_info.value) == PARTS_POSITIVE_MSG


def test_parse_iso_date_positive():
    result = parse_iso_date("2025-05-30T12:00:00")
    assert result == datetime(2025, 5, 30, 12, 0, 0)


def test_compute_refund_positive_half():
    assert compute_refund(100.0, 0.5) == 50.0


def test_compute_refund_positive_zero():
    assert compute_refund(100.0, 0.0) == 0.0


def test_compute_refund_positive_full():
    assert compute_refund(100.0, 1.0) == 100.0


@pytest.mark.parametrize("percentage", [-0.1, 1.1])
def test_compute_refund_negative_out_of_range(percentage):
    with pytest.raises(ValueError) as exc_info:
        compute_refund(100.0, percentage)
    assert str(exc_info.value) == PERCENTAGE_RANGE_MSG


@pytest.mark.parametrize(
    ("qty", "expected"),
    [(9, 0.0), (10, 0.08), (19, 0.08), (20, 0.15), (25, 0.15)],
)
def test_bulk_discount_boundaries(qty, expected):
    assert bulk_discount(qty) == expected


def test_compute_bulk_total_qty_10():
    assert compute_bulk_total(10.0, 10) == 111.32


def test_compute_bulk_total_qty_20():
    assert compute_bulk_total(10.0, 20) == 205.7


def test_tax_breakdown_positive():
    assert tax_breakdown(100.0) == (100.0, 21.0)


def test_validate_tax_number_positive():
    assert validate_tax_number("LV1234567890") is True


@pytest.mark.parametrize("tax_num", ["123456789012", "LV12345", "DE1234567890"])
def test_validate_tax_number_negative(tax_num):
    assert validate_tax_number(tax_num) is False


def test_apply_dynamic_tax_lv():
    assert apply_dynamic_tax(100.0, "LV") == 121.0


def test_apply_dynamic_tax_other_country():
    assert apply_dynamic_tax(100.0, "DE") == 120.0


def test_loyalty_points_earned_positive():
    assert loyalty_points_earned(100.0) == 2


def test_loyalty_points_earned_truncates():
    assert loyalty_points_earned(49.0) == 0


def test_apply_loyalty_discount_positive():
    assert apply_loyalty_discount(10.0, 50) == 9.5


def test_apply_loyalty_discount_caps_at_zero():
    assert apply_loyalty_discount(5.0, 1000) == 0.0


def test_cap_price_above_cap():
    assert cap_price(150.0, 100.0) == 100.0


def test_cap_price_below_cap():
    assert cap_price(80.0, 100.0) == 80.0


def test_round_money_default_decimals():
    assert round_money(1.005) == 1.01


def test_round_money_explicit_decimals():
    assert round_money(1.005, decimals=2) == 1.01


def test_round_money_three_decimals():
    assert round_money(1.2345, decimals=3) == 1.235


def test_is_weekend_rate_saturday():
    assert is_weekend_rate(datetime(2025, 5, 17)) is True


def test_is_weekend_rate_sunday():
    assert is_weekend_rate(datetime(2025, 5, 18)) is True


def test_is_weekend_rate_monday():
    assert is_weekend_rate(datetime(2025, 5, 19)) is False
