"""Tests for the implied-volatility solver and its input model.

These tests cover:

- the public API import surface and immutability of ``ImpliedVolatilityInputs``;
- reference round-trip recovery for established no-dividend and dividend cases;
- a deterministic round-trip matrix across strikes, expiries, yields, and rates;
- European no-arbitrage boundary handling (exact lower/upper bounds);
- adaptive bracketing and maximum-volatility behaviour;
- put-call parity consistency and repricing residuals.

They do not reimplement the bisection algorithm to assert the same logic; they
exercise the public solver against the pricing oracle and documented identities.
"""

from __future__ import annotations

import math

import pytest

from blackscholeslab import (
    BlackScholesInputs,
    ImpliedVolatilityInputs,
    OptionType,
    implied_volatility,
    price_european,
)

# --------------------------------------------------------------------------- #
# Reference constants (independently verified against the closed-form BSM
# formulas via math.erf and the standard normal CDF).
# --------------------------------------------------------------------------- #

NO_DIV_TRUE_VOL = 0.20
NO_DIV_CALL = 10.450583572185565
NO_DIV_PUT = 5.573526022256971

DIV_TRUE_VOL = 0.30
DIV_CALL = 13.020281268727338
DIV_PUT = 10.123356388123227

RT_ABS_TOL = 1e-8
RT_REL_TOL = 1e-7

SOLVE_VOL_TOL = 1e-7


@pytest.fixture
def no_dividend_inputs() -> ImpliedVolatilityInputs:
    return ImpliedVolatilityInputs(
        market_price=NO_DIV_CALL,
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        dividend_yield=0.0,
    )


@pytest.fixture
def dividend_inputs() -> ImpliedVolatilityInputs:
    return ImpliedVolatilityInputs(
        market_price=DIV_CALL,
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        dividend_yield=0.02,
    )


# --------------------------------------------------------------------------- #
# Public API and immutability
# --------------------------------------------------------------------------- #


def test_public_imports_work() -> None:
    from blackscholeslab import (
        ImpliedVolatilityInputs,
        OptionType,
        implied_volatility,
    )

    assert ImpliedVolatilityInputs is not None
    assert OptionType is not None
    assert callable(implied_volatility)


def test_inputs_are_immutable() -> None:
    inputs = ImpliedVolatilityInputs(
        market_price=10.0,
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
    )
    with pytest.raises((AttributeError, TypeError)):
        inputs.spot = 50.0  # type: ignore[misc]


def test_inputs_default_dividend_yield() -> None:
    inputs = ImpliedVolatilityInputs(
        market_price=10.0,
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
    )
    assert inputs.dividend_yield == 0.0


# --------------------------------------------------------------------------- #
# Input-model validation
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "kwargs",
    [
        {"market_price": -1.0},
        {"market_price": True},
        {"market_price": "x"},
        {"market_price": None},
        {"market_price": float("nan")},
        {"market_price": float("inf")},
        {"spot": 0.0},
        {"spot": -1.0},
        {"spot": 1 + 0j},
        {"strike": 0.0},
        {"strike": -2.0},
        {"strike": False},
        {"time_to_expiry": 0.0},
        {"time_to_expiry": -0.1},
        {"time_to_expiry": float("-inf")},
        {"risk_free_rate": "0.05"},
        {"risk_free_rate": 1 + 1j},
        {"dividend_yield": None},
        {"dividend_yield": float("nan")},
    ],
)
def test_invalid_inputs_rejected_at_construction(kwargs: dict[str, object]) -> None:
    base: dict[str, object] = dict(
        market_price=10.0,
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        dividend_yield=0.0,
    )
    base.update(kwargs)
    with pytest.raises((TypeError, ValueError)):
        ImpliedVolatilityInputs(**base)  # type: ignore[arg-type]


def test_inputs_allow_negative_rates_and_yields() -> None:
    inputs = ImpliedVolatilityInputs(
        market_price=10.0,
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=-0.02,
        dividend_yield=-0.01,
    )
    assert inputs.risk_free_rate == -0.02
    assert inputs.dividend_yield == -0.01


# --------------------------------------------------------------------------- #
# Reference round-trip recovery
# --------------------------------------------------------------------------- #


def test_reference_no_dividend_call() -> None:
    vol = implied_volatility(
        ImpliedVolatilityInputs(
            market_price=NO_DIV_CALL,
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            dividend_yield=0.0,
        ),
        OptionType.CALL,
    )
    assert vol == pytest.approx(NO_DIV_TRUE_VOL, abs=SOLVE_VOL_TOL, rel=SOLVE_VOL_TOL)


