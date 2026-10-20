"""Tests for the HTTP transport layer (uses ``requests_mock``)."""

from __future__ import annotations

import pytest
import requests

from finopal import Config, FinoPal, RequestsTransport, TransportError

REQUEST_PATH = "/api/v1/payment/request"
REQUEST_OK = {
    "success": True,
    "code": 100,
    "data": {"authority": "FP_1", "payment_url": "https://pna.shaparak.ir/x"},
}


class TestRequestsTransport:
    def test_posts_json_and_returns_a_dict(self, requests_mock):
        requests_mock.post("https://payment.finopal.ir" + REQUEST_PATH, json=REQUEST_OK)

        transport = RequestsTransport()
        result = transport.post_json(
            "https://payment.finopal.ir" + REQUEST_PATH, {"amount": 1_100}
        )

        assert result == REQUEST_OK
        assert requests_mock.last_request.json() == {"amount": 1_100}
        assert requests_mock.last_request.headers["Content-Type"] == "application/json"

    def test_non_json_body_raises_transport_error(self, requests_mock):
        requests_mock.post(
            "https://payment.finopal.ir" + REQUEST_PATH,
            text="<html>502 Bad Gateway</html>",
            status_code=200,
        )
        transport = RequestsTransport()
        with pytest.raises(TransportError, match="non-JSON"):
            transport.post_json("https://payment.finopal.ir" + REQUEST_PATH, {})

    def test_server_error_raises_transport_error(self, requests_mock):
        requests_mock.post(
            "https://payment.finopal.ir" + REQUEST_PATH,
            json={"error": "boom"},
            status_code=503,
        )
        transport = RequestsTransport()
        with pytest.raises(TransportError) as excinfo:
            transport.post_json("https://payment.finopal.ir" + REQUEST_PATH, {})
        assert excinfo.value.status_code == 503

    def test_client_error_json_is_passed_through_for_the_resource_layer(
        self, requests_mock
    ):
        """A 4xx carrying a structured FinoPal error must reach the caller."""
        payload = {
            "success": False,
            "message": "merchant not valid",
            "errors": {"code": -10},
        }
        requests_mock.post(
            "https://payment.finopal.ir" + REQUEST_PATH, json=payload, status_code=400
        )
        transport = RequestsTransport()
        assert transport.post_json(
            "https://payment.finopal.ir" + REQUEST_PATH, {}
        ) == payload

    def test_connection_error_is_retried_then_wrapped(self, requests_mock):
        requests_mock.post(
            "https://payment.finopal.ir" + REQUEST_PATH,
            exc=requests.ConnectionError("boom"),
        )
        transport = RequestsTransport(max_retries=1)
        with pytest.raises(TransportError, match="Could not reach"):
            transport.post_json("https://payment.finopal.ir" + REQUEST_PATH, {})
        assert requests_mock.call_count == 2

    def test_timeout_is_wrapped(self, requests_mock):
        requests_mock.post(
            "https://payment.finopal.ir" + REQUEST_PATH, exc=requests.Timeout()
        )
        transport = RequestsTransport()
        with pytest.raises(TransportError, match="Could not reach"):
            transport.post_json("https://payment.finopal.ir" + REQUEST_PATH, {})


class TestEndToEndOverHttp:
    """Drive the real client over a mocked socket to prove wiring end-to-end."""

    def test_request_then_verify(self, requests_mock):
        requests_mock.post(
            "https://sandbox.finopal.ir" + REQUEST_PATH,
            json={
                "success": True,
                "code": 100,
                "data": {
                    "authority": "FP_636E4A5CBBCE0F222B46829BD74AB4A9",
                    "payment_url": "https://pna.shaparak.ir/sandbox",
                },
            },
        )
        requests_mock.post(
            "https://sandbox.finopal.ir/api/v1/payment/verify",
            json={
                "success": True,
                "data": {"code": 100, "ref_id": "999", "amount": "1100.00"},
            },
        )

        finopal = FinoPal(Config(merchant_id="fino-1234-5678-9012-3456", sandbox=True))

        payment = finopal.payments.create(
            {
                "amount": 1_100,
                "callback_url": "https://shop.example.com/cb",
                "order_id": "ORD-1",
                "description": "Order 1",
            }
        )
        assert payment.authority == "FP_636E4A5CBBCE0F222B46829BD74AB4A9"

        verified = finopal.verifications.verify(
            {"authority": payment.authority, "amount": 1_100}
        )
        assert verified.ref_id == "999"
        assert verified.is_successful is True
