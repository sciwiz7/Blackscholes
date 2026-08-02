# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Expiry-only multi-leg strategy payoff analysis:
  - `OptionLeg` for signed option positions.
  - `UnderlyingLeg` for signed underlying positions.
  - `PayoffPoint` for aggregate strategy payoff and net profit results.
  - `strategy_payoff` for one expiry spot.
  - `evaluate_strategy_profile` for ordered caller-supplied expiry spot profiles.
  - Reference coverage for long/short options, bull call spreads, long straddles,
    covered calls, protective puts, validation, order preservation, and duplicate
    preservation.

## [0.1.0]

BlackScholesLab 0.1.0 is prepared as a release candidate. It is **not yet
published**; publication to PyPI remains pending explicit human maintainer
approval. The package has not been published to PyPI.

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
    - Command-line interface for selected core functionality:
      - `blackscholeslab` console script entry point
        (`blackscholeslab.cli:main`) registered in `pyproject.toml`.
      - Seven CLI subcommands: `price`, `greeks`, `implied-volatility`, `payoff`,
        `expiry-pnl`, `expiry-scenarios`, and `price-scenarios`.
      - Human-readable text output and deterministic JSON output (`--json`) using
        `json.dumps(..., sort_keys=True, allow_nan=False)`.
      - Stable exit-code policy: `0` on success, `2` for expected `TypeError`/
        `ValueError` input errors, and `3` for `RuntimeError` from the implied
        volatility solver on non-convergence.
      - Scenario-order and duplicate preservation in `expiry-scenarios` and
        `price-scenarios`.
      - No-runtime-dependency design; the CLI uses only the standard library
        (`argparse`, `json`, `sys`) plus the existing public core API.
      - CLI tests and clean-install command smoke tests (wheel and sdist).
    - Optional interactive Streamlit demonstration (`demo/`):
      - `demo/app.py` — a browser-based educational demonstration of European
        option analytics with no duplicated financial formulas, depending only
        on the existing public core APIs.
      - Five tabs: Price, Greeks, Implied volatility, Expiry payoff, and
        Scenario analysis.
      - Shared, keyed sidebar inputs for the base option assumptions with
        educational defaults (call, spot 100, strike 100, time 1.0, rate 0.05,
        volatility 0.20, dividend yield 0.02).
      - Price section using `price_european`, with stable human formatting that
        retains the raw value internally.
      - Greeks section using `greeks_european`, displaying the six Greeks with
        explicit raw-unit explanations.
      - Implied-volatility section using `implied_volatility` with public solver
        defaults, showing the annualised decimal result plus an explicitly
        labelled percent display, the repriced value, and the absolute
        repricing residual.
      - Expiry-payoff section using `evaluate_expiry_scenarios`, with a
        deterministic inclusive grid helper, an ordered table, a native line
        chart, maximum-loss and break-even explanations, and explicit long-option
        premium semantics.
      - Scenario-analysis section using `evaluate_price_scenarios`, with one to
        five keyed scenarios (Downside/Base/Upside presets plus neutral
        defaults), preserving order and duplicates, keeping the strike fixed, and
        rendering `undefined` for a zero-base percentage change.
      - `demo/helpers.py` — deterministic, typed, framework-independent
        preparation logic (inclusive grid, option-type mapping, formatting,
        break-even arithmetic, row construction, default scenario specs) with no
        Streamlit imports, no financial-formula duplication, and no network or
        file I/O.
      - `demo/__init__.py` — package marker; the demonstration is never exported
        from the core package.
      - Expected-error handling that shows concise user-facing messages without
        raw tracebacks for `TypeError`, `ValueError`, `RuntimeError` (implied
        volatility non-convergence), and `OverflowError` (extreme exponential
        calculations), without broadly swallowing programming bugs.
      - `tests/test_demo.py` — focused headless application tests using
        `streamlit.testing.v1.AppTest` plus direct tests of `demo/helpers`,
        including core-delegation verification that the demonstration calls the
        existing public APIs and contains no duplicated mathematics.
      - Telemetry configuration in `.streamlit/config.toml` disabling Streamlit
        usage statistics (`gatherUsageStats = false`) with no secrets or
        deployment credentials and no permissive cross-origin settings.
      - No impact on core runtime dependencies: `dependencies = []` is
        preserved and Streamlit remains isolated in the `demo` optional extra.
    - Documentation and tutorials (Stage 8):
      - Documentation index `docs/index.md` with project purpose, development
        status, installation paths, quick-start navigation, tutorial/reference
        links, architecture/development links, CLI and demo links, and the
        educational/non-advice warning.
      - Public API reference `docs/api-reference.md` covering every symbol in
        `blackscholeslab.__all__` (category, purpose, parameters/fields, return
        type, validation, exceptions, boundary behaviour, and a usage example),
        verified against `__all__` by the documentation tests.
      - Five worked tutorials under `docs/tutorials/`:
        - `pricing-and-greeks.md` — inputs, call/put pricing, dividends, expiry
          and zero-volatility boundaries, finite negative rates/yields, and all
          six Greeks with raw-unit explanations and deterministic expected
          results.
        - `implied-volatility.md` — market snapshot, solving, repricing residual,
          solver controls, no-arbitrage bounds, zero-volatility lower bound,
          upper-bound policy, non-convergence behaviour, and decimal/percent
          display.
        - `payoff-and-scenarios.md` — intrinsic payoff, long-option expiry P&L,
          ordered expiry grids, fixed-strike pre-expiry repricing, order/duplicate
          preservation, percentage-change `None` policy, and excluded market
          mechanics.
        - `command-line-interface.md` — all seven commands with purpose,
          invocation, important arguments, human/JSON modes, deterministic JSON
          semantics, decimal-unit policy, exit codes, stderr behaviour, scenario
          ordering, and negative-leading scenario syntax.
        - `interactive-demo.md` — installation, launch, five tabs, sidebar inputs,
          raw Greek units, implied-volatility controls, long-option premium
          semantics, scenario ordering, percentage-change policy, error
          presentation, telemetry-disabled/local-only limitation, and
          educational disclaimer.
      - Three executable, deterministic examples under `examples/`
        (`pricing_and_greeks.py`, `implied_volatility.py`, `payoff_and_scenarios.py`),
        each with a `main()` function, complete type annotations, a `__main__`
        guard, no network/file I/O, no randomness, and no duplicated financial
        formulas; validated for successful, deterministic execution.
      - `tests/test_documentation.py` validating local Markdown links, API-reference
        coverage of `__all__`, example execution and determinism, documented CLI
        command execution, absence of release/PyPI claims, absence of secrets and
        absolute local paths, and compilation of contractual Python snippets,
        using only the standard library.
      - Expanded `docs/architecture.md` (documentation/examples layer and
        dependency direction), `docs/development.md` (running examples,
        documentation validation, supported Python versions, contribution
        workflow), and an updated `examples/README.md`.
      - A concise `README.md` entry point linking to the documentation index and
        tutorials rather than duplicating them.

