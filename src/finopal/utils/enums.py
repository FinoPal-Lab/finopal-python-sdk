"""Enumerations used across the FinoPal SDK.

These are convenience wrappers around the string/number values documented at
https://finopal.ir/docs — they never replace raw values, they only make them
easier to compare against.
"""

from __future__ import annotations

from enum import Enum, IntEnum

__all__ = [
    "Currency",
    "TransactionStatus",
    "CallbackStatus",
    "FeeType",
    "ResultCode",
]


class Currency(str, Enum):
    """Currency codes understood by :func:`finopal.utils.amount.to_rial`."""

    IRR = "IRR"  # ریال — the unit FinoPal expects on the wire
    IRT = "IRT"  # تومان
    TOMAN = "TOMAN"
    IRHR = "IRHR"  # هزار ریال
    IRHT = "IRHT"  # هزار تومان


class TransactionStatus(str, Enum):
    """Values returned by the ``inquiry`` endpoint."""

    PENDING = "pending"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    CALLBACK = "callback"


class CallbackStatus(str, Enum):
    """``Status`` query-string values sent to ``callback_url``.

    The live gateway sends ``OK`` / ``NOK``; the sandbox sends ``0`` / ``-1``.
    """

    OK = "OK"
    NOK = "NOK"
    SANDBOX_SUCCESS = "0"
    SANDBOX_FAILED = "-1"
    SANDBOX_CANCELLED = "-138"


class FeeType(str, Enum):
    """Who pays the transaction fee."""

    MERCHANT = "Merchant"  # پذیرنده
    PAYER = "Payer"  # پرداخت‌کننده


class ResultCode(IntEnum):
    """Gateway result codes that matter to application logic."""

    SUCCESS = 100
    ALREADY_VERIFIED = 101
