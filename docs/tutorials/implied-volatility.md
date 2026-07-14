# Tutorial: implied volatility

This tutorial shows how to recover the implied volatility of a European option
using only the public BlackScholesLab API. It assumes the package is installed
from source (see the [documentation index](../index.md)).

All snippets are runnable Python. You can also run the included example
`examples/implied_volatility.py`.

## Imports

```python
from blackscholeslab import (
    BlackScholesInputs,
    ImpliedVolatilityInputs,
    OptionType,
    implied_volatility,
    price_european,
)
```

## Build a base case and a "market" price

Start from ordinary pricing inputs. To keep the example self-contained, we use
`price_european` to manufacture a theoretical market price at a known volatility
(`0.20`). In practice you would substitute a real quoted price.

```python
inputs = BlackScholesInputs(
    spot=100.0,
    strike=100.0,
    time_to_expiry=1.0,
    risk_free_rate=0.05,
    volatility=0.20,
    dividend_yield=0.02,
)

market_price = price_european(inputs, OptionType.CALL)
print(market_price)
```

This prints the theoretical price, for example `9.227005508154`.

## Construct the solver inputs and solve

`ImpliedVolatilityInputs` holds the observed `market_price` plus the market
snapshot (spot, strike, time, rate, dividend yield). Time to expiry must be
strictly positive — implied volatility is undefined at expiry.

```python
iv_inputs = ImpliedVolatilityInputs(
    market_price=market_price,
    spot=inputs.spot,
    strike=inputs.strike,
    time_to_expiry=inputs.time_to_expiry,
    risk_free_rate=inputs.risk_free_rate,
    dividend_yield=inputs.dividend_yield,
)

solved = implied_volatility(iv_inputs, OptionType.CALL)
print(solved)          # 0.2000000000007276 (annualised decimal)
print(solved * 100.0)  # 20.00000000007276 (percent display only)
```

The solver returns the **annualised decimal** volatility. `0.20` means 20%.
Multiply by `100.0` yourself only for display; do **not** pass the percentage
back into the pricing API.

## Reprice and check the residual

Because the solver reuses `price_european` as its single source of truth, the
solved volatility should reproduce the market price. The absolute difference
(residual) is typically on the order of `1e-11`:

```python
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
print(repriced, residual)
```

This prints a repriced value equal to the market price up to the solver
tolerance, with an absolute residual near `2.7576163574849488e-11`.

## Solver controls

`implied_volatility` accepts optional keyword controls:

| Control | Default | Meaning |
| ------- | ------- | ------- |
| `price_tolerance` | `1e-10` | Absolute price tolerance; bisection stops when `|price(mid) - market_price| <= price_tolerance`. |
| `volatility_tolerance` | `1e-12` | Absolute volatility-interval tolerance; bisection also stops when `upper - lower <= volatility_tolerance`, returning the midpoint. |
| `max_iterations` | `200` | Maximum bisection iterations (strictly positive integer). |
| `initial_upper_volatility` | `0.5` | Initial upper volatility bracket (strictly positive, and `<= max_volatility`). |
| `max_volatility` | `10.0` | Maximum volatility before bracketing stops (strictly positive). |

If `initial_upper_volatility` is too small to bracket the target price, the
solver doubles the upper bound repeatedly (never exceeding `max_volatility`)
until the price is bracketed. If the price at `max_volatility` is still below
the market price, a `ValueError` is raised rather than silently returning
`max_volatility`.

## No-arbitrage bounds

The solver validates `market_price` against the European no-arbitrage bounds
before solving:

- **Lower bound** — the exact zero-volatility deterministic price. If
  `market_price` equals the lower bound, the solver returns exactly `0.0`.
- **Below the lower bound** — `ValueError` is raised. A below-lower-bound price
  is never reinterpreted as zero volatility.
- **At or above the upper bound** — `ValueError` is raised, because no finite
  implied volatility produces that price. The upper bound is approached only as
  volatility tends to infinity, so equality has no finite solution.

```python
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
print(lower_bound_price, lower_bound_iv)  # 2.896924880604 0.0
```

## Non-convergence behaviour

If the solver cannot satisfy the tolerances within `max_iterations`, it raises
`RuntimeError`. You can trigger this (for testing) by setting a very low
iteration limit; in normal use the defaults converge quickly.

```python
from blackscholeslab import implied_volatility

# With max_iterations=1 the bisection cannot converge and raises RuntimeError.
try:
    implied_volatility(iv_inputs, OptionType.CALL, max_iterations=1)
except RuntimeError as exc:
    print("non-convergence:", exc)
```

## Decimal volatility versus percent display

The solver output is a decimal (`0.20`). The percent value (`20.0`) is only a
display convenience. The CLI and the interactive demo make this distinction
explicit; the value passed back into `price_european` must remain the raw
decimal.

## Running the included example

```bash
python examples/implied_volatility.py
```

## Where to go next

- [Pricing and Greeks tutorial](pricing-and-greeks.md)
- [Payoff and scenarios tutorial](payoff-and-scenarios.md)
- [Mathematical conventions](../mathematical-conventions.md) (implied-volatility section)
- [API reference](../api-reference.md)

> **Educational only.** BlackScholesLab is not financial advice.