def test_reference_no_dividend_put() -> None:
    vol = implied_volatility(
        ImpliedVolatilityInputs(
            market_price=NO_DIV_PUT,
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            dividend_yield=0.0,
        ),
        OptionType.PUT,
    )
    assert vol == pytest.approx(NO_DIV_TRUE_VOL, abs=SOLVE_VOL_TOL, rel=SOLVE_VOL_TOL)


def test_reference_dividend_call() -> None:
    vol = implied_volatility(
        ImpliedVolatilityInputs(
            market_price=DIV_CALL,
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            dividend_yield=0.02,
        ),
        OptionType.CALL,
    )
    assert vol == pytest.approx(DIV_TRUE_VOL, abs=SOLVE_VOL_TOL, rel=SOLVE_VOL_TOL)


def test_reference_dividend_put() -> None:
    vol = implied_volatility(
        ImpliedVolatilityInputs(
            market_price=DIV_PUT,
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            dividend_yield=0.02,
        ),
        OptionType.PUT,
    )
    assert vol == pytest.approx(DIV_TRUE_VOL, abs=SOLVE_VOL_TOL, rel=SOLVE_VOL_TOL)


# --------------------------------------------------------------------------- #
# Deterministic round-trip matrix
# --------------------------------------------------------------------------- #

MATRIX = [
    # (spot, strike, T, r, q, true_vol, label)
    (100.0, 100.0, 1.0, 0.05, 0.0, 0.05, "ATM short/no-div low-vol"),
    (100.0, 100.0, 1.0, 0.05, 0.0, 0.20, "ATM short/no-div mid-vol"),
    (100.0, 100.0, 1.0, 0.05, 0.0, 0.50, "ATM short/no-div high-vol"),
    (100.0, 100.0, 1.0, 0.05, 0.0, 1.00, "ATM short/no-div very-high-vol"),
    (100.0, 100.0, 1.0, 0.05, 0.0, 3.00, "ATM short/no-div extreme-vol"),
    (100.0, 100.0, 1.0, 0.05, 0.02, 0.20, "ATM div mid-vol"),
    (100.0, 100.0, 1.0, 0.05, 0.02, 1.00, "ATM div high-vol"),
    (100.0, 100.0, 0.25, 0.05, 0.0, 0.20, "ATM short-expiry"),
    (100.0, 100.0, 5.0, 0.05, 0.0, 0.30, "ATM long-expiry"),
    (100.0, 110.0, 1.0, 0.05, 0.0, 0.20, "OTM call / ITM put"),
    (100.0, 90.0, 1.0, 0.05, 0.0, 0.20, "ITM call / OTM put"),
    (100.0, 100.0, 1.0, -0.02, 0.0, 0.20, "negative rate"),
    (100.0, 100.0, 1.0, 0.05, -0.03, 0.20, "negative dividend yield"),
    (50.0, 60.0, 2.0, 0.03, 0.01, 0.50, "deep OTM/long"),
    (200.0, 150.0, 0.5, 0.08, 0.02, 0.30, "deep ITM/short"),
]


@pytest.mark.parametrize(
    "spot,strike,T,r,q,true_vol,label",
    MATRIX,
    ids=[m[6] for m in MATRIX],
)
def test_round_trip_matrix(
    spot: float, strike: float, T: float, r: float, q: float, true_vol: float, label: str
) -> None:
    pricing_inputs = BlackScholesInputs(
        spot=spot,
        strike=strike,
        time_to_expiry=T,
        risk_free_rate=r,
        volatility=true_vol,
        dividend_yield=q,
    )
    for option_type in (OptionType.CALL, OptionType.PUT):
        market_price = price_european(pricing_inputs, option_type)
        solved = implied_volatility(
            ImpliedVolatilityInputs(
                market_price=market_price,
                spot=spot,
                strike=strike,
                time_to_expiry=T,
                risk_free_rate=r,
                dividend_yield=q,
            ),
            option_type,
        )
        assert solved == pytest.approx(true_vol, abs=SOLVE_VOL_TOL, rel=SOLVE_VOL_TOL)


# --------------------------------------------------------------------------- #
# No-arbitrage boundary handling
# --------------------------------------------------------------------------- #


def _discounted_spot(spot: float, q: float, T: float) -> float:
    return spot * math.exp(-q * T)


