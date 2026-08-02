# Roadmap

This roadmap describes the planned stages for BlackScholesLab. Stages are
marked as **Completed**, **In progress**, or **Planned** to distinguish actual
state from future intent.

## Stage 1 — Repository foundation

**Status: Completed**

- `src`-based package layout.
- Packaging with `pyproject.toml` and a standards-compliant build backend.
- Development tooling: Ruff, mypy, pytest, pytest-cov.
- CI workflow on Python 3.11 and 3.12.
- Documentation: architecture, mathematical conventions, development guide.
- Community documents: README, LICENSE, CONTRIBUTING, CODE_OF_CONDUCT,
  SECURITY, GOVERNANCE, and this roadmap.
- Foundation-level tests.

## Stage 2 — European call and put pricing

**Status: Completed**

- Option data models (`BlackScholesInputs`) and option-type definitions
  (`OptionType`).
- Input validation with explicit error handling.
- Analytical pricing for European call and put options (`price_european`).
- Continuous dividend-yield support.
- Behaviour at expiry and zero-volatility handling.
- Reference, parity, and invariant tests.

## Stage 3 — Analytical Greeks

**Status: Completed**

- OptionGreeks result model with delta, gamma, vega, theta, rho, dividend_rho.
- Delta, gamma, vega, annual theta, rho, dividend rho implementations.
- Call and put Greeks with identical gamma and vega, distinct delta, theta, rho, and dividend rho.
- Support for dividend-paying and zero-dividend options.
- Support for finite negative risk-free rates and dividend yields.
- Finite-difference verification against analytical results.
- Validation to reject zero time to expiry and zero volatility.
- Immutable OptionGreeks result type.
- Top-level public API exports.

## Stage 4 — Implied volatility

**Status: Completed**

- `ImpliedVolatilityInputs` immutable, typed market-input model.
- `implied_volatility` deterministic solver for European call and put options.
- European no-arbitrage lower- and upper-bound validation of the market price.
- Exact zero-volatility lower-bound handling and explicit upper-bound rejection.
- Adaptive volatility bracketing with a configurable maximum.
- Deterministic bisection with explicit price and volatility tolerances and a
  maximum iteration count.
- Reference, round-trip, boundary, bracketing, and put-call parity tests.

## Stage 5 — Payoff and scenario analysis

**Status: Completed**

- Intrinsic payoff evaluation (`intrinsic_payoff`) for European call and put
  options.
- Expiry profit and loss after an explicitly paid premium (`expiry_profit_loss`)
  with explicit long-option and no-multiplier semantics.
- Ordered single-option expiry payoff/P&L evaluation
  (`evaluate_expiry_scenarios`) that preserves input order and duplicate
  underlying prices and returns an immutable tuple.
- Immutable signed strategy leg models:
  - `OptionLeg` for long and short option positions.
  - `UnderlyingLeg` for long and short underlying positions.
- Immutable aggregate strategy result model (`PayoffPoint`) with
  `spot_at_expiry`, `gross_payoff`, and `net_profit`.
- Expiry-only multi-leg strategy payoff aggregation (`strategy_payoff`) using
  signed integer quantities.
- Ordered multi-spot strategy payoff profile evaluation
  (`evaluate_strategy_profile`) that preserves input order and duplicate expiry
  spot prices.
- Immutable pre-expiry scenario definitions (`OptionScenario`).
- Pre-expiry option repricing under scenario assumptions
  (`evaluate_price_scenarios`), reusing `price_european` as the single pricing
  oracle and keeping the strike fixed from the base case.
- Immutable result models (`ExpiryScenarioResult`, `ScenarioPriceResult`) and
  deterministic, fully tested reference and invariant tests.

The core scenario evaluation deliberately avoids pandas, NumPy batch arrays, and
plotting dependencies.

## Stage 6 — Command-line interface

**Status: Completed**

- A thin CLI exposing selected core functionality via the `blackscholeslab`
  console script and `python -m blackscholeslab.cli`.
- Seven subcommands: `price`, `greeks`, `implied-volatility`, `payoff`,
  `expiry-pnl`, `expiry-scenarios`, and `price-scenarios`.
- Standard-library-only implementation (`argparse`, `json`, `sys`); no new
  runtime dependencies.
