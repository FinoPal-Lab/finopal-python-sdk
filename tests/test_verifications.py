"""Tests for the ``verifications`` resource."""

from __future__ import annotations

import pytest

from finopal import FinoPalException, ValidationError
from tests.conftest import TEST_AUTHORITY, VERIFY_ALREADY, VERIFY_OK, error

VERIFY_PATH = "/api/v1/payment/verify"

VALID = {"authority": TEST_AUTHORITY, "amount": 1_100}


class TestVerify:
    def test_successful_verify(self, finopal, gateway):
        gateway.route(VERIFY_PATH, VERIFY_OK)
        result = finopal.verifications.verify(VALID)

        assert result.code == 100
        assert result.ref_id == "123456789"
        assert result.is_successful is True
        assert result.is_already_verified is False

    def test_amount_is_returned_as_integer_too(self, finopal, gateway):
        gateway.route(VERIFY_PATH, VERIFY_OK)
        assert finopal.verifications.verify(VALID).amount_rial == 1100

    def test_code_101_means_already_verified_but_still_paid(self, finopal, gateway):
        gateway.route(VERIFY_PATH, VERIFY_ALREADY)
        result = finopal.verifications.verify(VALID)

        assert result.code == 101
        assert result.is_successful is True
        assert result.is_already_verified is True

    def test_sends_authority_and_amount(self, finopal, gateway):
        gateway.route(VERIFY_PATH, VERIFY_OK)
        finopal.verifications.verify(VALID)
        body = gateway.payload_for(VERIFY_PATH)
        assert body["authority"] == TEST_AUTHORITY
        assert body["amount"] == 1100
        assert body["merchant_id"] == "fino-1234-5678-9012-3456"

    def test_missing_authority_raises(self, finopal, gateway):
        with pytest.raises(ValidationError, match="authority"):
            finopal.verifications.verify({"amount": 1_100})
        assert gateway.calls == []

    def test_missing_amount_raises(self, finopal, gateway):
        with pytest.raises(ValidationError, match="amount"):
            finopal.verifications.verify({"authority": TEST_AUTHORITY})
        assert gateway.calls == []

    def test_amount_mismatch_code_minus_50(self, finopal, gateway):
        gateway.route(VERIFY_PATH, error(-50, "amount mismatch"))
        with pytest.raises(FinoPalException) as excinfo:
            finopal.verifications.verify(VALID)
        assert excinfo.value.code == -50
        assert excinfo.value.scope == "PaymentVerify"
        assert "differs" in excinfo.value.describe()

    def test_invalid_authority_code_minus_54(self, finopal, gateway):
        gateway.route(VERIFY_PATH, error(-54, "invalid authority"))
        with pytest.raises(FinoPalException) as excinfo:
            finopal.verifications.verify(VALID)
        assert excinfo.value.code == -54

    def test_keyword_wrapper(self, finopal, gateway):
        gateway.route(VERIFY_PATH, VERIFY_OK)
        result = finopal.verifications.verify_authority(TEST_AUTHORITY, 1_100)
        assert result.ref_id == "123456789"


class TestIsVerified:
    def test_true_on_first_verify(self, finopal, gateway):
        gateway.route(VERIFY_PATH, VERIFY_OK)
        assert finopal.verifications.is_verified(TEST_AUTHORITY, 1_100) is True

    def test_true_when_already_verified(self, finopal, gateway):
        gateway.route(VERIFY_PATH, VERIFY_ALREADY)
        assert finopal.verifications.is_verified(TEST_AUTHORITY, 1_100) is True

    def test_false_on_real_failure(self, finopal, gateway):
        gateway.route(VERIFY_PATH, error(-51, "payment failed"))
        assert finopal.verifications.is_verified(TEST_AUTHORITY, 1_100) is False
