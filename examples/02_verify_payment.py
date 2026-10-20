"""Example 2 — verify a payment after the callback.

The golden rule: **only** verify when the callback query string says the
payment succeeded. Verifying an abandoned or failed transaction is how unpaid
orders get fulfilled.

Run::

    export FINOPAL_MERCHANT_ID="fino-xxxx-xxxx-xxxx-xxxx"
    export FINOPAL_SANDBOX=1
    python examples/02_verify_payment.py FP_636E4A5CBBCE0F222B46829BD74AB4A9 120000

Docs: https://finopal.ir/docs/connectToGateway
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _shared import build_client, header  # noqa: E402

from finopal import (  # noqa: E402
    FinoPalException,
    TransportError,
    ValidationError,
    parse_callback,
)


def main() -> None:
    header("2. Verifying a payment")

    authority = sys.argv[1] if len(sys.argv) > 1 else "FP_636E4A5CBBCE0F222B46829BD74AB4A9"
    amount_rial = int(sys.argv[2]) if len(sys.argv) > 2 else 120_000

    # What FinoPal appends to your callback_url:
    #   production : ?Authority=...&Status=OK
    #   sandbox    : ?authority=...&status=0&sandbox=1
    callback = parse_callback({"Authority": authority, "Status": "OK"})
    print("callback parsed ->", dict(callback))

    if not callback.is_success:
        print("\nPayment was NOT successful (or the buyer cancelled).")
        print("Do not verify; show a failure page instead.")
        return

    finopal = build_client()

    try:
        result = finopal.verifications.verify(
            {"authority": callback.authority, "amount": amount_rial}
        )
    except ValidationError as exc:
        print("invalid input:", exc)
        return
    except FinoPalException as exc:
        print("verify failed")
        print("  code   :", exc.code)
        print("  message:", exc.message)
        print("  meaning:", exc.describe())
        if exc.code == 101:
            print("  -> already verified: the payment IS paid, fulfil the order.")
        return
    except TransportError as exc:
        # We do not know whether the verify landed. Never re-issue the payment;
        # ask the gateway what happened instead (see example 3).
        print("network problem:", exc)
        print("-> call finopal.inquiries.inquire() before deciding.")
        return

    print("\ncode      :", result.code)
    print("ref_id    :", result.ref_id, "  <- show this to the buyer")
    print("amount    :", result.amount)
    print("amount_rial:", result.amount_rial)

    if result.is_already_verified:
        print("\n(code 101) This transaction had already been verified.")
    print("\nFulfil the order and store ref_id for the receipt.")


if __name__ == "__main__":
    main()
