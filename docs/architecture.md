# Architecture

This document describes the **actual** architecture of the BlackScholesLab
development version. The European pricing core is implemented. Planned modules
for Greeks, implied volatility, scenario analysis, CLI, and demonstration are
described as future connections and are not yet present.

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
    models.py         # OptionType enum and BlackScholesInputs model
    validation.py     # Reusable numeric and option-type validation
    numerical.py      # Internal numerical helpers (standard normal CDF)
    pricing.py        # European Black-Scholes-Merton pricing
    greeks.py         # Analytical Greeks and OptionGreeks result model
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

## Dependency direction

The dependency graph is strictly layered and acyclic:

```
cli / demo  ->  pricing / greeks  ->  models / validation / numerical
```

- Future interfaces (CLI, demo) will depend on the core (`pricing`, `greeks`,
  `models`, `validation`, `numerical`).
- The core depends only on its sibling modules and the standard library.
- The mathematical core must **not** depend on the CLI or any web/visualisation
  layer.

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
- `__version__`, `__author__`, `__license__` — package metadata.

Internal helpers (`validate_inputs`, `validate_real_number`, `norm_cdf`,
`_norm_pdf`, and similar) remain private and are not part of the public API. The
`greeks_european` function reuses `validate_option_type` from `validation` and
`norm_cdf` from `numerical`; the new `_norm_pdf` helper is private to
`greeks.py`.

## Future module connections

- **Implied volatility** (future): will reuse `models`, `validation`,
  `numerical`, and `price_european` as the pricing oracle for root-finding.
- **Scenario/payoff analysis** (future): will reuse `models` and `pricing`.
- **CLI** and **demonstration** (future, optional): will depend on the core but
  never the reverse, and will not be imported by the core.

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

The European pricing core (`models`, `validation`, `numerical`, `pricing`) and
the analytical Greeks (`greeks.py`) are implemented and tested. See
[ROADMAP.md](../ROADMAP.md) for the staged plan and the remaining planned
capabilities.
