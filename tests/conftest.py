"""Shared pytest fixtures.

Every test drives the SDK through :class:`FakeGateway`, a scripted
:class:`~finopal.http.transport.CallableTransport`. That keeps the suite fast,
offline and deterministic — no monkeypatching of ``requests`` internals.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

import pytest

from finopal import CallableTransport, Config, FinoPal

TEST_MERCHANT_ID = "fino-1234-5678-9012-3456"
TEST_AUTHORITY = "FP_636E4A5CBBCE0F222B46829BD74AB4A9"
TEST_REF_ID = "123456789"


class FakeGateway:
    """Replays scripted JSON payloads and records every request it receives."""

    def __init__(self) -> None:
        self.routes: Dict[str, Dict[str, Any]] = {}
        self.calls: List[Dict[str, Any]] = []

    def route(self, path: str, response: Mapping[str, Any]) -> "FakeGateway":
        """Register the payload returned for requests ending with ``path``."""
        self.routes[path] = dict(response)
        return self

    def __call__(
        self,
        url: str,
        body: Mapping[str, Any],
        headers: Mapping[str, str],
    ) -> Dict[str, Any]:
        self.calls.append({"url": url, "body": dict(body), "headers": dict(headers)})

        for path, response in self.routes.items():
            if url.endswith(path):
                return response

        raise AssertionError("FakeGateway has no route registered for {!r}".format(url))

    # ------------------------------------------------------------- assertions
    @property
    def last_call(self) -> Dict[str, Any]:
        assert self.calls, "no request was made"
        return self.calls[-1]

    def payload_for(self, path: str) -> Dict[str, Any]:
        for call in reversed(self.calls):
            if call["url"].endswith(path):
                return call["body"]
        raise AssertionError("no request was made to {!r}".format(path))


# --------------------------------------------------------------- well-known payloads
REQUEST_OK: Dict[str, Any] = {
    "success": True,
    "code": 100,
    "data": {
        "authority": TEST_AUTHORITY,
        "payment_url": "https://pna.shaparak.ir/mhui/home/index/SANDBOX_MTAwMTAw",
    },
    "message": "درخواست پرداخت با موفقیت ایجاد شد",
}

VERIFY_OK: Dict[str, Any] = {
    "success": True,
    "data": {"code": 100, "ref_id": TEST_REF_ID, "amount": "1100.00"},
    "message": "پرداخت با موفقیت تایید شد",
}

VERIFY_ALREADY: Dict[str, Any] = {
    "success": True,
    "data": {"code": 101, "ref_id": TEST_REF_ID, "amount": "1100.00"},
    "message": "تراکنش قبلا تایید شده است",
}

INQUIRY_OK: Dict[str, Any] = {
    "success": True,
    "status": "successful",
    "message": "استعلام وضعیت تراکنش با موفقیت انجام شد",
    "errors": [],
}

REVERSE_OK: Dict[str, Any] = {
    "success": True,
    "message": "تراکنش با موفقیت برگشت داده شد",
}

FEE_OK: Dict[str, Any] = {
    "success": True,
    "code": 100,
    "message": "محاسبه کارمزد با موفقیت انجام شد",
    "amount": 1_000_000,
    "fee": 20_000,
    "fee_type": "Merchant",
}


def error(code: int, message: str = "gateway error") -> Dict[str, Any]:
    """Build a gateway error payload of the shape FinoPal uses."""
    return {"success": False, "message": message, "errors": {"code": code, "message": message}}


# ------------------------------------------------------------------- fixtures
@pytest.fixture
def gateway() -> FakeGateway:
    return FakeGateway()


@pytest.fixture
def config() -> Config:
    return Config(merchant_id=TEST_MERCHANT_ID)


@pytest.fixture
def sandbox_config() -> Config:
    return Config(merchant_id=TEST_MERCHANT_ID, sandbox=True)


@pytest.fixture
def finopal(gateway: FakeGateway, config: Config) -> FinoPal:
    return FinoPal(config, transport=CallableTransport(gateway))


@pytest.fixture
def sandbox_finopal(gateway: FakeGateway, sandbox_config: Config) -> FinoPal:
    return FinoPal(sandbox_config, transport=CallableTransport(gateway))
