"""Tests for the immutable BlackScholesInputs model and OptionType enum."""

from __future__ import annotations

import pytest

from blackscholeslab import BlackScholesInputs, OptionType
from blackscholeslab.validation import validate_inputs


def test_option_type_members() -> None:
    assert OptionType.CALL.value == "call"
    assert OptionType.PUT.value == "put"
    assert set(OptionType) == {OptionType.CALL, OptionType.PUT}


def test_inputs_default_dividend_yield() -> None:
    inputs = BlackScholesInputs(
        spot=100.0, strike=100.0, time_to_expiry=1.0, risk_free_rate=0.05, volatility=0.2
    )
    assert inputs.dividend_yield == 0.0


def test_inputs_accept_int_equivalent() -> None:
    inputs = BlackScholesInputs(
        spot=42, strike=40, time_to_expiry=1, risk_free_rate=0, volatility=2, dividend_yield=0
    )
    assert inputs.spot == 42
    assert inputs.strike == 40
    assert inputs.time_to_expiry == 1
    assert inputs.volatility == 2


def test_inputs_are_immutable() -> None:
    inputs = BlackScholesInputs(
        spot=100.0, strike=100.0, time_to_expiry=1.0, risk_free_rate=0.05, volatility=0.2
    )
    with pytest.raises((AttributeError, TypeError)):
        inputs.spot = 50.0  # type: ignore[misc]


def test_inputs_are_comparable_and_hashable() -> None:
    a = BlackScholesInputs(
        spot=100.0, strike=100.0, time_to_expiry=1.0, risk_free_rate=0.05, volatility=0.2
    )
    b = BlackScholesInputs(
        spot=100.0, strike=100.0, time_to_expiry=1.0, risk_free_rate=0.05, volatility=0.2
    )
    assert a == b
    assert hash(a) == hash(b)
    assert a != BlackScholesInputs(
        spot=101.0, strike=100.0, time_to_expiry=1.0, risk_free_rate=0.05, volatility=0.2
    )


def test_inputs_constructed_then_validated() -> None:
    inputs = BlackScholesInputs(
        spot=100.0, strike=100.0, time_to_expiry=1.0, risk_free_rate=0.05, volatility=0.2
    )
    validate_inputs(inputs)  # should not raise


@pytest.mark.parametrize(
    "kwargs",
    [
        {"spot": 0.0},
        {"spot": -1.0},
        {"strike": 0.0},
        {"strike": -5.0},
        {"time_to_expiry": -0.1},
        {"volatility": -0.2},
    ],
)
def test_invalid_inputs_rejected_at_construction(kwargs: dict[str, float]) -> None:
    base = dict(spot=100.0, strike=100.0, time_to_expiry=1.0, risk_free_rate=0.05, volatility=0.2)
    base.update(kwargs)
    with pytest.raises(ValueError):
        BlackScholesInputs(**base)
