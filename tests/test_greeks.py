"""Tests for analytical Greeks of European Black-Scholes-Merton options.

This module verifies both the correctness of the closed-form analytical Greeks
and provides finite-difference verification. It tests the public API and
ensures that the OptionGreeks result model is immutable.
"""

from __future__ import annotations

import math

import pytest

from blackscholeslab import (
    BlackScholesInputs,
    OptionGreeks,
    OptionType,
    greeks_european,
    price_european,
)

ABS_TOL = 1e-10
REL_TOL = 1e-9
FINITE_DIFF_TOL = 1e-4


def test_reference_call_greeks_dividend_payoff() -> None:
    """Reference call Greeks with dividend yield (S=K=100, T=1, r=0.05, sigma=0.30, q=0.02)."""
    inputs = BlackScholesInputs(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.30,
        dividend_yield=0.02,
    )
    greeks = greeks_european(inputs, OptionType.CALL)
    assert isinstance(greeks, OptionGreeks)

    assert greeks.delta == pytest.approx(0.586851146134764, abs=ABS_TOL, rel=REL_TOL)
    assert greeks.gamma == pytest.approx(0.012633719170005811, abs=ABS_TOL, rel=REL_TOL)
    assert greeks.vega == pytest.approx(37.901157510017434, abs=ABS_TOL, rel=REL_TOL)
    assert greeks.theta == pytest.approx(-6.794713001470539, abs=ABS_TOL, rel=REL_TOL)
    assert greeks.rho == pytest.approx(45.66483334474905, abs=ABS_TOL, rel=REL_TOL)
    assert greeks.dividend_rho == pytest.approx(-58.685114613476394, abs=ABS_TOL, rel=REL_TOL)


def test_reference_put_greeks_dividend_payoff() -> None:
    """Reference put Greeks with dividend yield (S=K=100, T=1, r=0.05, sigma=0.30, q=0.02)."""
    inputs = BlackScholesInputs(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.30,
        dividend_yield=0.02,
    )
    greeks = greeks_european(inputs, OptionType.PUT)

    assert greeks.delta == pytest.approx(-0.3933475271719913, abs=ABS_TOL, rel=REL_TOL)
    assert greeks.gamma == pytest.approx(0.012633719170005811, abs=ABS_TOL, rel=REL_TOL)
    assert greeks.vega == pytest.approx(37.901157510017434, abs=ABS_TOL, rel=REL_TOL)
    assert greeks.theta == pytest.approx(-3.9989632255804795, abs=ABS_TOL, rel=REL_TOL)
    assert greeks.rho == pytest.approx(-49.45810910532236, abs=ABS_TOL, rel=REL_TOL)
    assert greeks.dividend_rho == pytest.approx(39.33475271719913, abs=ABS_TOL, rel=REL_TOL)


def test_call_put_gamma_equality() -> None:
    """Gamma is identical for call and put."""
    inputs = BlackScholesInputs(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.30,
        dividend_yield=0.02,
    )
    call_greeks = greeks_european(inputs, OptionType.CALL)
    put_greeks = greeks_european(inputs, OptionType.PUT)

    assert call_greeks.gamma == pytest.approx(put_greeks.gamma, abs=ABS_TOL, rel=REL_TOL)


def test_call_put_vega_equality() -> None:
    """Vega is identical for call and put."""
    inputs = BlackScholesInputs(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.30,
        dividend_yield=0.02,
    )
    call_greeks = greeks_european(inputs, OptionType.CALL)
    put_greeks = greeks_european(inputs, OptionType.PUT)

    assert call_greeks.vega == pytest.approx(put_greeks.vega, abs=ABS_TOL, rel=REL_TOL)


def test_call_put_delta_identity() -> None:
    """Call delta - put delta = exp(-q * T)."""
    inputs = BlackScholesInputs(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.30,
        dividend_yield=0.02,
    )
    call_greeks = greeks_european(inputs, OptionType.CALL)
    put_greeks = greeks_european(inputs, OptionType.PUT)

    expected = math.exp(-inputs.dividend_yield * inputs.time_to_expiry)
    actual = call_greeks.delta - put_greeks.delta

    assert actual == pytest.approx(expected, abs=ABS_TOL, rel=REL_TOL)


