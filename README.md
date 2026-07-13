# BlackScholesLab

A transparent and carefully tested Python toolkit for European option pricing,
analytical Greeks, implied-volatility calculation, and scenario analysis based
on the Black-Scholes framework.

> **Status: early development.** The European call and put pricing core, the
> analytical Greeks, and implied-volatility solving are implemented in the
> current development version, but the project remains **unreleased** and is
> **not yet available from PyPI**. Scenario analysis is not implemented. Do not
> rely on this project for calculations until a stable release is published.

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

## Planned capabilities

The following capabilities are planned and will be added in later stages:

- Payoff analysis
- Scenario analysis
- Educational visualisations
- Command-line usage
- An optional interactive demonstration

These are not available yet.

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

The Greeks use raw decimal units, not percentage points:

- `vega` is the price change per a **1.0** absolute change in volatility, so the
  change per one volatility percentage point is `vega / 100`.
- `rho` is the price change per a **1.0** absolute change in the risk-free rate,
  so the change per one interest-rate percentage point is `rho / 100`.
- `dividend_rho` is the price change per a **1.0** absolute change in dividend
  yield, so the change per one yield percentage point is `dividend_rho / 100`.
- `theta` is the price change per **one year** of calendar time passing. The
  library does not silently divide by 100 or 365.

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
