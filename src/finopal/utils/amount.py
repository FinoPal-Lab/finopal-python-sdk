"""Amount helpers.

FinoPal expects every amount as an **integer in Rials**. Most Iranian shops
price in Tomans, and store plugins may price in Toman, Thousand Toman or
Thousand Rial. These helpers centralise the conversion so callers never get it
wrong by a factor of ten.

The conversion table matches the FinoPal WooCommerce plugin
(``finopal-woocommerce/src/Support/Amount.php``).
"""

from __future__ import annotations

from typing import Union

from finopal.utils.enums import Currency

__all__ = ["to_rial", "to_toman", "MIN_AMOUNT_RIAL", "MAX_AMOUNT_RIAL"]

Number = Union[int, float, str]

#: Documented minimum accepted by ``feeCalculation`` (and by ``request``).
MIN_AMOUNT_RIAL = 1_000

#: Documented maximum: 100,000,000 tomans.
MAX_AMOUNT_RIAL = 1_000_000_000

_MULTIPLIERS = {
    "irr": 1,
    "rial": 1,
    "irt": 10,
    "toman": 10,
    "irhr": 1_000,
    "irht": 10_000,
}


def to_rial(amount: Number, currency: Union[str, Currency] = Currency.IRR) -> int:
    """Convert ``amount`` in ``currency`` to an integer number of Rials.

    :param amount: Numeric value (``int``, ``float`` or numeric ``str``).
    :param currency: ``IRR``/``IRT``/``TOMAN``/``IRHR``/``IRHT``. Unknown
        values are treated as Rial, matching the plugin behaviour.

    >>> to_rial(12_000, "TOMAN")
    120000
    >>> to_rial(1_100)
    1100
    """
    key = str(getattr(currency, "value", currency)).strip().lower()
    multiplier = _MULTIPLIERS.get(key, 1)

    try:
        value = float(amount)
    except (TypeError, ValueError) as exc:
        raise ValueError("amount must be numeric, got {!r}".format(amount)) from exc

    return int(round(value * multiplier))


def to_toman(amount_rial: Number) -> float:
    """Convert an integer Rial amount back to Tomans.

    >>> to_toman(120_000)
    12000.0
    """
    try:
        return float(amount_rial) / 10.0
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "amount_rial must be numeric, got {!r}".format(amount_rial)
        ) from exc
