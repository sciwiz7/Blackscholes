"""Intrinsic payoff, expiry P&L, and multi-leg strategy payoff analysis.

This module provides deterministic, explicitly validated payoff analysis for
European call and put options. It does not price options and does not depend on
the pricing core. It reuses the shared :class:`OptionType` enumeration and the
reusable validation helpers so that error semantics stay consistent with the
rest of the toolkit.

The existing single-option APIs model one long option purchased for an
explicitly supplied premium. The strategy APIs extend expiry-only analysis to
signed option and underlying legs, without adding dividends, financing costs,
margin mechanics, transaction costs, taxes, assignment, pre-expiry pricing, or
contract multipliers.
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


@dataclass(frozen=True)
class OptionLeg:
    """Immutable option leg for expiry-only strategy payoff analysis.

    ``quantity`` is a signed integer: positive for long exposure and negative
    for short exposure. Zero quantity is rejected because it would add a
    non-economic leg to the strategy.
    """

    option_type: OptionType
    strike: float
    premium: float
    quantity: int

    def __post_init__(self) -> None:
        option_type = validate_option_type(self.option_type)
        validate_real_number(self.strike, "strike", allow_negative=False, allow_zero=False)
        validate_real_number(self.premium, "premium", allow_negative=False, allow_zero=True)
        quantity = _validate_quantity(self.quantity)

        object.__setattr__(self, "option_type", option_type)
        object.__setattr__(self, "strike", float(self.strike))
        object.__setattr__(self, "premium", float(self.premium))
        object.__setattr__(self, "quantity", quantity)


@dataclass(frozen=True)
class UnderlyingLeg:
    """Immutable underlying-asset leg for expiry-only strategy payoff analysis.

    ``quantity`` is a signed integer: positive for long exposure and negative
    for short exposure. ``entry_price`` is the per-unit entry price used for net
    profit calculations.
    """

    entry_price: float
    quantity: int

    def __post_init__(self) -> None:
        validate_real_number(
            self.entry_price,
            "entry_price",
            allow_negative=False,
            allow_zero=False,
        )
        quantity = _validate_quantity(self.quantity)

        object.__setattr__(self, "entry_price", float(self.entry_price))
        object.__setattr__(self, "quantity", quantity)


@dataclass(frozen=True)
class PayoffPoint:
    """Immutable aggregate payoff result for one strategy spot at expiry.

    Attributes:
        spot_at_expiry: Underlying spot price evaluated at expiry.
        gross_payoff: Aggregate gross payoff before entry costs and premiums.
        net_profit: Aggregate net profit after option premiums and underlying
            entry prices.
    """

    spot_at_expiry: float
    gross_payoff: float
    net_profit: float

    def __post_init__(self) -> None:
        validate_real_number(
            self.spot_at_expiry,
            "spot_at_expiry",
            allow_negative=False,
            allow_zero=True,
        )
        validate_real_number(
            self.gross_payoff,
            "gross_payoff",
            allow_negative=True,
            allow_zero=True,
        )
        validate_real_number(
            self.net_profit,
            "net_profit",
            allow_negative=True,
            allow_zero=True,
        )

        object.__setattr__(self, "spot_at_expiry", float(self.spot_at_expiry))
        object.__setattr__(self, "gross_payoff", float(self.gross_payoff))
        object.__setattr__(self, "net_profit", float(self.net_profit))


StrategyLeg = OptionLeg | UnderlyingLeg


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


def strategy_payoff(
    spot_at_expiry: float,
    legs: Iterable[StrategyLeg],
) -> PayoffPoint:
    """Aggregate gross payoff and net profit for a strategy at expiry.

    Option legs use these definitions:

    ``gross payoff = quantity * intrinsic_payoff(...)``

    ``net profit = quantity * (intrinsic_payoff(...) - premium)``

    Underlying legs use these definitions:

    ``gross payoff = quantity * spot_at_expiry``

    ``net profit = quantity * (spot_at_expiry - entry_price)``

    The function performs deterministic aggregation over the supplied legs. It
    does not model dividends, financing costs, borrow fees, transaction costs,
    taxes, margin mechanics, assignment, pre-expiry pricing, charts, or
    contract multipliers.
    """
    validate_real_number(
        spot_at_expiry,
        "spot_at_expiry",
        allow_negative=False,
        allow_zero=True,
    )
    validated_legs = _validate_strategy_legs(legs)

    return _strategy_payoff_from_validated_legs(float(spot_at_expiry), validated_legs)


def evaluate_strategy_profile(
    spot_prices: Iterable[float],
    legs: Iterable[StrategyLeg],
) -> tuple[PayoffPoint, ...]:
    """Evaluate a multi-leg strategy over supplied expiry spot prices.

    The supplied spot prices are evaluated in order. Order and duplicate prices
    are preserved exactly. The spot iterable is consumed exactly once.
    """
    validated_legs = _validate_strategy_legs(legs)

    results: list[PayoffPoint] = []
    for index, spot in enumerate(spot_prices):
        validate_real_number(
            spot,
            f"spot_prices[{index}]",
            allow_negative=False,
            allow_zero=True,
        )
        results.append(_strategy_payoff_from_validated_legs(float(spot), validated_legs))

    if not results:
        raise ValueError("spot_prices must not be empty")

    return tuple(results)


def _strategy_payoff_from_validated_legs(
    spot_at_expiry: float,
    legs: tuple[StrategyLeg, ...],
) -> PayoffPoint:
    gross_payoff = 0.0
    net_profit = 0.0

    for leg in legs:
        if isinstance(leg, OptionLeg):
            intrinsic = intrinsic_payoff(spot_at_expiry, leg.strike, leg.option_type)
            gross_payoff += leg.quantity * intrinsic
            net_profit += leg.quantity * (intrinsic - leg.premium)
        elif isinstance(leg, UnderlyingLeg):
            gross_payoff += leg.quantity * spot_at_expiry
            net_profit += leg.quantity * (spot_at_expiry - leg.entry_price)
        else:
            raise TypeError("unsupported leg type")

    return PayoffPoint(
        spot_at_expiry=spot_at_expiry,
        gross_payoff=gross_payoff,
        net_profit=net_profit,
    )


def _validate_strategy_legs(legs: Iterable[StrategyLeg]) -> tuple[StrategyLeg, ...]:
    validated: list[StrategyLeg] = []

    for index, leg in enumerate(legs):
        if not isinstance(leg, (OptionLeg, UnderlyingLeg)):
            raise TypeError(f"unsupported leg at legs[{index}]")
        validated.append(leg)

    if not validated:
        raise ValueError("legs must not be empty")

    return tuple(validated)


def _validate_quantity(quantity: int) -> int:
    if isinstance(quantity, bool) or not isinstance(quantity, int):
        raise TypeError("quantity must be an integer")
    if quantity == 0:
        raise ValueError("quantity must not be zero")
    return quantity
