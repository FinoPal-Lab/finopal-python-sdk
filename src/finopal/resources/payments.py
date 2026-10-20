"""``payments`` resource — creating a payment and building the redirect URL.

Covers ``POST /api/v1/payment/request`` and the redirect helper.
Docs: https://finopal.ir/docs/connectToGateway
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

from finopal.errors.exceptions import FinoPalException, ValidationError
from finopal.models import PaymentRequestResponse
from finopal.utils.response import extract_code, extract_message, unwrap_data
from finopal.utils.validator import Validator

__all__ = ["Payments"]


class Payments:
    """Create payment requests and build the buyer redirect URL."""

    REQUEST_PATH = "/api/v1/payment/request"
    REDIRECT_PATH = "/api/v1/payment/redirect/{authority}"

    def __init__(self, client: Any) -> None:
        self._client = client

    # ------------------------------------------------------------------ create
    def create(self, data: Mapping[str, Any]) -> PaymentRequestResponse:
        """Create a payment request.

        :param data: Mapping with the FinoPal request fields:

            ``amount`` (int, **Rials**, required)
                Transaction amount. Use :func:`finopal.to_rial` to convert
                from Tomans.
            ``callback_url`` (str, required)
                Absolute http(s) URL the buyer returns to. Must match the
                domain registered on the terminal, otherwise the gateway
                answers ``-14``.
            ``order_id`` (str, required)
                Your own order identifier (max 100 chars).
            ``description`` (str, required)
                Free text, max 255 characters.
            ``mobile`` / ``email`` (str, optional)
                Buyer contact details.
            ``metadata`` (dict, optional)
                Arbitrary extra fields (documented keys: ``user_id``,
                ``product_id``).

        :returns: :class:`~finopal.models.PaymentRequestResponse` with
            ``authority`` and ``payment_url``.
        :raises ValidationError: input is invalid — no request is sent.
        :raises FinoPalException: the gateway rejected the request.
        :raises TransportError: the gateway could not be reached.

        Example::

            payment = finopal.payments.create({
                "amount": 1_100,
                "callback_url": "https://shop.example.com/payment/callback",
                "order_id": "ORD-1001",
                "description": "Order #1001",
            })
            redirect_the_buyer_to(payment.payment_url)
        """
        if not isinstance(data, Mapping):
            raise ValidationError("data must be a mapping (dict).")

        payload = dict(data)

        for field in ("amount", "callback_url", "order_id", "description"):
            if field not in payload or payload[field] is None:
                raise ValidationError(
                    "Missing required parameter: {!r}.".format(field)
                )

        payload["amount"] = Validator.validate_amount(payload["amount"])
        payload["callback_url"] = Validator.validate_callback_url(payload["callback_url"])
        payload["order_id"] = Validator.validate_order_id(payload["order_id"])
        payload["description"] = Validator.validate_description(payload["description"])
        if payload.get("mobile"):
            payload["mobile"] = Validator.validate_mobile(payload["mobile"])
        if payload.get("email"):
            payload["email"] = Validator.validate_email(payload["email"])
        if payload.get("metadata") is not None:
            Validator.validate_metadata(payload["metadata"])

        response = self._client.post(self.REQUEST_PATH, payload)

        code = extract_code(response)
        if not response.get("success") or code != 100:
            raise FinoPalException(
                extract_message(response, "Payment request failed."), code, response
            )

        block = unwrap_data(response)
        authority = block.get("authority")
        if not authority:
            raise FinoPalException(
                "The gateway reported success but returned no authority.",
                code,
                response,
            )

        payment_url = block.get("payment_url") or self.redirect_url(str(authority))

        return PaymentRequestResponse(
            authority=str(authority),
            payment_url=str(payment_url),
            code=code,
            message=extract_message(response, "Payment request created."),
            expires_at=block.get("expires_at"),
            sandbox=bool(self._client.config.sandbox),
            raw=response,
        )

    def request(
        self,
        amount: int,
        callback_url: str,
        order_id: str,
        description: str,
        mobile: Optional[str] = None,
        email: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> PaymentRequestResponse:
        """Keyword-argument convenience wrapper around :meth:`create`.

        Example::

            payment = finopal.payments.request(
                amount=1_100,
                callback_url="https://shop.example.com/payment/callback",
                order_id="ORD-1001",
                description="Order #1001",
            )
        """
        data: dict = {
            "amount": amount,
            "callback_url": callback_url,
            "order_id": order_id,
            "description": description,
        }
        if mobile is not None:
            data["mobile"] = mobile
        if email is not None:
            data["email"] = email
        if metadata is not None:
            data["metadata"] = metadata
        return self.create(data)

    # ---------------------------------------------------------------- redirect
    def redirect_url(self, authority: str) -> str:
        """Absolute URL that sends the buyer to the FinoPal payment page.

        Usually you do not need this — ``create()`` already returns
        ``payment_url``. It is here for flows that persist only the authority
        and rebuild the URL later::

            finopal.payments.redirect_url("FP_636E4A5C...")
        """
        authority = Validator.validate_authority(authority)
        path = self.REDIRECT_PATH.format(authority=authority)
        return self._client.config.endpoint(path)

    #: Alias kept for parity with the ZarinPal SDK's ``generate_payment_url``.
    generate_payment_url = redirect_url
