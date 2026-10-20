"""The :class:`FinoPal` entry point.

Mirrors the ergonomics of the ZarinPal Python SDK — one client object, lazily
created resource namespaces — while speaking FinoPal's REST API exactly as
documented at https://finopal.ir/docs.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from finopal.http.client import HttpClient
from finopal.http.transport import RequestsTransport, Transport
from finopal.resources.fees import Fees
from finopal.resources.inquiries import Inquiries
from finopal.resources.payments import Payments
from finopal.resources.reversals import Reversals
from finopal.resources.verifications import Verifications
from finopal.utils.config import Config

__all__ = ["FinoPal"]


class FinoPal:
    """Client for the FinoPal online payment gateway.

    :param config: A :class:`~finopal.utils.config.Config`.
    :param transport: Optional transport override (proxies, stubs, an async
        adapter...). Defaults to :class:`~finopal.http.transport.RequestsTransport`.

    Example::

        from finopal import FinoPal, Config

        finopal = FinoPal(Config(merchant_id="fino-1234-5678-9012-3456"))

        payment = finopal.payments.create({
            "amount": 1_100,
            "callback_url": "https://shop.example.com/payment/callback",
            "order_id": "ORD-1001",
        })
        print(payment.payment_url)
    """

    def __init__(self, config: Config, transport: Optional[Transport] = None) -> None:
        if not isinstance(config, Config):
            raise TypeError(
                "config must be a finopal.Config instance, got {}.".format(
                    type(config).__name__
                )
            )

        self.config = config
        self.transport: Transport = transport or RequestsTransport(
            timeout=config.timeout,
            verify=config.verify_ssl,
            max_retries=config.max_retries,
        )
        self.http = HttpClient(config, self.transport)

        self._payments: Optional[Payments] = None
        self._verifications: Optional[Verifications] = None
        self._inquiries: Optional[Inquiries] = None
        self._reversals: Optional[Reversals] = None
        self._fees: Optional[Fees] = None

    # --------------------------------------------------------------- resources
    @property
    def payments(self) -> Payments:
        """Create payment requests. ``POST /api/v1/payment/request``."""
        if self._payments is None:
            self._payments = Payments(self.http)
        return self._payments

    @property
    def verifications(self) -> Verifications:
        """Verify payments. ``POST /api/v1/payment/verify``."""
        if self._verifications is None:
            self._verifications = Verifications(self.http)
        return self._verifications

    @property
    def inquiries(self) -> Inquiries:
        """Read-only status lookups. ``POST /api/v1/payment/inquiry``."""
        if self._inquiries is None:
            self._inquiries = Inquiries(self.http)
        return self._inquiries

    @property
    def reversals(self) -> Reversals:
        """Reverse verified transactions. ``POST /api/v1/payment/reverse``."""
        if self._reversals is None:
            self._reversals = Reversals(self.http)
        return self._reversals

    @property
    def fees(self) -> Fees:
        """Preview gateway fees. ``POST /api/v1/payment/feeCalculation``."""
        if self._fees is None:
            self._fees = Fees(self.http)
        return self._fees

    # -------------------------------------------------------------- primitives
    @property
    def base_url(self) -> str:
        """Effective gateway host for this client."""
        return self.config.base_url

    @property
    def is_sandbox(self) -> bool:
        """Whether this client points at the sandbox host."""
        return bool(self.config.sandbox)

    def request(
        self,
        method: str,
        path: str,
        payload: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Escape hatch for endpoints the SDK does not wrap yet.

        ``merchant_id`` is injected automatically. Only ``POST`` is supported
        today because that is all the FinoPal gateway exposes::

            finopal.request("POST", "/api/v1/payment/inquiry",
                            {"authority": "FP_..."})
        """
        if str(method).upper() != "POST":
            raise ValueError(
                "The FinoPal gateway only exposes POST endpoints; got {!r}.".format(
                    method
                )
            )
        return self.http.post(path, payload)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        mode = "sandbox" if self.is_sandbox else "live"
        return "FinoPal(merchant_id={!r}, mode={!r})".format(
            self.config.merchant_id, mode
        )
