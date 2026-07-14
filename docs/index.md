# BlackScholesLab documentation

## Purpose

BlackScholesLab is a transparent and carefully tested Python toolkit for European
option analytics based on the Black-Scholes framework. It covers European call
and put pricing, analytical Greeks, implied-volatility solving, expiry payoff and
profit/loss, and pre-expiry scenario repricing. Every calculation is deterministic
and reproducible, and the mathematics is documented and inspectable.

## Status: development version

The current version is **`0.1.0.dev0`**, a development version. The core
analytics, command-line interface, and interactive demonstration are implemented
and tested, but the project remains **unreleased** and is **not yet available from
PyPI**. Do not rely on it for calculations until a stable release is published, and
do not use it for trading or investment decisions without independent verification.

## Installation

There is no published release. Install from source.

- **Source / editable install** (core + development tools):

  ```bash
  python -m pip install -e ".[dev]"
  ```

- **With the interactive demo** (adds the isolated Streamlit `demo` extra; core
  dependencies stay empty):

  ```bash
  python -m pip install -e ".[dev,demo]"
  ```

A Python **3.11 or newer** environment is required (`requires-python = ">=3.11"`).

## Quick start

- **Python:** see the [pricing-and-Greeks tutorial](tutorials/pricing-and-greeks.md)
  and run `examples/pricing_and_greeks.py`.
- **Command line:** see the [CLI tutorial](tutorials/command-line-interface.md)
  and run `blackscholeslab --help`.
- **Interactive demo:** see the [interactive-demo tutorial](tutorials/interactive-demo.md)
  and run `streamlit run demo/app.py`.

## Tutorials

- [Pricing and Greeks](tutorials/pricing-and-greeks.md) — inputs, call/put
  pricing, dividends, expiry and zero-volatility boundaries, all six Greeks with
  raw-unit explanations.
- [Implied volatility](tutorials/implied-volatility.md) — building a market
  snapshot, solving, repricing, no-arbitrage bounds, and convergence policy.
- [Payoff and scenarios](tutorials/payoff-and-scenarios.md) — intrinsic payoff,
  expiry P&L, ordered expiry grids, and pre-expiry scenario repricing.
- [Command-line interface](tutorials/command-line-interface.md) — all seven
  commands, output modes, exit codes, and scenario syntax.
- [Interactive demonstration](tutorials/interactive-demo.md) — the optional
  Streamlit demo: tabs, sidebar inputs, and conventions.

## Reference

- [API reference](api-reference.md) — every public symbol exported from
  `blackscholeslab.__all__`.
- [Mathematical conventions](mathematical-conventions.md) — inputs, formulas,
  boundary behaviour, Greek units, and no-arbitrage policy.
- [Architecture](architecture.md) — package and module structure, dependency
  direction, and public-API policy.
- [Development](development.md) — environment setup, testing, linting, type
  checking, building, and documentation validation.
- [Contributing](../CONTRIBUTING.md) — contribution expectations.
- [Roadmap](../ROADMAP.md) — staged plan (Stage 8 = documentation and tutorials).

## Educational / non-advice warning

BlackScholesLab is **educational and analytical software**. It is **not** financial
advice and must not be used for trading or investment decisions without
independent verification. The authors accept no liability for any use of this
software.
