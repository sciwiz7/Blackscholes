"""Intrinsic payoff and expiry profit-and-loss for European options.

This module provides deterministic, explicitly validated payoff analysis for
European call and put options. It does not price options and does not depend on
the pricing core. It reuses the shared :class:`OptionType` enumeration and the
reusable validation helpers so that error semantics stay consistent with the
rest of the toolkit.

The functions here describe a single **long** option purchased for an explicitly
supplied premium. They do not infer short positions, contract multipliers, or
position quantities.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from blackscholeslab.models import OptionType
from blackscholeslab.validation import validate_option_type, validate_real_number


@dataclass(frozen=True)
class ExpiryScenarioResult:
    """Immutable result of an expiry payoff/P&L evaluation for one underlying price.

    Attributes:
        underlying_price: The underlying price evaluated at expiry.
        payoff: The intrinsic payoff of a long option at that price.
        profit_loss: The expiry profit and loss after the paid premium.
    """

    underlying_price: float
    payoff: float
    profit_loss: float


def intrinsic_payoff(
    underlying_price: float,
    strike: float,
    option_type: OptionType,
) -> float:
    """Compute the intrinsic payoff of a European option at expiry.

    The intrinsic payoff is the amount received on exercise, ignoring any premium
    paid. It is never negative.

    Args:
        underlying_price: Underlying price at expiry. Must be a finite real
            number and must be ``>= 0``; a zero underlying price is valid.
        strike: Strike price. Must be a finite real number and must be ``> 0``.
        option_type: Either :attr:`OptionType.CALL` or :attr:`OptionType.PUT`.

    Returns:
        The intrinsic payoff as a ``float``.

    Raises:
        TypeError: If any argument has an invalid type (bool, str, None, complex,
            or an invalid ``option_type``).
        ValueError: If any argument is non-finite, if ``underlying_price`` is
            negative, or if ``strike`` is not strictly positive.

    Call: ``max(underlying_price - strike, 0.0)``.
    Put: ``max(strike - underlying_price, 0.0)``.
    """
    validate_real_number(
        underlying_price, "underlying_price", allow_negative=False, allow_zero=True
    )
    validate_real_number(strike, "strike", allow_negative=False, allow_zero=False)
    option_type = validate_option_type(option_type)

    if option_type is OptionType.CALL:
        return max(underlying_price - strike, 0.0)
    return max(strike - underlying_price, 0.0)


def expiry_profit_loss(
    underlying_price: float,
    strike: float,
    option_type: OptionType,
    premium: float,
) -> float:
    """Compute the expiry profit and loss of a long European option.

    The expiry profit and loss is the intrinsic payoff minus the premium paid for
    one option unit. No discounting is applied inside this function.

    Args:
        underlying_price: Underlying price at expiry. Must be a finite real
            number and must be ``>= 0``; a zero underlying price is valid.
        strike: Strike price. Must be a finite real number and must be ``> 0``.
        option_type: Either :attr:`OptionType.CALL` or :attr:`OptionType.PUT`.
        premium: Premium paid for one option unit. Must be a finite real number
            and must be ``>= 0``. This is the amount paid to acquire the long
            option; no contract multiplier or quantity is assumed.

    Returns:
        The expiry profit and loss as a ``float``.

    Raises:
        TypeError: If any argument has an invalid type (bool, str, None, complex,
            or an invalid ``option_type``).
        ValueError: If any argument is non-finite, if ``underlying_price`` is
            negative, if ``strike`` is not strictly positive, or if ``premium``
            is negative.

    Definition:
        ``expiry_profit_loss = intrinsic_payoff(...) - premium``

    This API represents a long option purchased for the supplied premium. It does
    not infer short positions and never silently changes the premium sign. The
    minimum profit and loss for a long option is ``-premium``.
    """
    validate_real_number(
        underlying_price, "underlying_price", allow_negative=False, allow_zero=True
    )
    validate_real_number(strike, "strike", allow_negative=False, allow_zero=False)
    option_type = validate_option_type(option_type)
    validate_real_number(premium, "premium", allow_negative=False, allow_zero=True)

    return intrinsic_payoff(underlying_price, strike, option_type) - premium


def evaluate_expiry_scenarios(
    underlying_prices: Iterable[float],
    strike: float,
    option_type: OptionType,
    premium: float = 0.0,
) -> tuple[ExpiryScenarioResult, ...]:
    """Evaluate intrinsic payoff and expiry P&L over supplied underlying prices.

    The supplied underlying prices are evaluated in order. Order and duplicate
    prices are preserved exactly. The input iterable is consumed exactly once.

    Args:
        underlying_prices: An iterable of underlying prices at expiry. Must not be
            empty. Each item must be a finite real number ``>= 0``.
        strike: Strike price. Must be a finite real number and must be ``> 0``.
        option_type: Either :attr:`OptionType.CALL` or :attr:`OptionType.PUT`.
        premium: Premium paid for one option unit. Must be a finite real number
            and must be ``>= 0``. Defaults to ``0.0``.

    Returns:
        An immutable tuple of :class:`ExpiryScenarioResult`, one per supplied
        underlying price, in the original order.

    Raises:
        TypeError: If any argument has an invalid type (bool, str, None, complex,
            or an invalid ``option_type``), including an invalid item type.
        ValueError: If ``underlying_prices`` is empty, or if any scalar argument
            or item is non-finite, negative where not allowed, or otherwise
            invalid. An invalid item reports its zero-based index.
    """
    validate_real_number(strike, "strike", allow_negative=False, allow_zero=False)
    option_type = validate_option_type(option_type)
    validate_real_number(premium, "premium", allow_negative=False, allow_zero=True)

    results: list[ExpiryScenarioResult] = []
    for index, price in enumerate(underlying_prices):
        validate_real_number(
            price,
            f"underlying_prices[{index}]",
            allow_negative=False,
            allow_zero=True,
        )
        payoff = intrinsic_payoff(price, strike, option_type)
        profit_loss = payoff - premium
        results.append(
            ExpiryScenarioResult(
                underlying_price=float(price),
                payoff=payoff,
                profit_loss=profit_loss,
            )
        )

    if not results:
        raise ValueError("underlying_prices must not be empty")

    return tuple(results)
