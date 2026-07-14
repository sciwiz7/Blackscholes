# Tutorial: payoff and scenarios

This tutorial covers intrinsic payoff, expiry profit/loss, and pre-expiry
scenario repricing using only the public BlackScholesLab API. It assumes the
package is installed from source (see the [documentation index](../index.md)).

All snippets are runnable Python. You can also run `examples/payoff_and_scenarios.py`.

## Imports

```python
from blackscholeslab import (
    BlackScholesInputs,
    OptionScenario,
    OptionType,
    evaluate_expiry_scenarios,
    evaluate_price_scenarios,
    expiry_profit_loss,
    intrinsic_payoff,
)
```

## Intrinsic payoff

`intrinsic_payoff` is the amount received on exercise, ignoring any premium. It
is never negative.

```python
call_payoff = intrinsic_payoff(underlying_price=120.0, strike=100.0, option_type=OptionType.CALL)
print(call_payoff)  # 20.0  (max(S - K, 0))
```

- Call: `max(S - K, 0)`
- Put: `max(K - S, 0)`

`underlying_price` may be zero (a zero call payoff, a `K` put payoff). The
function does not use `rate`, `dividend_yield`, `volatility`, or `time`.

## Expiry profit and loss

`expiry_profit_loss` is `intrinsic_payoff(...) - premium` for a **long** option
bought at the supplied premium. No discounting, contract multiplier, or
position quantity is applied, and short positions are not inferred.

```python
call_pnl = expiry_profit_loss(
    underlying_price=120.0,
    strike=100.0,
    option_type=OptionType.CALL,
    premium=7.0,
)
print(call_pnl)  # 13.0  (payoff 20.0 minus premium 7.0)
```

The minimum profit and loss for a long option is `-premium`. For a call the
break-even underlying price is `strike + premium`; for a put it is
`strike - premium`.

## Ordered expiry grids

`evaluate_expiry_scenarios` evaluates payoff and P&L over supplied underlying
prices, returning an immutable tuple of `ExpiryScenarioResult` in the supplied
order. Order and duplicate prices are preserved exactly.

```python
expiry = evaluate_expiry_scenarios(
    underlying_prices=[80.0, 100.0, 107.0, 120.0],
    strike=100.0,
    option_type=OptionType.CALL,
    premium=7.0,
)
for result in expiry:
    print(result.underlying_price, result.payoff, result.profit_loss)
```

The deterministic output is:

```
80.0 0.0 -7.0
100.0 0.0 -7.0
107.0 7.0 0.0
120.0 20.0 13.0
```

An empty `underlying_prices` raises `ValueError`. Each `ExpiryScenarioResult`
carries `underlying_price`, `payoff`, and `profit_loss`.

## Pre-expiry scenario repricing

`evaluate_price_scenarios` reprices a European option under pre-expiry
scenario assumptions. The strike is taken from the base case and stays **fixed**
across scenarios; only spot, time to expiry, volatility, risk-free rate, and
dividend yield vary per scenario.

```python
base = BlackScholesInputs(
    spot=100.0,
    strike=100.0,
    time_to_expiry=1.0,
    risk_free_rate=0.05,
    volatility=0.20,
    dividend_yield=0.02,
)
scenarios = [
    OptionScenario(spot=110.0, time_to_expiry=1.0, volatility=0.20,
                   risk_free_rate=0.05, dividend_yield=0.02, label="spot-up"),
    OptionScenario(spot=90.0, time_to_expiry=0.5, volatility=0.30,
                   risk_free_rate=0.08, dividend_yield=0.01, label="stress"),
    OptionScenario(spot=100.0, time_to_expiry=1.0, volatility=0.20,
                   risk_free_rate=0.05, dividend_yield=0.02, label="duplicate-base"),
]
results = evaluate_price_scenarios(base, OptionType.CALL, scenarios)
for index, result in enumerate(results):
    pct = "undefined" if result.percentage_change is None else result.percentage_change
    print(index, result.scenario.label, result.option_price,
          result.price_change, pct)
```

The deterministic output is:

```
0 spot-up 15.96129501756 6.734289509406 0.7298456149673859
1 stress 5.001705323547 -4.225300184608 -0.45792756716938826
2 duplicate-base 9.227005508154 0.0 0.0
```

Each `ScenarioPriceResult` carries the `scenario`, the repriced `option_price`,
the absolute `price_change` (`option_price - base_price`), and the
`percentage_change` (`price_change / base_price` as a decimal return).

### Order and duplicate preservation

Both `evaluate_expiry_scenarios` and `evaluate_price_scenarios` preserve the
order and duplicates of the supplied inputs. In the example above, the
`duplicate-base` scenario is kept (not de-duplicated) and appears in position 2.

### Percentage change

`percentage_change` is a **decimal** return (for example `0.7298...` means
roughly a 73% increase). It is not multiplied by 100. When the base option price
is exactly `0.0`, `percentage_change` is `None` rather than `inf` or a silently
substituted value:

```python
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
    [OptionScenario(spot=110.0, time_to_expiry=1.0, volatility=0.20,
                    risk_free_rate=0.05, dividend_yield=0.02)],
)
print(zero_results[0].option_price, zero_results[0].percentage_change)  # 0.019019258879899525 None
```

### Expiry and zero-volatility scenarios

Because scenarios are repriced with `price_european`, all boundary behaviour is
inherited unchanged: at `time_to_expiry == 0` the price equals the intrinsic
payoff, and at `volatility == 0` (with positive time) the exact deterministic
discounted payoff is used. Finite negative rates and yields are allowed in
scenarios, exactly as in pricing.

## What is not modelled

These functions describe a single long option unit. They deliberately exclude:

- transaction costs, taxes, and fees;
- contract multipliers and position quantities;
- margin, assignment, and exercise mechanics;
- any short-position inference.

Nothing here is a trading recommendation.

## Running the included example

```bash
python examples/payoff_and_scenarios.py
```

## Where to go next

- [Pricing and Greeks tutorial](pricing-and-greeks.md)
- [Implied volatility tutorial](implied-volatility.md)
- [Mathematical conventions](../mathematical-conventions.md) (payoff and scenario sections)
- [API reference](../api-reference.md)

> **Educational only.** BlackScholesLab is not financial advice.
