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

### Not yet implemented

The following planned capabilities are **not** part of this release and have
no implemented code:

- Implied-volatility calculation
- Payoff and scenario analysis
- Command-line interface
- Interactive demonstration

## [0.1.0-dev0]

This is an internal development version identifier used during the foundation
stage. No stable release has been published.
