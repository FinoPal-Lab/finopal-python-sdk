"""Example 5 — preview the gateway fee.

Creates no payment; safe to call as often as you like. Use it to show the buyer
"you pay X, of which Y is the fee" before they commit, or to cost out a
settlement.

Run::

    export FINOPAL_MERCHANT_ID="fino-xxxx-xxxx-xxxx-xxxx"
    export FINOPAL_SANDBOX=1
    python examples/05_fee_calculation.py 1000000

Docs: https://finopal.ir/docs/connectToGateway/feeCalculation
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _shared import build_client, header  # noqa: E402

from finopal import FinoPalException, TransportError, ValidationError, to_rial, to_toman  # noqa: E402


def main() -> None:
    header("5. Fee calculation")

    amount_rial = int(sys.argv[1]) if len(sys.argv) > 1 else to_rial(100_000, "TOMAN")
    finopal = build_client()

    try:
        result = finopal.fees.calculate({"amount": amount_rial})
    except ValidationError as exc:
        print("invalid input:", exc)
        return
    except FinoPalException as exc:
        print("fee calculation failed:", exc.code, exc.message, "-", exc.describe())
        return
    except TransportError as exc:
        print("network problem:", exc)
        return

    amount = result.amount if result.amount is not None else amount_rial
    fee = result.fee or 0

    print("amount      :", amount, "rials", "({:,.0f} tomans)".format(to_toman(amount)))
    print("fee         :", fee, "rials", "({:,.0f} tomans)".format(to_toman(fee)))
    print("fee_type    :", result.fee_type)

    if result.is_paid_by_customer:
        print("payer       : the buyer pays the fee on top")
        print("total to charge:", amount + fee, "rials")
    else:
        print("payer       : you (the merchant) absorb the fee")
        print("net to settle :", amount - fee, "rials")

    print("\neffective rate: {:.2%}".format(fee / amount if amount else 0))


if __name__ == "__main__":
    main()
