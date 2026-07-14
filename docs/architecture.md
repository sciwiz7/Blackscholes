# Architecture

This document describes the **actual** architecture of the BlackScholesLab
development version. The European pricing core, analytical Greeks, implied
volatility solver, payoff analysis, and pre-expiry scenario analysis are
implemented. A command-line interface (`cli.py`) is also implemented, and an
optional interactive Streamlit demonstration (`demo/`) is implemented with
strict isolation from the core.

## Goals

BlackScholesLab is a transparent and carefully tested Python toolkit for
European option analytics based on the Black-Scholes framework. The
architecture is designed so that:

- The mathematical core is independent of any user interface.
- Public APIs remain small, explicit, and stable in behaviour.
- Numerical behaviour is verified by tests with documented tolerances.
- Optional dependencies for visualisation or interactivity are isolated.
- Invalid inputs are represented explicitly through errors, never silently
  coerced.

## Package structure

```
src/blackscholeslab/
    __init__.py       # Package metadata and public exports
    py.typed          # PEP 561 marker
    cli.py            # Command-line interface (console script + python -m)
    models.py         # OptionType enum and BlackScholesInputs model
    validation.py     # Reusable numeric and option-type validation
    numerical.py      # Internal numerical helpers (standard normal CDF)
    pricing.py        # European Black-Scholes-Merton pricing
    greeks.py         # Analytical Greeks and OptionGreeks result model
    implied_volatility.py  # Implied-volatility solver and market-input model
    payoff.py         # Intrinsic payoff, expiry P&L, expiry scenario evaluation
    scenarios.py      # Pre-expiry scenario model and scenario repricing
```

The exact module layout may be refined during later stages, but the current
separation of concerns (model, validation, numerics, pricing, Greeks) is
intentional and is preserved as the core grows.

## Modules

### Option data model and option type (`models.py`)

`models.py` defines:

- `OptionType` — an `enum.Enum` with `CALL` and `PUT` members. Arbitrary
  strings or numbers are rejected by the pricing core.
- `BlackScholesInputs` — an immutable (`frozen`) typed dataclass holding `spot`,
  `strike`, `time_to_expiry`, `risk_free_rate`, `volatility`, and
  `dividend_yield` (defaulting to `0.0`). Construction validates every field.

`models.py` depends only on `validation.py`. It must not depend on `pricing.py`.

### Input validation (`validation.py`)

`validation.py` provides reusable validation:

- `validate_real_number(value, name, *, allow_negative, allow_zero)` — rejects
  booleans, strings, `None`, complex values, and non-finite numbers, and enforces
  per-field positivity/negativity rules.
- `validate_inputs(inputs)` — validates every field of a `BlackScholesInputs`
  instance.
- `validate_option_type(option_type)` — validates and returns an `OptionType`.

Type errors raise `TypeError`; invalid values raise `ValueError`. Validation is
reused both at model construction and wherever option types are accepted.

### Numerical helpers (`numerical.py`)

`numerical.py` holds internal, pure helpers such as `norm_cdf`, the standard
normal cumulative distribution function implemented with `math.erf`. These
helpers are intentionally private (not exported from the package root) so other
core modules can reuse them without exposing implementation details.

### Pricing (`pricing.py`)

`pricing.py` implements `price_european(inputs, option_type) -> float`, the
analytical Black-Scholes-Merton formula for European call and put options with
continuous dividend yield. It handles expiry and zero-volatility cases
explicitly. It depends on `models`, `validation`, and `numerical`, but on
nothing related to interfaces, CLI, or web layers.

### Greeks (`greeks.py`)

`greeks.py` implements `greeks_european(inputs, option_type) -> OptionGreeks`,
the analytical Black-Scholes-Merton Greeks (delta, gamma, vega, annual theta,
rho, dividend rho) for European call and put options with continuous dividend
yield. It defines the immutable `OptionGreeks` result model (a frozen
dataclass) and a private standard-normal PDF helper `_norm_pdf`. It reuses the
existing `BlackScholesInputs` model, `validate_option_type` validation, the
`norm_cdf` numerical helper, and the same `d1`/`d2` conventions as `pricing.py`.
Like `pricing.py`, it depends on `models`, `validation`, and `numerical`, but on
nothing related to interfaces, CLI, or web layers. It does **not** depend on
`pricing.py`; the Greeks are computed independently from the closed-form
formulas rather than by differentiating `price_european`.

### Implied volatility (`implied_volatility.py`)

`implied_volatility.py` implements `implied_volatility(inputs, option_type, ...) ->
float`, a transparent, deterministic solver for the annualised implied volatility
of European call and put options. It also defines the immutable
`ImpliedVolatilityInputs` market-input model (a frozen dataclass).

