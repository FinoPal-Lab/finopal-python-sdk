"""Example 4 — reverse a verified transaction.

A reverse is a same-day, fee-free cancellation of a verified payment. It is
only possible for a short window after verify (the docs say 15 minutes; the
error catalogue mentions 30 for some terminals — either way, act fast).

Run::

    export FINOPAL_MERCHANT_ID="fino-xxxx-xxxx-xxxx-xxxx"
    export FINOPAL_SANDBOX=1
    python examples/04_reverse.py FP_636E4A5CBBCE0F222B46829BD74AB4A9

Docs: https://finopal.ir/docs/connectToGateway/reverse
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _shared import build_client, header  # noqa: E402

from finopal import FinoPalException, TransportError, ValidationError  # noqa: E402


def main() -> None:
    header("4. Reversing a verified transaction")

    authority = sys.argv[1] if len(sys.argv) > 1 else "FP_636E4A5CBBCE0F222B46829BD74AB4A9"
    finopal = build_client()

    # A reverse only makes sense on a verified transaction. Check first so we
    # do not burn the short window on a guaranteed failure.
    try:
        status = finopal.inquiries.inquire({"authority": authority})
        print("current status:", status.status)
        if not status.is_paid:
            print("This transaction is not 'successful' — a reverse would fail.")
            return
    except FinoPalException as exc:
        print("could not read the status:", exc.code, exc.message)
        return

    try:
        result = finopal.reversals.reverse({"authority": authority})
    except ValidationError as exc:
        print("invalid input:", exc)
        return
    except FinoPalException as exc:
        print("reverse failed")
        print("  code   :", exc.code)
        print("  message:", exc.message)
        print("  meaning:", exc.describe())
        if exc.code == -1551:
            print("  -> already reversed; nothing to do.")
        elif exc.code == -1552:
            print("  -> the window expired; go through support / settlement.")
        return
    except TransportError as exc:
        print("network problem:", exc)
        print("-> the reverse may or may not have landed; re-run this script.")
        return

    print("\nresult  :", result.message)
    print("success :", result.is_successful)
    print("\nThe transaction is now 'refunded'. Repeat calls will fail with -1551.")


if __name__ == "__main__":
    main()