def _discounted_strike(strike: float, r: float, T: float) -> float:
    return strike * math.exp(-r * T)


def test_call_exact_lower_bound_returns_zero() -> None:
    spot, strike, T, r, q = 100.0, 110.0, 1.0, 0.05, 0.0
    ds = _discounted_spot(spot, q, T)
    dk = _discounted_strike(strike, r, T)
    lower = max(ds - dk, 0.0)
    vol = implied_volatility(
        ImpliedVolatilityInputs(
            market_price=lower,
            spot=spot,
            strike=strike,
            time_to_expiry=T,
            risk_free_rate=r,
            dividend_yield=q,
        ),
        OptionType.CALL,
    )
    assert vol == 0.0


def test_put_exact_lower_bound_returns_zero() -> None:
    spot, strike, T, r, q = 100.0, 90.0, 1.0, 0.05, 0.0
    ds = _discounted_spot(spot, q, T)
    dk = _discounted_strike(strike, r, T)
    lower = max(dk - ds, 0.0)
    vol = implied_volatility(
        ImpliedVolatilityInputs(
            market_price=lower,
            spot=spot,
            strike=strike,
            time_to_expiry=T,
            risk_free_rate=r,
            dividend_yield=q,
        ),
        OptionType.PUT,
    )
    assert vol == 0.0


@pytest.mark.parametrize("option_type", [OptionType.CALL, OptionType.PUT])
def test_price_below_lower_bound_rejected(option_type: OptionType) -> None:
    spot, strike, T, r, q = 100.0, 100.0, 1.0, 0.05, 0.0
    ds = _discounted_spot(spot, q, T)
    dk = _discounted_strike(strike, r, T)
    lower = max(ds - dk, 0.0) if option_type is OptionType.CALL else max(dk - ds, 0.0)
    with pytest.raises(ValueError):
        implied_volatility(
            ImpliedVolatilityInputs(
                market_price=lower - 1e-6,
                spot=spot,
                strike=strike,
                time_to_expiry=T,
                risk_free_rate=r,
                dividend_yield=q,
            ),
            option_type,
        )


@pytest.mark.parametrize("option_type", [OptionType.CALL, OptionType.PUT])
def test_price_at_or_above_upper_bound_rejected(option_type: OptionType) -> None:
    spot, strike, T, r, q = 100.0, 100.0, 1.0, 0.05, 0.0
    ds = _discounted_spot(spot, q, T)
    dk = _discounted_strike(strike, r, T)
    upper = ds if option_type is OptionType.CALL else dk
    with pytest.raises(ValueError):
        implied_volatility(
            ImpliedVolatilityInputs(
                market_price=upper,
                spot=spot,
                strike=strike,
                time_to_expiry=T,
                risk_free_rate=r,
                dividend_yield=q,
            ),
            option_type,
        )
    with pytest.raises(ValueError):
        implied_volatility(
            ImpliedVolatilityInputs(
                market_price=upper + 1.0,
                spot=spot,
                strike=strike,
                time_to_expiry=T,
                risk_free_rate=r,
                dividend_yield=q,
            ),
            option_type,
        )


# --------------------------------------------------------------------------- #
# Solver-control validation
# --------------------------------------------------------------------------- #


def test_initial_upper_volatility_above_max_rejected() -> None:
    with pytest.raises(ValueError):
        implied_volatility(
            ImpliedVolatilityInputs(
                market_price=10.0,
                spot=100.0,
                strike=100.0,
                time_to_expiry=1.0,
                risk_free_rate=0.05,
            ),
            OptionType.CALL,
            initial_upper_volatility=5.0,
            max_volatility=2.0,
        )


def test_invalid_solver_controls_rejected() -> None:
    base = dict(
        inputs=ImpliedVolatilityInputs(
            market_price=10.0,
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
        ),
        option_type=OptionType.CALL,
    )
    with pytest.raises((TypeError, ValueError)):
        implied_volatility(**base, price_tolerance=0.0)  # type: ignore[arg-type]
    with pytest.raises((TypeError, ValueError)):
        implied_volatility(**base, volatility_tolerance=-1.0)  # type: ignore[arg-type]
    with pytest.raises((TypeError, ValueError)):
        implied_volatility(**base, max_iterations=0)  # type: ignore[arg-type]
    with pytest.raises((TypeError, ValueError)):
        implied_volatility(**base, max_iterations=True)  # type: ignore[arg-type]
    with pytest.raises((TypeError, ValueError)):
        implied_volatility(**base, initial_upper_volatility="0.5")  # type: ignore[arg-type]
    with pytest.raises((TypeError, ValueError)):
        implied_volatility(**base, max_volatility=float("inf"))  # type: ignore[arg-type]