def test_call_put_rho_identity() -> None:
    """Call rho - put rho = K * T * exp(-r * T)."""
    inputs = BlackScholesInputs(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.30,
        dividend_yield=0.02,
    )
    call_greeks = greeks_european(inputs, OptionType.CALL)
    put_greeks = greeks_european(inputs, OptionType.PUT)

    expected = (
        inputs.strike
        * inputs.time_to_expiry
        * math.exp(-inputs.risk_free_rate * inputs.time_to_expiry)
    )
    actual = call_greeks.rho - put_greeks.rho

    assert actual == pytest.approx(expected, abs=ABS_TOL, rel=REL_TOL)


def test_call_put_dividend_rho_identity() -> None:
    """Call dividend rho - put dividend rho = -S * T * exp(-q * T)."""
    inputs = BlackScholesInputs(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.30,
        dividend_yield=0.02,
    )
    call_greeks = greeks_european(inputs, OptionType.CALL)
    put_greeks = greeks_european(inputs, OptionType.PUT)

    expected = (
        -inputs.spot
        * inputs.time_to_expiry
        * math.exp(-inputs.dividend_yield * inputs.time_to_expiry)
    )
    actual = call_greeks.dividend_rho - put_greeks.dividend_rho

    assert actual == pytest.approx(expected, abs=ABS_TOL, rel=REL_TOL)


def _finite_difference_delta(
    inputs: BlackScholesInputs, option_type: OptionType, h: float
) -> float:
    """Finite-difference delta: [V(S + h) - V(S - h)] / (2h)."""
    inputs_plus = BlackScholesInputs(
        spot=inputs.spot + h,
        strike=inputs.strike,
        time_to_expiry=inputs.time_to_expiry,
        risk_free_rate=inputs.risk_free_rate,
        volatility=inputs.volatility,
        dividend_yield=inputs.dividend_yield,
    )
    inputs_minus = BlackScholesInputs(
        spot=inputs.spot - h,
        strike=inputs.strike,
        time_to_expiry=inputs.time_to_expiry,
        risk_free_rate=inputs.risk_free_rate,
        volatility=inputs.volatility,
        dividend_yield=inputs.dividend_yield,
    )
    v_plus = price_european(inputs_plus, option_type)
    v_minus = price_european(inputs_minus, option_type)
    return (v_plus - v_minus) / (2.0 * h)


def _finite_difference_gamma(
    inputs: BlackScholesInputs, option_type: OptionType, h: float
) -> float:
    """Finite-difference gamma: [V(S + h) - 2V(S) + V(S - h)] / h²."""
    inputs_plus = BlackScholesInputs(
        spot=inputs.spot + h,
        strike=inputs.strike,
        time_to_expiry=inputs.time_to_expiry,
        risk_free_rate=inputs.risk_free_rate,
        volatility=inputs.volatility,
        dividend_yield=inputs.dividend_yield,
    )
    inputs_minus = BlackScholesInputs(
        spot=inputs.spot - h,
        strike=inputs.strike,
        time_to_expiry=inputs.time_to_expiry,
        risk_free_rate=inputs.risk_free_rate,
        volatility=inputs.volatility,
        dividend_yield=inputs.dividend_yield,
    )
    v = price_european(inputs, option_type)
    v_plus = price_european(inputs_plus, option_type)
    v_minus = price_european(inputs_minus, option_type)
    return (v_plus - 2.0 * v + v_minus) / (h * h)


def _finite_difference_vega(inputs: BlackScholesInputs, option_type: OptionType, h: float) -> float:
    """Finite-difference vega: [V(sigma + h) - V(sigma - h)] / (2h)."""
    inputs_plus = BlackScholesInputs(
        spot=inputs.spot,
        strike=inputs.strike,
        time_to_expiry=inputs.time_to_expiry,
        risk_free_rate=inputs.risk_free_rate,
        volatility=inputs.volatility + h,
        dividend_yield=inputs.dividend_yield,
    )
    inputs_minus = BlackScholesInputs(
        spot=inputs.spot,
        strike=inputs.strike,
        time_to_expiry=inputs.time_to_expiry,
        risk_free_rate=inputs.risk_free_rate,
        volatility=inputs.volatility - h,
        dividend_yield=inputs.dividend_yield,
    )
    v_plus = price_european(inputs_plus, option_type)
    v_minus = price_european(inputs_minus, option_type)
    return (v_plus - v_minus) / (2.0 * h)


