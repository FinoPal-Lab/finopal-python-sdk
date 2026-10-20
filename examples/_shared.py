"""Shared helpers for the example scripts.

Reads credentials from the environment so no secret ever lands in the repo:

    FINOPAL_MERCHANT_ID  (required)  your terminal id
    FINOPAL_SANDBOX      (optional)  "1" to use sandbox.finopal.ir
    FINOPAL_CALLBACK_URL (optional)  defaults to https://example.com/payment/callback
"""

from __future__ import annotations

import os
import sys

from finopal import Config, FinoPal


def build_client() -> FinoPal:
    merchant_id = os.environ.get("FINOPAL_MERCHANT_ID", "").strip()
    if not merchant_id:
        sys.exit(
            "FINOPAL_MERCHANT_ID is not set.\n"
            "  export FINOPAL_MERCHANT_ID='fino-xxxx-xxxx-xxxx-xxxx'\n"
            "  export FINOPAL_SANDBOX=1   # optional"
        )

    sandbox = os.environ.get("FINOPAL_SANDBOX", "").strip() in ("1", "true", "True")
    return FinoPal(Config(merchant_id=merchant_id, sandbox=sandbox))


def callback_url() -> str:
    return os.environ.get(
        "FINOPAL_CALLBACK_URL", "https://example.com/payment/callback"
    )


def header(title: str) -> None:
    print("\n" + "=" * 68)
    print(title)
    print("=" * 68)
