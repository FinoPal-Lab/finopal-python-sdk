"""Response-normalisation helpers.

The FinoPal gateway wraps its payloads in a few slightly different shapes:

* ``{"success": true, "code": 100, "data": {...}, "message": "..."}``
* ``{"success": true, "data": {"code": 100, "ref_id": "..."}, "message": "..."}``
* ``{"success": false, "message": "...", "errors": {"code": -11, "message": "..."}}``

These helpers pull the code, message and data block out of any of them so the
resource classes stay readable. Mirrors ``FinoPal\\Sdk\\Client`` in the
WooCommerce plugin.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

__all__ = ["extract_code", "extract_message", "unwrap_data", "as_dict"]


def as_dict(response: Any) -> Dict[str, Any]:
    """Coerce a decoded JSON payload into a plain ``dict``."""
    if isinstance(response, Mapping):
        return dict(response)
    return {}


def extract_code(response: Any) -> Optional[int]:
    """Return the first numeric result code found in ``response``.

    Checks ``code``, then ``data.code``, then ``errors.code`` — the same order
    used by the PHP SDK.
    """
    payload = as_dict(response)

    for candidate in (
        payload.get("code"),
        as_dict(payload.get("data")).get("code"),
        as_dict(payload.get("errors")).get("code"),
    ):
        if candidate is None or isinstance(candidate, bool):
            continue
        try:
            return int(candidate)
        except (TypeError, ValueError):
            continue
    return None


def extract_message(response: Any, fallback: str = "") -> str:
    """Return the most specific human-readable message in ``response``."""
    payload = as_dict(response)

    for candidate in (
        payload.get("message"),
        as_dict(payload.get("errors")).get("message"),
        as_dict(payload.get("data")).get("message"),
    ):
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return fallback


def unwrap_data(response: Any) -> Dict[str, Any]:
    """Return the ``data`` block, falling back to the whole payload.

    ``verify`` nests ``code``/``ref_id`` inside ``data``; ``request`` nests
    ``authority``/``payment_url``. When there is no ``data`` key at all the
    top-level payload is returned, which keeps the callers simple.
    """
    payload = as_dict(response)
    data = payload.get("data")
    if isinstance(data, Mapping):
        return dict(data)
    return payload
