# Tutorial: command-line interface

BlackScholesLab ships a command-line interface (`blackscholeslab`) that wraps the
public core API. The CLI is a thin, deterministic layer: it parses arguments,
builds the existing typed input models, calls the existing public functions, and
formats output. It never reimplements pricing, Greek, implied-volatility,
payoff, or scenario calculations.

> Run `blackscholeslab --help` for the top-level help, and
> `blackscholeslab <command> --help` for any subcommand.

## Common conventions

- **Decimal rates and volatility.** Every `--rate`, `--dividend-yield`,
  `--volatility`, and implied-volatility bracket value is an **annualised
  decimal** (for example `0.05` is 5%, `0.20` is 20%). The CLI does not accept
  percentage strings and does not scale inputs. This matches the Python API
  exactly.
- **Time in calendar years.** `--time` is `time_to_expiry` in years. There is no
  trading-day conversion.
- **Output modes.** Without `--json` each command prints stable human-readable
  text to **stdout**. With `--json` it prints exactly one JSON object to
  **stdout** with deterministic key ordering (`sort_keys=True`) and without
  `NaN`/`Infinity` (`allow_nan=False`). Errors and usage messages always go to
  **stderr**.
- **Exit codes.**
  - `0` — success.
  - `2` — expected input error (`TypeError`/`ValueError`), including `argparse`
    failures, an invalid option type, or a domain error (for example a market
    price outside the no-arbitrage bounds, or zero time/volatility for the
    Greeks).
  - `3` — the implied-volatility solver failed to converge within the configured
    iteration limit (`RuntimeError`). Only the `implied-volatility` command maps
    to `3`; an unexpected `RuntimeError` from another command propagates.

## `price`

Price a European call or put.

```bash
blackscholeslab price \
  --type call \
  --spot 100 --strike 100 --time 1 --rate 0.05 --volatility 0.20 --dividend-yield 0.02
```

Important arguments: `--type` (`call`/`put`, required), `--spot`, `--strike`,
`--time`, `--rate`, `--volatility`, `--dividend-yield` (default `0.0`),
`--json`. Human output:

```
Option type: call
Price: 9.22700550815
```

JSON output (`--json`):

```json
{"command": "price", "option_type": "call", "price": 9.227005508154036}
```

## `greeks`

Compute the six analytical Greeks. Requires positive `--time` and positive
`--volatility`; otherwise the command exits `2`.

```bash
blackscholeslab greeks \
  --type call \
  --spot 100 --strike 100 --time 1 --rate 0.05 --volatility 0.20 --dividend-yield 0.02
```

Human output prints delta, gamma, vega, theta, rho, and dividend rho. The Greek
values use **raw units** (vega per a `1.0` absolute change in volatility, rho
and dividend rho per a `1.0` absolute change in rate/yield, theta per one year);
they are **not** divided by 100 or 365. JSON output:

```json
{"command": "greeks", "option_type": "call", "delta": 0.586851146134764, "gamma": 0.018950578755008718, "vega": 37.901157510017434, "theta": -5.0893189139983335, "rho": 49.45810910532236, "dividend_rho": -58.685114613476394}
```

## `implied-volatility`

Recover the annualised implied volatility from an observed market price.

```bash
blackscholeslab implied-volatility \
  --type call \
  --market-price 9.227005508154036 \
  --spot 100 --strike 100 --time 1 --rate 0.05 --dividend-yield 0.02
```

Additional controls (all optional): `--price-tolerance` (default `1e-10`),
`--volatility-tolerance` (default `1e-12`), `--max-iterations` (default `200`),
`--initial-upper-volatility` (default `0.5`), `--max-volatility` (default `10.0`).
The result is the annualised decimal volatility; multiply by `100` only for
display. A market price below the no-arbitrage lower bound or at/above the upper
bound exits `2`; non-convergence within `--max-iterations` exits `3`.

JSON output:

```json
{"command": "implied-volatility", "option_type": "call", "implied_volatility": 0.2000000000007276}
```

## `payoff`

Intrinsic expiry payoff of a European option.

```bash
blackscholeslab payoff --type call --underlying-price 120 --strike 100
```

Arguments: `--type`, `--underlying-price`, `--strike`, `--json`. Output:

```
Option type: call
Payoff: 20
```

## `expiry-pnl`

Expiry profit and loss for a long option after the paid premium.

```bash
blackscholeslab expiry-pnl --type call --underlying-price 120 --strike 100 --premium 7
```

Arguments: `--type`, `--underlying-price`, `--strike`, `--premium`, `--json`.
Output `Payoff: 20` style; for the example above `Profit/loss: 13` (20 − 7).

## `expiry-scenarios`

Evaluate intrinsic payoff and P&L across one or more underlying prices at expiry.
Order and duplicates of the supplied prices are preserved exactly.

```bash
blackscholeslab expiry-scenarios \
  --type call --strike 100 --premium 7 \
  --underlying-prices 80 100 107 120
```

Human output is a table:

```
Underlying price | Payoff | Profit/loss
80 | 0 | -7
100 | 0 | -7
107 | 7 | 0
120 | 20 | 13
```

Arguments: `--type`, `--strike`, `--premium` (default `0.0`),
`--underlying-prices` (one or more, required), `--json`. Each row preserves the
supplied order.

## `price-scenarios`

Reprice a European option under one or more pre-expiry scenarios. The strike is
fixed from the base `--spot/--strike/--time/--rate/--volatility/--dividend-yield`
inputs; each `--scenario` varies spot, time, volatility, rate, and yield.

```bash
blackscholeslab price-scenarios \
  --type call \
  --spot 100 --strike 100 --time 1 --rate 0.05 --volatility 0.20 --dividend-yield 0.02 \
  --scenario "110,1,0.20,0.05,0.02,spot-up" \
  --scenario "90,0.5,0.30,0.03,0.01,stress"
```

Each `--scenario` is five or six comma-separated fields:

```
spot,time_to_expiry,volatility,risk_free_rate,dividend_yield[,label]
```

Order and duplicate scenarios are preserved. The `percentage_change` is a
**decimal** return (`price_change / base_price`); it is printed as `undefined`
in human mode and `null` in JSON when the base price is exactly `0.0`.

### Negative-leading scenario values

`--scenario` is a single string argument. If the **first** field is negative,
argparse would interpret the leading `-` as a flag, so use the `=` form:

```bash
blackscholeslab price-scenarios \
  --type call --spot 100 --strike 100 --time 1 --rate 0.05 --volatility 0.20 \
  --scenario="-90,1,0.20,0.05,0.02,spot-down"
```

Negative values in the **middle** fields (for example a negative rate) are
passed literally inside the string and need no special syntax:

```bash
blackscholeslab price-scenarios \
  --type call --spot 100 --strike 100 --time 1 --rate 0.05 --volatility 0.20 \
  --scenario "110,1,0.20,-0.02,0.02,neg-rate"
```

## Determinism and validation

The JSON contract is deterministic: keys are sorted, values are the raw Python
`float` results from the core (no rounding in the calculation), and no
`NaN`/`Infinity` is emitted. The same arguments always produce the same output.
Every command above is exercised by `tests/test_cli.py`, and the documentation
tests (`tests/test_documentation.py`) re-run them to keep this tutorial honest.

> **Educational only.** BlackScholesLab is not financial advice.