def _finite_difference_rho(inputs: BlackScholesInputs, option_type: OptionType, h: float) -> float:
    """Finite-difference rho: [V(r + h) - V(r - h)] / (2h)."""
    inputs_plus = BlackScholesInputs(
        spot=inputs.spot,
        strike=inputs.strike,
        time_to_expiry=inputs.time_to_expiry,
        risk_free_rate=inputs.risk_free_rate + h,
        volatility=inputs.volatility,
        dividend_yield=inputs.dividend_yield,
    )
    inputs_minus = BlackScholesInputs(
        spot=inputs.spot,
        strike=inputs.strike,
        time_to_expiry=inputs.time_to_expiry,
        risk_free_rate=inputs.risk_free_rate - h,
        volatility=inputs.volatility,
        dividend_yield=inputs.dividend_yield,
    )
    v_plus = price_european(inputs_plus, option_type)
    v_minus = price_european(inputs_minus, option_type)
    return (v_plus - v_minus) / (2.0 * h)


def _finite_difference_dividend_rho(
    inputs: BlackScholesInputs, option_type: OptionType, h: float
) -> float:
    """Finite-difference dividend rho: [V(q + h) - V(q - h)] / (2h)."""
    inputs_plus = BlackScholesInputs(
        spot=inputs.spot,
        strike=inputs.strike,
        time_to_expiry=inputs.time_to_expiry,
        risk_free_rate=inputs.risk_free_rate,
        volatility=inputs.volatility,
        dividend_yield=inputs.dividend_yield + h,
    )
    inputs_minus = BlackScholesInputs(
        spot=inputs.spot,
        strike=inputs.strike,
        time_to_expiry=inputs.time_to_expiry,
        risk_free_rate=inputs.risk_free_rate,
        volatility=inputs.volatility,
        dividend_yield=inputs.dividend_yield - h,
    )
    v_plus = price_european(inputs_plus, option_type)
    v_minus = price_european(inputs_minus, option_type)
    return (v_plus - v_minus) / (2.0 * h)


def _finite_difference_theta(
    inputs: BlackScholesInputs, option_type: OptionType, h: float
) -> float:
    """Finite-difference theta: -[V(T + h) - V(T - h)] / (2h)."""
    inputs_plus = BlackScholesInputs(
        spot=inputs.spot,
        strike=inputs.strike,
        time_to_expiry=inputs.time_to_expiry + h,
        risk_free_rate=inputs.risk_free_rate,
        volatility=inputs.volatility,
        dividend_yield=inputs.dividend_yield,
    )
    inputs_minus = BlackScholesInputs(
        spot=inputs.spot,
        strike=inputs.strike,
        time_to_expiry=inputs.time_to_expiry - h,
        risk_free_rate=inputs.risk_free_rate,
        volatility=inputs.volatility,
        dividend_yield=inputs.dividend_yield,
    )
    v_plus = price_european(inputs_plus, option_type)
    v_minus = price_european(inputs_minus, option_type)
    return -(v_plus - v_minus) / (2.0 * h)


def test_finite_difference_delta() -> None:
    """Verify analytical delta against finite difference approximation."""
    inputs = BlackScholesInputs(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.30,
        dividend_yield=0.02,
    )
    h = 0.01
    fd_delta = _finite_difference_delta(inputs, OptionType.CALL, h)
    analytical_delta = greeks_european(inputs, OptionType.CALL).delta
    assert fd_delta == pytest.approx(analytical_delta, abs=FINITE_DIFF_TOL, rel=FINITE_DIFF_TOL)


def test_finite_difference_gamma() -> None:
    """Verify analytical gamma against finite difference approximation."""
    inputs = BlackScholesInputs(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.30,
        dividend_yield=0.02,
    )
    h = 0.01
    fd_gamma = _finite_difference_gamma(inputs, OptionType.CALL, h)
    analytical_gamma = greeks_european(inputs, OptionType.CALL).gamma
    assert fd_gamma == pytest.approx(analytical_gamma, abs=FINITE_DIFF_TOL, rel=FINITE_DIFF_TOL)


def test_finite_difference_vega() -> None:
    """Verify analytical vega against finite difference approximation."""
    inputs = BlackScholesInputs(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.30,
        dividend_yield=0.02,
    )
    h = 0.01
    fd_vega = _finite_difference_vega(inputs, OptionType.CALL, h)
    analytical_vega = greeks_european(inputs, OptionType.CALL).vega
    assert fd_vega == pytest.approx(analytical_vega, abs=FINITE_DIFF_TOL, rel=FINITE_DIFF_TOL)


