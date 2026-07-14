"""Example: European pricing and analytical Greeks.

This script exercises only the public BlackScholesLab API. It prices a European
call and put with continuous dividend yield, demonstrates the expiry and
zero-volatility boundaries, and computes all six analytical Greeks. The outputs
are deterministic and contain no network or file I/O and no randomness.

Run with:

    python examples/pricing_and_greeks.py

The module is import-safe; the worked computations run only under the
``__main__`` guard.
"""

from __future__ import annotations

from blackscholeslab import (
    BlackScholesInputs,
    OptionGreeks,
    OptionType,
    greeks_european,
    price_european,
)


def _print_greeks(label: str, greeks: OptionGreeks) -> None:
    """Print the six Greeks with their raw-unit meaning."""
    print(f"  {label} Greeks:")
    print(f"    delta        = {greeks.delta}")
    print(f"    gamma        = {greeks.gamma}")
    print(f"    vega         = {greeks.vega}   (per 1.0 absolute change in volatility)")
    print(f"    theta        = {greeks.theta}   (per one year of calendar time)")
    print(f"    rho          = {greeks.rho}   (per 1.0 absolute change in rate)")
    print(f"    dividend_rho = {greeks.dividend_rho}   (per 1.0 absolute change in yield)")


def main() -> int:
    """Run the pricing-and-Greeks worked example and print deterministic output."""
    # Base market assumptions for a dividend-paying underlying.
    inputs = BlackScholesInputs(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.20,
        dividend_yield=0.02,
    )

    call_price = price_european(inputs, OptionType.CALL)
    put_price = price_european(inputs, OptionType.PUT)
    print("European prices (spot=100, strike=100, T=1, r=0.05, sigma=0.20, q=0.02):")
    print(f"  call = {call_price}")
    print(f"  put  = {put_price}")

    # Expiry boundary: time_to_expiry == 0 collapses to the intrinsic payoff.
    at_expiry = BlackScholesInputs(
        spot=120.0,
        strike=100.0,
        time_to_expiry=0.0,
        risk_free_rate=0.05,
        volatility=0.20,
        dividend_yield=0.02,
    )
    print("At expiry (T=0, S=120, K=100):")
    print(f"  call = {price_european(at_expiry, OptionType.CALL)}  (max(S-K, 0))")
    print(f"  put  = {price_european(at_expiry, OptionType.PUT)}  (max(K-S, 0))")

    # Zero-volatility boundary: deterministic discounted payoff, no /0.
    zero_vol = BlackScholesInputs(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.0,
        dividend_yield=0.02,
    )
    print("Zero volatility (sigma=0, T=1, S=100, K=100):")
    print(f"  call = {price_european(zero_vol, OptionType.CALL)}")
    print(f"  put  = {price_european(zero_vol, OptionType.PUT)}")

    # Analytical Greeks for the base case (require T>0 and sigma>0).
    call_greeks = greeks_european(inputs, OptionType.CALL)
    put_greeks = greeks_european(inputs, OptionType.PUT)
    _print_greeks("Call", call_greeks)
    _print_greeks("Put", put_greeks)

    # Finite negative rate and dividend yield are allowed.
    negative_inputs = BlackScholesInputs(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=-0.02,
        volatility=0.20,
        dividend_yield=-0.01,
    )
    print("Finite negative rate (r=-0.02) and yield (q=-0.01):")
    print(f"  call price = {price_european(negative_inputs, OptionType.CALL)}")
    _print_greeks("Call", greeks_european(negative_inputs, OptionType.CALL))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
