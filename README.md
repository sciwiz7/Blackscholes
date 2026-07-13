# BlackScholesLab

A transparent and carefully tested Python toolkit for European option pricing,
analytical Greeks, implied-volatility calculation, and scenario analysis based
on the Black-Scholes framework.

> **Status: early development.** This project is in its foundation stage. The
> mathematical core (pricing, Greeks, implied volatility, scenario analysis)
> has **not** been implemented yet. The repository currently contains project
> structure, packaging, tooling, and documentation only. Do not rely on this
> project for calculations until a stable release is published.

## Purpose

BlackScholesLab is built for people who want to understand and verify
option-pricing mathematics rather than treat it as a black box. Every
calculation is intended to be transparent, deterministic, and reproducible.

## Planned capabilities

The following capabilities are planned and will be added in later stages:

- European call and put option pricing
- Analytical Greeks (delta, gamma, vega, theta, rho)
- Implied-volatility calculation
- Payoff analysis
- Scenario analysis
- Educational visualisations
- Command-line usage
- An optional interactive demonstration

None of these are available yet.

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

**Installation is not available yet.** There is no published release. The
package cannot be installed from PyPI, and no stable API exists.

Once the first release is published, installation will be documented here.

## Local development setup

A Python 3.11+ environment is required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

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