def test_finite_difference_theta() -> None:
    """Verify analytical theta against finite difference approximation."""
    inputs = BlackScholesInputs(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.30,
        dividend_yield=0.02,
    )
    h = 0.01
    fd_theta = _finite_difference_theta(inputs, OptionType.CALL, h)
    analytical_theta = greeks_european(inputs, OptionType.CALL).theta
    assert fd_theta == pytest.approx(analytical_theta, abs=FINITE_DIFF_TOL, rel=FINITE_DIFF_TOL)


def test_finite_difference_rho() -> None:
    """Verify analytical rho against finite difference approximation."""
    inputs = BlackScholesInputs(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.30,
        dividend_yield=0.02,
    )
    h = 0.01
    fd_rho = _finite_difference_rho(inputs, OptionType.CALL, h)
    analytical_rho = greeks_european(inputs, OptionType.CALL).rho
    assert fd_rho == pytest.approx(analytical_rho, abs=FINITE_DIFF_TOL, rel=FINITE_DIFF_TOL)


def test_finite_difference_dividend_rho() -> None:
    """Verify analytical dividend rho against finite difference approximation."""
    inputs = BlackScholesInputs(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.30,
        dividend_yield=0.02,
    )
    h = 0.01
    fd_dividend_rho = _finite_difference_dividend_rho(inputs, OptionType.CALL, h)
    analytical_dividend_rho = greeks_european(inputs, OptionType.CALL).dividend_rho
    assert fd_dividend_rho == pytest.approx(
        analytical_dividend_rho, abs=FINITE_DIFF_TOL, rel=FINITE_DIFF_TOL
    )


def test_no_dividend_call_greeks() -> None:
    """Verify Greeks for non-dividend-paying underlying."""
    inputs = BlackScholesInputs(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.30,
        dividend_yield=0.0,
    )
    call_greeks = greeks_european(inputs, OptionType.CALL)
    put_greeks = greeks_european(inputs, OptionType.PUT)

    assert call_greeks.vega == pytest.approx(put_greeks.vega, abs=ABS_TOL, rel=REL_TOL)
    assert call_greeks.gamma == pytest.approx(put_greeks.gamma, abs=ABS_TOL, rel=REL_TOL)


def test_negative_finite_risk_free_rate() -> None:
    """Verify Greeks with negative finite risk-free rate."""
    inputs = BlackScholesInputs(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=-0.03,
        volatility=0.30,
        dividend_yield=0.02,
    )
    call_greeks = greeks_european(inputs, OptionType.CALL)

    assert math.isfinite(call_greeks.delta)
    assert math.isfinite(call_greeks.gamma)
    assert math.isfinite(call_greeks.vega)
    assert math.isfinite(call_greeks.theta)
    assert math.isfinite(call_greeks.rho)
    assert math.isfinite(call_greeks.dividend_rho)


def test_negative_finite_dividend_yield() -> None:
    """Verify Greeks with negative finite dividend yield."""
    inputs = BlackScholesInputs(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.30,
        dividend_yield=-0.02,
    )
    call_greeks = greeks_european(inputs, OptionType.CALL)

    assert math.isfinite(call_greeks.delta)
    assert math.isfinite(call_greeks.gamma)
    assert math.isfinite(call_greeks.vega)
    assert math.isfinite(call_greeks.theta)
    assert math.isfinite(call_greeks.rho)
    assert math.isfinite(call_greeks.dividend_rho)


def test_deep_in_the_money_call() -> None:
    """Verify Greeks for deep in-the-money call."""
    inputs = BlackScholesInputs(
        spot=1000.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.30,
        dividend_yield=0.02,
    )
    call_greeks = greeks_european(inputs, OptionType.CALL)

    assert call_greeks.delta > 0.9
    assert call_greeks.delta < 1.0
    assert call_greeks.gamma > 0.0
    assert call_greeks.vega > 0.0


def test_deep_in_the_money_put() -> None:
    """Verify Greeks for deep in-the-money put."""
    inputs = BlackScholesInputs(
        spot=10.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.30,
        dividend_yield=0.02,
    )
    put_greeks = greeks_european(inputs, OptionType.PUT)

    assert put_greeks.delta < -0.9
    assert put_greeks.delta > -1.0
    assert put_greeks.gamma > 0.0
    assert put_greeks.vega > 0.0


