"""Deterministic, typed, framework-independent helpers for the BlackScholesLab
interactive demonstration.

This module contains no Streamlit imports, no network or file I/O, and no
duplicated financial formulas. It prepares and validates data for the
demonstration layer and builds immutable core results into display rows. Every
function is deterministic and free of hidden global state.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from blackscholeslab.models import OptionType
    from blackscholeslab.payoff import ExpiryScenarioResult
    from blackscholeslab.scenarios import OptionScenario, ScenarioPriceResult


@dataclass(frozen=True)
class ScenarioSpec:
    """Immutable default specification for one demonstration scenario.

    Attributes:
        label: Human-readable label for the scenario.
        spot: Scenario underlying price.
        time_to_expiry: Scenario time to expiry in years.
        volatility: Scenario annualised volatility as a decimal.
        risk_free_rate: Scenario continuously compounded annual risk-free rate.
        dividend_yield: Scenario continuously compounded annual dividend yield.
    """

    label: str
    spot: float
    time_to_expiry: float
    volatility: float
    risk_free_rate: float
    dividend_yield: float


def _require_real_number(value: object, name: str) -> float:
    """Validate a finite, non-boolean real number and return it as a float.

    Raises:
        TypeError: If ``value`` is not a real number (bool, str, None, complex).
        ValueError: If ``value`` is non-finite.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a real number, got {type(value).__name__}")
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite, got {value!r}")
    return float(value)


def inclusive_grid(start: float, stop: float, points: int) -> tuple[float, ...]:
    """Return an inclusive, evenly spaced grid using only the standard library.

    The first value is exactly ``start`` and the last value is exactly ``stop``.
    Values are ascending and the number of points equals ``points``. Direct
    index-based interpolation is used to avoid cumulative iterative drift, and the
    endpoints are pinned explicitly.

    Args:
        start: First grid value. Must be a finite real number and ``>= 0``.
        stop: Last grid value. Must be a finite real number strictly greater
            than ``start``.
        points: Number of grid points. Must be an ``int`` (a ``bool`` is rejected)
            and ``>= 2``.

    Returns:
        An immutable tuple of ``points`` ascending ``float`` values.

    Raises:
        TypeError: If any argument has an invalid type (for example a ``bool``,
            ``str``, ``None``, or complex value).
        ValueError: If any argument is non-finite, ``start < 0``, ``stop <=
            start``, or ``points < 2``.
    """
    if isinstance(points, bool) or not isinstance(points, int):
        raise TypeError(f"points must be an int, got {type(points).__name__}")
    start_f = _require_real_number(start, "start")
    stop_f = _require_real_number(stop, "stop")

    if points < 2:
        raise ValueError(f"points must be >= 2, got {points}")
    if start_f < 0:
        raise ValueError(f"start must be non-negative, got {start_f}")
    if stop_f <= start_f:
        raise ValueError(
            f"stop must be strictly greater than start, got start={start_f}, stop={stop_f}"
        )

    if points == 2:
        return (start_f, stop_f)

    step = (stop_f - start_f) / (points - 1)
    grid = [start_f + step * i for i in range(points)]
    grid[0] = start_f
    grid[-1] = stop_f
    return tuple(grid)


def option_type_from_label(label: str) -> OptionType:
    """Map an explicit option-type label to an ``OptionType`` member.

    Only the canonical lowercase labels ``"call"`` and ``"put"`` are accepted.
    Arbitrary strings are rejected; the demonstration never infers an option type.

    Args:
        label: The option-type label (``"call"`` or ``"put"``).

    Returns:
        The matching :class:`OptionType`.

    Raises:
        TypeError: If ``label`` is not a ``str``.
        ValueError: If ``label`` is not ``"call"`` or ``"put"``.
    """
    if not isinstance(label, str):
        raise TypeError(f"label must be a str, got {type(label).__name__}")
    normalized = label.strip().lower()
    if normalized == "call":
        from blackscholeslab.models import OptionType

        return OptionType.CALL
    if normalized == "put":
        from blackscholeslab.models import OptionType

        return OptionType.PUT
    raise ValueError(f"unsupported option type label: {label!r}")


def format_number(value: float, precision: int = 6) -> str:
    """Return a stable human-readable representation of a finite number.

    The raw numeric value is never altered; only its display string changes.

    Args:
        value: A finite real number.
        precision: Number of significant digits used in the ``g`` format.

    Returns:
        A formatted ``str``.

    Raises:
        TypeError: If ``value`` is not a real number or ``precision`` is not an int.
        ValueError: If ``value`` is non-finite.
    """
    if not isinstance(precision, int) or isinstance(precision, bool):
        raise TypeError(f"precision must be an int, got {type(precision).__name__}")
    value_f = _require_real_number(value, "value")
    return f"{value_f:.{precision}g}"


