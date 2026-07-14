# BlackScholesLab

A transparent and carefully tested Python toolkit for European option pricing,
analytical Greeks, implied-volatility calculation, and scenario analysis based
on the Black-Scholes framework.

> **Status: early development.** The European call and put pricing core, the
> analytical Greeks, implied-volatility solving, payoff and scenario analysis,
> a command-line interface, and an optional interactive Streamlit demonstration
> are implemented in the current development version, but the project remains
> **unreleased** and is **not yet available from PyPI**. Do not rely on this
> project for calculations until a stable release is published.

## Purpose

BlackScholesLab is built for people who want to understand and verify
option-pricing mathematics rather than treat it as a black box. Every
calculation is intended to be transparent, deterministic, and reproducible.

## Implemented capabilities (development version)

The following are implemented in the current development version:

- European call and put option pricing under Black-Scholes-Merton.
- Continuous dividend-yield support.
- Analytical Greeks for European options: delta, gamma, vega, annual theta,
  rho, and dividend rho.
- Implied-volatility solving for European call and put options with continuous
  dividend yield, finite negative rates, and finite negative dividend yields.
- Explicit input validation.
- Deterministic, fully tested reference and invariant tests.
- Payoff and scenario analysis for European options:
  - Intrinsic expiry payoff (`intrinsic_payoff`).
  - Expiry profit and loss after a paid premium (`expiry_profit_loss`).
  - Ordered expiry payoff/P&L evaluation (`evaluate_expiry_scenarios`).
  - Immutable pre-expiry scenario definitions (`OptionScenario`).
  - Pre-expiry option repricing under scenario assumptions
    (`evaluate_price_scenarios`).
- A command-line interface (`blackscholeslab`) exposing pricing, Greeks,
  implied volatility, payoff, expiry profit/loss, and scenario analysis with
  human-readable and deterministic JSON output. The CLI is implemented in the
  development version but is not yet published on a package index.
- An optional interactive Streamlit demonstration (`demo/`) for exploring
  European option prices, analytical Greeks, implied volatility, expiry payoff,
  and pre-expiry scenarios in the browser. The demonstration depends only on the
  public core APIs and is implemented in the development version but is not yet
  published on a package index.

## Planned capabilities

The following capabilities are planned and will be added in later stages:

- Additional educational visualisations

## Interactive demonstration

The interactive demonstration is implemented in the development version and is
**not** available from PyPI. It is an educational, browser-based view over the
existing public BlackScholesLab APIs; it performs no financial mathematics of
its own and makes no network calls, uses no live market data, requires no
account or authentication, and stores no user data.

Install the development and demonstration extras:

```bash
python -m pip install -e ".[dev,demo]"
```

Launch the demonstration:

```bash
streamlit run demo/app.py
```

The demonstration presents five sections:

1. **Price** — European call and put prices from `price_european`.
2. **Greeks** — analytical Greeks (delta, gamma, vega, annual theta, rho,
   dividend rho) from `greeks_european`.
3. **Implied volatility** — implied volatility solving from `implied_volatility`.
4. **Expiry payoff** — intrinsic payoff and long-option profit/loss from
   `evaluate_expiry_scenarios`.
5. **Scenario analysis** — pre-expiry scenario repricing from
   `evaluate_price_scenarios`, with the strike fixed from the base option.

### Conventions used by the demonstration

- **Annualised decimal rates and volatility** — every rate and volatility input
  is an annualised decimal (for example `0.05` is a 5% rate and `0.20` is 20%
  volatility). The demonstration does not accept percentage strings and does not
  scale inputs.
- **Long-option premium policy** — the expiry payoff section treats the premium
  as the amount paid for one option unit; no contract multiplier or position
  quantity is assumed, no discounting is applied, and short positions are not
  inferred.
- **Raw Greek units** — the Greeks use raw decimal units, not percentage
  points: vega is the price change for an absolute `1.0` change in volatility,
  rho and dividend rho are for an absolute `1.0` change in rate or yield, and
  theta is per one year of calendar time. Values are not divided by 100 or 365.
- **Zero-base percentage policy** — scenario percentage change is a decimal
  return (`price_change / base_price`); when the base option price is exactly
  zero, the demonstration shows `undefined` rather than substituting zero or
  infinity.

The demonstration is optional and isolated: Streamlit is only an extra
dependency for the demo, the core runtime dependencies remain empty, and the
core package never imports the demonstration or Streamlit.

## Intended users

- Finance students
- Quantitative-finance learners
- Researchers
- Traders who want transparent calculations
- Python developers building analytical or educational tools

## Design principles