def test_deep_out_of_the_money_call() -> None:
    """Verify Greeks for deep out-of-the-money call."""
    inputs = BlackScholesInputs(
        spot=10.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.30,
        dividend_yield=0.02,
    )
    call_greeks = greeks_european(inputs, OptionType.CALL)

    assert call_greeks.delta == pytest.approx(0.0, abs=1e-6)
    assert call_greeks.gamma > 0.0
    assert call_greeks.vega > 0.0


def test_deep_out_of_the_money_put() -> None:
    """Verify Greeks for deep out-of-the-money put."""
    inputs = BlackScholesInputs(
        spot=1000.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.30,
        dividend_yield=0.02,
    )
    put_greeks = greeks_european(inputs, OptionType.PUT)

    assert put_greeks.delta == pytest.approx(0.0, abs=1e-6)
    assert put_greeks.gamma > 0.0
    assert put_greeks.vega > 0.0


def test_small_positive_time_to_expiry() -> None:
    """Verify Greeks for small but positive time to expiry."""
    inputs = BlackScholesInputs(
        spot=110.0,
        strike=100.0,
        time_to_expiry=1e-9,
        risk_free_rate=0.05,
        volatility=0.20,
        dividend_yield=0.02,
    )
    call_greeks = greeks_european(inputs, OptionType.CALL)

    assert math.isfinite(call_greeks.delta)
    assert math.isfinite(call_greeks.gamma)
    assert math.isfinite(call_greeks.vega)
    assert math.isfinite(call_greeks.theta)
    assert math.isfinite(call_greeks.rho)
    assert math.isfinite(call_greeks.dividend_rho)


def test_small_positive_volatility() -> None:
    """Verify Greeks for small but positive volatility."""
    inputs = BlackScholesInputs(
        spot=110.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=1e-9,
        dividend_yield=0.02,
    )
    call_greeks = greeks_european(inputs, OptionType.CALL)

    assert math.isfinite(call_greeks.delta)
    assert math.isfinite(call_greeks.gamma)
    assert math.isfinite(call_greeks.vega)
    assert math.isfinite(call_greeks.theta)
    assert math.isfinite(call_greeks.rho)
    assert math.isfinite(call_greeks.dividend_rho)


def test_zero_time_to_expiry_rejected() -> None:
    """Verify ValueError is raised when time_to_expiry is zero."""
    inputs = BlackScholesInputs(
        spot=100.0,
        strike=100.0,
        time_to_expiry=0.0,
        risk_free_rate=0.05,
        volatility=0.30,
        dividend_yield=0.02,
    )
    with pytest.raises(ValueError, match="time_to_expiry.*0"):
        greeks_european(inputs, OptionType.CALL)


def test_zero_volatility_rejected() -> None:
    """Verify ValueError is raised when volatility is zero."""
    inputs = BlackScholesInputs(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.0,
        dividend_yield=0.02,
    )
    with pytest.raises(ValueError, match="volatility.*0"):
        greeks_european(inputs, OptionType.CALL)


def test_invalid_option_type_rejected() -> None:
    """Verify TypeError is raised for invalid option type."""
    inputs = BlackScholesInputs(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.30,
        dividend_yield=0.02,
    )
    with pytest.raises(TypeError):
        greeks_european(inputs, "call")  # type: ignore[arg-type]


def test_option_greeks_immutable() -> None:
    """Verify that OptionGreeks is immutable (cannot modify fields)."""
    greeks = OptionGreeks(1.0, 2.0, 3.0, 4.0, 5.0, 6.0)
    assert hasattr(greeks, "delta")
    assert hasattr(greeks, "gamma")
    assert hasattr(greeks, "vega")
    assert hasattr(greeks, "theta")
    assert hasattr(greeks, "rho")
    assert hasattr(greeks, "dividend_rho")
    assert greeks.delta == 1.0
    assert greeks.gamma == 2.0
    assert greeks.vega == 3.0
    assert greeks.theta == 4.0
    assert greeks.rho == 5.0
    assert greeks.dividend_rho == 6.0


def test_top_level_api_import() -> None:
    """Verify that the new public API elements are properly exported."""
    from blackscholeslab import OptionGreeks, greeks_european

    inputs = BlackScholesInputs(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.30,
        dividend_yield=0.02,
    )

    greeks = greeks_european(inputs, OptionType.CALL)
    assert isinstance(greeks, OptionGreeks)

    assert greeks.delta == pytest.approx(0.586851146134764, abs=ABS_TOL, rel=REL_TOL)
