"""Tests for pre-expiry scenario analysis using the shared pricing core."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest

from blackscholeslab import (
    BlackScholesInputs,
    OptionScenario,
    OptionType,
    ScenarioPriceResult,
    evaluate_price_scenarios,
    price_european,
)

ABS_TOL = 1e-10
REL_TOL = 1e-9


class _OneShotIterable:
    """Iterator that fails if iterated more than once."""

    def __init__(self, items: list[OptionScenario]) -> None:
        self._items = items
        self._used = False

    def __iter__(self) -> Iterator[OptionScenario]:
        if self._used:
            raise RuntimeError("scenarios iterable was iterated more than once")
        self._used = True
        return iter(self._items)


BASE = BlackScholesInputs(
    spot=100.0,
    strike=100.0,
    time_to_expiry=1.0,
    risk_free_rate=0.05,
    volatility=0.20,
    dividend_yield=0.02,
)


def _scenario_price(scenario: OptionScenario, option_type: OptionType) -> float:
    inputs = BlackScholesInputs(
        spot=scenario.spot,
        strike=BASE.strike,
        time_to_expiry=scenario.time_to_expiry,
        risk_free_rate=scenario.risk_free_rate,
        volatility=scenario.volatility,
        dividend_yield=scenario.dividend_yield,
    )
    return price_european(inputs, option_type)


def _base_scenario() -> OptionScenario:
    return OptionScenario(
        spot=BASE.spot,
        time_to_expiry=BASE.time_to_expiry,
        volatility=BASE.volatility,
        risk_free_rate=BASE.risk_free_rate,
        dividend_yield=BASE.dividend_yield,
    )


def _scenarios() -> list[OptionScenario]:
    return [
        OptionScenario(spot=110.0, time_to_expiry=1.0, volatility=0.20, risk_free_rate=0.05),
        OptionScenario(spot=90.0, time_to_expiry=1.0, volatility=0.20, risk_free_rate=0.05),
        OptionScenario(spot=100.0, time_to_expiry=0.5, volatility=0.20, risk_free_rate=0.05),
        OptionScenario(spot=100.0, time_to_expiry=1.0, volatility=0.30, risk_free_rate=0.05),
        OptionScenario(spot=100.0, time_to_expiry=1.0, volatility=0.10, risk_free_rate=0.05),
        OptionScenario(spot=100.0, time_to_expiry=1.0, volatility=0.20, risk_free_rate=0.08),
        OptionScenario(
            spot=100.0,
            time_to_expiry=1.0,
            volatility=0.20,
            risk_free_rate=0.05,
            dividend_yield=0.05,
        ),
        OptionScenario(
            spot=110.0,
            time_to_expiry=0.5,
            volatility=0.30,
            risk_free_rate=0.08,
            dividend_yield=0.05,
        ),
        OptionScenario(spot=100.0, time_to_expiry=0.0, volatility=0.20, risk_free_rate=0.05),
        OptionScenario(spot=100.0, time_to_expiry=1.0, volatility=0.0, risk_free_rate=0.05),
        OptionScenario(spot=100.0, time_to_expiry=1.0, volatility=0.20, risk_free_rate=-0.02),
        OptionScenario(
            spot=100.0,
            time_to_expiry=1.0,
            volatility=0.20,
            risk_free_rate=0.05,
            dividend_yield=-0.03,
        ),
        OptionScenario(
            spot=110.0, time_to_expiry=1.0, volatility=0.20, risk_free_rate=0.05, label="up"
        ),
        OptionScenario(
            spot=90.0, time_to_expiry=1.0, volatility=0.20, risk_free_rate=0.05, label=None
        ),
    ]


# --------------------------------------------------------------------------- #
# Reference scenario pricing
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("option_type", [OptionType.CALL, OptionType.PUT])
def test_scenario_prices_match_direct_pricing(option_type: OptionType) -> None:
    results = evaluate_price_scenarios(BASE, option_type, _scenarios())
    assert len(results) == len(_scenarios())
    for scenario, result in zip(_scenarios(), results, strict=True):
        expected = _scenario_price(scenario, option_type)
        assert result.option_price == pytest.approx(expected, abs=ABS_TOL, rel=REL_TOL)


@pytest.mark.parametrize("option_type", [OptionType.CALL, OptionType.PUT])
def test_labels_preserved(option_type: OptionType) -> None:
    scenarios = [
        OptionScenario(
            spot=110.0, time_to_expiry=1.0, volatility=0.20, risk_free_rate=0.05, label="up"
        ),
        OptionScenario(
            spot=90.0, time_to_expiry=1.0, volatility=0.20, risk_free_rate=0.05, label=None
        ),
        OptionScenario(
            spot=100.0, time_to_expiry=1.0, volatility=0.20, risk_free_rate=0.05, label=""
        ),
    ]
    results = evaluate_price_scenarios(BASE, option_type, scenarios)
    assert results[0].scenario.label == "up"
    assert results[1].scenario.label is None
    assert results[2].scenario.label == ""


# --------------------------------------------------------------------------- #
# Scenario invariants
# --------------------------------------------------------------------------- #


def test_spot_increase_does_not_reduce_call() -> None:
    # Dividend yield fixed at 0.0 here so the direct prices and the scenario
    # prices (which default dividend_yield to 0.0) stay consistent.
    up_price = price_european(
        BlackScholesInputs(
            spot=110.0,
            strike=BASE.strike,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.20,
            dividend_yield=0.0,
        ),
        OptionType.CALL,
    )
    base_price = price_european(
        BlackScholesInputs(
            spot=100.0,
            strike=BASE.strike,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.20,
            dividend_yield=0.0,
        ),
        OptionType.CALL,
    )
    assert up_price >= base_price
    assert up_price == _scenario_price(
        OptionScenario(spot=110.0, time_to_expiry=1.0, volatility=0.20, risk_free_rate=0.05),
        OptionType.CALL,
    )
    assert base_price == _scenario_price(
        OptionScenario(spot=100.0, time_to_expiry=1.0, volatility=0.20, risk_free_rate=0.05),
        OptionType.CALL,
    )


def test_spot_increase_does_not_increase_put() -> None:
    up_price = price_european(
        BlackScholesInputs(
            spot=110.0,
            strike=BASE.strike,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.20,
            dividend_yield=0.02,
        ),
        OptionType.PUT,
    )
    base_price = price_european(
        BlackScholesInputs(
            spot=100.0,
            strike=BASE.strike,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.20,
            dividend_yield=0.02,
        ),
        OptionType.PUT,
    )
    assert up_price <= base_price


def test_identical_scenario_has_zero_change() -> None:
    result = evaluate_price_scenarios(BASE, OptionType.CALL, [_base_scenario()])[0]
    assert result.price_change == pytest.approx(0.0, abs=ABS_TOL)
    assert result.percentage_change == pytest.approx(0.0, abs=ABS_TOL)


def test_base_price_consistent_with_direct_pricing() -> None:
    base_call = price_european(BASE, OptionType.CALL)
    base_put = price_european(BASE, OptionType.PUT)
    results_call = evaluate_price_scenarios(BASE, OptionType.CALL, [_base_scenario()])
    results_put = evaluate_price_scenarios(BASE, OptionType.PUT, [_base_scenario()])
    assert results_call[0].option_price == pytest.approx(base_call, abs=ABS_TOL, rel=REL_TOL)
    assert results_put[0].option_price == pytest.approx(base_put, abs=ABS_TOL, rel=REL_TOL)


def test_base_inputs_unchanged() -> None:
    original = (
        BASE.spot,
        BASE.strike,
        BASE.time_to_expiry,
        BASE.risk_free_rate,
        BASE.volatility,
        BASE.dividend_yield,
    )
    scenario = OptionScenario(spot=110.0, time_to_expiry=0.5, volatility=0.30, risk_free_rate=0.08)
    evaluate_price_scenarios(BASE, OptionType.CALL, [scenario])
    assert (
        BASE.spot,
        BASE.strike,
        BASE.time_to_expiry,
        BASE.risk_free_rate,
        BASE.volatility,
        BASE.dividend_yield,
    ) == original


def test_scenario_inputs_unchanged() -> None:
    scenario = OptionScenario(
        spot=110.0, time_to_expiry=0.5, volatility=0.30, risk_free_rate=0.08, label="x"
    )
    frozen = (
        scenario.spot,
        scenario.time_to_expiry,
        scenario.volatility,
        scenario.risk_free_rate,
        scenario.dividend_yield,
        scenario.label,
    )
    evaluate_price_scenarios(BASE, OptionType.CALL, [scenario])
    assert (
        scenario.spot,
        scenario.time_to_expiry,
        scenario.volatility,
        scenario.risk_free_rate,
        scenario.dividend_yield,
        scenario.label,
    ) == frozen


def test_output_order_preserved() -> None:
    scenarios = [
        _base_scenario(),
        OptionScenario(spot=110.0, time_to_expiry=1.0, volatility=0.20, risk_free_rate=0.05),
        OptionScenario(spot=90.0, time_to_expiry=1.0, volatility=0.20, risk_free_rate=0.05),
    ]
    results = evaluate_price_scenarios(BASE, OptionType.CALL, scenarios)
    assert [r.scenario for r in results] == scenarios


def test_duplicates_preserved() -> None:
    scenario = OptionScenario(spot=110.0, time_to_expiry=1.0, volatility=0.20, risk_free_rate=0.05)
    results = evaluate_price_scenarios(BASE, OptionType.CALL, [scenario, scenario, scenario])
    assert len(results) == 3
    assert all(r.scenario is scenario for r in results)
    assert all(r.option_price == results[0].option_price for r in results)


def test_results_immutable() -> None:
    scenario = OptionScenario(spot=110.0, time_to_expiry=1.0, volatility=0.20, risk_free_rate=0.05)
    results = evaluate_price_scenarios(BASE, OptionType.CALL, [scenario])
    assert isinstance(results, tuple)
    assert isinstance(results[0], ScenarioPriceResult)
    with pytest.raises(AttributeError):
        results.append(scenario)  # type: ignore[attr-defined]


def test_percentage_change_none_when_base_price_zero() -> None:
    # Build a base case whose price is exactly zero (at-the-money put at expiry).
    zero_base = BlackScholesInputs(
        spot=100.0,
        strike=100.0,
        time_to_expiry=0.0,
        risk_free_rate=0.05,
        volatility=0.20,
    )
    assert price_european(zero_base, OptionType.PUT) == 0.0
    scenario = OptionScenario(spot=100.0, time_to_expiry=0.0, volatility=0.20, risk_free_rate=0.05)
    result = evaluate_price_scenarios(zero_base, OptionType.PUT, [scenario])[0]
    assert result.percentage_change is None
    assert result.price_change == pytest.approx(0.0, abs=ABS_TOL)


# --------------------------------------------------------------------------- #
# Iterable behaviour
# --------------------------------------------------------------------------- #


def test_scenarios_with_tuple() -> None:
    scenarios = (
        _base_scenario(),
        OptionScenario(spot=110.0, time_to_expiry=1.0, volatility=0.20, risk_free_rate=0.05),
    )
    results = evaluate_price_scenarios(BASE, OptionType.CALL, scenarios)
    assert len(results) == 2


def test_scenarios_with_generator() -> None:
    def gen() -> Iterator[OptionScenario]:
        yield OptionScenario(spot=110.0, time_to_expiry=1.0, volatility=0.20, risk_free_rate=0.05)
        yield OptionScenario(spot=90.0, time_to_expiry=1.0, volatility=0.20, risk_free_rate=0.05)

    results = evaluate_price_scenarios(BASE, OptionType.CALL, gen())
    assert len(results) == 2


def test_scenarios_one_shot_iterable() -> None:
    # A generator-like iterable must not be consumed twice (once for emptiness,
    # once for evaluation). The custom one-shot iterable raises if iterated again.
    scenarios = [
        OptionScenario(spot=110.0, time_to_expiry=1.0, volatility=0.20, risk_free_rate=0.05),
        OptionScenario(spot=90.0, time_to_expiry=1.0, volatility=0.20, risk_free_rate=0.05),
    ]
    results = evaluate_price_scenarios(BASE, OptionType.CALL, _OneShotIterable(scenarios))
    assert len(results) == 2
    assert [r.scenario.spot for r in results] == [110.0, 90.0]


def test_scenarios_rejects_empty_list() -> None:
    with pytest.raises(ValueError, match="scenarios must not be empty"):
        evaluate_price_scenarios(BASE, OptionType.CALL, [])


def test_scenarios_rejects_empty_generator() -> None:
    def gen() -> Iterator[OptionScenario]:
        return
        yield  # pragma: no cover

    with pytest.raises(ValueError, match="scenarios must not be empty"):
        evaluate_price_scenarios(BASE, OptionType.CALL, gen())


def test_scenarios_invalid_content_raises_with_index() -> None:
    bad: list[object] = [
        OptionScenario(spot=110.0, time_to_expiry=1.0, volatility=0.20, risk_free_rate=0.05),
        "not-a-scenario",
        OptionScenario(spot=90.0, time_to_expiry=1.0, volatility=0.20, risk_free_rate=0.05),
    ]
    with pytest.raises(TypeError, match=r"scenarios\[1\]"):
        evaluate_price_scenarios(BASE, OptionType.CALL, bad)  # type: ignore[arg-type]


def test_scenarios_no_partial_results() -> None:
    seen: list[object] = []

    def gen() -> Iterator[OptionScenario]:
        for s in [
            OptionScenario(spot=110.0, time_to_expiry=1.0, volatility=0.20, risk_free_rate=0.05),
            "bad",
        ]:
            seen.append(s)
            yield s  # type: ignore[misc]

    with pytest.raises(TypeError):
        evaluate_price_scenarios(BASE, OptionType.CALL, gen())
    assert len(seen) == 2


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #


def test_invalid_base_inputs() -> None:
    with pytest.raises(TypeError):
        evaluate_price_scenarios("not-inputs", OptionType.CALL, [_base_scenario()])  # type: ignore[arg-type]


def test_invalid_option_type() -> None:
    with pytest.raises(TypeError):
        evaluate_price_scenarios(BASE, "call", [_base_scenario()])  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "bad_kwargs",
    [
        {"spot": 0.0, "time_to_expiry": 1.0, "volatility": 0.2, "risk_free_rate": 0.05},
        {"spot": -1.0, "time_to_expiry": 1.0, "volatility": 0.2, "risk_free_rate": 0.05},
        {"spot": 100.0, "time_to_expiry": -1.0, "volatility": 0.2, "risk_free_rate": 0.05},
        {"spot": 100.0, "time_to_expiry": 1.0, "volatility": -0.2, "risk_free_rate": 0.05},
        {"spot": True, "time_to_expiry": 1.0, "volatility": 0.2, "risk_free_rate": 0.05},
        {"spot": "100", "time_to_expiry": 1.0, "volatility": 0.2, "risk_free_rate": 0.05},
        {"spot": 100.0, "time_to_expiry": float("nan"), "volatility": 0.2, "risk_free_rate": 0.05},
        {"spot": 100.0, "time_to_expiry": float("inf"), "volatility": 0.2, "risk_free_rate": 0.05},
        {"spot": 100.0, "time_to_expiry": 1.0, "volatility": 0.2, "risk_free_rate": float("nan")},
    ],
)
def test_option_scenario_field_validation(bad_kwargs: dict[str, Any]) -> None:
    with pytest.raises((TypeError, ValueError)):
        OptionScenario(**bad_kwargs)


def test_option_scenario_invalid_label() -> None:
    with pytest.raises(TypeError):
        OptionScenario(
            spot=100.0,
            time_to_expiry=1.0,
            volatility=0.2,
            risk_free_rate=0.05,
            label=123,  # type: ignore[arg-type]
        )


def test_scenario_boundary_values_allowed() -> None:
    # Zero time, zero volatility, negative finite rates/yields are valid.
    scenario = OptionScenario(
        spot=100.0,
        time_to_expiry=0.0,
        volatility=0.0,
        risk_free_rate=-0.02,
        dividend_yield=-0.03,
    )
    assert scenario.time_to_expiry == 0.0
    assert scenario.volatility == 0.0
    assert scenario.risk_free_rate == -0.02
    assert scenario.dividend_yield == -0.03
