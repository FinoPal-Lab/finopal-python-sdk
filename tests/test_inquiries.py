"""Tests for the ``inquiries`` resource."""

from __future__ import annotations

import pytest

from finopal import FinoPalException, ValidationError
from finopal.utils.enums import TransactionStatus
from tests.conftest import INQUIRY_OK, TEST_AUTHORITY, error

INQUIRY_PATH = "/api/v1/payment/inquiry"


class TestInquire:
    def test_returns_the_transaction_status(self, finopal, gateway):
        gateway.route(INQUIRY_PATH, INQUIRY_OK)
        result = finopal.inquiries.inquire({"authority": TEST_AUTHORITY})

        assert result.status == "successful"
        assert result.is_paid is True
        assert result.success is True
        assert result.errors == []

    @pytest.mark.parametrize(
        "status,paid",
        [
            ("pending", False),
            ("successful", True),
            ("failed", False),
            ("cancelled", False),
            ("refunded", False),
            ("callback", False),
        ],
    )
    def test_every_documented_status(self, finopal, gateway, status, paid):
        gateway.route(
            INQUIRY_PATH,
            {"success": True, "status": status, "message": "ok", "errors": []},
        )
        result = finopal.inquiries.inquire({"authority": TEST_AUTHORITY})
        assert result.status == status
        assert result.is_paid is paid

    def test_missing_authority_raises(self, finopal, gateway):
        with pytest.raises(ValidationError, match="authority"):
            finopal.inquiries.inquire({})
        assert gateway.calls == []

    def test_not_found_error_code_minus_11(self, finopal, gateway):
        gateway.route(INQUIRY_PATH, error(-11, "transaction not found"))
        with pytest.raises(FinoPalException) as excinfo:
            finopal.inquiries.inquire({"authority": TEST_AUTHORITY})
        assert excinfo.value.code == -11


class TestStatusOf:
    def test_returns_an_enum(self, finopal, gateway):
        gateway.route(INQUIRY_PATH, INQUIRY_OK)
        assert finopal.inquiries.status_of(TEST_AUTHORITY) is TransactionStatus.SUCCESSFUL

    def test_unknown_status_falls_back_to_the_raw_value(self, finopal, gateway):
        gateway.route(
            INQUIRY_PATH, {"success": True, "status": "something-new", "errors": []}
        )
        assert finopal.inquiries.status_of(TEST_AUTHORITY) == "something-new"
