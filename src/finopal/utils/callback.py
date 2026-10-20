"""Callback query-string parsing.

After the buyer finishes (or abandons) the payment, FinoPal redirects them to
the merchant's ``callback_url`` with a query string. The parameter casing and
the success sentinel differ between production and sandbox:

===============  =========================  ==============================
Environment      Query string               Success sentinel
===============  =========================  ==============================
Production       ``Authority``, ``Status``  ``Status=OK``
Sandbox          ``authority``, ``status``  ``status=OK`` and/or ``Status=0``
                 (+ ``sandbox=1``, ``token``)
===============  =========================  ==============================

:func:`parse_callback` normalises both shapes into one small result object, so
application code never has to branch on environment. The logic mirrors
``finopal-woocommerce/src/Support/Callback.php``.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Sequence

__all__ = ["CallbackResult", "parse_callback", "is_success_status", "first_param"]


def first_param(keys: Sequence[str], query: Mapping[str, Any]) -> Optional[str]:
    """Return the first present, non-empty scalar value among ``keys``."""
    for key in keys:
        if key in query:
            value = query[key]
            if isinstance(value, (str, int, float)) and str(value) != "":
                return str(value)
    return None


def is_success_status(status: Optional[str]) -> bool:
    """Whether a raw ``Status``/``status`` value means the payment succeeded.

    ``"OK"`` (production) and ``"0"`` (sandbox) both count as success. Note
    that ``"0"`` is truthy here even though it is falsy in many languages.
    """
    if status is None:
        return False
    value = str(status).strip()
    if value == "":
        return False
    return value.upper() == "OK" or value == "0"


class CallbackResult(dict):
    """Normalised callback payload.

    Behaves like a ``dict`` (``result["authority"]``) and also supports
    attribute access (``result.authority``).

    Keys: ``authority``, ``status``, ``is_success``, ``sandbox``, ``raw``.
    """

    def __getattr__(self, item: str) -> Any:
        if item.startswith("_"):
            raise AttributeError(item)
        try:
            return self[item]
        except KeyError as exc:  # pragma: no cover - defensive
            raise AttributeError(
                "CallbackResult has no attribute {!r}".format(item)
            ) from exc

    @property
    def is_cancelled(self) -> bool:
        """True when the buyer explicitly cancelled in the sandbox UI."""
        return str(self.get("status")) == "-138"


def parse_callback(query: Mapping[str, Any]) -> CallbackResult:
    """Normalise a callback query string (``request.args``, ``request.GET``…).

    >>> parse_callback({"Authority": "FP_ABC", "Status": "OK"}).is_success
    True
    >>> parse_callback({"authority": "FP_ABC", "status": "0"}).is_success
    True
    >>> parse_callback({"Authority": "FP_ABC", "Status": "NOK"}).is_success
    False

    :param query: Any mapping of query parameters.
    :returns: A :class:`CallbackResult`.
    """
    if query is None:
        query = {}

    authority = first_param(("Authority", "authority", "Token", "token"), query)
    status = first_param(("Status", "status"), query)
    sandbox_raw = first_param(("sandbox", "Sandbox", "is_sandbox"), query)

    return CallbackResult(
        authority=authority,
        status=status,
        is_success=is_success_status(status),
        sandbox=str(sandbox_raw) in ("1", "true", "True") if sandbox_raw else False,
        raw=dict(query),
    )
