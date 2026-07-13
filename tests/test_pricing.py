"""Tests for the European pricing core, including references and invariants."""

from __future__ import annotations

import math

import pytest

from blackscholeslab import BlackScholesInputs, OptionType, price_european

ABS_TOL = 1e-10
REL_TOL = 1e-9


def _price(inputs: BlackScholesInputs, option_type: OptionType) -> float:
    return price_european(inputs, option_type)


# --------------------------------------------------------------------------- #
# Reference values
# --------------------------------------------------------------------------- #


def test_reference_no_dividend_call_put() -> None:
    # Established no-dividend reference case.
    inputs = BlackScholesInputs(
        spot=42.0,
        strike=40.0,
        time_to_expiry=0.5,
        risk_free_rate=0.10,
        volatility=0.20,
        dividend_yield=0.0,
    )
    call = _price(inputs, OptionType.CALL)
    put = _price(inputs, OptionType.PUT)
    assert call == pytest.approx(4.759422392871535, abs=ABS_TOL, rel=REL_TOL)
    assert put == pytest.approx(0.8085993729000958, abs=ABS_TOL, rel=REL_TOL)


def test_reference_dividend_call_put() -> None:
    # Independently computed dividend-paying reference (S=K=100, T=1, r=0.05,
    # sigma=0.30, q=0.02). Verified against the closed-form BSM formulas using
    # math.erf and the standard normal CDF.
    inputs = BlackScholesInputs(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.30,
        dividend_yield=0.02,
    )
    call = _price(inputs, OptionType.CALL)
    put = _price(inputs, OptionType.PUT)
    assert call == pytest.approx(13.020281268727338, abs=ABS_TOL, rel=REL_TOL)
    assert put == pytest.approx(10.123356388123227, abs=ABS_TOL, rel=REL_TOL)


# --------------------------------------------------------------------------- #
# Put-call parity
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "risk_free_rate, dividend_yield",
    [
        (0.10, 0.0),
        (0.05, 0.02),
        (-0.03, 0.0),
        (0.0, -0.01),
    ],
)
def test_put_call_parity(risk_free_rate: float, dividend_yield: float) -> None:
    inputs = BlackScholesInputs(
        spot=42.0,
        strike=40.0,
        time_to_expiry=0.5,
        risk_free_rate=risk_free_rate,
        volatility=0.20,
        dividend_yield=dividend_yield,
    )
    call = _price(inputs, OptionType.CALL)
    put = _price(inputs, OptionType.PUT)
    lhs = call - put
    rhs = inputs.spot * math.exp(
        -dividend_yield * inputs.time_to_expiry
    ) - inputs.strike * math.exp(-risk_free_rate * inputs.time_to_expiry)
    assert lhs == pytest.approx(rhs, abs=ABS_TOL, rel=REL_TOL)


# --------------------------------------------------------------------------- #
# Expiry behaviour
# --------------------------------------------------------------------------- #


def test_expiry_call_intrinsic() -> None:
    inputs = BlackScholesInputs(
        spot=110.0,
        strike=100.0,
        time_to_expiry=0.0,
        risk_free_rate=0.10,
        volatility=0.20,
        dividend_yield=0.05,
    )
    assert _price(inputs, OptionType.CALL) == pytest.approx(10.0)


def test_expiry_call_out_of_money() -> None:
    inputs = BlackScholesInputs(
        spot=90.0, strike=100.0, time_to_expiry=0.0, risk_free_rate=0.10, volatility=0.20
    )
    assert _price(inputs, OptionType.CALL) == pytest.approx(0.0)


def test_expiry_put_intrinsic() -> None:
    inputs = BlackScholesInputs(
        spot=90.0, strike=100.0, time_to_expiry=0.0, risk_free_rate=0.10, volatility=0.20
    )
    assert _price(inputs, OptionType.PUT) == pytest.approx(10.0)


def test_expiry_put_out_of_money() -> None:
    inputs = BlackScholesInputs(
        spot=110.0, strike=100.0, time_to_expiry=0.0, risk_free_rate=0.10, volatility=0.20
    )
    assert _price(inputs, OptionType.PUT) == pytest.approx(0.0)


