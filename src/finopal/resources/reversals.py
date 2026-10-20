"""``reversals`` resource — reversing a verified transaction.

Covers ``POST /api/v1/payment/reverse``.
Docs: https://finopal.ir/docs/connectToGateway/reverse

The reverse window is short. After a successful verify you have **15 minutes**
to reverse without a fee; past that the gateway answers ``-1552`` and you must
go through support / settlement instead. Only verified, not-yet-reversed
transactions can be reversed, and the ``merchant_id`` must own the
``authority`` (otherwise ``-1551`` / merchant mismatch).
"""

from __future__ import annotations

from typing import Any, Mapping

from finopal.errors.exceptions import FinoPalException, ValidationError
from finopal.models import ReverseResponse
from finopal.utils.response import extract_code, extract_message
from finopal.utils.validator import Validator

__all__ = ["Reversals"]


class Reversals:
    """Reverse a previously verified payment."""

    REVERSE_PATH = "/api/v1/payment/reverse"

    def __init__(self, client: Any) -> None:
        self._client = client

    def reverse(self, data: Mapping[str, Any]) -> ReverseResponse:
        """Reverse the transaction identified by ``authority``.

        :param data: Mapping with ``authority`` (str, required).
        :returns: :class:`~finopal.models.ReverseResponse`.
        :raises FinoPalException: e.g. ``-1551`` already reversed, ``-1552``
            not verified or the 15-minute window expired.

        Example::

            finopal.reversals.reverse({"authority": "FP_636E4A5C..."})
        """
        if not isinstance(data, Mapping):
            raise ValidationError("data must be a mapping (dict).")
        if not data.get("authority"):
            raise ValidationError("Missing required parameter: 'authority'.")

        payload = {"authority": Validator.validate_authority(data["authority"])}
        response = self._client.post(self.REVERSE_PATH, payload)

        code = extract_code(response)
        if not response.get("success"):
            raise FinoPalException(
                extract_message(response, "Reverse failed."), code, response
            )

        return ReverseResponse(
            success=True,
            message=extract_message(response, "Transaction reversed."),
            code=code,
            raw=response,
        )

    def reverse_authority(self, authority: str) -> ReverseResponse:
        """Keyword-argument convenience wrapper around :meth:`reverse`."""
        return self.reverse({"authority": authority})
