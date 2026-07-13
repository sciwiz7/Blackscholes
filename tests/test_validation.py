"""Tests for input validation helpers."""

from __future__ import annotations

import pytest

from blackscholeslab import BlackScholesInputs, OptionType
from blackscholeslab.validation import (
    validate_inputs,
    validate_option_type,
    validate_real_number,
)


@pytest.mark.parametrize(
    "value",
    [
        True,
        False,
        "42",
        None,
        1 + 2j,
        float("nan"),
        float("inf"),
        float("-inf"),
        [1, 2],
        {"a": 1},
    ],
)
def test_validate_real_number_rejects_wrong_types_and_nonfinite(value: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        validate_real_number(value, "field", allow_negative=True, allow_zero=True)


def test_validate_real_number_allows_finite_negative_when_permitted() -> None:
    validate_real_number(-0.05, "rate", allow_negative=True, allow_zero=True)


def test_validate_real_number_rejects_negative_when_not_allowed() -> None:
    with pytest.raises(ValueError):
        validate_real_number(-1.0, "spot", allow_negative=False, allow_zero=False)


def test_validate_real_number_rejects_zero_when_not_allowed() -> None:
    with pytest.raises(ValueError):
        validate_real_number(0.0, "spot", allow_negative=False, allow_zero=False)


@pytest.mark.parametrize(
    "field,value",
    [
        ("spot", 0.0),
        ("spot", -1.0),
        ("spot", True),
        ("spot", "x"),
        ("spot", None),
        ("spot", 1 + 0j),
        ("spot", float("nan")),
        ("spot", float("inf")),
        ("spot", float("-inf")),
        ("strike", 0.0),
        ("strike", -2.0),
        ("strike", False),
        ("strike", "10"),
        ("strike", None),
        ("strike", complex(1, 1)),
        ("strike", float("nan")),
        ("strike", float("inf")),
        ("strike", float("-inf")),
        ("time_to_expiry", -0.1),
        ("time_to_expiry", True),
        ("time_to_expiry", "0.5"),
        ("time_to_expiry", None),
        ("time_to_expiry", float("nan")),
        ("time_to_expiry", float("inf")),
        ("time_to_expiry", float("-inf")),
        ("volatility", -0.1),
        ("volatility", True),
        ("volatility", "0.2"),
        ("volatility", None),
        ("volatility", 1j),
        ("volatility", float("nan")),
        ("volatility", float("inf")),
        ("volatility", float("-inf")),
        ("risk_free_rate", True),
        ("risk_free_rate", "0.05"),
        ("risk_free_rate", None),
        ("risk_free_rate", 1 + 1j),
        ("risk_free_rate", float("nan")),
        ("risk_free_rate", float("inf")),
        ("risk_free_rate", float("-inf")),
        ("dividend_yield", True),
        ("dividend_yield", "0.0"),
        ("dividend_yield", None),
        ("dividend_yield", 1j),
        ("dividend_yield", float("nan")),
        ("dividend_yield", float("inf")),
        ("dividend_yield", float("-inf")),
    ],
)
def test_validate_inputs_rejects_invalid_field(field: str, value: object) -> None:
    base: dict[str, object] = dict(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.2,
        dividend_yield=0.0,
    )
    base[field] = value
    with pytest.raises((TypeError, ValueError)):
        validate_inputs(BlackScholesInputs(**base))  # type: ignore[arg-type]


def test_validate_inputs_allows_negative_rates_and_yields() -> None:
    inputs = BlackScholesInputs(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=-0.02,
        volatility=0.2,
        dividend_yield=-0.01,
    )
    validate_inputs(inputs)  # should not raise


def test_validate_inputs_rejects_non_input_object() -> None:
    with pytest.raises(TypeError):
        validate_inputs("not inputs")


@pytest.mark.parametrize("bad", ["call", "PUT", 1, 0, None, True, "CALL"])
def test_validate_option_type_rejects_invalid(bad: object) -> None:
    with pytest.raises(TypeError):
        validate_option_type(bad)


def test_validate_option_type_accepts_members() -> None:
    assert validate_option_type(OptionType.CALL) is OptionType.CALL
    assert validate_option_type(OptionType.PUT) is OptionType.PUT
