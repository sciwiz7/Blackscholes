"""European Black-Scholes-Merton pricing core for BlackScholesLab.

This module implements analytical pricing for European call and put options
with continuous dividend yield. It depends on the typed input model, the
reusable validation helpers, and the internal numerical helpers. It does not
depend on any interface, CLI, or web layer.
"""

from __future__ import annotations

import math

from blackscholeslab.models import BlackScholesInputs, OptionType
from blackscholeslab.numerical import norm_cdf
from blackscholeslab.validation import validate_option_type


def price_european(inputs: BlackScholesInputs, option_type: OptionType) -> float:
    """Price a European option under the Black-Scholes-Merton model.

    Args:
        inputs: Validated :class:`BlackScholesInputs`. Construction validates
            every numeric field, so no further numeric validation is performed
            here.
        option_type: Either :attr:`OptionType.CALL` or :attr:`OptionType.PUT`.

    Returns:
        The option price as a ``float``.

    Raises:
        TypeError: If ``option_type`` is not a valid :class:`OptionType`.

    Behaviour:
        - At expiry (``time_to_expiry == 0``) the price equals the intrinsic
          payoff; rates, dividend yield, and volatility do not affect it.
        - At zero volatility (``volatility == 0`` with positive time to
          expiry) the exact discounted payoff is returned; the regular d1/d2
          formula is avoided to prevent division by zero.
        - Otherwise the standard Black-Scholes-Merton formulas with continuous
          dividend yield are used.
    """
    option_type = validate_option_type(option_type)

    spot = inputs.spot
    strike = inputs.strike
    time_to_expiry = inputs.time_to_expiry
    risk_free_rate = inputs.risk_free_rate
    volatility = inputs.volatility
    dividend_yield = inputs.dividend_yield

    if time_to_expiry == 0.0:
        if option_type is OptionType.CALL:
            return max(spot - strike, 0.0)
        return max(strike - spot, 0.0)

    if volatility == 0.0:
        discounted_spot = spot * math.exp(-dividend_yield * time_to_expiry)
        discounted_strike = strike * math.exp(-risk_free_rate * time_to_expiry)
        if option_type is OptionType.CALL:
            return max(discounted_spot - discounted_strike, 0.0)
        return max(discounted_strike - discounted_spot, 0.0)

    sqrt_time = math.sqrt(time_to_expiry)
    d1 = (
        math.log(spot / strike)
        + (risk_free_rate - dividend_yield + 0.5 * volatility * volatility) * time_to_expiry
    ) / (volatility * sqrt_time)
    d2 = d1 - volatility * sqrt_time

    discounted_spot = spot * math.exp(-dividend_yield * time_to_expiry)
    discounted_strike = strike * math.exp(-risk_free_rate * time_to_expiry)

    if option_type is OptionType.CALL:
        return discounted_spot * norm_cdf(d1) - discounted_strike * norm_cdf(d2)
    return discounted_strike * norm_cdf(-d2) - discounted_spot * norm_cdf(-d1)
