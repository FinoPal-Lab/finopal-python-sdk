"""Example 6 — a complete buy → callback → verify flow in Flask.

This is the shape most real integrations take: an in-memory "order store",
one route that starts the payment, and one route the buyer returns to.

Run::

    pip install flask
    export FINOPAL_MERCHANT_ID="fino-xxxx-xxxx-xxxx-xxxx"
    export FINOPAL_SANDBOX=1
    export FINOPAL_CALLBACK_URL="http://localhost:5000/payment/callback"
    python examples/06_flask_checkout.py
    # then open http://localhost:5000/buy

Notes:

* The order store is a dict purely to keep the example short — use your real
  database and make the callback handler idempotent.
* ``callback_url`` must match the domain registered on your FinoPal terminal,
  otherwise the gateway answers ``-14``.
* In production serve the callback over HTTPS.
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _shared import build_client, callback_url  # noqa: E402

from flask import Flask, jsonify, redirect, request  # noqa: E402

from finopal import (  # noqa: E402
    FinoPalException,
    TransportError,
    ValidationError,
    parse_callback,
    to_rial,
)

app = Flask(__name__)
finopal = build_client()

# order_id -> {"amount_rial": int, "status": str, "ref_id": str | None}
ORDERS: dict = {}


@app.get("/buy")
def buy():
    """Create an order and send the buyer to FinoPal."""
    order_id = "ORD-" + uuid.uuid4().hex[:8].upper()
    amount_rial = to_rial(12_000, "TOMAN")

    ORDERS[order_id] = {"amount_rial": amount_rial, "status": "new", "ref_id": None}

    try:
        payment = finopal.payments.create(
            {
                "amount": amount_rial,
                "callback_url": callback_url(),
                "order_id": order_id,
                "description": "Sample order {}".format(order_id),
            }
        )
    except ValidationError as exc:
        return jsonify(error="invalid input", detail=str(exc)), 400
    except FinoPalException as exc:
        return jsonify(error="gateway rejected", code=exc.code, detail=exc.message), 502
    except TransportError as exc:
        return jsonify(error="gateway unreachable", detail=str(exc)), 502

    ORDERS[order_id]["authority"] = payment.authority
    ORDERS[order_id]["status"] = "redirected"

    # The buyer must be redirected (302), not just shown the URL.
    return redirect(payment.payment_url, code=302)


@app.get("/payment/callback")
def payment_callback():
    """Where FinoPal sends the buyer back."""
    callback = parse_callback(request.args)

    if not callback.authority:
        return jsonify(error="missing authority in callback"), 400

    order = next(
        (
            (oid, o)
            for oid, o in ORDERS.items()
            if o.get("authority") == callback.authority
        ),
        None,
    )
    if order is None:
        return jsonify(error="unknown authority"), 404

    order_id, record = order

    # Already settled? Return the same answer — the callback can be replayed.
    if record["status"] == "paid":
        return jsonify(order_id=order_id, status="paid", ref_id=record["ref_id"])

    if not callback.is_success:
        record["status"] = "cancelled" if callback.is_cancelled else "failed"
        return jsonify(order_id=order_id, status=record["status"]), 402

    try:
        result = finopal.verifications.verify(
            {"authority": callback.authority, "amount": record["amount_rial"]}
        )
    except FinoPalException as exc:
        if exc.code == 101:  # already verified — still paid
            record["status"] = "paid"
            return jsonify(order_id=order_id, status="paid", ref_id=record["ref_id"])
        record["status"] = "verify_failed"
        return (
            jsonify(order_id=order_id, status="verify_failed", code=exc.code, detail=exc.message),
            502,
        )
    except TransportError as exc:
        # Unknown outcome — ask the gateway before deciding anything.
        try:
            status = finopal.inquiries.inquire({"authority": callback.authority})
            return (
                jsonify(
                    order_id=order_id,
                    status="unknown_after_transport_error",
                    gateway_status=status.status,
                    detail=str(exc),
                ),
                503,
            )
        except FinoPalException as inquiry_exc:
            return jsonify(order_id=order_id, error=inquiry_exc.message), 503

    record["status"] = "paid"
    record["ref_id"] = result.ref_id

    return jsonify(
        order_id=order_id,
        status="paid",
        ref_id=result.ref_id,
        amount=result.amount,
        already_verified=result.is_already_verified,
    )


@app.get("/orders")
def orders():
    return jsonify(ORDERS)


if __name__ == "__main__":
    print("gateway:", finopal.base_url)
    print("callback:", callback_url())
    print("open http://localhost:5000/buy")
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
