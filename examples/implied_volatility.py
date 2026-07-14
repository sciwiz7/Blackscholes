"""Example: implied-volatility solving.

This script exercises only the public BlackScholesLab API. It constructs a
theoretical market price with ``price_european``, builds an
``ImpliedVolatilityInputs`` snapshot, solves for the implied volatility, and
reprices with the solved value to show the absolute residual. It uses the
public solver as the single source of truth and never reimplements bisection.

Run with:

    python examples/implied_volatility.py

The module is import-safe; the worked computations run only under the
``__main__`` guard.
"""

from __future__ import annotations

from blackscholeslab import (
    BlackScholesInputs,
    ImpliedVolatilityInputs,
    OptionType,
    implied_volatility,
    price_european,
)


def main() -> int:
    """Run the implied-volatility worked example and print deterministic output."""
    # Base market assumptions (the same ones used in the pricing tutorial).
    inputs = BlackScholesInputs(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.20,
        dividend_yield=0.02,
    )

    # The "observed" market price is a theoretical price at sigma = 0.20.
    market_price = price_european(inputs, OptionType.CALL)
    print(f"Theoretical market price at sigma=0.20: {market_price}")

    iv_inputs = ImpliedVolatilityInputs(
        market_price=market_price,
        spot=inputs.spot,
        strike=inputs.strike,
        time_to_expiry=inputs.time_to_expiry,
        risk_free_rate=inputs.risk_free_rate,
        dividend_yield=inputs.dividend_yield,
    )

    # Solve for the implied volatility (annualised decimal, e.g. 0.20 == 20%).
    solved = implied_volatility(iv_inputs, OptionType.CALL)
    print(f"Solved implied volatility (decimal): {solved}")
    print(f"Solved implied volatility (percent): {solved * 100.0}")

    # Reprice with the solved volatility and show the absolute residual.
    repriced = price_european(
        BlackScholesInputs(
            spot=inputs.spot,
            strike=inputs.strike,
            time_to_expiry=inputs.time_to_expiry,
            risk_free_rate=inputs.risk_free_rate,
            volatility=solved,
            dividend_yield=inputs.dividend_yield,
        ),
        OptionType.CALL,
    )
    residual = abs(repriced - market_price)
    print(f"Repriced option value: {repriced}")
    print(f"Absolute repricing residual: {residual}")

    # Zero-volatility lower bound: the solver returns exactly 0.0.
    zero_vol_inputs = BlackScholesInputs(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.0,
        dividend_yield=0.02,
    )
    lower_bound_price = price_european(zero_vol_inputs, OptionType.CALL)
    lower_bound_iv = implied_volatility(
        ImpliedVolatilityInputs(
            market_price=lower_bound_price,
            spot=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            dividend_yield=0.02,
        ),
        OptionType.CALL,
    )
    print(f"Lower-bound price: {lower_bound_price} -> implied volatility: {lower_bound_iv}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
