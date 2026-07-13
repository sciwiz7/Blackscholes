"""Typed input model and option-type definition for BlackScholesLab.

This module defines the immutable pricing input model and the public
``OptionType`` enumeration. It depends only on the reusable validation
helpers in :mod:`blackscholeslab.validation` and must not depend on the
pricing core.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from blackscholeslab.validation import validate_inputs


class OptionType(Enum):
    """Type of a European option.

    Only ``CALL`` and ``PUT`` are supported. Arbitrary string or numeric
    values are rejected by :func:`price_european`.
    """

    CALL = "call"
    PUT = "put"


@dataclass(frozen=True)
class BlackScholesInputs:
    """Immutable, typed inputs for European Black-Scholes-Merton pricing.

    Attributes:
        spot: Current price of the underlying asset. Must be strictly positive.
        strike: Exercise price of the option. Must be strictly positive.
        time_to_expiry: Time to expiry in years. Must be non-negative; ``0``
            means the option is at expiry.
        risk_free_rate: Continuously compounded annual risk-free rate. Must be
            finite; negative values are allowed.
        volatility: Annualised volatility as a decimal. Must be non-negative;
            ``0`` selects the deterministic discounted-payoff path.
        dividend_yield: Continuously compounded annual dividend yield. Must be
            finite; negative values are allowed. Defaults to ``0.0``.

    Instances are validated on construction. Malformed or invalid inputs raise
    :class:`TypeError` (wrong type) or :class:`ValueError` (invalid value).
    """

    spot: float
    strike: float
    time_to_expiry: float
    risk_free_rate: float
    volatility: float
    dividend_yield: float = 0.0

    def __post_init__(self) -> None:
        validate_inputs(self)