def test_expiry_exactly_at_money() -> None:
    inputs = BlackScholesInputs(
        spot=100.0, strike=100.0, time_to_expiry=0.0, risk_free_rate=0.10, volatility=0.20
    )
    assert _price(inputs, OptionType.CALL) == pytest.approx(0.0)
    assert _price(inputs, OptionType.PUT) == pytest.approx(0.0)


def test_expiry_ignores_rates_vol_dividends() -> None:
    base = dict(spot=120.0, strike=100.0, time_to_expiry=0.0)
    a = _price(BlackScholesInputs(**base, risk_free_rate=0.0, volatility=0.0), OptionType.CALL)
    b = _price(
        BlackScholesInputs(**base, risk_free_rate=0.5, volatility=0.9, dividend_yield=0.3),
        OptionType.CALL,
    )
    assert a == pytest.approx(20.0)
    assert b == pytest.approx(20.0)


# --------------------------------------------------------------------------- #
# Zero-volatility behaviour
# --------------------------------------------------------------------------- #


def test_zero_vol_call() -> None:
    inputs = BlackScholesInputs(
        spot=110.0, strike=100.0, time_to_expiry=1.0, risk_free_rate=0.05, volatility=0.0
    )
    expected = max(110.0 * math.exp(0.0) - 100.0 * math.exp(-0.05 * 1.0), 0.0)
    assert _price(inputs, OptionType.CALL) == pytest.approx(expected)


def test_zero_vol_put() -> None:
    inputs = BlackScholesInputs(
        spot=90.0, strike=100.0, time_to_expiry=1.0, risk_free_rate=0.05, volatility=0.0
    )
    expected = max(100.0 * math.exp(-0.05 * 1.0) - 90.0 * math.exp(0.0), 0.0)
    assert _price(inputs, OptionType.PUT) == pytest.approx(expected)


def test_zero_vol_with_dividend() -> None:
    inputs = BlackScholesInputs(
        spot=110.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.0,
        dividend_yield=0.02,
    )
    expected = max(110.0 * math.exp(-0.02 * 1.0) - 100.0 * math.exp(-0.05 * 1.0), 0.0)
    assert _price(inputs, OptionType.CALL) == pytest.approx(expected)


def test_zero_vol_negative_rate() -> None:
    inputs = BlackScholesInputs(
        spot=110.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=-0.05,
        volatility=0.0,
    )
    expected = max(110.0 - 100.0 * math.exp(0.05 * 1.0), 0.0)
    assert _price(inputs, OptionType.CALL) == pytest.approx(expected)


# --------------------------------------------------------------------------- #
# Edge cases
# --------------------------------------------------------------------------- #


def test_at_the_money_call_put() -> None:
    inputs = BlackScholesInputs(
        spot=100.0, strike=100.0, time_to_expiry=1.0, risk_free_rate=0.05, volatility=0.20
    )
    assert _price(inputs, OptionType.CALL) > 0.0
    assert _price(inputs, OptionType.PUT) > 0.0


def test_deep_itm_call() -> None:
    inputs = BlackScholesInputs(
        spot=1000.0, strike=100.0, time_to_expiry=1.0, risk_free_rate=0.05, volatility=0.20
    )
    price = _price(inputs, OptionType.CALL)
    assert price > 0.0
    assert price < 1000.0


def test_deep_itm_put() -> None:
    inputs = BlackScholesInputs(
        spot=10.0, strike=100.0, time_to_expiry=1.0, risk_free_rate=0.05, volatility=0.20
    )
    price = _price(inputs, OptionType.PUT)
    assert price > 0.0
    assert price < 100.0 * math.exp(-0.05 * 1.0) + 1e-9


def test_deep_otm_call() -> None:
    inputs = BlackScholesInputs(
        spot=10.0, strike=100.0, time_to_expiry=1.0, risk_free_rate=0.05, volatility=0.20
    )
    assert _price(inputs, OptionType.CALL) == pytest.approx(0.0, abs=1e-6)


