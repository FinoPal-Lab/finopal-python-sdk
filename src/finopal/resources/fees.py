"""``fees`` resource — previewing the transaction fee.

Covers ``POST /api/v1/payment/feeCalculation``.
Docs: https://finopal.ir/docs/connectToGateway/feeCalculation

Creates no payment; safe to call as often as you like. Handy for showing the
buyer "you pay X, of which Y is the fee" before they commit, or for costing
out a settlement.
"""

from __future__ import annotations

from typing import Any, Mapping

from finopal.errors.exceptions import FinoPalException, ValidationError
from finopal.models import FeeResponse
from finopal.utils.response import extract_code, extract_message
from finopal.utils.validator import Validator

__all__ = ["Fees"]


class Fees:
    """Calculate the gateway fee for a given amount."""

    FEE_PATH = "/api/v1/payment/feeCalculation"

    def __init__(self, client: Any) -> None:
        self._client = client

    def calculate(self, data: Mapping[str, Any]) -> FeeResponse:
        """Return the fee for ``amount`` (Rials).

        :param data: Mapping with ``amount`` (int, Rials, minimum 1,000).
        :returns: :class:`~finopal.models.FeeResponse` with ``amount``,
            ``fee`` and ``fee_type`` (``Merchant`` or ``Payer``).
        :raises ValidationError: input is invalid.
        :raises FinoPalException: the gateway rejected the request.

        Example::

            fee = finopal.fees.calculate({"amount": 1_000_000})
            print(fee.fee, fee.fee_type)   # 20000 Merchant
        """
        if not isinstance(data, Mapping):
            raise ValidationError("data must be a mapping (dict).")
        if "amount" not in data or data["amount"] is None:
            raise ValidationError("Missing required parameter: 'amount'.")

        payload = {"amount": Validator.validate_amount(data["amount"])}
        response = self._client.post(self.FEE_PATH, payload)

        code = extract_code(response)
        if not response.get("success") and code != 100:
            raise FinoPalException(
                extract_message(response, "Fee calculation failed."), code, response
            )

        return FeeResponse(
            code=code,
            message=extract_message(response, "Fee calculated."),
            amount=response.get("amount"),
            fee=response.get("fee"),
            fee_type=response.get("fee_type"),
            raw=response,
        )

    def calculate_amount(self, amount: int) -> FeeResponse:
        """Keyword-argument convenience wrapper around :meth:`calculate`."""
        return self.calculate({"amount": amount})
