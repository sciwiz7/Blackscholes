"""Example: payoff and scenario analysis.

This script exercises only the public BlackScholesLab API. It demonstrates the
intrinsic expiry payoff, long-option expiry profit and loss after a premium,
ordered expiry scenario evaluation, and pre-expiry scenario repricing with a
fixed strike. It contains no network or file I/O and no randomness.

Run with:

    python examples/payoff_and_scenarios.py

The module is import-safe; the worked computations run only under the
``__main__`` guard.
"""

from __future__ import annotations

from blackscholeslab import (
    BlackScholesInputs,
    ExpiryScenarioResult,
    OptionScenario,
    OptionType,
    ScenarioPriceResult,
    evaluate_expiry_scenarios,
    evaluate_price_scenarios,
    expiry_profit_loss,
    intrinsic_payoff,
)


def _print_expiry(results: tuple[ExpiryScenarioResult, ...]) -> None:
    """Print ordered expiry scenario results."""
    for result in results:
        print(
            f"  S={result.underlying_price:>7}  payoff={result.payoff:>7}"
            f"  profit_loss={result.profit_loss:>7}"
        )


def _print_price_scenarios(results: tuple[ScenarioPriceResult, ...]) -> None:
    """Print ordered pre-expiry scenario results."""
    for index, result in enumerate(results):
        label = result.scenario.label if result.scenario.label is not None else "none"
        pct = "undefined" if result.percentage_change is None else result.percentage_change
        print(
            f"  Scenario {index} (label={label}): price={result.option_price}"
            f"  change={result.price_change}  pct_change={pct}"
        )


def main() -> int:
    """Run the payoff-and-scenarios worked example and print deterministic output."""
    # Intrinsic expiry payoff for a call with strike 100.
    call_payoff = intrinsic_payoff(
        underlying_price=120.0, strike=100.0, option_type=OptionType.CALL
    )
    print(f"Intrinsic payoff (call, S=120, K=100): {call_payoff}")

    # Long-option expiry profit and loss after a paid premium of 7.0.
    call_pnl = expiry_profit_loss(
        underlying_price=120.0,
        strike=100.0,
        option_type=OptionType.CALL,
        premium=7.0,
    )
    print(f"Expiry profit/loss (call, S=120, K=100, premium=7): {call_pnl}")

    # Ordered expiry payoff/P&L across underlying prices (order preserved).
    print("Ordered expiry scenarios (call, K=100, premium=7):")
    expiry = evaluate_expiry_scenarios(
        underlying_prices=[80.0, 100.0, 107.0, 120.0],
        strike=100.0,
        option_type=OptionType.CALL,
        premium=7.0,
    )
    _print_expiry(expiry)

    # Pre-expiry scenario repricing relative to a fixed-strike base case.
    base = BlackScholesInputs(
        spot=100.0,
        strike=100.0,
        time_to_expiry=1.0,
        risk_free_rate=0.05,
        volatility=0.20,
        dividend_yield=0.02,
    )
    scenarios = [
        OptionScenario(
            spot=110.0,
            time_to_expiry=1.0,
            volatility=0.20,
            risk_free_rate=0.05,
            dividend_yield=0.02,
            label="spot-up",
        ),
        OptionScenario(
            spot=90.0,
            time_to_expiry=0.5,
            volatility=0.30,
            risk_free_rate=0.08,
            dividend_yield=0.01,
            label="stress",
        ),
        OptionScenario(
            spot=100.0,
            time_to_expiry=1.0,
            volatility=0.20,
            risk_free_rate=0.05,
            dividend_yield=0.02,
            label="duplicate-base",
        ),
    ]
    print("Pre-expiry price scenarios (strike fixed at 100.0):")
    results = evaluate_price_scenarios(base, OptionType.CALL, scenarios)
    _print_price_scenarios(results)

    # Zero-base-price case: percentage change is None, never inf or 0.
    zero_base = BlackScholesInputs(
        spot=100.0,
        strike=200.0,
        time_to_expiry=0.0,
        risk_free_rate=0.05,
        volatility=0.20,
    )
    zero_results = evaluate_price_scenarios(
        zero_base,
        OptionType.CALL,
        [
            OptionScenario(
                spot=110.0,
                time_to_expiry=1.0,
                volatility=0.20,
                risk_free_rate=0.05,
                dividend_yield=0.02,
            )
        ],
    )
    print("Zero-base-price scenario (percentage_change must be None):")
    _print_price_scenarios(zero_results)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