- **Transparent calculations** — formulas and assumptions are documented and
  inspectable.
- **Deterministic behaviour** — the same inputs always produce the same
  outputs.
- **Explicit assumptions** — model inputs and conventions are stated clearly.
- **Numerical correctness** — results are verified against references with
  documented tolerances.
- **Reproducibility** — calculations are independent of hidden state.
- **Educational clarity** — code and documentation prioritise understanding.

## Installation

**Installation is not available yet from PyPI.** There is no published release.
The European pricing core is available only in the development version of the
source repository and should be installed from source for evaluation and
testing. It is not yet published on a package index.

Once the first release is published, installation will be documented here.

## Local development setup

A Python 3.11+ environment is required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Minimal working example

```python
from blackscholeslab import (
    BlackScholesInputs,
    OptionType,
    price_european,
)

inputs = BlackScholesInputs(
    spot=42.0,
    strike=40.0,
    time_to_expiry=0.5,
    risk_free_rate=0.10,
    volatility=0.20,
)

call_price = price_european(inputs, OptionType.CALL)
put_price = price_european(inputs, OptionType.PUT)
```

This computes the Black-Scholes-Merton European call and put prices for a
non-dividend-paying underlying.

Greeks example:

```python
from blackscholeslab import (
    BlackScholesInputs,
    OptionType,
    greeks_european,
)

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
```

This computes the analytical Greeks for call and put options using the
Black-Scholes-Merton model with continuous dividend yield. See
[Mathematical conventions](docs/mathematical-conventions.md) for the formulas,
units, and validation rules.

Implied-volatility example:

```python
from blackscholeslab import (
    ImpliedVolatilityInputs,
    OptionType,
    implied_volatility,
)

inputs = ImpliedVolatilityInputs(
    market_price=10.450583572185565,
    spot=100.0,
    strike=100.0,
    time_to_expiry=1.0,
    risk_free_rate=0.05,
    dividend_yield=0.0,
)

vol = implied_volatility(inputs, OptionType.CALL)
# vol is the annualised decimal implied volatility (here approximately 0.20).
```

The observed `market_price` must satisfy the European no-arbitrage bounds
documented in [Mathematical conventions](docs/mathematical-conventions.md): it
must be at least the zero-volatility lower bound and strictly below the
upper bound approached only as volatility tends to infinity. The solver returns
annualised decimal volatility (for example `0.20` for 20%). See
[Mathematical conventions](docs/mathematical-conventions.md) for the formulas,
units, and validation rules.

Payoff and scenario analysis example:

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

# Intrinsic expiry payoff for a call with strike 100.
call_payoff = intrinsic_payoff(underlying_price=120.0, strike=100.0, option_type=OptionType.CALL)
# call_payoff is 20.0

# Expiry profit and loss for a long call bought at a premium of 7.0.
call_pnl = expiry_profit_loss(
    underlying_price=120.0,
    strike=100.0,
    option_type=OptionType.CALL,
    premium=7.0,
)
# call_pnl is 13.0 (payoff 20.0 minus premium 7.0)

