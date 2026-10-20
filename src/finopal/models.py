"""Normalised response objects.

Every resource method returns one of the classes below. They subclass ``dict``
so existing dict-style code keeps working, while also offering attribute
access and a few semantic helpers::

    payment = finopal.payments.create({...})
    payment.authority          # attribute access
    payment["payment_url"]     # dict access
    payment.raw                # the untouched gateway payload

``raw`` is always populated, so nothing the gateway returned is ever lost.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

__all__ = [
    "ApiResponse",
    "PaymentRequestResponse",
    "VerificationResponse",
    "InquiryResponse",
    "ReverseResponse",
    "FeeResponse",
]


class ApiResponse(dict):
    """A ``dict`` with attribute access and a ``raw`` payload.

    >>> r = ApiResponse(authority="FP_1", raw={"success": True})
    >>> r.authority
    'FP_1'
    >>> r["authority"]
    'FP_1'
    >>> r.raw
    {'success': True}
    """

    def __getattr__(self, item: str) -> Any:
        # Keep dunder lookups (copy, pickle, ...) from looping into __getattr__.
        if item.startswith("_"):
            raise AttributeError(item)
        try:
            return self[item]
        except KeyError as exc:
            raise AttributeError(
                "{} has no attribute {!r}".format(type(self).__name__, item)
            ) from exc

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain ``dict`` copy (safe to serialise)."""
        return dict(self)

    def __repr__(self) -> str:
        body = ", ".join(
            "{}={!r}".format(key, value) for key, value in self.items() if key != "raw"
        )
        return "{}({})".format(type(self).__name__, body)


class PaymentRequestResponse(ApiResponse):
    """Result of ``POST /api/v1/payment/request``.

    :ivar authority: Unique transaction handle (e.g. ``FP_636E4A5C...``).
    :ivar payment_url: URL the buyer must be redirected to.
    :ivar code: Gateway result code (``100`` on success).
    :ivar sandbox: Whether the call was routed to the sandbox host.
    """

    def __init__(
        self,
        authority: str,
        payment_url: str,
        code: Optional[int] = None,
        message: Optional[str] = None,
        expires_at: Optional[str] = None,
        sandbox: bool = False,
        raw: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(
            authority=authority,
            payment_url=payment_url,
            code=code,
            message=message,
            expires_at=expires_at,
            sandbox=bool(sandbox),
            raw=dict(raw or {}),
        )

    @property
    def is_successful(self) -> bool:
        return self.get("code") == 100


class VerificationResponse(ApiResponse):
    """Result of ``POST /api/v1/payment/verify``.

    :ivar code: ``100`` on the first successful verify, ``101`` when the
        transaction had already been verified (which still means *paid*).
    :ivar ref_id: Shaparak reference id to show the buyer.
    """

    def __init__(
        self,
        code: int,
        ref_id: Optional[str] = None,
        amount: Optional[str] = None,
        message: Optional[str] = None,
        raw: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(
            code=code,
            ref_id=ref_id,
            amount=amount,
            message=message,
            raw=dict(raw or {}),
        )

    @property
    def is_successful(self) -> bool:
        """True for both ``100`` (fresh verify) and ``101`` (already verified)."""
        return self.get("code") in (100, 101)

    @property
    def is_already_verified(self) -> bool:
        return self.get("code") == 101

    @property
    def amount_rial(self) -> Optional[int]:
        """``amount`` parsed back into an integer, when present."""
        raw_amount = self.get("amount")
        if raw_amount is None:
            return None
        try:
            return int(float(raw_amount))
        except (TypeError, ValueError):  # pragma: no cover - defensive
            return None


class InquiryResponse(ApiResponse):
    """Result of ``POST /api/v1/payment/inquiry``.

    Inquiry is **read-only**: it never verifies or fulfils a transaction.
    """

    def __init__(
        self,
        status: Optional[str],
        success: bool = True,
        message: Optional[str] = None,
        errors: Optional[Any] = None,
        raw: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(
            status=status,
            success=bool(success),
            message=message,
            errors=errors if errors is not None else [],
            raw=dict(raw or {}),
        )

    @property
    def is_paid(self) -> bool:
        """True only when the gateway reports ``status == 'successful'``."""
        return str(self.get("status")) == "successful"


class ReverseResponse(ApiResponse):
    """Result of ``POST /api/v1/payment/reverse``."""

    def __init__(
        self,
        success: bool,
        message: Optional[str] = None,
        code: Optional[int] = None,
        raw: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(
            success=bool(success),
            message=message,
            code=code,
            raw=dict(raw or {}),
        )

    @property
    def is_successful(self) -> bool:
        return bool(self.get("success"))


class FeeResponse(ApiResponse):
    """Result of ``POST /api/v1/payment/feeCalculation``.

    :ivar fee: Fee amount in Rials.
    :ivar fee_type: ``Merchant`` (پذیرنده) or ``Payer`` (پرداخت‌کننده).
    """

    def __init__(
        self,
        code: Optional[int] = None,
        message: Optional[str] = None,
        amount: Optional[int] = None,
        fee: Optional[int] = None,
        fee_type: Optional[str] = None,
        raw: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            amount=amount,
            fee=fee,
            fee_type=fee_type,
            raw=dict(raw or {}),
        )

    @property
    def is_successful(self) -> bool:
        return self.get("code") == 100

    @property
    def is_paid_by_customer(self) -> bool:
        """True when the buyer, not the merchant, bears the fee."""
        return str(self.get("fee_type")) == "Payer"