def test_deep_otm_put() -> None:
    inputs = BlackScholesInputs(
        spot=1000.0, strike=100.0, time_to_expiry=1.0, risk_free_rate=0.05, volatility=0.20
    )
    assert _price(inputs, OptionType.PUT) == pytest.approx(0.0, abs=1e-6)


def test_very_small_time_to_expiry() -> None:
    inputs = BlackScholesInputs(
        spot=110.0,
        strike=100.0,
        time_to_expiry=1e-9,
        risk_free_rate=0.05,
        volatility=0.20,
    )
    assert _price(inputs, OptionType.CALL) == pytest.approx(10.0, abs=1e-6)


def test_very_small_volatility() -> None:
    inputs = BlackScholesInputs(
        spot=110.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=1e-9,
    )
    expected = max(110.0 - 100.0 * math.exp(-0.05), 0.0)
    assert _price(inputs, OptionType.CALL) == pytest.approx(expected, rel=1e-6)


def test_negative_finite_risk_free_rate() -> None:
    inputs = BlackScholesInputs(
        spot=100.0, strike=100.0, time_to_expiry=1.0, risk_free_rate=-0.03, volatility=0.20
    )
    assert _price(inputs, OptionType.CALL) > 0.0


def test_negative_finite_dividend_yield() -> None:
    inputs = BlackScholesInputs(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.20,
        dividend_yield=-0.02,
    )
    assert _price(inputs, OptionType.CALL) > 0.0


def test_large_spot_and_strike() -> None:
    inputs = BlackScholesInputs(
        spot=1e6,
        strike=1.1e6,
        time_to_expiry=0.5,
        risk_free_rate=0.03,
        volatility=0.25,
    )
    assert math.isfinite(_price(inputs, OptionType.CALL))
    assert math.isfinite(_price(inputs, OptionType.PUT))


# --------------------------------------------------------------------------- #
# Invariants
# --------------------------------------------------------------------------- #


def test_call_put_non_negative() -> None:
    inputs = BlackScholesInputs(
        spot=42.0, strike=40.0, time_to_expiry=0.5, risk_free_rate=0.10, volatility=0.20
    )
    assert _price(inputs, OptionType.CALL) >= 0.0
    assert _price(inputs, OptionType.PUT) >= 0.0


def test_increasing_spot_does_not_reduce_call() -> None:
    base = dict(strike=100.0, time_to_expiry=1.0, risk_free_rate=0.05, volatility=0.20)
    low = _price(BlackScholesInputs(spot=90.0, **base), OptionType.CALL)
    high = _price(BlackScholesInputs(spot=110.0, **base), OptionType.CALL)
    assert high >= low


def test_increasing_spot_does_not_increase_put() -> None:
    base = dict(strike=100.0, time_to_expiry=1.0, risk_free_rate=0.05, volatility=0.20)
    low = _price(BlackScholesInputs(spot=90.0, **base), OptionType.PUT)
    high = _price(BlackScholesInputs(spot=110.0, **base), OptionType.PUT)
    assert high <= low


def test_call_does_not_exceed_discounted_spot() -> None:
    inputs = BlackScholesInputs(
        spot=100.0, strike=100.0, time_to_expiry=1.0, risk_free_rate=0.05, volatility=0.20
    )
    call = _price(inputs, OptionType.CALL)
    discounted_spot = inputs.spot * math.exp(-inputs.dividend_yield * inputs.time_to_expiry)
    assert call <= discounted_spot + 1e-12


def test_put_does_not_exceed_discounted_strike() -> None:
    inputs = BlackScholesInputs(
        spot=100.0, strike=100.0, time_to_expiry=1.0, risk_free_rate=0.05, volatility=0.20
    )
    put = _price(inputs, OptionType.PUT)
    assert put <= inputs.strike * math.exp(-inputs.risk_free_rate * inputs.time_to_expiry) + 1e-12


def test_invalid_option_type_rejected() -> None:
    inputs = BlackScholesInputs(
        spot=100.0, strike=100.0, time_to_expiry=1.0, risk_free_rate=0.05, volatility=0.20
    )
    with pytest.raises(TypeError):
        price_european(inputs, "call")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        price_european(inputs, 1)  # type: ignore[arg-type]
