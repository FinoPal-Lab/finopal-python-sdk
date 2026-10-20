"""Tests for the ``reversals`` resource."""

from __future__ import annotations

import pytest

from finopal import FinoPalException, ValidationError
from tests.conftest import REVERSE_OK, TEST_AUTHORITY

REVERSE_PATH = "/api/v1/payment/reverse"


class TestReverse:
    def test_successful_reverse(self, finopal, gateway):
        gateway.route(REVERSE_PATH, REVERSE_OK)
        result = finopal.reversals.reverse({"authority": TEST_AUTHORITY})

        assert result.is_successful is True
        assert result.message == "تراکنش با موفقیت برگشت داده شد"

    def test_sends_authority_and_merchant_id(self, finopal, gateway):
        gateway.route(REVERSE_PATH, REVERSE_OK)
        finopal.reversals.reverse({"authority": TEST_AUTHORITY})
        body = gateway.payload_for(REVERSE_PATH)
        assert body["authority"] == TEST_AUTHORITY
        assert body["merchant_id"] == "fino-1234-5678-9012-3456"

    def test_missing_authority_raises(self, finopal, gateway):
        with pytest.raises(ValidationError, match="authority"):
            finopal.reversals.reverse({})
        assert gateway.calls == []

    def test_already_reversed_code_minus_1551(self, finopal, gateway):
        gateway.route(
            REVERSE_PATH,
            {
                "success": False,
                "message": "تراکنش قبلاً برگشت داده شده است",
                "code": -1551,
            },
        )
        with pytest.raises(FinoPalException) as excinfo:
            finopal.reversals.reverse({"authority": TEST_AUTHORITY})
        assert excinfo.value.code == -1551
        assert "already been reversed" in excinfo.value.describe()

    def test_window_expired_code_minus_1552(self, finopal, gateway):
        gateway.route(
            REVERSE_PATH,
            {
                "success": False,
                "message": "زمان مجاز برای برگشت تراکنش (15 دقیقه) سپری شده است",
                "code": -1552,
            },
        )
        with pytest.raises(FinoPalException) as excinfo:
            finopal.reversals.reverse({"authority": TEST_AUTHORITY})
        assert excinfo.value.code == -1552
        assert "15-minute" in excinfo.value.describe()

    def test_keyword_wrapper(self, finopal, gateway):
        gateway.route(REVERSE_PATH, REVERSE_OK)
        assert finopal.reversals.reverse_authority(TEST_AUTHORITY).is_successful is True