# Ordered expiry payoff/P&L evaluation across several underlying prices.
expiry = evaluate_expiry_scenarios(
    underlying_prices=[80.0, 100.0, 107.0, 120.0],
    strike=100.0,
    option_type=OptionType.CALL,
    premium=7.0,
)
# expiry preserves order and duplicates; each result carries underlying_price,
# payoff, and profit_loss.

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
    OptionScenario(spot=110.0, time_to_expiry=1.0, volatility=0.20, risk_free_rate=0.05),
    OptionScenario(spot=90.0, time_to_expiry=0.5, volatility=0.30, risk_free_rate=0.08),
]
results = evaluate_price_scenarios(base, OptionType.CALL, scenarios)
# The strike remains fixed at the base value (100.0); only scenario fields vary.
# Each result carries scenario, option_price, price_change, and percentage_change.
```

The payoff API represents a **long** option purchased for the supplied premium.
The premium is the amount paid for one option unit; no contract multiplier or
position quantity is assumed, no discounting is applied inside `expiry_profit_loss`,
and short positions are not inferred. `percentage_change` returned by
`evaluate_price_scenarios` is a **decimal** return (for example `0.1` means a 10%
increase); multiply by 100 if you need percentage points. When the base option
price is exactly `0.0`, `percentage_change` is `None` rather than `inf` or a
silently substituted value.

The Greeks use raw decimal units, not percentage points:

- `vega` is the price change per a **1.0** absolute change in volatility, so the
  change per one volatility percentage point is `vega / 100`.
- `rho` is the price change per a **1.0** absolute change in the risk-free rate,
  so the change per one interest-rate percentage point is `rho / 100`.
- `dividend_rho` is the price change per a **1.0** absolute change in dividend
  yield, so the change per one yield percentage point is `dividend_rho / 100`.
- `theta` is the price change per **one year** of calendar time passing. The
  library does not silently divide by 100 or 365.

## Command-line interface

A command-line interface named `blackscholeslab` is implemented in the
development version. It is **not** available from PyPI; install the development
source as described in [Local development setup](#local-development-setup) to use
it. The CLI is a thin layer over the core: it parses arguments, builds the
existing typed input models, calls the existing public functions, and formats
output. It never reimplements pricing, Greek, implied-volatility, payoff, or
scenario calculations.

Run the top-level help to see all subcommands:

```bash
blackscholeslab --help
```

Each subcommand also supports `--help`, for example:

```bash
blackscholeslab price --help
```

### Decimal rates and volatility

All rate and volatility inputs are **annualised decimals**, not percentages:

- `0.05` means a 5% continuously compounded risk-free rate.
- `0.20` means 20% annualised volatility.
- `0.02` means a 2% continuous dividend yield.

The CLI does not interpret percentage strings and does not scale inputs.

### JSON output

Every calculation command accepts a `--json` flag. Without `--json`, the command
prints stable human-readable text to stdout. With `--json`, it prints exactly one
JSON object to stdout with deterministic key ordering (`sort_keys=True`) and
without `NaN` or `Infinity` (`allow_nan=False`). Errors and usage messages are
always written to stderr, never stdout.

### Exit codes

- `0` — success.
- `2` — expected input error (`TypeError`/`ValueError`), including missing or
  malformed arguments detected by `argparse`, an invalid option type, or a
  domain error from the core (for example a market price outside the
  no-arbitrage bounds, or zero time/volatility for the Greeks).
- `3` — the implied-volatility solver failed to converge within the configured
  iteration limit (`RuntimeError`).

### Examples

Price a European call:

```bash
blackscholeslab price \
  --type call \
  --spot 100 --strike 100 --time 1 --rate 0.05 --volatility 0.20 --dividend-yield 0.02
```

Compute the Greeks:

```bash
blackscholeslab greeks \
  --type call \
  --spot 100 --strike 100 --time 1 --rate 0.05 --volatility 0.30 --dividend-yield 0.02
```

Recover implied volatility from a market price (JSON):

```bash
blackscholeslab implied-volatility \
  --type call \
  --market-price 10.450583572185565 \
  --spot 100 --strike 100 --time 1 --rate 0.05 --dividend-yield 0
```

Intrinsic expiry payoff:

```bash
blackscholeslab payoff --type call --underlying-price 120 --strike 100
```

Expiry profit and loss for a long option after the paid premium:

```bash
blackscholeslab expiry-pnl --type call --underlying-price 120 --strike 100 --premium 7
```

Expiry scenarios (human-readable table):

```bash
blackscholeslab expiry-scenarios \
  --type call --strike 100 --premium 7 \
  --underlying-prices 80 100 107 120
```

Pre-expiry price scenarios (repeatable `--scenario` encoded as
`spot,time,volatility,rate,dividend_yield[,label]`):

```bash
blackscholeslab price-scenarios \
  --type call \
  --spot 100 --strike 100 --time 1 --rate 0.05 --volatility 0.20 --dividend-yield 0.02 \
  --scenario "110,1,0.20,0.05,0.02,spot-up" \
  --scenario "90,0.5,0.30,0.03,0.01,stress"
```

The `price-scenarios` `percentage_change` is a **decimal** return (for example
`0.1` means a 10% increase); it is not multiplied by 100. When the base option
price is exactly `0.0`, `percentage_change` is reported as `undefined` in the
human view and `null` in JSON. Scenario order and duplicates are preserved, and
the strike is always taken from the base case.

## Quality commands

Run these from the repository root after installing development dependencies:

| Task | Command |
| ---- | ------- |
| Tests with coverage | `pytest` |
| Lint | `ruff check .` |
| Format check | `ruff format --check .` |
| Type check | `mypy` |
| Build | `python -m build` |

## Links

- [Roadmap](ROADMAP.md)
- [Contributing](CONTRIBUTING.md)
- [Architecture](docs/architecture.md)
- [Mathematical conventions](docs/mathematical-conventions.md)

## Licence

BlackScholesLab is released under the [MIT Licence](LICENSE).

## Disclaimer

BlackScholesLab is educational and analytical software. It is **not** financial
advice and must not be used for trading or investment decisions without
independent verification. The authors accept no liability for any use of this
software.
