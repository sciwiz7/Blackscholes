"""Pre-expiry scenario analysis for European options.

This module defines immutable scenario assumptions and reprices European options
under those assumptions using the shared pricing core. It reuses
:class:`BlackScholesInputs`, :func:`price_european`, and the validation helpers so
that a single pricing oracle remains the source of truth.

The strike is always taken from the supplied base case and remains fixed across
scenarios. Only spot, time to expiry, volatility, risk-free rate, and dividend
yield are varied per scenario.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from blackscholeslab.models import BlackScholesInputs, OptionType
from blackscholeslab.pricing import price_european
from blackscholeslab.validation import validate_option_type, validate_real_number


@dataclass(frozen=True)
class OptionScenario:
    """Immutable pre-expiry scenario assumptions for one repricing.

    Attributes:
        spot: Scenario underlying price. Must be strictly positive.
        time_to_expiry: Scenario time to expiry in years. Must be non-negative;
            ``0`` means the option is at expiry.
        volatility: Scenario annualised volatility as a decimal. Must be
            non-negative; ``0`` selects the deterministic discounted-payoff path.
        risk_free_rate: Scenario continuously compounded annual risk-free rate.
            Must be finite; negative values are allowed.
        dividend_yield: Scenario continuously compounded annual dividend yield.
            Must be finite; negative values are allowed. Defaults to ``0.0``.
        label: Optional human-readable label for the scenario. May be ``None``.
            An empty string is permitted; it is treated as a present-but-empty
            label rather than rejected.

    A zero ``time_to_expiry`` and a zero ``volatility`` are valid because
    :func:`price_european` already defines explicit boundary behaviour for them.
    Finite negative ``risk_free_rate`` and ``dividend_yield`` are allowed.
    """

    spot: float
    time_to_expiry: float
    volatility: float
    risk_free_rate: float
    dividend_yield: float = 0.0
    label: str | None = None

    def __post_init__(self) -> None:
        validate_real_number(self.spot, "spot", allow_negative=False, allow_zero=False)
        validate_real_number(
            self.time_to_expiry, "time_to_expiry", allow_negative=False, allow_zero=True
        )
        validate_real_number(self.volatility, "volatility", allow_negative=False, allow_zero=True)
        validate_real_number(
            self.risk_free_rate, "risk_free_rate", allow_negative=True, allow_zero=True
        )
        validate_real_number(
            self.dividend_yield, "dividend_yield", allow_negative=True, allow_zero=True
        )
        if self.label is not None and not isinstance(self.label, str):
            raise TypeError(f"label must be a str or None, got {type(self.label).__name__}")


@dataclass(frozen=True)
class ScenarioPriceResult:
    """Immutable price result for one pre-expiry scenario.

    Attributes:
        scenario: The scenario that produced this result.
        option_price: The repriced option value under the scenario.
        price_change: ``option_price - base option price`` (absolute change).
        percentage_change: ``price_change / base option price`` as a decimal
            return, or ``None`` when the base option price is exactly ``0.0``.
    """

    scenario: OptionScenario
    option_price: float
    price_change: float
    percentage_change: float | None


def evaluate_price_scenarios(
    base_inputs: BlackScholesInputs,
    option_type: OptionType,
    scenarios: Iterable[OptionScenario],
) -> tuple[ScenarioPriceResult, ...]:
    """Reprice a European option under pre-expiry scenario assumptions.

    The base price is computed once from ``base_inputs``. Each scenario reprices
    the option with the scenario's spot, time to expiry, volatility, risk-free
    rate, and dividend yield, while the strike stays fixed at the base value.

    Args:
        base_inputs: A :class:`BlackScholesInputs` instance defining the base
            case. The strike is taken from here and fixed across scenarios.
        option_type: Either :attr:`OptionType.CALL` or :attr:`OptionType.PUT`.
        scenarios: An iterable of :class:`OptionScenario`. Must not be empty.
            Order and duplicates are preserved exactly.

    Returns:
        An immutable tuple of :class:`ScenarioPriceResult`, one per scenario, in
        the original order.

    Raises:
        TypeError: If ``base_inputs`` is not a :class:`BlackScholesInputs`, if
            ``option_type`` is invalid, or if any scenario is not an
            :class:`OptionScenario`.
        ValueError: If ``scenarios`` is empty or any scenario is invalid.
        RuntimeError: Re-raised from :func:`price_european` if a scenario's
            assumptions are numerically invalid.

    Neither ``base_inputs`` nor any scenario object is mutated.
    """
    from blackscholeslab.validation import validate_inputs

    validate_inputs(base_inputs)
    option_type = validate_option_type(option_type)

    base_price = price_european(base_inputs, option_type)
    strike = base_inputs.strike

    results: list[ScenarioPriceResult] = []
    for index, scenario in enumerate(scenarios):
        if not isinstance(scenario, OptionScenario):
            raise TypeError(
                f"scenarios[{index}] must be an OptionScenario, got {type(scenario).__name__}"
            )
        scenario_inputs = BlackScholesInputs(
            spot=scenario.spot,
            strike=strike,
            time_to_expiry=scenario.time_to_expiry,
            risk_free_rate=scenario.risk_free_rate,
            volatility=scenario.volatility,
            dividend_yield=scenario.dividend_yield,
        )
        scenario_price = price_european(scenario_inputs, option_type)
        price_change = scenario_price - base_price
        if base_price == 0.0:
            percentage_change: float | None = None
        else:
            percentage_change = price_change / base_price
        results.append(
            ScenarioPriceResult(
                scenario=scenario,
                option_price=scenario_price,
                price_change=price_change,
                percentage_change=percentage_change,
            )
        )

    if not results:
        raise ValueError("scenarios must not be empty")

    return tuple(results)
