"""FinoPal Python SDK — a friendly client for the FinoPal payment gateway.

Quick start::

    from finopal import FinoPal, Config

    finopal = FinoPal(Config(merchant_id="fino-xxxx-xxxx-xxxx-xxxx", sandbox=True))

    payment = finopal.payments.create({
        "amount": 1_100,                                  # Rials
        "callback_url": "https://shop.example.com/callback",
        "order_id": "ORD-1001",
    })
    print(payment.payment_url)

    # ... buyer returns to callback_url ...

    from finopal import parse_callback

    cb = parse_callback(request.args)
    if cb.is_success:
        result = finopal.verifications.verify({
            "authority": cb.authority,
            "amount": 1_100,
        })
        print(result.ref_id)

Docs: https://finopal.ir/docs
"""

from finopal.errors import (
    ApiError,
    FinoPalError,
    FinoPalException,
    TransportError,
    ValidationError,
)
from finopal.finopal import FinoPal
from finopal.http import CallableTransport, RequestsTransport, Transport
from finopal.models import (
    ApiResponse,
    FeeResponse,
    InquiryResponse,
    PaymentRequestResponse,
    ReverseResponse,
    VerificationResponse,
)
from finopal.utils import (
    MAX_AMOUNT_RIAL,
    MIN_AMOUNT_RIAL,
    CallbackResult,
    CallbackStatus,
    Config,
    Currency,
    FeeType,
    ResultCode,
    TransactionStatus,
    Validator,
    describe,
    is_success_status,
    parse_callback,
    to_rial,
    to_toman,
)

__version__ = "0.1.0"

__all__ = [
    # client
    "FinoPal",
    "Config",
    # transports
    "Transport",
    "RequestsTransport",
    "CallableTransport",
    # errors
    "FinoPalError",
    "ValidationError",
    "TransportError",
    "FinoPalException",
    "ApiError",
    # response models
    "ApiResponse",
    "PaymentRequestResponse",
    "VerificationResponse",
    "InquiryResponse",
    "ReverseResponse",
    "FeeResponse",
    # helpers
    "Validator",
    "to_rial",
    "to_toman",
    "MIN_AMOUNT_RIAL",
    "MAX_AMOUNT_RIAL",
    "parse_callback",
    "is_success_status",
    "CallbackResult",
    "describe",
    # enums
    "Currency",
    "TransactionStatus",
    "CallbackStatus",
    "FeeType",
    "ResultCode",
    "__version__",
]
