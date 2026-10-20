"""Human-readable catalogue of FinoPal gateway error codes.

Transcribed from https://finopal.ir/docs/connectToGateway/errorList plus the
codes documented on the reverse / verify pages.
"""

from __future__ import annotations

from typing import Dict, Optional

__all__ = ["ERROR_CODES", "ERROR_SCOPES", "describe", "scope_of"]


#: Numeric code -> English description.
ERROR_CODES: Dict[int, str] = {
    # --- public / terminal level -------------------------------------------
    -9: "Validation error (missing merchant id, callback_url or description; "
        "invalid amount; invalid referrer_id).",
    -10: "Terminal is not valid, please check merchant_id or ip address.",
    -11: "Terminal is not active, please contact our support team.",
    -12: "Too many attempts, please try again later.",
    -13: "Terminal limit reached.",
    -14: "The callback URL domain does not match the registered terminal domain.",
    -15: "Terminal user is suspended, please contact our support team.",
    -16: "Terminal user level is not valid (below silver level).",
    -17: "Terminal user level restriction (blue level).",
    -18: "The referrer address does not match the registered domain.",
    -19: "Terminal user transactions are banned.",
    100: "Success.",
    101: "Verified — the transaction was already verified.",
    # --- PaymentRequest ----------------------------------------------------
    -30: "Terminal does not allow floating shared settlement.",
    -31: "Terminal does not allow wages; add a default bank account in the panel.",
    -32: "Floating wages total exceeds the transaction amount.",
    -33: "Invalid floating wage percentages.",
    -34: "Fixed wages total exceeds the transaction amount.",
    -35: "Too many wage recipients (max parts exceeded).",
    -36: "The minimum amount for floating wages is 10,000 Rials.",
    -37: "One or more IBANs entered for wages are inactive on the bank side.",
    -38: "Wages need an IBAN defined in Shaparak.",
    -39: "Wages have an error, please contact our support team.",
    -40: "Invalid extra params, expire_in is not valid.",
    -41: "Maximum amount is 100,000,000 tomans.",
    # --- PaymentVerify -----------------------------------------------------
    -50: "The paid amount differs from the amount sent to verify.",
    -51: "Session is not valid, the session is not an active paid try.",
    -52: "Unexpected error, please contact our support team.",
    -53: "Session does not belong to this merchant_id.",
    -54: "Invalid authority.",
    -55: "Manual payment request not found.",
    # --- PaymentReverse ----------------------------------------------------
    -60: "Session cannot be reversed with the bank.",
    -61: "Session is not in success status, or it was already reversed.",
    -62: "Terminal ip limit must be active.",
    -63: "Maximum time to reverse this session has expired.",
    -1551: "Transaction has already been reversed.",
    -1552: "Transaction is not verified, or the 15-minute reverse window expired.",
    -1553: "Transaction has already been verified.",
}


#: Which API surface a code belongs to. Handy when building error messages.
ERROR_SCOPES: Dict[str, tuple] = {
    "public": tuple(range(-19, -8)),
    "PaymentRequest": tuple(range(-41, -29)),
    "PaymentVerify": tuple(range(-55, -49)),
    "PaymentReverse": tuple(range(-63, -59)),
}


def describe(code: Optional[int]) -> str:
    """Return a human-readable description for ``code``.

    Unknown codes fall back to a generic message so the caller always gets a
    string it can show to a developer.
    """
    if code is None:
        return "Unknown FinoPal error (no code returned)."
    try:
        numeric = int(code)
    except (TypeError, ValueError):
        return "Unknown FinoPal error (code={!r}).".format(code)
    return ERROR_CODES.get(numeric, "Unknown FinoPal error (code={}).".format(numeric))


def scope_of(code: Optional[int]) -> str:
    """Return the API surface a code belongs to, or ``'unknown'``."""
    if code is None:
        return "unknown"
    try:
        numeric = int(code)
    except (TypeError, ValueError):
        return "unknown"
    for scope, codes in ERROR_SCOPES.items():
        if numeric in codes:
            return scope
    if numeric in (-1551, -1552, -1553):
        return "PaymentReverse" if numeric in (-1551, -1552) else "PaymentVerify"
    if numeric in (100, 101):
        return "public"
    return "unknown"
