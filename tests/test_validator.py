"""Tests for the input validators."""

from __future__ import annotations

import pytest

from finopal import ValidationError, Validator
from finopal.utils.amount import MAX_AMOUNT_RIAL, MIN_AMOUNT_RIAL


class TestAmount:
    @pytest.mark.parametrize("value", [1_000, 1_100, "50000", 1_000_000])
    def test_accepts_valid_amounts(self, value):
        assert Validator.validate_amount(value) == int(value)

    def test_minimum_boundary(self):
        assert Validator.validate_amount(MIN_AMOUNT_RIAL) == MIN_AMOUNT_RIAL
        with pytest.raises(ValidationError):
            Validator.validate_amount(MIN_AMOUNT_RIAL - 1)

    def test_maximum_boundary(self):
        assert Validator.validate_amount(MAX_AMOUNT_RIAL) == MAX_AMOUNT_RIAL
        with pytest.raises(ValidationError, match="must not exceed"):
            Validator.validate_amount(MAX_AMOUNT_RIAL + 1)

    @pytest.mark.parametrize("value", [None, "", "abc", [], {}, True, False])
    def test_rejects_non_numeric(self, value):
        with pytest.raises(ValidationError):
            Validator.validate_amount(value)

    def test_rejects_fractional_rial(self):
        with pytest.raises(ValidationError, match="whole number"):
            Validator.validate_amount(1100.5)


class TestAuthority:
    @pytest.mark.parametrize(
        "value",
        [
            "FP_636E4A5CBBCE0F222B46829BD74AB4A9",
            "A0000000000000000000000000000wwOGYpd",
        ],
    )
    def test_accepts_real_world_authorities(self, value):
        assert Validator.validate_authority(value) == value

    @pytest.mark.parametrize("value", ["", "short", "has spaces", None, 12345])
    def test_rejects_bad_authorities(self, value):
        with pytest.raises(ValidationError):
            Validator.validate_authority(value)

    def test_strips_whitespace(self):
        assert Validator.validate_authority("  FP_636E4A5C  ") == "FP_636E4A5C"


class TestCallbackUrl:
    @pytest.mark.parametrize(
        "value",
        [
            "https://shop.example.com/payment/callback",
            "http://localhost:8000/callback",
            "https://example.com/cb?x=1",
        ],
    )
    def test_accepts_absolute_urls(self, value):
        assert Validator.validate_callback_url(value) == value

    @pytest.mark.parametrize(
        "value", ["", "example.com/cb", "ftp://example.com", "/cb", None, 42]
    )
    def test_rejects_relative_or_non_http(self, value):
        with pytest.raises(ValidationError):
            Validator.validate_callback_url(value)

    def test_optional_https_enforcement(self):
        with pytest.raises(ValidationError, match="https"):
            Validator.validate_callback_url(
                "http://shop.example.com/cb", require_https=True
            )


class TestOrderId:
    def test_accepts_strings_and_numbers(self):
        assert Validator.validate_order_id("ORD-1001") == "ORD-1001"
        assert Validator.validate_order_id(1001) == "1001"

    @pytest.mark.parametrize("value", [None, "", "   "])
    def test_rejects_empty(self, value):
        with pytest.raises(ValidationError, match="order_id is required"):
            Validator.validate_order_id(value)

    def test_rejects_over_100_chars(self):
        with pytest.raises(ValidationError, match="100 characters"):
            Validator.validate_order_id("x" * 101)


class TestOther:
    @pytest.mark.parametrize(
        "value", ["09121234567", "+989121234567", "00989121234567", "989121234567"]
    )
    def test_accepts_iranian_mobiles(self, value):
        assert Validator.validate_mobile(value) == value

    @pytest.mark.parametrize("value", ["12345", "08121234567", "0912123456"])
    def test_rejects_bad_mobiles(self, value):
        with pytest.raises(ValidationError):
            Validator.validate_mobile(value)

    def test_email(self):
        assert Validator.validate_email("a@b.co") == "a@b.co"
        with pytest.raises(ValidationError):
            Validator.validate_email("a@b")

    def test_description_length(self):
        assert Validator.validate_description("x" * 255) == "x" * 255
        with pytest.raises(ValidationError):
            Validator.validate_description("x" * 256)

    def test_description_blank_is_rejected(self):
        with pytest.raises(ValidationError, match="description is required"):
            Validator.validate_description("   ")
        with pytest.raises(ValidationError, match="description is required"):
            Validator.validate_description(None)

    def test_metadata_must_be_a_mapping(self):
        assert Validator.validate_metadata({"a": 1}) == {"a": 1}
        with pytest.raises(ValidationError, match="mapping"):
            Validator.validate_metadata(["a"])

    def test_merchant_id(self):
        assert Validator.validate_merchant_id("fino-1234-5678-9012-3456")
        with pytest.raises(ValidationError):
            Validator.validate_merchant_id("nope")

    def test_currency(self):
        assert Validator.validate_currency("irr") == "IRR"
        with pytest.raises(ValidationError):
            Validator.validate_currency("USD")
