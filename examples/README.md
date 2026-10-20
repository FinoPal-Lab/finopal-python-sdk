"""Examples for the FinoPal Python SDK.

Each file is standalone and runnable. Set the environment first::

    # Windows (PowerShell)
    $env:FINOPAL_MERCHANT_ID = "fino-xxxx-xxxx-xxxx-xxxx"
    $env:FINOPAL_SANDBOX = "1"

    # macOS / Linux
    export FINOPAL_MERCHANT_ID="fino-xxxx-xxxx-xxxx-xxxx"
    export FINOPAL_SANDBOX="1"

    python examples/01_request_payment.py

Files:

* ``01_request_payment.py``  — create a payment and print the redirect URL
* ``02_verify_payment.py``   — verify a payment after the callback
* ``03_inquiry.py``          — read-only status lookup
* ``04_reverse.py``          — reverse a verified transaction
* ``05_fee_calculation.py``  — preview the gateway fee
* ``06_flask_checkout.py``   — full buy → callback → verify flow in Flask
"""
