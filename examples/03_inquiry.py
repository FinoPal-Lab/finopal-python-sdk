"""Example 3 — read-only status lookup (inquiry).

Inquiry never verifies or fulfils a transaction. Use it when:

* a verify call timed out and you need to know what actually happened;
* a support agent asks "did order #1234 get paid?";
* you want to reconcile a batch of orders against the gateway.

Run::

    export FINOPAL_MERCHANT_ID="fino-xxxx-xxxx-xxxx-xxxx"
    export FINOPAL_SANDBOX=1
    python examples/03_inquiry.py FP_636E4A5CBBCE0F222B46829BD74AB4A9

Docs: https://finopal.ir/docs/connectToGateway/Inquiry
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _shared import build_client, header  # noqa: E402

from finopal import FinoPalException, TransportError  # noqa: E402

MEANING = {
    "pending": "waiting for the buyer to pay",
    "successful": "paid — you should verify it if you have not already",
    "failed": "the attempt failed",
    "cancelled": "the buyer cancelled",
    "refunded": "reversed / refunded",
    "callback": "returned from the gateway, not settled yet",
}


def main() -> None:
    header("3. Inquiry (status only)")

    authority = sys.argv[1] if len(sys.argv) > 1 else "FP_636E4A5CBBCE0F222B46829BD74AB4A9"
    finopal = build_client()

    try:
        result = finopal.inquiries.inquire({"authority": authority})
    except FinoPalException as exc:
        print("inquiry failed")
        print("  code   :", exc.code)
        print("  message:", exc.message)
        print("  meaning:", exc.describe())
        return
    except TransportError as exc:
        print("network problem:", exc)
        return

    status = result.status
    print("status  :", status)
    print("meaning :", MEANING.get(str(status), "unknown status"))
    print("message :", result.message)
    print("errors  :", result.errors)

    if result.is_paid:
        print("\n-> The transaction is paid. Call verify to obtain the ref_id")
        print("   if you have not stored it yet.")

    # The enum flavour, handy for branching in application code:
    from finopal import TransactionStatus

    print("\nenum    :", finopal.inquiries.status_of(authority) is TransactionStatus.SUCCESSFUL)


if __name__ == "__main__":
    main()