The solver:

- validates the observed `market_price` against the European no-arbitrage bounds
  (a zero-volatility lower bound and an upper bound approached only as volatility
  tends to infinity);
- returns exactly `0.0` when the market price equals the zero-volatility lower
  bound;
- raises `ValueError` when the market price is below the lower bound or at/above
  the upper bound;
- adaptively brackets the volatility, doubling the upper bound up to a configured
  maximum when the default bracket is insufficient;
- performs deterministic bisection with explicit price and volatility tolerances
  and a maximum iteration count, raising `RuntimeError` on non-convergence.

`implied_volatility.py` depends on `models`, `validation`, `numerical`, and
`pricing`. Crucially, it does **not** reimplement the Black-Scholes formula: it
constructs a `BlackScholesInputs` for each candidate volatility and calls
`price_european`. The pricing core remains the single source of truth. There is
no dependency from `pricing.py` (or `greeks.py`) back to the solver.

### Payoff (`payoff.py`)

`payoff.py` implements deterministic, explicitly validated payoff analysis for
European options. It provides `intrinsic_payoff`, `expiry_profit_loss`, the
immutable `ExpiryScenarioResult` result model, and `evaluate_expiry_scenarios`.

- `intrinsic_payoff(underlying_price, strike, option_type)` returns the
  non-negative intrinsic payoff at expiry (call: `max(S - K, 0)`; put:
  `max(K - S, 0)`).
- `expiry_profit_loss(underlying_price, strike, option_type, premium)` returns
  `intrinsic_payoff(...) - premium` for a long option purchased at the supplied
  premium. No discounting, contract multiplier, or position quantity is applied,
  and short positions are not inferred.
- `evaluate_expiry_scenarios(underlying_prices, strike, option_type, premium=0.0)`
  evaluates payoff and P&L over the supplied underlying prices, preserving order
  and duplicates and returning an immutable tuple of `ExpiryScenarioResult`.

`payoff.py` depends only on `models` and `validation`. It does **not** use
`price_european` because it describes intrinsic value and long-option P&L, not
priced option value. Invalid inputs raise `TypeError` or `ValueError` through the
shared `validate_real_number` and `validate_option_type` helpers, with malformed
items reported by zero-based index.

### Scenario analysis (`scenarios.py`)

`scenarios.py` implements pre-expiry scenario analysis for European options. It
defines the immutable `OptionScenario` scenario model (spot, time to expiry,
volatility, risk-free rate, dividend yield, optional label) and the immutable
`ScenarioPriceResult` result model (scenario, option price, absolute change,
decimal percentage change), plus `evaluate_price_scenarios`.

`evaluate_price_scenarios(base_inputs, option_type, scenarios)` computes the base
price once with `price_european`, then reprices each scenario by constructing a
`BlackScholesInputs` that reuses the base `strike` and the scenario's own fields.
The `percentage_change` is the decimal return `price_change / base_price`; when
the base price is exactly `0.0`, `percentage_change` is `None` rather than
`inf` or a substituted value.

`scenarios.py` depends on `models`, `validation`, and `pricing`. Crucially, it
does **not** reimplement the Black-Scholes formula: each scenario price is
produced by `price_european`. The pricing core remains the single source of
truth, and `pricing.py` does not depend on `scenarios.py`.

### Command-line interface (`cli.py`)

`cli.py` is a thin, deterministic command-line interface over the existing core
analytics. It is exposed as the `blackscholeslab` console script
(`blackscholeslab.cli:main` in `pyproject.toml`) and is also runnable with
`python -m blackscholeslab.cli`. It depends only on the standard library
(`argparse`, `json`, `sys`) and on the public core API; it never reimplements
pricing, Greek, implied-volatility, payoff, or scenario calculations.

The CLI provides seven subcommands:

- `price` — price a European option via `price_european`.
- `greeks` — compute analytical Greeks via `greeks_european`.
- `implied-volatility` — solve for implied volatility via `implied_volatility`.
- `payoff` — intrinsic expiry payoff via `intrinsic_payoff`.
- `expiry-pnl` — expiry profit and loss via `expiry_profit_loss`.
- `expiry-scenarios` — ordered expiry payoff/P&L via `evaluate_expiry_scenarios`.
- `price-scenarios` — pre-expiry repricing via `evaluate_price_scenarios`.

Design properties:

- **Command dispatch**: `build_parser` constructs an `argparse` parser with one
  subparser per command. Each subparser records its handler via
  `set_defaults(handler=...)`; `main` parses once and dispatches to the handler.
