"""Tests for intrinsic payoff and expiry profit-and-loss analysis."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from blackscholeslab import (
    ExpiryScenarioResult,
    OptionLeg,
    OptionType,
    PayoffPoint,
    UnderlyingLeg,
    evaluate_expiry_scenarios,
    evaluate_strategy_profile,
    expiry_profit_loss,
    intrinsic_payoff,
    strategy_payoff,
)

ABS_TOL = 1e-10
REL_TOL = 1e-9


class _OneShotIterable:
    """Iterator that fails if iterated more than once."""

    def __init__(self, items: list[float]) -> None:
        self._items = items
        self._used = False

    def __iter__(self) -> Iterator[float]:
        if self._used:
            raise RuntimeError("underlying_prices iterable was iterated more than once")
        self._used = True
        return iter(self._items)


# --------------------------------------------------------------------------- #
# Reference payoff and P&L
# --------------------------------------------------------------------------- #


def test_call_reference_premium_7() -> None:
    strike = 100.0
    premium = 7.0
    cases = {
        80.0: (0.0, -7.0),
        100.0: (0.0, -7.0),
        107.0: (7.0, 0.0),
        120.0: (20.0, 13.0),
    }
    for underlying, (payoff, pnl) in cases.items():
        assert intrinsic_payoff(underlying, strike, OptionType.CALL) == pytest.approx(
            payoff, abs=ABS_TOL
        )
        assert expiry_profit_loss(underlying, strike, OptionType.CALL, premium) == pytest.approx(
            pnl, abs=ABS_TOL
        )


def test_put_reference_premium_6() -> None:
    strike = 100.0
    premium = 6.0
    cases = {
        80.0: (20.0, 14.0),
        94.0: (6.0, 0.0),
        100.0: (0.0, -6.0),
        120.0: (0.0, -6.0),
    }
    for underlying, (payoff, pnl) in cases.items():
        assert intrinsic_payoff(underlying, strike, OptionType.PUT) == pytest.approx(
            payoff, abs=ABS_TOL
        )
        assert expiry_profit_loss(underlying, strike, OptionType.PUT, premium) == pytest.approx(
            pnl, abs=ABS_TOL
        )


def test_call_break_even() -> None:
    strike = 100.0
    premium = 7.0
    # At strike + premium, call P&L is exactly zero.
    assert expiry_profit_loss(strike + premium, strike, OptionType.CALL, premium) == pytest.approx(
        0.0, abs=ABS_TOL
    )
    # Just below break-even, P&L is negative.
    assert expiry_profit_loss(strike + premium - 0.01, strike, OptionType.CALL, premium) < 0.0
    # Just above break-even, P&L is positive.
    assert expiry_profit_loss(strike + premium + 0.01, strike, OptionType.CALL, premium) > 0.0


def test_put_break_even() -> None:
    strike = 100.0
    premium = 6.0
    # At strike - premium, put P&L is exactly zero.
    assert expiry_profit_loss(strike - premium, strike, OptionType.PUT, premium) == pytest.approx(
        0.0, abs=ABS_TOL
    )
    # Below break-even (lower underlying), the put payoff exceeds premium, so P&L is positive.
    assert expiry_profit_loss(strike - premium - 0.01, strike, OptionType.PUT, premium) > 0.0
    # Above break-even (higher underlying), the put payoff is below premium, so P&L is negative.
    assert expiry_profit_loss(strike - premium + 0.01, strike, OptionType.PUT, premium) < 0.0


# --------------------------------------------------------------------------- #
# Payoff invariants
# --------------------------------------------------------------------------- #


def test_payoff_non_negative() -> None:
    strike = 100.0
    for underlying in [0.0, 50.0, 100.0, 150.0, 200.0]:
        assert intrinsic_payoff(underlying, strike, OptionType.CALL) >= 0.0
        assert intrinsic_payoff(underlying, strike, OptionType.PUT) >= 0.0


def test_call_payoff_non_decreasing() -> None:
    strike = 100.0
    prices = [0.0, 50.0, 99.0, 100.0, 101.0, 150.0, 200.0]
    values = [intrinsic_payoff(p, strike, OptionType.CALL) for p in prices]
    assert values == sorted(values)


def test_put_payoff_non_increasing() -> None:
    strike = 100.0
    prices = [0.0, 50.0, 99.0, 100.0, 101.0, 150.0, 200.0]
    values = [intrinsic_payoff(p, strike, OptionType.PUT) for p in prices]
    assert values == sorted(values, reverse=True)


def test_call_payoff_zero_at_and_below_strike() -> None:
    strike = 100.0
    for underlying in [0.0, 50.0, 99.999, 100.0]:
        assert intrinsic_payoff(underlying, strike, OptionType.CALL) == 0.0


def test_put_payoff_zero_at_and_above_strike() -> None:
    strike = 100.0
    for underlying in [100.0, 100.001, 150.0, 200.0]:
        assert intrinsic_payoff(underlying, strike, OptionType.PUT) == 0.0


def test_zero_premium_pnl_equals_payoff() -> None:
    strike = 100.0
    for underlying in [0.0, 80.0, 100.0, 120.0, 140.0]:
        assert expiry_profit_loss(underlying, strike, OptionType.CALL, 0.0) == pytest.approx(
            intrinsic_payoff(underlying, strike, OptionType.CALL), abs=ABS_TOL
        )
        assert expiry_profit_loss(underlying, strike, OptionType.PUT, 0.0) == pytest.approx(
            intrinsic_payoff(underlying, strike, OptionType.PUT), abs=ABS_TOL
        )


def test_long_pnl_minimum_is_negative_premium() -> None:
    strike = 100.0
    premium = 5.0
    for underlying in [0.0, 50.0, 100.0, 150.0, 200.0]:
        assert expiry_profit_loss(underlying, strike, OptionType.CALL, premium) >= -premium
        assert expiry_profit_loss(underlying, strike, OptionType.PUT, premium) >= -premium


# --------------------------------------------------------------------------- #
# Expiry scenario evaluation
# --------------------------------------------------------------------------- #


def test_expiry_evaluation_preserves_order() -> None:
    underlying = [80.0, 100.0, 107.0, 120.0]
    results = evaluate_expiry_scenarios(underlying, 100.0, OptionType.CALL, premium=7.0)
    assert [r.underlying_price for r in results] == underlying
    assert [r.payoff for r in results] == [0.0, 0.0, 7.0, 20.0]
    assert [r.profit_loss for r in results] == [-7.0, -7.0, 0.0, 13.0]


def test_expiry_evaluation_preserves_duplicates() -> None:
    underlying = [100.0, 100.0, 100.0]
    results = evaluate_expiry_scenarios(underlying, 100.0, OptionType.CALL, premium=7.0)
    assert len(results) == 3
    assert all(r.underlying_price == 100.0 for r in results)
    assert all(r.profit_loss == -7.0 for r in results)


def test_expiry_evaluation_returns_immutable_tuple() -> None:
    results = evaluate_expiry_scenarios([100.0], 100.0, OptionType.CALL, premium=7.0)
    assert isinstance(results, tuple)
    with pytest.raises(AttributeError):
        results.append(ExpiryScenarioResult(1.0, 0.0, 0.0))  # type: ignore[attr-defined]


def test_expiry_evaluation_default_premium_zero() -> None:
    results = evaluate_expiry_scenarios([120.0], 100.0, OptionType.CALL)
    assert results[0].payoff == 20.0
    assert results[0].profit_loss == 20.0


def test_expiry_evaluation_reuses_helpers() -> None:
    # Results must agree with the standalone payoff/P&L functions.
    underlying = [80.0, 100.0, 107.0, 120.0]
    results = evaluate_expiry_scenarios(underlying, 100.0, OptionType.CALL, premium=7.0)
    for price, result in zip(underlying, results, strict=True):
        assert result.payoff == intrinsic_payoff(price, 100.0, OptionType.CALL)
        assert result.profit_loss == expiry_profit_loss(price, 100.0, OptionType.CALL, 7.0)


# --------------------------------------------------------------------------- #
# Iterable behaviour
# --------------------------------------------------------------------------- #


def test_expiry_evaluation_with_tuple() -> None:
    results = evaluate_expiry_scenarios((80.0, 120.0), 100.0, OptionType.CALL, premium=7.0)
    assert [r.payoff for r in results] == [0.0, 20.0]


def test_expiry_evaluation_with_generator() -> None:
    def gen() -> Iterator[float]:
        yield from (80.0, 100.0, 120.0)

    results = evaluate_expiry_scenarios(gen(), 100.0, OptionType.CALL, premium=7.0)
    assert [r.payoff for r in results] == [0.0, 0.0, 20.0]


def test_expiry_evaluation_rejects_empty_list() -> None:
    with pytest.raises(ValueError, match="underlying_prices must not be empty"):
        evaluate_expiry_scenarios([], 100.0, OptionType.CALL, premium=7.0)


def test_expiry_evaluation_rejects_empty_tuple() -> None:
    with pytest.raises(ValueError, match="underlying_prices must not be empty"):
        evaluate_expiry_scenarios((), 100.0, OptionType.CALL, premium=7.0)


def test_expiry_evaluation_rejects_empty_generator() -> None:
    def gen() -> Iterator[float]:
        return
        yield  # pragma: no cover

    with pytest.raises(ValueError, match="underlying_prices must not be empty"):
        evaluate_expiry_scenarios(gen(), 100.0, OptionType.CALL, premium=7.0)


def test_expiry_evaluation_invalid_item_raises_with_index() -> None:
    with pytest.raises((TypeError, ValueError), match=r"underlying_prices\[2\]"):
        evaluate_expiry_scenarios([80.0, 100.0, float("nan"), 120.0], 100.0, OptionType.CALL)


def test_expiry_evaluation_one_shot_iterable() -> None:
    # A generator-like iterable must not be consumed twice (once for emptiness,
    # once for evaluation). The custom one-shot iterable raises if iterated again.
    iterable = _OneShotIterable([80.0, 100.0, 107.0, 120.0])
    results = evaluate_expiry_scenarios(iterable, 100.0, OptionType.CALL, premium=7.0)
    assert [r.payoff for r in results] == [0.0, 0.0, 7.0, 20.0]
    assert [r.profit_loss for r in results] == [-7.0, -7.0, 0.0, 13.0]


def test_expiry_evaluation_no_partial_results() -> None:
    # A failure after valid items must raise before returning any result.
    seen: list[float] = []

    def gen() -> Iterator[float]:
        for value in [80.0, 100.0, float("inf")]:
            seen.append(value)
            yield value

    with pytest.raises(ValueError):
        evaluate_expiry_scenarios(gen(), 100.0, OptionType.CALL)
    assert seen == [80.0, 100.0, float("inf")]


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "bad_underlying",
    [None, True, False, "100", 100 + 0j, float("nan"), float("inf"), float("-inf"), -1.0],
)
def test_intrinsic_payoff_invalid_underlying(bad_underlying: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        intrinsic_payoff(bad_underlying, 100.0, OptionType.CALL)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "bad_strike", [None, True, "100", 100 + 0j, float("nan"), float("inf"), 0.0, -1.0]
)
def test_intrinsic_payoff_invalid_strike(bad_strike: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        intrinsic_payoff(100.0, bad_strike, OptionType.CALL)  # type: ignore[arg-type]


def test_intrinsic_payoff_invalid_option_type() -> None:
    with pytest.raises(TypeError):
        intrinsic_payoff(100.0, 100.0, "call")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "bad_premium",
    [None, True, "7", 7 + 0j, float("nan"), float("inf"), -1.0],
)
def test_expiry_pnl_invalid_premium(bad_premium: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        expiry_profit_loss(100.0, 100.0, OptionType.CALL, bad_premium)  # type: ignore[arg-type]


def test_zero_underlying_price_allowed() -> None:
    assert intrinsic_payoff(0.0, 100.0, OptionType.CALL) == 0.0
    assert intrinsic_payoff(0.0, 100.0, OptionType.PUT) == 100.0


# --------------------------------------------------------------------------- #
# Multi-leg strategy payoff and net profit
# --------------------------------------------------------------------------- #


def test_long_call_strategy_payoff_reference() -> None:
    leg = OptionLeg(option_type=OptionType.CALL, strike=100.0, premium=7.0, quantity=1)

    point = strategy_payoff(120.0, (leg,))

    assert point == PayoffPoint(
        spot_at_expiry=120.0,
        gross_payoff=20.0,
        net_profit=13.0,
    )


def test_short_call_strategy_payoff_reference() -> None:
    leg = OptionLeg(option_type=OptionType.CALL, strike=100.0, premium=7.0, quantity=-1)

    point = strategy_payoff(120.0, (leg,))

    assert point.gross_payoff == pytest.approx(-20.0, abs=ABS_TOL)
    assert point.net_profit == pytest.approx(-13.0, abs=ABS_TOL)


def test_bull_call_spread_reference() -> None:
    legs = (
        OptionLeg(option_type=OptionType.CALL, strike=100.0, premium=6.0, quantity=1),
        OptionLeg(option_type=OptionType.CALL, strike=110.0, premium=2.0, quantity=-1),
    )

    point = strategy_payoff(120.0, legs)

    assert point.gross_payoff == pytest.approx(10.0, abs=ABS_TOL)
    assert point.net_profit == pytest.approx(6.0, abs=ABS_TOL)


def test_long_straddle_reference() -> None:
    legs = (
        OptionLeg(option_type=OptionType.CALL, strike=100.0, premium=4.0, quantity=1),
        OptionLeg(option_type=OptionType.PUT, strike=100.0, premium=3.0, quantity=1),
    )

    below = strategy_payoff(80.0, legs)
    at_strike = strategy_payoff(100.0, legs)
    above = strategy_payoff(120.0, legs)

    assert below.gross_payoff == pytest.approx(20.0, abs=ABS_TOL)
    assert below.net_profit == pytest.approx(13.0, abs=ABS_TOL)
    assert at_strike.gross_payoff == pytest.approx(0.0, abs=ABS_TOL)
    assert at_strike.net_profit == pytest.approx(-7.0, abs=ABS_TOL)
    assert above.gross_payoff == pytest.approx(20.0, abs=ABS_TOL)
    assert above.net_profit == pytest.approx(13.0, abs=ABS_TOL)


def test_covered_call_reference_with_underlying_leg() -> None:
    legs = (
        UnderlyingLeg(entry_price=100.0, quantity=1),
        OptionLeg(option_type=OptionType.CALL, strike=110.0, premium=4.0, quantity=-1),
    )

    point = strategy_payoff(120.0, legs)

    assert point.gross_payoff == pytest.approx(110.0, abs=ABS_TOL)
    assert point.net_profit == pytest.approx(14.0, abs=ABS_TOL)


def test_protective_put_reference_with_underlying_leg() -> None:
    legs = (
        UnderlyingLeg(entry_price=100.0, quantity=1),
        OptionLeg(option_type=OptionType.PUT, strike=95.0, premium=3.0, quantity=1),
    )

    point = strategy_payoff(80.0, legs)

    assert point.gross_payoff == pytest.approx(95.0, abs=ABS_TOL)
    assert point.net_profit == pytest.approx(-8.0, abs=ABS_TOL)


def test_strategy_profile_preserves_order_and_duplicates() -> None:
    legs = (OptionLeg(option_type=OptionType.CALL, strike=100.0, premium=5.0, quantity=1),)

    profile = evaluate_strategy_profile([90.0, 120.0, 90.0], legs)

    assert profile == (
        PayoffPoint(spot_at_expiry=90.0, gross_payoff=0.0, net_profit=-5.0),
        PayoffPoint(spot_at_expiry=120.0, gross_payoff=20.0, net_profit=15.0),
        PayoffPoint(spot_at_expiry=90.0, gross_payoff=0.0, net_profit=-5.0),
    )


def test_strategy_profile_returns_immutable_tuple() -> None:
    legs = (OptionLeg(option_type=OptionType.PUT, strike=100.0, premium=5.0, quantity=1),)

    profile = evaluate_strategy_profile((80.0, 100.0), legs)

    assert isinstance(profile, tuple)


def test_strategy_rejects_empty_legs() -> None:
    with pytest.raises(ValueError, match="legs must not be empty"):
        strategy_payoff(100.0, ())


def test_strategy_profile_rejects_empty_spots() -> None:
    legs = (OptionLeg(option_type=OptionType.CALL, strike=100.0, premium=5.0, quantity=1),)

    with pytest.raises(ValueError, match="spot_prices must not be empty"):
        evaluate_strategy_profile((), legs)


def test_option_leg_rejects_zero_quantity() -> None:
    with pytest.raises(ValueError, match="quantity must not be zero"):
        OptionLeg(option_type=OptionType.CALL, strike=100.0, premium=5.0, quantity=0)


@pytest.mark.parametrize("bad_quantity", [1.5, True, "1", None])
def test_option_leg_rejects_non_integer_quantity(bad_quantity: object) -> None:
    with pytest.raises(TypeError, match="quantity"):
        OptionLeg(
            option_type=OptionType.CALL,
            strike=100.0,
            premium=5.0,
            quantity=bad_quantity,  # type: ignore[arg-type]
        )


def test_underlying_leg_rejects_zero_quantity() -> None:
    with pytest.raises(ValueError, match="quantity must not be zero"):
        UnderlyingLeg(entry_price=100.0, quantity=0)


@pytest.mark.parametrize("bad_quantity", [1.5, True, "1", None])
def test_underlying_leg_rejects_non_integer_quantity(bad_quantity: object) -> None:
    with pytest.raises(TypeError, match="quantity"):
        UnderlyingLeg(entry_price=100.0, quantity=bad_quantity)  # type: ignore[arg-type]


def test_strategy_rejects_unknown_leg_type() -> None:
    with pytest.raises(TypeError, match="unsupported leg"):
        strategy_payoff(100.0, (object(),))  # type: ignore[arg-type]
