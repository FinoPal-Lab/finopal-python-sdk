"""``inquiries`` resource — read-only transaction status.

Covers ``POST /api/v1/payment/inquiry``.
Docs: https://finopal.ir/docs/connectToGateway/Inquiry

.. warning::
   Inquiry **never** verifies or fulfils a transaction. It only reports status.
   Use :meth:`finopal.resources.verifications.Verifications.verify` to settle a
   payment. Inquiry is the right tool when a verify call timed out and you need
   to find out what actually happened before deciding whether to retry.
"""

from __future__ import annotations

from typing import Any, Mapping

from finopal.errors.exceptions import FinoPalException, ValidationError
from finopal.models import InquiryResponse
from finopal.utils.enums import TransactionStatus
from finopal.utils.response import extract_code, extract_message
from finopal.utils.validator import Validator

__all__ = ["Inquiries"]


class Inquiries:
    """Query the status of a transaction without changing it."""

    INQUIRY_PATH = "/api/v1/payment/inquiry"

    def __init__(self, client: Any) -> None:
        self._client = client

    def inquire(self, data: Mapping[str, Any]) -> InquiryResponse:
        """Return the current status of ``authority``.

        :param data: Mapping with ``authority`` (str, required).
        :returns: :class:`~finopal.models.InquiryResponse` whose ``status`` is
            one of ``pending``, ``successful``, ``failed``, ``cancelled``,
            ``refunded`` or ``callback``.
        :raises FinoPalException: the gateway could not answer (e.g. ``-11``
            "transaction not found").
        """
        if not isinstance(data, Mapping):
            raise ValidationError("data must be a mapping (dict).")
        if not data.get("authority"):
            raise ValidationError("Missing required parameter: 'authority'.")

        payload = {"authority": Validator.validate_authority(data["authority"])}
        response = self._client.post(self.INQUIRY_PATH, payload)

        if not response.get("success"):
            raise FinoPalException(
                extract_message(response, "Inquiry failed."),
                extract_code(response),
                response,
            )

        return InquiryResponse(
            status=response.get("status"),
            success=True,
            message=extract_message(response, "Inquiry succeeded."),
            errors=response.get("errors", []),
            raw=response,
        )

    def status_of(self, authority: str) -> TransactionStatus:
        """Convenience wrapper returning a :class:`TransactionStatus` enum.

        Unknown values are passed through as a raw string comparison target,
        so the enum is returned as-is when recognised.
        """
        result = self.inquire({"authority": authority})
        try:
            return TransactionStatus(str(result.get("status")))
        except ValueError:
            return result.get("status")  # type: ignore[return-value]