- **Option-type parsing**: only lowercase `call` and `put` are accepted through
  `argparse` `choices`; `main` maps them to `OptionType.CALL`/`OptionType.PUT`.
- **Output formatting**: without `--json`, each command prints stable
  human-readable text (floats via a `.12g` helper). With `--json`, each command
  emits exactly one JSON object via `json.dumps(payload, sort_keys=True,
  allow_nan=False)`. Human text goes to stdout; errors and usage go to stderr.
- **Exit-code policy**: `main` returns `0` on success; `TypeError`/`ValueError`
  are mapped to exit code `2` (expected input errors); `RuntimeError` from the
  implied-volatility solver on non-convergence is mapped to exit code `3`.
  `argparse` parsing failures preserve their standard exit code `2`.
- **No financial math**: the CLI translates arguments into the existing typed
  input models (`BlackScholesInputs`, `ImpliedVolatilityInputs`,
  `OptionScenario`) and invokes the existing public functions. There are no
  hidden defaults that differ from the Python API.
- **JSON contract**: every JSON object uses deterministic key ordering and
  contains only JSON-compatible values; `NaN`/`Infinity` are never emitted.

The CLI is intentionally not exported from `blackscholeslab.__init__`; importing
the core package must not import the CLI, and the core modules must never import
`cli`.

### Interactive demonstration (`demo/`)

`demo/` is an optional, dependency-isolated Streamlit demonstration for
education. It depends only on the public core API (`price_european`,
`greeks_european`, `implied_volatility`, `evaluate_expiry_scenarios`,
`evaluate_price_scenarios`, and the typed input/result models) and reuses those
functions as the single source of truth. It contains no duplicated pricing,
Greek, implied-volatility, intrinsic-payoff, or scenario-repricing formulas.

The demonstration is organised as:

- `demo/app.py` — the Streamlit application. It builds a shared
  `BlackScholesInputs` from keyed sidebar widgets, maps the displayed Call/Put
  value explicitly to `OptionType.CALL`/`OptionType.PUT`, and renders five tabs
  (Price, Greeks, Implied volatility, Expiry payoff, Scenario analysis). Each
  tab calls the corresponding public core function and renders the result with
  native Streamlit elements (`st.metric`, `st.table`, `st.line_chart`). Expected
  user/domain errors (`TypeError`, `ValueError`, `RuntimeError` from implied
  volatility non-convergence, and `OverflowError` from extreme standard-library
  exponentials) are caught and shown as concise `st.error` messages without raw
  tracebacks, while unexpected internal failures remain visible during
  development and testing.
- `demo/helpers.py` — deterministic, typed, framework-independent preparation
  logic. It contains no Streamlit imports, no financial-formula duplication, no
  network or file I/O, no hidden global state, and no mutable defaults. It
  provides `inclusive_grid` (an inclusive, index-interpolated underlying-price
  grid built only from the standard library), `option_type_from_label` (explicit
  Call/Put mapping), formatting helpers, `break_even_price` (explanatory
  long-option arithmetic only), row builders from immutable core results, and
  `default_scenario_specs` (deterministic scenario presets).
- `demo/__init__.py` — package marker. The demonstration is never exported from
  `blackscholeslab.__init__`.

`.streamlit/config.toml` disables Streamlit usage-statistics collection
(`gatherUsageStats = false`) and adds no secrets or deployment credentials and no
permissive cross-origin or security settings.

Design properties:

- **Optional dependency isolation**: Streamlit is confined to the `demo` optional
  extra in `pyproject.toml`; the core `dependencies` list remains empty. The
  core package imports neither Streamlit nor `demo`.
- **Demo-to-core dependency direction**: `demo` depends on the core, never the
  reverse. The core modules never import `demo` or Streamlit, and `demo` is not
  part of the importable core package.
- **No duplicated mathematics**: every price, Greek, implied volatility, payoff,
  and scenario value is produced by the existing public core functions; the
  demonstration performs no financial calculations of its own.
- **No persistence, network access, or live data**: the demonstration makes no
  network calls, uses no live market data, requires no account or authentication,
  and stores no user data; it provides no financial recommendations.
- **Headless testing with AppTest**: `tests/test_demo.py` uses
  `streamlit.testing.v1.AppTest` for focused headless application tests and also
  tests `demo/helpers.py` directly, including verification (by monkeypatching)
  that the demonstration calls the existing public APIs.

## Dependency direction

The dependency graph is strictly layered and acyclic:

```
cli / demo  ->  pricing / greeks / implied_volatility / payoff / scenarios  ->  models / validation / numerical
```

- Interfaces (`cli`, `demo`) depend on the core (`pricing`, `greeks`,
  `implied_volatility`, `payoff`, `scenarios`, `models`, `validation`,
  `numerical`).
