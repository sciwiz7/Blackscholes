"""Implied-volatility solver for European Black-Scholes-Merton options.

This module implements a transparent, deterministic implied-volatility solver
for European call and put options under the Black-Scholes-Merton framework. It
reuses the existing pricing oracle :func:`blackscholeslab.pricing.price_european`
as the single source of truth for option prices, and never reimplements the
pricing formula.

The solver:

- validates observed market prices against European no-arbitrage bounds;
- returns exactly ``0.0`` when the market price equals the zero-volatility
  lower bound;
- adaptively brackets the implied volatility when the default upper bound is
  insufficient;
- applies deterministic bisection with explicit price and volatility
  tolerances and a maximum iteration count.

It depends on the typed input model, validation helpers, and pricing core, and
on nothing outside the standard library.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from blackscholeslab.models import BlackScholesInputs, OptionType
from blackscholeslab.pricing import price_european
from blackscholeslab.validation import validate_option_type, validate_real_number

if TYPE_CHECKING:
    from blackscholeslab.models import OptionType as _OptionType


@dataclass(frozen=True)
class ImpliedVolatilityInputs:
    """Immutable, typed market inputs for implied-volatility solving.

    Attributes:
        market_price: Observed European option price. Must be non-negative.
        spot: Current price of the underlying asset. Must be strictly positive.
        strike: Exercise price of the option. Must be strictly positive.
        time_to_expiry: Time to expiry in years. Must be strictly positive;
            implied volatility is undefined at expiry.
        risk_free_rate: Continuously compounded annual risk-free rate. Must be
            finite; negative values are allowed.
        dividend_yield: Continuously compounded annual dividend yield. Must be
            finite; negative values are allowed. Defaults to ``0.0``.

    Instances are validated on construction. Malformed or invalid inputs raise
    :class:`TypeError` (wrong type) or :class:`ValueError` (invalid value). The
    model is immutable and reuses the shared validation helpers.
    """

    market_price: float
    spot: float
    strike: float
    time_to_expiry: float
    risk_free_rate: float
    dividend_yield: float = 0.0

    def __post_init__(self) -> None:
        # Reuse the shared validation helpers so that rejection rules stay
        # consistent with the rest of the toolkit.
        validate_real_number(
            self.market_price, "market_price", allow_negative=False, allow_zero=True
        )
        validate_real_number(self.spot, "spot", allow_negative=False, allow_zero=False)
        validate_real_number(self.strike, "strike", allow_negative=False, allow_zero=False)
        # Implied volatility requires strictly positive time to expiry; the
        # deterministic price at expiry is not a volatility problem.
        validate_real_number(
            self.time_to_expiry, "time_to_expiry", allow_negative=False, allow_zero=False
        )
        validate_real_number(
            self.risk_free_rate, "risk_free_rate", allow_negative=True, allow_zero=True
        )
        validate_real_number(
            self.dividend_yield, "dividend_yield", allow_negative=True, allow_zero=True
        )


def _price_at_volatility(
    inputs: ImpliedVolatilityInputs, option_type: _OptionType, volatility: float
) -> float:
    """Price the option at a candidate annualised volatility.

    A :class:`BlackScholesInputs` is constructed internally for each candidate
    volatility so that the pricing core remains the single source of truth.

    Args:
        inputs: Validated implied-volatility market inputs.
        option_type: The validated :class:`OptionType`.
        volatility: Candidate annualised volatility (decimal). Must be
            non-negative and finite.

    Returns:
        The European option price under the candidate volatility.
    """
    pricing_inputs = BlackScholesInputs(
        spot=inputs.spot,
        strike=inputs.strike,
        time_to_expiry=inputs.time_to_expiry,
        risk_free_rate=inputs.risk_free_rate,
        volatility=volatility,
        dividend_yield=inputs.dividend_yield,
    )
    return price_european(pricing_inputs, option_type)


def _no_arbitrage_bounds(
    inputs: ImpliedVolatilityInputs, option_type: _OptionType
) -> tuple[float, float]:
    """Return the European no-arbitrage (lower, upper) price bounds.

    The lower bound is the exact zero-volatility deterministic price. The upper
    bound is approached only as volatility tends toward infinity, so equality
    with the upper bound has no finite implied-volatility solution.

    Args:
        inputs: Validated implied-volatility market inputs.
        option_type: The validated :class:`OptionType`.

    Returns:
        A tuple ``(lower_bound, upper_bound)``.
    """
    discounted_spot = inputs.spot * math.exp(-inputs.dividend_yield * inputs.time_to_expiry)
    discounted_strike = inputs.strike * math.exp(-inputs.risk_free_rate * inputs.time_to_expiry)

    if option_type is OptionType.CALL:
        lower_bound = max(discounted_spot - discounted_strike, 0.0)
        upper_bound = discounted_spot
    else:
        lower_bound = max(discounted_strike - discounted_spot, 0.0)
        upper_bound = discounted_strike

    return lower_bound, upper_bound


def _validate_solver_controls(
    *,
    price_tolerance: Any,
    volatility_tolerance: Any,
    max_iterations: Any,
    initial_upper_volatility: Any,
    max_volatility: Any,
) -> None:
    """Validate the solver-control parameters.

    Type errors raise :class:`TypeError`; invalid values raise
    :class:`ValueError`. The policy is consistent with the rest of the toolkit.
    """
    validate_real_number(price_tolerance, "price_tolerance", allow_negative=False, allow_zero=False)
    validate_real_number(
        volatility_tolerance, "volatility_tolerance", allow_negative=False, allow_zero=False
    )

    if not isinstance(max_iterations, int) or isinstance(max_iterations, bool):
        raise TypeError(f"max_iterations must be an int, got {type(max_iterations).__name__}")
    if max_iterations <= 0:
        raise ValueError(f"max_iterations must be strictly positive, got {max_iterations!r}")

    validate_real_number(
        initial_upper_volatility,
        "initial_upper_volatility",
        allow_negative=False,
        allow_zero=False,
    )
    validate_real_number(max_volatility, "max_volatility", allow_negative=False, allow_zero=False)

    if initial_upper_volatility > max_volatility:
        raise ValueError(
            "initial_upper_volatility must not exceed max_volatility: "
            f"got initial_upper_volatility={initial_upper_volatility!r}, "
            f"max_volatility={max_volatility!r}"
        )


def implied_volatility(
    inputs: ImpliedVolatilityInputs,
    option_type: OptionType,
    *,
    price_tolerance: float = 1e-10,
    volatility_tolerance: float = 1e-12,
    max_iterations: int = 200,
    initial_upper_volatility: float = 0.5,
    max_volatility: float = 10.0,
) -> float:
    """Solve for the implied volatility of a European option.

    The solver uses the existing :func:`price_european` as its pricing oracle,
    validates the observed market price against European no-arbitrage bounds,
    applies adaptive volatility bracketing, and then performs deterministic
    bisection.

    Args:
        inputs: Validated :class:`ImpliedVolatilityInputs` market snapshot.
        option_type: Either :attr:`OptionType.CALL` or :attr:`OptionType.PUT`.
        price_tolerance: Absolute price tolerance for convergence. Must be a
            finite, strictly positive real number.
        volatility_tolerance: Absolute volatility-interval tolerance for
            convergence. Must be a finite, strictly positive real number.
        max_iterations: Maximum bisection iterations. Must be a strictly
            positive integer.
        initial_upper_volatility: Initial upper bracket for the volatility.
            Must be a finite, strictly positive real number not exceeding
            ``max_volatility``.
        max_volatility: Maximum allowable volatility before bracketing stops.
            Must be a finite, strictly positive real number.

    Returns:
        The annualised implied volatility as a ``float`` (decimal). The value
        is returned exactly as computed; no rounding is applied.

    Raises:
        TypeError: If ``inputs`` is not a valid :class:`ImpliedVolatilityInputs`,
            ``option_type`` is not a valid :class:`OptionType`, or any solver
            control has the wrong type.
        ValueError: If ``inputs`` or any solver control has an invalid value, or
            the market price violates the no-arbitrage bounds.
        RuntimeError: If the bisection fails to converge within
            ``max_iterations``.
    """
    if not isinstance(inputs, ImpliedVolatilityInputs):
        raise TypeError(
            f"inputs must be an ImpliedVolatilityInputs instance, got {type(inputs).__name__}"
        )
    option_type = validate_option_type(option_type)
    _validate_solver_controls(
        price_tolerance=price_tolerance,
        volatility_tolerance=volatility_tolerance,
        max_iterations=max_iterations,
        initial_upper_volatility=initial_upper_volatility,
        max_volatility=max_volatility,
    )

    lower_bound, upper_bound = _no_arbitrage_bounds(inputs, option_type)
    market_price = inputs.market_price

    if market_price < lower_bound:
        raise ValueError(
            "market_price is below the European no-arbitrage lower bound: "
            f"market_price={market_price!r}, lower_bound={lower_bound!r}"
        )
    if market_price == lower_bound:
        # The zero-volatility deterministic price is the exact solution.
        return 0.0
    if market_price >= upper_bound:
        raise ValueError(
            "market_price is at or above the European no-arbitrage upper bound, "
            "so no finite implied volatility exists: "
            f"market_price={market_price!r}, upper_bound={upper_bound!r}"
        )

    # Adaptive bracketing: start at 0.0 and expand the upper bound until the
    # target price is bracketed or max_volatility is reached.
    lower_volatility = 0.0
    upper_volatility = float(initial_upper_volatility)

    # The price at lower_volatility equals the zero-volatility lower bound,
    # which we already know is strictly below market_price.
    while _price_at_volatility(inputs, option_type, upper_volatility) < market_price:
        next_upper = upper_volatility * 2.0
        if next_upper > max_volatility:
            if _price_at_volatility(inputs, option_type, max_volatility) < market_price:
                raise ValueError(
                    "implied volatility exceeds the configured maximum or cannot "
                    f"be bracketed: max_volatility={max_volatility!r}, "
                    f"market_price={market_price!r}"
                )
            upper_volatility = float(max_volatility)
            break
        upper_volatility = next_upper

    # Deterministic bisection. The European price is monotonic non-decreasing in
    # volatility for ordinary valid inputs, so the bracket invariant
    # price(lower) <= market_price <= price(upper) is preserved.
    for _ in range(max_iterations):
        midpoint = (lower_volatility + upper_volatility) / 2.0
        price_mid = _price_at_volatility(inputs, option_type, midpoint)
        price_error = price_mid - market_price

        if abs(price_error) <= price_tolerance:
            return midpoint

        if price_error < 0.0:
            lower_volatility = midpoint
        else:
            upper_volatility = midpoint

        if upper_volatility - lower_volatility <= volatility_tolerance:
            return (lower_volatility + upper_volatility) / 2.0

    raise RuntimeError(
        "implied volatility did not converge within the maximum number of "
        f"iterations: max_iterations={max_iterations!r}, "
        f"price_tolerance={price_tolerance!r}, "
        f"volatility_tolerance={volatility_tolerance!r}"
    )
