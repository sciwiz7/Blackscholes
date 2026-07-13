# BlackScholesLab

A transparent and carefully tested Python toolkit for European option pricing,
analytical Greeks, implied-volatility calculation, and scenario analysis based
on the Black-Scholes framework.

> **Status: early development.** The European call and put pricing core is
> implemented in the current development version, but the project remains
> **unreleased** and is **not yet available from PyPI**. Greeks, implied
> volatility, and scenario analysis are not implemented. Do not rely on this
> project for calculations until a stable release is published.

## Purpose

BlackScholesLab is built for people who want to understand and verify
option-pricing mathematics rather than treat it as a black box. Every
calculation is intended to be transparent, deterministic, and reproducible.

## Implemented capabilities (development version)

The following are implemented in the current development version:

- European call and put option pricing under Black-Scholes-Merton.
- Continuous dividend-yield support.
- Explicit input validation.
- Deterministic, fully tested reference and invariant tests.

## Planned capabilities

The following capabilities are planned and will be added in later stages:

- Analytical Greeks (delta, gamma, vega, theta, rho)
- Implied-volatility calculation
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
non-dividend-paying underlying. See
[Mathematical conventions](docs/mathematical-conventions.md) for the formulas,
units, and validation rules.

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