- Release documentation (`docs/releasing.md`) explaining version formats,
  clean-checkout release preparation, changelog finalization, version
  synchronization, release-candidate validation, artifact building and
  inspection, TestPyPI rehearsal, production publication, Git tag and GitHub
  release procedure, post-publication verification, failure/rollback/yank
  guidance, and educational limitation.
- Operational release checklist (`RELEASE_CHECKLIST.md`) with checkbox-based
  steps for pre-release preparation, release-candidate verification, explicit
  human approval, version bump, tag creation, artifact publication, GitHub
  release, post-release checks, and rollback/yank response.
- Secure GitHub Actions release workflow (`.github/workflows/release.yml`)
  using OIDC Trusted Publishing, build-once artifact validation, pinned action
  SHAs, protected environments, and separate TestPyPI/production publication
  paths.
- Version-consistency and artifact-validation tests (`tests/test_release.py`)
  verifying pyproject.toml, `__version__`, wheel metadata, sdist metadata,
  artifact contents, `py.typed`, forbidden-file exclusion, Streamlit
  non-dependency, and SHA-256 hash computation.
- Updated Stage 9 roadmap with a staged plan for the first public 0.1.0
  release: release-readiness preparation, candidate, TestPyPI rehearsal,
  explicit approval, production publication, and compatibility history before
  1.0.0.

### Not yet implemented

The following planned capabilities are **not** yet part of this release and
have no implemented code:

- Additional educational visualisations

## [0.1.0-dev0]

This is an internal development version identifier used during the foundation
stage. No stable release has been published.
