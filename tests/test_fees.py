"""Tests for the ``fees`` resource."""

from __future__ import annotations

import pytest

from finopal import FinoPalException, ValidationError
from tests.conftest import FEE_OK, error

FEE_PATH = "/api/v1/payment/feeCalculation"


class TestCalculate:
    def test_returns_amount_fee_and_fee_type(self, finopal, gateway):
        gateway.route(FEE_PATH, FEE_OK)
        result = finopal.fees.calculate({"amount": 1_000_000})

        assert result.fee == 20_000
        assert result.amount == 1_000_000
        assert result.fee_type == "Merchant"
        assert result.is_successful is True
        assert result.is_paid_by_customer is False

    def test_payer_fee_type(self, finopal, gateway):
        gateway.route(FEE_PATH, {**FEE_OK, "fee_type": "Payer"})
        assert finopal.fees.calculate({"amount": 1_000_000}).is_paid_by_customer is True

    def test_sends_amount_and_merchant_id(self, finopal, gateway):
        gateway.route(FEE_PATH, FEE_OK)
        finopal.fees.calculate({"amount": 1_000_000})
        body = gateway.payload_for(FEE_PATH)
        assert body["amount"] == 1_000_000
        assert body["merchant_id"] == "fino-1234-5678-9012-3456"

    def test_missing_amount_raises(self, finopal, gateway):
        with pytest.raises(ValidationError, match="amount"):
            finopal.fees.calculate({})
        assert gateway.calls == []

    def test_below_minimum_raises(self, finopal):
        with pytest.raises(ValidationError, match="at least 1000"):
            finopal.fees.calculate({"amount": 999})

    def test_gateway_failure_raises(self, finopal, gateway):
        gateway.route(FEE_PATH, error(-41, "amount too large"))
        with pytest.raises(FinoPalException) as excinfo:
            finopal.fees.calculate({"amount": 1_000_000})
        assert excinfo.value.code == -41

    def test_keyword_wrapper(self, finopal, gateway):
        gateway.route(FEE_PATH, FEE_OK)
        assert finopal.fees.calculate_amount(1_000_000).fee == 20_000
