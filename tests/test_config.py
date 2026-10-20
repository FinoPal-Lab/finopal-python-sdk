"""Tests for :mod:`finopal.utils.config` and the :class:`FinoPal` client."""

from __future__ import annotations

import pytest

from finopal import Config, FinoPal, RequestsTransport
from finopal.utils.config import LIVE_BASE_URL, SANDBOX_BASE_URL
from tests.conftest import TEST_AUTHORITY


class TestConfig:
    def test_defaults_to_live(self):
        config = Config(merchant_id="fino-1")
        assert config.base_url == LIVE_BASE_URL
        assert config.sandbox is False

    def test_sandbox_switches_host(self):
        config = Config(merchant_id="fino-1", sandbox=True)
        assert config.base_url == SANDBOX_BASE_URL

    def test_explicit_base_url_wins_over_sandbox(self):
        config = Config(
            merchant_id="fino-1", sandbox=True, base_url="http://localhost:8000/"
        )
        assert config.base_url == "http://localhost:8000"

    def test_endpoint_joins_paths_cleanly(self):
        config = Config(merchant_id="fino-1")
        assert config.endpoint("/api/v1/payment/request") == (
            LIVE_BASE_URL + "/api/v1/payment/request"
        )
        assert config.endpoint("api/v1/payment/request") == (
            LIVE_BASE_URL + "/api/v1/payment/request"
        )

    def test_merchant_id_is_stripped(self):
        assert Config(merchant_id="  fino-1  ").merchant_id == "fino-1"

    @pytest.mark.parametrize("bad", [None, "", "   "])
    def test_missing_merchant_id_raises(self, bad):
        with pytest.raises(ValueError, match="merchant_id is required"):
            Config(merchant_id=bad)


class TestFinoPalClient:
    def test_requires_a_config_instance(self):
        with pytest.raises(TypeError, match="config must be a finopal.Config"):
            FinoPal({"merchant_id": "fino-1"})  # type: ignore[arg-type]

    def test_builds_a_default_transport(self, config):
        client = FinoPal(config)
        assert isinstance(client.transport, RequestsTransport)
        assert client.transport.timeout == config.timeout

    def test_resources_are_cached(self, finopal):
        assert finopal.payments is finopal.payments
        assert finopal.verifications is finopal.verifications
        assert finopal.inquiries is finopal.inquiries
        assert finopal.reversals is finopal.reversals
        assert finopal.fees is finopal.fees

    def test_reports_mode_and_base_url(self, finopal, sandbox_finopal):
        assert finopal.is_sandbox is False
        assert finopal.base_url == LIVE_BASE_URL
        assert sandbox_finopal.is_sandbox is True
        assert sandbox_finopal.base_url == SANDBOX_BASE_URL

    def test_generic_request_rejects_non_post(self, finopal):
        with pytest.raises(ValueError, match="only exposes POST"):
            finopal.request("GET", "/api/v1/payment/inquiry")

    def test_generic_request_injects_merchant_id(self, finopal, gateway):
        gateway.route("/api/v1/payment/inquiry", {"success": True, "status": "pending"})
        finopal.request("POST", "/api/v1/payment/inquiry", {"authority": "FP_1"})
        assert gateway.last_call["body"]["merchant_id"] == "fino-1234-5678-9012-3456"

    def test_caller_can_override_merchant_id(self, finopal, gateway):
        gateway.route(
            "/api/v1/payment/request",
            {
                "success": True,
                "code": 100,
                "data": {"authority": "FP_1", "payment_url": "https://x"},
            },
        )
        finopal.payments.create(
            {
                "amount": 1_000,
                "callback_url": "https://shop.example.com/cb",
                "order_id": "1",
                "description": "Order 1",
                "merchant_id": "fino-other-terminal",
            }
        )
        assert gateway.last_call["body"]["merchant_id"] == "fino-other-terminal"

    def test_sends_expected_headers(self, finopal, gateway):
        gateway.route("/api/v1/payment/inquiry", {"success": True, "status": "pending"})
        finopal.inquiries.inquire({"authority": TEST_AUTHORITY})
        headers = gateway.last_call["headers"]
        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"
        assert headers["User-Agent"].startswith("FinoPalPythonSdk/")
