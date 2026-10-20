"""Example 1 — create a payment request.

Run::

    export FINOPAL_MERCHANT_ID="fino-xxxx-xxxx-xxxx-xxxx"
    export FINOPAL_SANDBOX=1
    python examples/01_request_payment.py

Docs: https://finopal.ir/docs/connectToGateway
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _shared import build_client, callback_url, header  # noqa: E402

from finopal import FinoPalException, TransportError, ValidationError, to_rial  # noqa: E402


def main() -> None:
    header("1. Creating a payment request")

    finopal = build_client()
    print("gateway :", finopal.base_url)

    # Most Iranian shops price in Tomans; FinoPal wants Rials.
    amount_rial = to_rial(12_000, "TOMAN")  # 12,000 tomans -> 120,000 rials
    print("amount  :", amount_rial, "rials")

    try:
        payment = finopal.payments.create(
            {
                "amount": amount_rial,
                "callback_url": callback_url(),
                "order_id": "ORD-1001",
                "description": "خرید تستی از فروشگاه نمونه",
                "mobile": "09121234567",
                "email": "buyer@example.com",
                "metadata": {"product_id": "123", "user_id": "960"},
            }
        )
    except ValidationError as exc:
        # Bad input — nothing was sent to the gateway.
        print("invalid input:", exc)
        return
    except FinoPalException as exc:
        # The gateway answered with success=false.
        print("gateway rejected the request:")
        print("  code   :", exc.code)
        print("  message:", exc.message)
        print("  meaning:", exc.describe())
        return
    except TransportError as exc:
        print("could not reach the gateway:", exc)
        return

    print("\nauthority   :", payment.authority)
    print("payment_url :", payment.payment_url)
    if payment.expires_at:
        print("expires_at  :", payment.expires_at)

    print("\n--- next steps ---")
    print("1. Persist the authority against your order (it expires in ~15 min).")
    print("2. Redirect the buyer:")
    print("     HTTP 302 Location:", payment.payment_url)
    print("   or rebuild the URL later from the authority:")
    print("     ", finopal.payments.redirect_url(payment.authority))


if __name__ == "__main__":
    main()
