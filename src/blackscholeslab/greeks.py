"""Analytical Greek functions for European Black-Scholes-Merton options.

This module implements analytical Greeks for European call and put options with
continuous dividend yield. All Greeks are calculated deterministically using
the closed-form formulas. The implementation reuses existing Black-Scholes-
Merton conventions for inputs, validation, and numerical helpers.

Greeks are defined with specific units and signs. A ValueError is raised when
``time_to_expiry`` or ``volatility`` is zero because several formulas divide by
these values. This prevents misleading zero-value Greek objects and enforces
the mathematical domain requirement for well-defined Greeks.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from blackscholeslab.models import BlackScholesInputs, OptionType
from blackscholeslab.numerical import norm_cdf
from blackscholeslab.validation import validate_option_type


def _norm_pdf(x: float) -> float:
    """Standard normal probability density function (private helper).

    Implemented as:

        phi(x) = exp(-0.5 * x²) / sqrt(2π)

    Args:
        x: Input value (any finite real number).

    Returns:
        The probability density of a standard normal random variable at ``x``.
    """
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


@dataclass(frozen=True)
class OptionGreeks:
    """Immutable result model for European Black-Scholes-Merton Greeks.

    Attributes:
        delta: Price change per one-unit change in the underlying spot price.
        gamma: Delta change per one-unit change in the underlying spot price.
        vega: Price change per 1.0 absolute change in volatility.
        theta: Price change per one year of calendar time passing.
        rho: Price change per 1.0 absolute change in the risk-free rate.
        dividend_rho: Price change per 1.0 absolute change in dividend yield.

    The object is immutable (a frozen dataclass, like ``BlackScholesInputs``) so
    that Greek values cannot be accidentally altered after computation.
    """

    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float
    dividend_rho: float


def greeks_european(
    inputs: BlackScholesInputs,
    option_type: OptionType,
) -> OptionGreeks:
    """Calculate analytical Greeks for a European option using the Black-Scholes-Merton model.

    The Greeks are defined with the following units:

    - Delta: price change per one-unit change in spot.
    - Gamma: delta change per one-unit change in spot.
    - Vega: price change per 1.0 absolute change in volatility.
    - Theta: price change per one year of calendar time passing.
    - Rho: price change per 1.0 absolute change in the risk-free rate.
    - Dividend rho: price change per 1.0 absolute change in dividend yield.

    Domain restrictions:
        - Requires time_to_expiry > 0 (positive time to expiry).
        - Requires volatility > 0 (positive volatility).

    Zero time or zero volatility raises ValueError because:
        - Delta may be discontinuous at expiry.
        - Gamma may become singular or distributional.
        - Several formulas divide by volatility × sqrt(time).
        - Defining a complete OptionGreeks object at those boundaries would be
          misleading.

    Args:
        inputs: Validated :class:`BlackScholesInputs`. Construction validates
            every numeric field, so no further numeric validation is performed
            here.
        option_type: Either :attr:`OptionType.CALL` or :attr:`OptionType.PUT`.

    Returns:
        An :class:`OptionGreeks` object containing the six Greek values.

    Raises:
        TypeError: If ``option_type`` is not a valid :class:`OptionType`.
        ValueError: If ``time_to_expiry == 0`` or ``volatility == 0``.

    Reference formulas:

        Let S = spot, K = strike, T = time_to_expiry, r = risk_free_rate,
            q = dividend_yield, sigma = volatility.

        d1 = [ ln(S / K) + (r - q + 0.5 * sigma^2) * T ] / (sigma * sqrt(T))
        d2 = d1 - sigma * sqrt(T)

        Call delta: exp(-q * T) * N(d1)
        Call theta: [-S * exp(-q * T) * phi(d1) * sigma] / [2 * sqrt(T)]
                   - r * K * exp(-r * T) * N(d2) + q * S * exp(-q * T) * N(d1)
        Call rho: K * T * exp(-r * T) * N(d2)
        Call dividend rho: -S * T * exp(-q * T) * N(d1)

        All Greeks are identical for calls and puts, except for delta, theta,
        rho, and dividend rho which have call and put variants.

        Call gamma: [exp(-q * T) * phi(d1)] / [S * sigma * sqrt(T)]
        Call vega: S * exp(-q * T) * phi(d1) * sqrt(T)

        Put delta: exp(-q * T) * [N(d1) - 1]
        Put theta: [-S * exp(-q * T) * phi(d1) * sigma] / [2 * sqrt(T)]
                  + r * K * exp(-r * T) * N(-d2) - q * S * exp(-q * T) * N(-d1)
        Put rho: -K * T * exp(-r * T) * N(-d2)
        Put dividend rho: S * T * exp(-q * T) * N(-d1)
    """
    option_type = validate_option_type(option_type)

    spot = inputs.spot
    strike = inputs.strike
    time_to_expiry = inputs.time_to_expiry
    risk_free_rate = inputs.risk_free_rate
    volatility = inputs.volatility
    dividend_yield = inputs.dividend_yield

    if time_to_expiry == 0.0:
        raise ValueError("greeks_european requires time_to_expiry > 0, got 0.0") from None

    if volatility == 0.0:
        raise ValueError("greeks_european requires volatility > 0, got 0.0") from None

    sqrt_time = math.sqrt(time_to_expiry)
    d1 = (
        math.log(spot / strike)
        + (risk_free_rate - dividend_yield + 0.5 * volatility * volatility) * time_to_expiry
    ) / (volatility * sqrt_time)
    d2 = d1 - volatility * sqrt_time

    exp_qt = math.exp(-dividend_yield * time_to_expiry)
    exp_rt = math.exp(-risk_free_rate * time_to_expiry)
    phi_d1 = _norm_pdf(d1)

    common_exp_factor = exp_qt

    if option_type is OptionType.CALL:
        n_d1 = norm_cdf(d1)
        n_d2 = norm_cdf(d2)

        delta = common_exp_factor * n_d1

        gamma = common_exp_factor * phi_d1 / (spot * volatility * sqrt_time)

        vega = spot * common_exp_factor * phi_d1 * sqrt_time

        theta = (
            -spot * common_exp_factor * phi_d1 * volatility / (2.0 * sqrt_time)
            - risk_free_rate * strike * exp_rt * n_d2
            + dividend_yield * spot * common_exp_factor * n_d1
        )

        rho = strike * time_to_expiry * exp_rt * n_d2

        dividend_rho = -spot * time_to_expiry * common_exp_factor * n_d1

    else:
        n_d1 = norm_cdf(d1)
        n_neg_d1 = norm_cdf(-d1)
        n_neg_d2 = norm_cdf(-d2)

        delta = common_exp_factor * (n_d1 - 1.0)

        gamma = common_exp_factor * phi_d1 / (spot * volatility * sqrt_time)

        vega = spot * common_exp_factor * phi_d1 * sqrt_time

        theta = (
            -spot * common_exp_factor * phi_d1 * volatility / (2.0 * sqrt_time)
            + risk_free_rate * strike * exp_rt * n_neg_d2
            - dividend_yield * spot * common_exp_factor * n_neg_d1
        )

        rho = -strike * time_to_expiry * exp_rt * n_neg_d2

        dividend_rho = spot * time_to_expiry * common_exp_factor * n_neg_d1

    return OptionGreeks(delta, gamma, vega, theta, rho, dividend_rho)
