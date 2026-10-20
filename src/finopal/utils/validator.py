"""Client-side input validation.

Catching bad input locally produces a far better developer experience than a
round-trip that comes back as ``-9 Validation error``. Every rule below is
derived from the FinoPal API documentation.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Optional
from urllib.parse import urlparse

from finopal.errors.exceptions import ValidationError
from finopal.utils.amount import MAX_AMOUNT_RIAL, MIN_AMOUNT_RIAL

__all__ = ["Validator"]

#: Terminal ids look like ``fino-xxxx-xxxx-xxxx-xxxx`` but FinoPal has used
#: several formats over time, so we only enforce the loose shape.
_MERCHANT_ID_RE = re.compile(r"^[A-Za-z0-9_\-]{8,64}$")

#: ``FP_636E4A5CBB...`` (production) and ``A0000...`` (legacy Shaparak style).
_AUTHORITY_RE = re.compile(r"^[A-Za-z0-9_\-]{8,64}$")

_MOBILE_RE = re.compile(r"^(?:\+98|0098|98|0)?9\d{9}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")

_MAX_DESCRIPTION_LENGTH = 255
_MAX_ORDER_ID_LENGTH = 100


class Validator:
    """Namespace for the validation helpers. All methods are static."""

    @staticmethod
    def validate_amount(amount: Any, *, minimum: int = MIN_AMOUNT_RIAL) -> int:
        """Ensure ``amount`` is an integer Rial value inside the allowed range.

        :raises ValidationError: if the value is not numeric, is not a whole
            number, is below ``minimum`` or exceeds the documented maximum.
        """
        if isinstance(amount, bool):
            raise ValidationError("amount must be a number, not a boolean.")

        try:
            value = float(amount)
        except (TypeError, ValueError) as exc:
            raise ValidationError(
                "amount must be a number in Rials, got {!r}".format(amount)
            ) from exc

        if value != int(value):
            raise ValidationError(
                "amount must be a whole number of Rials, got {!r}.".format(amount)
            )

        rial = int(value)

        if rial < minimum:
            raise ValidationError(
                "amount must be at least {} Rials, got {}.".format(minimum, rial)
            )
        if rial > MAX_AMOUNT_RIAL:
            raise ValidationError(
                "amount must not exceed {} Rials (100,000,000 tomans), got {}.".format(
                    MAX_AMOUNT_RIAL, rial
                )
            )
        return rial

    @staticmethod
    def validate_merchant_id(merchant_id: Any) -> str:
        if not isinstance(merchant_id, str) or not _MERCHANT_ID_RE.match(merchant_id):
            raise ValidationError(
                "merchant_id looks invalid: {!r}. Expected the 24-character "
                "terminal id from your FinoPal panel.".format(merchant_id)
            )
        return merchant_id

    @staticmethod
    def validate_authority(authority: Any) -> str:
        if not isinstance(authority, str) or not _AUTHORITY_RE.match(authority.strip()):
            raise ValidationError(
                "authority looks invalid: {!r}. Expected the value returned by "
                "the payment request (e.g. FP_636E4A5C...).".format(authority)
            )
        return authority.strip()

    @staticmethod
    def validate_callback_url(url: Any, *, require_https: bool = False) -> str:
        if not isinstance(url, str) or not url.strip():
            raise ValidationError("callback_url is required and must be a string.")

        url = url.strip()
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            raise ValidationError(
                "callback_url must be an absolute http(s) URL, got {!r}.".format(url)
            )
        if not parsed.netloc:
            raise ValidationError(
                "callback_url is missing a host, got {!r}.".format(url)
            )
        if require_https and parsed.scheme != "https":
            raise ValidationError(
                "callback_url must use https, got {!r}.".format(url)
            )
        return url

    @staticmethod
    def validate_order_id(order_id: Any) -> str:
        if order_id is None or str(order_id).strip() == "":
            raise ValidationError("order_id is required by the FinoPal gateway.")
        value = str(order_id).strip()
        if len(value) > _MAX_ORDER_ID_LENGTH:
            raise ValidationError(
                "order_id must be {} characters or fewer, got {}.".format(
                    _MAX_ORDER_ID_LENGTH, len(value)
                )
            )
        return value

    @staticmethod
    def validate_description(description: Any) -> str:
        if not isinstance(description, str):
            raise ValidationError("description is required and must be a string.")
        value = description.strip()
        if value == "" or len(value) > _MAX_DESCRIPTION_LENGTH:
            raise ValidationError(
                "description is required and must be {} characters or fewer, got {}.".format(
                    _MAX_DESCRIPTION_LENGTH, len(value)
                )
            )
        return value

    @staticmethod
    def validate_mobile(mobile: Any) -> str:
        value = str(mobile).strip()
        if not _MOBILE_RE.match(value):
            raise ValidationError(
                "mobile must be an Iranian mobile number, got {!r}.".format(mobile)
            )
        return value

    @staticmethod
    def validate_email(email: Any) -> str:
        value = str(email).strip()
        if not _EMAIL_RE.match(value):
            raise ValidationError("email looks invalid: {!r}.".format(email))
        return value

    @staticmethod
    def validate_metadata(metadata: Any) -> Mapping[str, Any]:
        if not isinstance(metadata, Mapping):
            raise ValidationError(
                "metadata must be a mapping (dict), got {!r}.".format(type(metadata))
            )
        return metadata

    @staticmethod
    def validate_currency(currency: Any) -> Optional[str]:
        allowed = {"IRR", "IRT", "TOMAN", "IRHR", "IRHT"}
        value = str(getattr(currency, "value", currency)).upper()
        if value not in allowed:
            raise ValidationError(
                "currency must be one of {}, got {!r}.".format(
                    ", ".join(sorted(allowed)), currency
                )
            )
        return value