def break_even_price(option_type: OptionType, strike: float, premium: float) -> float:
    """Educational long-option break-even underlying price (arithmetic only).

    This is explanatory arithmetic, not a core payoff calculation:

    - Call: ``strike + premium``
    - Put: ``strike - premium``

    Args:
        option_type: The validated :class:`OptionType`.
        strike: Strike price. Must be a finite real number.
        premium: Premium paid per unit. Must be a finite real number and ``>= 0``.

    Returns:
        The break-even underlying price as a ``float``.

    Raises:
        TypeError: If ``option_type`` is invalid or any numeric argument is the
            wrong type.
        ValueError: If any numeric argument is non-finite or ``premium`` is
            negative.
    """
    from blackscholeslab.models import OptionType as _OptionType

    if not isinstance(option_type, _OptionType):
        raise TypeError(f"option_type must be OptionType, got {type(option_type).__name__}")
    strike_f = _require_real_number(strike, "strike")
    premium_f = _require_real_number(premium, "premium")
    if premium_f < 0:
        raise ValueError(f"premium must be non-negative, got {premium_f}")

    if option_type is _OptionType.CALL:
        return strike_f + premium_f
    return strike_f - premium_f


def expiry_rows(results: Iterable[ExpiryScenarioResult]) -> list[dict[str, float]]:
    """Build ordered display rows from immutable expiry scenario results.

    Args:
        results: An iterable of :class:`ExpiryScenarioResult` in display order.

    Returns:
        A list of row dictionaries with ``Underlying price``, ``Payoff``, and
        ``Profit/Loss`` keys, in the same order as ``results``.
    """
    return [
        {
            "Underlying price": result.underlying_price,
            "Payoff": result.payoff,
            "Profit/Loss": result.profit_loss,
        }
        for result in results
    ]


def expiry_chart_data(results: Iterable[ExpiryScenarioResult]) -> dict[str, list[float]]:
    """Build line-chart series from immutable expiry scenario results.

    Args:
        results: An iterable of :class:`ExpiryScenarioResult` in display order.

    Returns:
        A mapping of series name to an ordered list of values suitable for
        ``st.line_chart``.
    """
    return {
        "Underlying price": [result.underlying_price for result in results],
        "Payoff": [result.payoff for result in results],
        "Profit/Loss": [result.profit_loss for result in results],
    }


def scenario_rows(results: Iterable[ScenarioPriceResult]) -> list[dict[str, object]]:
    """Build ordered display rows from immutable scenario price results.

    A ``None`` ``percentage_change`` is rendered as the literal string
    ``"undefined"`` so the demonstration never substitutes zero or infinity.

    Args:
        results: An iterable of :class:`ScenarioPriceResult` in display order.

    Returns:
        A list of row dictionaries, one per scenario, preserving input order.
    """
    rows: list[dict[str, object]] = []
    for index, result in enumerate(results, start=1):
        scenario: OptionScenario = result.scenario
        percentage = result.percentage_change
        rows.append(
            {
                "Scenario": index,
                "Label": scenario.label if scenario.label is not None else "",
                "Spot": scenario.spot,
                "Time to expiry": scenario.time_to_expiry,
                "Volatility": scenario.volatility,
                "Risk-free rate": scenario.risk_free_rate,
                "Dividend yield": scenario.dividend_yield,
                "Option price": result.option_price,
                "Price change": result.price_change,
                "Percentage change": "undefined" if percentage is None else percentage,
            }
        )
    return rows


def default_scenario_specs(
    base_spot: float,
    base_time: float,
    base_volatility: float,
    base_rate: float,
    base_dividend: float,
    count: int,
) -> list[ScenarioSpec]:
    """Return deterministic default scenario specifications for ``count`` scenarios.

    The first three scenarios are the educational presets Downside, Base, and
    Upside (with spot scaled by ``0.9``, ``1.0``, and ``1.1``). Additional
    scenarios use neutral base values. All other fields default to the supplied
    base assumptions so the demonstration remains deterministic.

    Args:
        base_spot: Base spot price.
        base_time: Base time to expiry.
        base_volatility: Base volatility.
        base_rate: Base risk-free rate.
        base_dividend: Base dividend yield.
        count: Number of scenarios (``>= 1``).

    Returns:
        A list of :class:`ScenarioSpec` instances, one per scenario, in display
        order.

    Raises:
        TypeError: If ``count`` is not an ``int``.
        ValueError: If ``count`` is outside ``[1, 5]``.
    """
    if isinstance(count, bool) or not isinstance(count, int):
        raise TypeError(f"count must be an int, got {type(count).__name__}")
    if count < 1 or count > 5:
        raise ValueError(f"count must be between 1 and 5, got {count}")

    presets = [
        ScenarioSpec(
            "Downside", base_spot * 0.9, base_time, base_volatility, base_rate, base_dividend
        ),
        ScenarioSpec("Base", base_spot * 1.0, base_time, base_volatility, base_rate, base_dividend),
        ScenarioSpec(
            "Upside", base_spot * 1.1, base_time, base_volatility, base_rate, base_dividend
        ),
    ]
    specs: list[ScenarioSpec] = []
    for index in range(count):
        if index < len(presets):
            specs.append(presets[index])
        else:
            specs.append(
                ScenarioSpec(
                    f"Scenario {index + 1}",
                    base_spot,
                    base_time,
                    base_volatility,
                    base_rate,
                    base_dividend,
                )
            )
    return specs