- Human-readable text output and deterministic JSON output (`--json`) with
  `sort_keys=True` and `allow_nan=False`.
- Stable exit-code policy: `0` on success, `2` for expected `TypeError`/
  `ValueError` input errors, and `3` for `RuntimeError` from the implied
  volatility solver on non-convergence.
- Scenario-order and duplicate preservation; no reimplemented financial math.
- Strictly dependent on the core, never the reverse.

## Stage 7 — Interactive demonstration

**Status: Completed**

- An optional, dependency-isolated Streamlit demonstration (`demo/`) for
  education, depending only on the existing public core APIs.
- Five tabs: Price, Greeks, Implied volatility, Expiry payoff, and Scenario
  analysis, with shared keyed sidebar inputs and educational defaults.
- `demo/helpers.py` provides deterministic, typed, framework-independent
  preparation logic with no Streamlit imports and no duplicated financial
  formulas.
- Expected-error handling shows concise user-facing messages without raw
  tracebacks.
- Telemetry disabled in `.streamlit/config.toml`; no secrets or deployment
  credentials.
- No impact on the importable core: `dependencies = []` is preserved and
  Streamlit remains isolated in the `demo` optional extra.
- Headless application tests via `streamlit.testing.v1.AppTest`, plus direct
  tests of `demo/helpers` and core-delegation verification.

## Stage 8 — Documentation and tutorials

**Status: Completed**

- Documentation index `docs/index.md` with project purpose, development status,
  installation paths (core and demo), quick-start navigation, tutorial/reference
  links, architecture/development links, CLI and demo links, and the
  educational/non-advice warning.
- Public API reference `docs/api-reference.md` covering every symbol in
  `blackscholeslab.__all__`, verified against `__all__` by the documentation tests.
- Five worked tutorials under `docs/tutorials/`: pricing-and-greeks,
  implied-volatility, payoff-and-scenarios, command-line-interface, and
  interactive-demo.
- Three executable, deterministic examples under `examples/` validated for
  successful, deterministic execution by `tests/test_documentation.py`.
- `tests/test_documentation.py` validating local Markdown links, API-reference
  coverage of `__all__`, example execution and determinism, documented CLI command
  execution, absence of release/PyPI claims, absence of secrets and absolute
  local paths, and compilation of contractual Python snippets, using only the
  standard library.
- Expanded `docs/architecture.md` and `docs/development.md`, plus an updated
  `examples/README.md` and a concise `README.md` entry point linking to the
  documentation index and tutorials.

## Stage 9 — Release-readiness infrastructure

**Status: In progress (release candidate prepared)**

- Release documentation (`docs/releasing.md`) describing the full release
  process, version formats, TestPyPI rehearsal, production publication, and
  rollback guidance.
- Operational release checklist (`RELEASE_CHECKLIST.md`).
- Secure GitHub Actions release workflow (`.github/workflows/release.yml`)
  using OIDC Trusted Publishing.
- Version-consistency and artifact-validation tests (`tests/test_release.py`).
- Staged plan for the first public release.

### Planned path to first public release

- **Release-readiness preparation** — complete: documentation, checklist,
  workflow, and validation tests.
- **First public 0.1.0 candidate** — in progress: the candidate version is
  bumped from `0.1.0.dev0` to `0.1.0` on the `release/0.1.0-candidate` branch,
  pending an explicitly approved pull request into `main`.
- **TestPyPI rehearsal** — pending: publish to TestPyPI to validate Trusted
  Publishing, artifact integrity, and installation.
- **Explicit approval** — pending: human maintainer approval of the release
  candidate.
- **Production publication** — pending: publish `0.1.0` to production PyPI.
- **Compatibility history before 1.0.0** — pending: accumulate real-world usage,
  feedback, and compatibility evidence before considering a `1.0.0` release.

A `1.0.0` release would signal a stronger public API stability promise and
should only be considered after sufficient real-world compatibility history
and explicit maintainer agreement that the stability bar has been reached.

The project remains unreleased and is not available from PyPI.

## Notes

European call and put pricing is implemented in the development version but the
project remains unreleased and is not available from PyPI. Progress will be
tracked through issues and pull requests against the repository.