- The core depends only on its sibling modules and the standard library.
- The mathematical core must **not** depend on the CLI, the demonstration, or any
  web/visualisation layer.

### Why the core must not depend on the CLI or web layer

Keeping the core free of interface concerns ensures that:

- Numerical correctness can be tested in isolation, without UI or I/O.
- The toolkit can be reused as a library in notebooks, services, or other
  applications without pulling in interface dependencies.
- Changes to presentation or transport layers cannot introduce regressions in
  the mathematics.

## Public API policy

The public surface is deliberately small. From the package root, only the
following are exported:

- `BlackScholesInputs` — immutable input model.
- `OptionType` — call/put enumeration.
- `price_european` — European pricing entry point.
- `OptionGreeks` — immutable Greek result model.
- `greeks_european` — analytical Greek entry point for European options.
- `ImpliedVolatilityInputs` — immutable market-input model for implied
  volatility.
- `implied_volatility` — deterministic implied-volatility solver for European
  options.
- `intrinsic_payoff` — intrinsic expiry payoff for European options.
- `expiry_profit_loss` — long-option expiry profit and loss after a paid premium.
- `ExpiryScenarioResult` — immutable expiry scenario result model.
- `evaluate_expiry_scenarios` — ordered expiry payoff/P&L evaluation.
- `OptionScenario` — immutable pre-expiry scenario definition.
- `ScenarioPriceResult` — immutable scenario price result model.
- `evaluate_price_scenarios` — pre-expiry scenario repricing.
- `__version__`, `__author__`, `__license__` — package metadata.

Internal helpers (`validate_inputs`, `validate_real_number`, `norm_cdf`,
`_norm_pdf`, `_price_at_volatility`, `_no_arbitrage_bounds`,
`_validate_solver_controls`, and similar) remain private and are not part of the
public API. The `greeks_european` function reuses `validate_option_type` from
`validation` and `norm_cdf` from `numerical`; the new `_norm_pdf` helper is
private to `greeks.py`. The solver reuses `price_european` from `pricing` as its
pricing oracle and reuses `validate_real_number` and `validate_option_type` from
`validation`. The scenario module reuses `price_european` from `pricing` as its
pricing oracle and reuses `validate_inputs`, `validate_real_number`, and
`validate_option_type` from `validation`; the `OptionScenario` model validates
its own fields on construction.

## Future module connections

- **Implied volatility** (implemented): reuses `models`, `validation`,
  `numerical`, and `price_european` as the pricing oracle for root-finding.
- **Payoff analysis** (implemented): reuses `models` and `validation`. It does
  not price options and does not depend on `pricing`.
- **Scenario analysis** (implemented): reuses `models`, `validation`, and
  `pricing`, using `price_european` as its pricing oracle.
- **CLI** (implemented): `cli.py` depends on the core (pricing, greeks,
  implied-volatility, payoff, scenarios, models, validation) and on the standard
  library, but never the reverse; the core does not import the CLI.
- **Demonstration** (implemented, optional): `demo/` depends on the core
  (pricing, greeks, implied-volatility, payoff, scenarios, models, validation)
  and on Streamlit as an optional extra, but never the reverse; the core does not
  import the demonstration or Streamlit. The demonstration is not exported from
  `blackscholeslab.__init__`.

## Numerical testing strategy

Numerical behaviour is verified by tests that:

- Compare against independently derived reference values or known closed-form
  limits (for example the established no-dividend case and a dividend-paying
  reference case).
- Use explicit relative and absolute tolerances documented alongside the test.
- Cover edge cases explicitly (for example behaviour at expiry, zero dividend
  yield, deep in/out of the money, zero volatility, and negative finite rates).
- Assert deterministic invariants such as put-call parity, non-negativity, and
  monotonicity in the underlying price.
- Are deterministic and reproducible across runs and platforms.

## Optional dependency isolation

Visualisation and interactivity dependencies (for example plotting or notebook
libraries) will be optional and confined to demonstration code. The core does
not require them at import time or runtime, and the project adds no runtime
dependencies.

## Error and invalid-input representation

Invalid inputs are represented explicitly through raised exceptions with clear
messages, naming the offending input. The library does not return sentinel
values or silently clamp inputs.

## Status

The European pricing core (`models`, `validation`, `numerical`, `pricing`), the
analytical Greeks (`greeks.py`), the implied-volatility solver
(`implied_volatility.py`), the payoff module (`payoff.py`), and the scenario
module (`scenarios.py`) are implemented and tested. See [ROADMAP.md](../ROADMAP.md)
for the staged plan and the remaining planned capabilities.