def test_wrong_inputs_type_rejected() -> None:
    with pytest.raises(TypeError):
        implied_volatility(
            BlackScholesInputs(  # type: ignore[arg-type]
                spot=100.0,
                strike=100.0,
                time_to_expiry=1.0,
                risk_free_rate=0.05,
                volatility=0.2,
            ),
            OptionType.CALL,
        )


def test_bracket_clamps_to_max_volatility_when_bracketed() -> None:
    # initial_upper_volatility=0.6 and max_volatility=2.0 make the doubling step
    # overshoot max_volatility; the bracket is then clamped to max_volatility
    # because the target is bracketed there.
    true_vol = 1.5
    spot, strike, T, r, q = 100.0, 100.0, 1.0, 0.05, 0.0
    pricing_inputs = BlackScholesInputs(
        spot=spot,
        strike=strike,
        time_to_expiry=T,
        risk_free_rate=r,
        volatility=true_vol,
        dividend_yield=q,
    )
    market_price = price_european(pricing_inputs, OptionType.CALL)
    solved = implied_volatility(
        ImpliedVolatilityInputs(
            market_price=market_price,
            spot=spot,
            strike=strike,
            time_to_expiry=T,
            risk_free_rate=r,
            dividend_yield=q,
        ),
        OptionType.CALL,
        initial_upper_volatility=0.6,
        max_volatility=2.0,
    )
    assert solved == pytest.approx(true_vol, abs=SOLVE_VOL_TOL, rel=SOLVE_VOL_TOL)


def test_volatility_tolerance_terminates() -> None:
    # With an extremely tight price tolerance and a loose volatility tolerance,
    # the solver terminates on the interval-width criterion.
    spot, strike, T, r, q = 100.0, 100.0, 1.0, 0.05, 0.0
    market_price = NO_DIV_CALL
    solved = implied_volatility(
        ImpliedVolatilityInputs(
            market_price=market_price,
            spot=spot,
            strike=strike,
            time_to_expiry=T,
            risk_free_rate=r,
            dividend_yield=q,
        ),
        OptionType.CALL,
        price_tolerance=1e-15,
        volatility_tolerance=0.05,
    )
    assert solved == pytest.approx(NO_DIV_TRUE_VOL, abs=0.05)


def test_malformed_option_type_rejected() -> None:
    with pytest.raises(TypeError):
        implied_volatility(
            ImpliedVolatilityInputs(
                market_price=10.0,
                spot=100.0,
                strike=100.0,
                time_to_expiry=1.0,
                risk_free_rate=0.05,
            ),
            "call",  # type: ignore[arg-type]
        )


# --------------------------------------------------------------------------- #
# Adaptive bracketing and maximum volatility
# --------------------------------------------------------------------------- #


def test_bracket_expands_beyond_default_upper() -> None:
    # A very high true volatility forces the bracket to expand past 0.5.
    true_vol = 3.0
    spot, strike, T, r, q = 100.0, 100.0, 1.0, 0.05, 0.0
    pricing_inputs = BlackScholesInputs(
        spot=spot,
        strike=strike,
        time_to_expiry=T,
        risk_free_rate=r,
        volatility=true_vol,
        dividend_yield=q,
    )
    market_price = price_european(pricing_inputs, OptionType.CALL)
    solved = implied_volatility(
        ImpliedVolatilityInputs(
            market_price=market_price,
            spot=spot,
            strike=strike,
            time_to_expiry=T,
            risk_free_rate=r,
            dividend_yield=q,
        ),
        OptionType.CALL,
    )
    assert solved == pytest.approx(true_vol, abs=SOLVE_VOL_TOL, rel=SOLVE_VOL_TOL)


def test_max_volatility_prevents_required_solution() -> None:
    true_vol = 4.0
    spot, strike, T, r, q = 100.0, 100.0, 1.0, 0.05, 0.0
    pricing_inputs = BlackScholesInputs(
        spot=spot,
        strike=strike,
        time_to_expiry=T,
        risk_free_rate=r,
        volatility=true_vol,
        dividend_yield=q,
    )
    market_price = price_european(pricing_inputs, OptionType.CALL)
    with pytest.raises(ValueError):
        implied_volatility(
            ImpliedVolatilityInputs(
                market_price=market_price,
                spot=spot,
                strike=strike,
                time_to_expiry=T,
                risk_free_rate=r,
                dividend_yield=q,
            ),
            OptionType.CALL,
            max_volatility=2.0,
        )


