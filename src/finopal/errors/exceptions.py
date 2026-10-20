"""Exception hierarchy for the FinoPal SDK.

Every exception raised by this package derives from :class:`FinoPalError`, so
``except FinoPalError`` is always a safe catch-all::

    from finopal import FinoPalError, FinoPalException, ValidationError

    try:
        payment = finopal.payments.create({...})
    except ValidationError as exc:
        # Bad input caught before the HTTP call.
        ...
    except FinoPalException as exc:
        # The gateway answered with success=false or a non-100 code.
        print(exc.code, exc.describe())
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

__all__ = [
    "FinoPalError",
    "ValidationError",
    "TransportError",
    "FinoPalException",
    "ApiError",
]


class FinoPalError(Exception):
    """Base class for every error raised by the SDK."""


class ValidationError(FinoPalError):
    """Raised when input fails client-side validation.

    No HTTP request is made when this is raised.
    """


class TransportError(FinoPalError):
    """Raised when the gateway could not be reached or answered with garbage.

    Covers DNS/TLS/connection failures, timeouts, non-JSON bodies and 5xx
    responses. It means "we do not know what happened", which is exactly why
    the caller should retry the *inquiry* endpoint rather than blindly
    re-issuing a payment request.

    :ivar status_code: HTTP status if a response was received, else ``None``.
    :ivar response: Decoded body if available, else ``{}``.
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response: Dict[str, Any] = dict(response or {})

    def __str__(self) -> str:  # pragma: no cover - trivial
        if self.status_code is not None:
            return "{} (HTTP {})".format(self.message, self.status_code)
        return self.message


class FinoPalException(FinoPalError):
    """Raised when the gateway rejects a request.

    Carries the numeric gateway ``code`` so callers can branch on it::

        from finopal.utils.error_codes import describe

        try:
            finopal.verifications.verify({"authority": authority, "amount": amount})
        except FinoPalException as exc:
            if exc.code == -50:
                ...  # amount mismatch
            elif exc.code == 101:
                ...  # already verified — treat as success

    :ivar code: Numeric gateway code, or ``None`` if none was returned.
    :ivar message: Human-readable message from the gateway.
    :ivar response: The full decoded payload, useful for logging.
    """

    def __init__(
        self,
        message: str,
        code: Optional[int] = None,
        response: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.response: Dict[str, Any] = dict(response or {})

    def describe(self) -> str:
        """English description of :attr:`code` from the published error list."""
        # Imported lazily: ``finopal.utils`` pulls in the validator, which in
        # turn imports this module — a module-level import would be circular.
        from finopal.utils.error_codes import describe

        return describe(self.code)

    @property
    def scope(self) -> str:
        """API surface the code belongs to (``PaymentRequest``, ...)."""
        from finopal.utils.error_codes import scope_of

        return scope_of(self.code)

    def __str__(self) -> str:
        if self.code is None:
            return self.message
        return "{} (code={})".format(self.message, self.code)


#: Backwards/forwards-friendly alias — ``ApiError`` reads better in some codebases.
ApiError = FinoPalException
