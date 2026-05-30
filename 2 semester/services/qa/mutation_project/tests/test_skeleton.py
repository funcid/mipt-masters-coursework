"""
Starter tests for Mutation Shootout.
"""
import pytest
from billing import (
    price_with_tax,
    apply_coupon,
    compute_total,
    booking_fee,
    compute_subtotal,
    convert_currency,
)

NET_NEGATIVE_MSG = "net must be non‑negative"
QTY_POSITIVE_MSG = "qty must be positive"
UNSUPPORTED_CURRENCY_MSG = "Unsupported currency {currency}"


class TestPriceWithTax:
    def test_positive_value(self):
        assert price_with_tax(100.0) == 121.0

    def test_zero_returns_zero(self):
        assert price_with_tax(0.0) == 0.0

    @pytest.mark.parametrize("negative", [-1.0, -100])
    def test_negative_raises(self, negative):
        with pytest.raises(ValueError) as exc_info:
            price_with_tax(negative)
        assert str(exc_info.value) == NET_NEGATIVE_MSG


class TestApplyCoupon:
    def test_valid_coupon(self):
        assert apply_coupon(100.0, "SPORT10") == 90.0

    def test_newuser5_coupon(self):
        assert apply_coupon(100.0, "NEWUSER5") == 95.0

    def test_blackfriday_coupon(self):
        assert apply_coupon(100.0, "BLACKFRIDAY") == 75.0

    def test_invalid_coupon(self):
        assert apply_coupon(100.0, "UNKNOWN") == 100.0

    def test_none_coupon(self):
        assert apply_coupon(100.0, None) == 100.0

    def test_empty_coupon(self):
        assert apply_coupon(100.0, "") == 100.0

    def test_lowercase_coupon(self):
        assert apply_coupon(100.0, "sport10") == 90.0


class TestComputeSubtotal:
    def test_positive_qty(self):
        assert compute_subtotal(10.0, 3) == 30.0

    def test_qty_one(self):
        assert compute_subtotal(10.0, 1) == 10.0

    @pytest.mark.parametrize("qty", [0, -1])
    def test_non_positive_qty_raises(self, qty):
        with pytest.raises(ValueError) as exc_info:
            compute_subtotal(10.0, qty)
        assert str(exc_info.value) == QTY_POSITIVE_MSG


class TestBookingFee:
    def test_positive_qty(self):
        assert booking_fee(4) == 2.0


class TestConvertCurrency:
    def test_eur(self):
        assert convert_currency(100.0, "EUR") == 100.0

    def test_usd(self):
        assert convert_currency(92.0, "USD") == 100.0

    def test_gbp(self):
        assert convert_currency(115.0, "GBP") == 100.0

    def test_unsupported_currency_raises(self):
        with pytest.raises(KeyError) as exc_info:
            convert_currency(100.0, "RUB")
        assert exc_info.value.args[0] == UNSUPPORTED_CURRENCY_MSG.format(currency="RUB")


class TestPipeline:
    def test_happy_flow_eur(self):
        assert compute_total(10.0, 2) == 25.41

    def test_happy_flow_with_coupon(self):
        assert compute_total(10.0, 2, "SPORT10") == 22.87

    def test_happy_flow_with_blackfriday(self):
        assert compute_total(10.0, 2, "BLACKFRIDAY") == 19.06
