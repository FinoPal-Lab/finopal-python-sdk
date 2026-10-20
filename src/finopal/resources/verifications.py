"""``verifications`` resource — finalising a payment.

Covers ``POST /api/v1/payment/verify``.
Docs: https://finopal.ir/docs/connectToGateway

Golden rule: **only** call verify when the callback query string carried
``Status=OK`` (production) or ``status=OK``/``Status=0`` (sandbox). Never call
it from an unconditional success page — that is how merchants end up
fulfilling unpaid orders.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

from finopal.errors.exceptions import FinoPalException, ValidationError
from finopal.models import VerificationResponse
from finopal.utils.response import extract_code, extract_message, unwrap_data
from finopal.utils.validator import Validator

__all__ = ["Verifications"]

#: 100 = verified now, 101 = already verified (both mean "paid").
SUCCESS_CODES = (100, 101)


class Verifications:
    """Verify a transaction and obtain its ``ref_id``."""

    VERIFY_PATH = "/api/v1/payment/verify"

    def __init__(self, client: Any) -> None:
        self._client = client

    def verify(self, data: Mapping[str, Any]) -> VerificationResponse:
        """Verify the payment identified by ``authority``.

        :param data: Mapping with:

            ``authority`` (str, required) — value from the callback query.
            ``amount`` (int, required) — **exactly** the amount (Rials) sent to
                the payment request, otherwise the gateway answers ``-50``.

        :returns: :class:`~finopal.models.VerificationResponse`.
        :raises ValidationError: input is invalid.
        :raises FinoPalException: the gateway rejected the verification.

        Example::

            from finopal import parse_callback

            cb = parse_callback(request.args)
            if not cb.is_success:
                return render("payment_failed.html")

            try:
                result = finopal.verifications.verify({
                    "authority": cb.authority,
                    "amount": order.amount_rial,
                })
            except FinoPalException as exc:
                if exc.code == 101:      # already verified → still paid
                    ...
                raise

            order.mark_paid(ref_id=result.ref_id)
        """
        if not isinstance(data, Mapping):
            raise ValidationError("data must be a mapping (dict).")

        payload = dict(data)

        if not payload.get("authority"):
            raise ValidationError("Missing required parameter: 'authority'.")
        if "amount" not in payload or payload["amount"] is None:
            raise ValidationError("Missing required parameter: 'amount'.")

        payload["authority"] = Validator.validate_authority(payload["authority"])
        payload["amount"] = Validator.validate_amount(payload["amount"])

        response = self._client.post(self.VERIFY_PATH, payload)

        block = unwrap_data(response)
        code = extract_code(response)
        if code is None:
            code = extract_code(block)

        if code in SUCCESS_CODES:
            return VerificationResponse(
                code=int(code),
                ref_id=str(block["ref_id"]) if block.get("ref_id") is not None else None,
                amount=str(block["amount"]) if block.get("amount") is not None else None,
                message=extract_message(response, "Payment verified."),
                raw=response,
            )

        raise FinoPalException(
            extract_message(response, "Payment verification failed."), code, response
        )

    def verify_authority(
        self, authority: str, amount: int
    ) -> VerificationResponse:
        """Keyword-argument convenience wrapper around :meth:`verify`."""
        return self.verify({"authority": authority, "amount": amount})

    def is_verified(self, authority: str, amount: int) -> bool:
        """Non-throwing check: ``True`` when the transaction is (or was) verified.

        Useful in idempotent callbacks where a replayed request should not
        raise::

            if finopal.verifications.is_verified(authority, amount):
                return render("already_paid.html")
        """
        try:
            self.verify({"authority": authority, "amount": amount})
            return True
        except FinoPalException as exc:
            return exc.code == 101
