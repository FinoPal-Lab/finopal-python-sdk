"""Tests for the ``payments`` resource."""

from __future__ import annotations

import pytest

from finopal import FinoPalException, ValidationError
from finopal.utils.config import LIVE_BASE_URL, SANDBOX_BASE_URL
from tests.conftest import REQUEST_OK, TEST_AUTHORITY, error

REQUEST_PATH = "/api/v1/payment/request"

VALID = {
    "amount": 1_100,
    "callback_url": "https://shop.example.com/payment/callback",
    "order_id": "ORD-1001",
    "description": "Order #1001",
}


class TestCreate:
    def test_returns_authority_and_payment_url(self, finopal, gateway):
        gateway.route(REQUEST_PATH, REQUEST_OK)
        payment = finopal.payments.create(VALID)

        assert payment.authority == TEST_AUTHORITY
        assert payment.payment_url.startswith("https://pna.shaparak.ir/")
        assert payment.code == 100
        assert payment.is_successful is True
        assert payment.raw == REQUEST_OK

    def test_hits_the_documented_endpoint(self, finopal, gateway):
        gateway.route(REQUEST_PATH, REQUEST_OK)
        finopal.payments.create(VALID)
        assert gateway.last_call["url"] == LIVE_BASE_URL + REQUEST_PATH

    def test_sandbox_routes_to_sandbox_host(self, sandbox_finopal, gateway):
        gateway.route(REQUEST_PATH, REQUEST_OK)
        payment = sandbox_finopal.payments.create(VALID)
        assert gateway.last_call["url"] == SANDBOX_BASE_URL + REQUEST_PATH
        assert payment.sandbox is True

    def test_optional_fields_are_forwarded_when_present(self, finopal, gateway):
        gateway.route(REQUEST_PATH, REQUEST_OK)
        finopal.payments.create(
            {
                **VALID,
                "description": "Order #1001",
                "mobile": "09121234567",
                "email": "buyer@example.com",
                "metadata": {"product_id": "123", "user_id": "960"},
            }
        )
        body = gateway.payload_for(REQUEST_PATH)
        assert body["description"] == "Order #1001"
        assert body["mobile"] == "09121234567"
        assert body["email"] == "buyer@example.com"
        assert body["metadata"] == {"product_id": "123", "user_id": "960"}

    def test_optional_fields_are_omitted_when_absent(self, finopal, gateway):
        gateway.route(REQUEST_PATH, REQUEST_OK)
        finopal.payments.create(VALID)
        body = gateway.payload_for(REQUEST_PATH)
        assert set(body) == {
            "merchant_id",
            "amount",
            "callback_url",
            "order_id",
            "description",
        }

    def test_amount_is_coerced_to_int(self, finopal, gateway):
        gateway.route(REQUEST_PATH, REQUEST_OK)
        finopal.payments.create({**VALID, "amount": "1100"})
        assert gateway.payload_for(REQUEST_PATH)["amount"] == 1100

    @pytest.mark.parametrize("missing", ["amount", "callback_url", "order_id", "description"])
    def test_missing_required_field_raises_before_any_request(
        self, finopal, gateway, missing
    ):
        data = dict(VALID)
        data.pop(missing)
        with pytest.raises(ValidationError, match="Missing required parameter"):
            finopal.payments.create(data)
        assert gateway.calls == []

    @pytest.mark.parametrize(
        "bad_amount",
        [0, 999, -1, 1_000_000_001, "abc", None, True, 1100.5],
    )
    def test_invalid_amounts_are_rejected_locally(self, finopal, gateway, bad_amount):
        with pytest.raises(ValidationError):
            finopal.payments.create({**VALID, "amount": bad_amount})
        assert gateway.calls == []

    @pytest.mark.parametrize(
        "bad_url", ["", "shop.example.com/cb", "ftp://x.com/cb", "/relative"]
    )
    def test_invalid_callback_urls_are_rejected_locally(self, finopal, bad_url):
        with pytest.raises(ValidationError):
            finopal.payments.create({**VALID, "callback_url": bad_url})

    def test_invalid_mobile_is_rejected(self, finopal):
        with pytest.raises(ValidationError, match="mobile"):
            finopal.payments.create({**VALID, "mobile": "12345"})

    def test_invalid_email_is_rejected(self, finopal):
        with pytest.raises(ValidationError, match="email"):
            finopal.payments.create({**VALID, "email": "not-an-email"})

    def test_description_longer_than_255_chars_is_rejected(self, finopal):
        with pytest.raises(ValidationError, match="description"):
            finopal.payments.create({**VALID, "description": "x" * 256})

    def test_non_mapping_data_is_rejected(self, finopal):
        with pytest.raises(ValidationError, match="must be a mapping"):
            finopal.payments.create([("amount", 1)])  # type: ignore[arg-type]

    def test_gateway_failure_raises_finopal_exception(self, finopal, gateway):
        gateway.route(REQUEST_PATH, error(-10, "merchant_id or ip is wrong"))
        with pytest.raises(FinoPalException) as excinfo:
            finopal.payments.create(VALID)
        assert excinfo.value.code == -10
        assert "ip is wrong" in excinfo.value.message
        assert excinfo.value.scope == "public"

    def test_success_without_authority_is_treated_as_failure(self, finopal, gateway):
        gateway.route(
            REQUEST_PATH,
            {"success": True, "code": 100, "data": {"payment_url": "https://x"}},
        )
        with pytest.raises(FinoPalException, match="no authority"):
            finopal.payments.create(VALID)


class TestRequestKwargs:
    def test_matches_create(self, finopal, gateway):
        gateway.route(REQUEST_PATH, REQUEST_OK)
        payment = finopal.payments.request(
            amount=1_100,
            callback_url=VALID["callback_url"],
            order_id="ORD-1001",
            description="Order #1001",
            mobile="09121234567",
            email="buyer@example.com",
            metadata={"user_id": "960"},
        )
        assert payment.authority == TEST_AUTHORITY
        body = gateway.payload_for(REQUEST_PATH)
        assert body["description"] == "Order #1001"
        assert body["metadata"] == {"user_id": "960"}

    def test_omits_none_kwargs(self, finopal, gateway):
        gateway.route(REQUEST_PATH, REQUEST_OK)
        finopal.payments.request(
            amount=1_100,
            callback_url=VALID["callback_url"],
            order_id="ORD-1",
            description="Order #1",
        )
        assert "mobile" not in gateway.payload_for(REQUEST_PATH)


class TestRedirectUrl:
    def test_builds_the_redirect_path(self, finopal):
        assert finopal.payments.redirect_url(TEST_AUTHORITY) == (
            LIVE_BASE_URL + "/api/v1/payment/redirect/" + TEST_AUTHORITY
        )

    def test_sandbox_variant(self, sandbox_finopal):
        assert sandbox_finopal.payments.redirect_url(TEST_AUTHORITY).startswith(
            SANDBOX_BASE_URL
        )

    def test_generate_payment_url_is_an_alias(self, finopal):
        assert finopal.payments.generate_payment_url(TEST_AUTHORITY) == (
            finopal.payments.redirect_url(TEST_AUTHORITY)
        )

    def test_rejects_a_bogus_authority(self, finopal):
        with pytest.raises(ValidationError):
            finopal.payments.redirect_url("")
