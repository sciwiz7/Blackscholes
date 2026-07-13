# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Repository foundation: `src`-based package layout for `blackscholeslab`.
- Project metadata and packaging configuration in `pyproject.toml`.
- Development tooling: Ruff, mypy, pytest, and pytest-cov.
- Continuous integration workflow running on Python 3.11 and 3.12.
- Documentation: architecture, mathematical conventions, and development guide.
- Community documents: README, LICENSE (MIT), CONTRIBUTING, CODE_OF_CONDUCT,
  SECURITY, GOVERNANCE, and ROADMAP.
- Issue and pull-request templates.
- Foundation-level tests verifying package importability and version metadata.
- Immutable, typed pricing input model `BlackScholesInputs` (frozen dataclass).
- `OptionType` enumeration with `CALL` and `PUT` members.
- European call pricing via `price_european`.
- European put pricing via `price_european`.
- Continuous dividend-yield support in the Black-Scholes-Merton formulas.
- Expiry handling (intrinsic payoff) for `time_to_expiry == 0`.
- Zero-volatility handling (deterministic discounted payoff) for
  `volatility == 0` with positive time to expiry.
- Explicit input validation rejecting booleans, strings, `None`, complex
  values, non-finite numbers, and out-of-domain values.
- Reference tests against independently derived Black-Scholes-Merton values.
- Put-call parity and invariant tests.
- Analytical Greeks for European options:
  - OptionGreeks result model with delta, gamma, vega, theta, rho, dividend_rho.
  - Delta, gamma, vega, annual theta, rho, dividend rho implementations.
  - Call and put Greeks with identical gamma and vega, distinct delta, theta, rho, and dividend rho.
  - Support for dividend-paying and zero-dividend options.
  - Support for finite negative risk-free rates and dividend yields.
  - Finite-difference verification against analytical results.
  - Validation to reject zero time to expiry and zero volatility.
  - Immutable OptionGreeks result type.
  - Top-level public API exports.
- Implied-volatility solver for European options:
  - `ImpliedVolatilityInputs` immutable, typed market-input model.
  - `implied_volatility` deterministic solver for European call and put options.
  - European no-arbitrage lower- and upper-bound validation of the market price.
  - Exact zero-volatility lower-bound handling (returns exactly `0.0`).
  - Explicit upper-bound rejection (no finite implied volatility exists).
  - Adaptive volatility bracketing with a configurable maximum.
  - Deterministic bisection with explicit price and volatility tolerances and a
    maximum iteration count.
  - Support for continuous dividend yields, finite negative rates, and finite
    negative dividend yields.
  - Reuse of `price_european` as the single pricing oracle (no reimplemented
    formula).
  - Round-trip tests against independently derived reference values, a
    deterministic matrix across strikes, expiries, yields, and rates, boundary
    tests, bracketing and maximum-volatility tests, and put-call parity and
    repricing-consistency tests.
  - Configurable tolerances and iteration limits with clear error policies.
  - Payoff and scenario analysis for European options:
    - `intrinsic_payoff` — intrinsic expiry payoff for European call and put
      options (`max(S - K, 0)` for calls, `max(K - S, 0)` for puts).
    - `expiry_profit_loss` — long-option expiry profit and loss after an
      explicitly paid premium (`intrinsic_payoff - premium`).
    - `ExpiryScenarioResult` — immutable, typed expiry scenario result
      (underlying price, payoff, profit and loss).
    - `evaluate_expiry_scenarios` — ordered expiry payoff/P&L evaluation over
      supplied underlying prices, preserving order and duplicates.
    - `OptionScenario` — immutable, typed pre-expiry scenario definition (spot,
      time to expiry, volatility, risk-free rate, dividend yield, optional label).
    - `ScenarioPriceResult` — immutable, typed scenario price result (scenario,
      option price, absolute change, decimal percentage change).
    - `evaluate_price_scenarios` — pre-expiry repricing under scenario
      assumptions, reusing `price_european` as the single pricing oracle.
    - Immutable, ordered result tuples for both expiry and pre-expiry analysis.
    - Explicit premium semantics (long option, one unit, no discounting, no
      multiplier, no inferred short position).
    - Explicit `percentage_change` semantics (decimal return; `None` when the
      base price is exactly zero).
    - Reference and invariant tests covering payoff monotonicity, break-even
      behaviour, order/duplicate preservation, scenario monotonicity, base-price
      consistency, and zero-base-price percentage handling.

### Not yet implemented

The following planned capabilities are **not** part of this release and have
no implemented code:

- Command-line interface
- Interactive demonstration

## [0.1.0-dev0]

This is an internal development version identifier used during the foundation
stage. No stable release has been published.