def test_tiny_max_iterations_raises_runtime_error() -> None:
    spot, strike, T, r, q = 100.0, 100.0, 1.0, 0.05, 0.0
    pricing_inputs = BlackScholesInputs(
        spot=spot,
        strike=strike,
        time_to_expiry=T,
        risk_free_rate=r,
        volatility=0.20,
        dividend_yield=q,
    )
    market_price = price_european(pricing_inputs, OptionType.CALL)
    with pytest.raises(RuntimeError):
        implied_volatility(
            ImpliedVolatilityInputs(
                market_price=market_price,
                spot=spot,
                strike=strike,
                time_to_expiry=T,
                risk_free_rate=r,
                dividend_yield=q,
            ),
            OptionType.CALL,
            max_iterations=1,
        )


def test_repeated_calls_are_deterministic() -> None:
    inputs = ImpliedVolatilityInputs(
        market_price=12.0,
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        dividend_yield=0.0,
    )
    first = implied_volatility(inputs, OptionType.CALL)
    second = implied_volatility(inputs, OptionType.CALL)
    assert first == second


# --------------------------------------------------------------------------- #
# Put-call parity consistency and repricing residuals
# --------------------------------------------------------------------------- #


def test_put_call_parity_consistency() -> None:
    spot, strike, T, r, q, true_vol = 100.0, 100.0, 1.0, 0.05, 0.02, 0.30
    pricing_inputs = BlackScholesInputs(
        spot=spot,
        strike=strike,
        time_to_expiry=T,
        risk_free_rate=r,
        volatility=true_vol,
        dividend_yield=q,
    )
    call_price = price_european(pricing_inputs, OptionType.CALL)

    # Parity-consistent put price:
    #   P = C - S*exp(-qT) + K*exp(-rT)
    ds = _discounted_spot(spot, q, T)
    dk = _discounted_strike(strike, r, T)
    put_price = call_price - ds + dk

    call_iv = implied_volatility(
        ImpliedVolatilityInputs(
            market_price=call_price,
            spot=spot,
            strike=strike,
            time_to_expiry=T,
            risk_free_rate=r,
            dividend_yield=q,
        ),
        OptionType.CALL,
    )
    put_iv = implied_volatility(
        ImpliedVolatilityInputs(
            market_price=put_price,
            spot=spot,
            strike=strike,
            time_to_expiry=T,
            risk_free_rate=r,
            dividend_yield=q,
        ),
        OptionType.PUT,
    )
    assert call_iv == pytest.approx(put_iv, abs=1e-10, rel=1e-9)


def test_repricing_residual_call() -> None:
    spot, strike, T, r, q = 100.0, 100.0, 1.0, 0.05, 0.0
    market_price = NO_DIV_CALL
    solved = implied_volatility(
        ImpliedVolatilityInputs(
            market_price=market_price,
            spot=spot,
            strike=strike,
            time_to_expiry=T,
            risk_free_rate=r,
            dividend_yield=q,
        ),
        OptionType.CALL,
    )
    residual = abs(
        price_european(
            BlackScholesInputs(
                spot=spot,
                strike=strike,
                time_to_expiry=T,
                risk_free_rate=r,
                volatility=solved,
                dividend_yield=q,
            ),
            OptionType.CALL,
        )
        - market_price
    )
    assert residual <= 1e-8


def test_repricing_residual_put() -> None:
    spot, strike, T, r, q = 100.0, 100.0, 1.0, 0.05, 0.02
    market_price = DIV_PUT
    solved = implied_volatility(
        ImpliedVolatilityInputs(
            market_price=market_price,
            spot=spot,
            strike=strike,
            time_to_expiry=T,
            risk_free_rate=r,
            dividend_yield=q,
        ),
        OptionType.PUT,
    )
    residual = abs(
        price_european(
            BlackScholesInputs(
                spot=spot,
                strike=strike,
                time_to_expiry=T,
                risk_free_rate=r,
                volatility=solved,
                dividend_yield=q,
            ),
            OptionType.PUT,
        )
        - market_price
    )
    assert residual <= 1e-8
