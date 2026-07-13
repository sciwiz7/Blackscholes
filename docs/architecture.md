# Architecture

This document describes the **planned** architecture for BlackScholesLab. The
mathematical core and interfaces described below are not yet implemented. Stage 1
of the project establishes the repository, packaging, tooling, and documentation
only.

## Goals

BlackScholesLab is intended to be a transparent and carefully tested Python
toolkit for European option analytics based on the Black-Scholes framework. The
architecture is designed so that:

- The mathematical core is independent of any user interface.
- Public APIs remain small, explicit, and stable in behaviour.
- Numerical behaviour is verified by tests with documented tolerances.
- Optional dependencies for visualisation or interactivity are isolated.
- Invalid inputs are represented explicitly through errors, never silently
  coerced.

## Planned package structure

```
src/blackscholeslab/
    __init__.py          # Package metadata only (present in Stage 1)
    py.typed             # PEP 561 marker (present in Stage 1)
    models/              # Option data models (planned)
    core/                # Mathematical core (planned)
        types.py         # Option-type definitions (planned)
        validate.py      # Input validation (planned)
        pricing.py       # Black-Scholes pricing (planned)
        greeks.py        # Analytical Greeks (planned)
        implied_vol.py   # Implied-volatility solving (planned)
        numerics.py      # Numerical utilities (planned)
        payoff.py        # Payoff calculations (planned)
        scenario.py      # Scenario analysis (planned)
    cli.py               # Command-line interface (planned, optional)
    demo.py              # Optional interactive demonstration (planned)
```

The exact module layout may be refined during implementation. The structure
above expresses the intended separation of concerns.

## Planned modules

### Option data models (`models/`)
Plain, typed containers describing an option contract: spot price, strike,
time to expiry, risk-free rate, dividend yield, volatility, and option type.
Models are expected to be immutable and free of numerical logic.

### Option-type definitions (`core/types.py`)
Enumerations or explicit constants distinguishing European call and put
options. These definitions are consumed throughout the core.

### Input validation (`core/validate.py`)
Explicit validation of numeric inputs (positivity, finite values, domain
constraints). Invalid inputs raise typed exceptions rather than producing
numerically meaningless results.

### Black-Scholes pricing (`core/pricing.py`)
Analytical pricing formulas for European call and put options.

### Analytical Greeks (`core/greeks.py`)
First- and second-order sensitivities (for example delta, gamma, vega, theta,
rho). Units and signs will follow the conventions documented in
[mathematical-conventions.md](mathematical-conventions.md).

### Implied-volatility solving (`core/implied_vol.py`)
Root-finding against observed market prices using a deterministic, well-bounded
solver.

### Numerical utilities (`core/numerics.py`)
Shared helpers such as normal cumulative distribution evaluation, safe
comparison with tolerance, and convergence helpers.

### Payoff calculations (`core/payoff.py`)
Intrinsic payoff of call and put options at expiry and across a range of
underlying prices.

### Scenario analysis (`core/scenario.py`)
Batched evaluation of prices or Greeks across grids of inputs.

### Command-line interface (`cli.py`)
A thin, optional interface exposing selected core functionality. It must depend
on the core but never the reverse.

### Optional interactive demonstration (`demo.py`)
An optional, dependency-isolated demonstration for education. It must not be
imported by the core.

## Dependency direction

The dependency graph is strictly layered:

```
cli / demo  ->  core  ->  models / types / numerics
```

- Interfaces (CLI, demo) depend on the core.
- The core depends only on its own submodules, the option models, and numerical
  utilities.
- The mathematical core must **not** depend on the CLI or any web/visualisation
  layer.

### Why the core must not depend on the CLI or web layer

Keeping the core free of interface concerns guarantees that:

- Numerical correctness can be tested in isolation, without UI or I/O.
- The toolkit can be reused as a library in notebooks, services, or other
  applications without pulling in interface dependencies.
- Changes to presentation or transport layers cannot introduce regressions in
  the mathematics.

## Public API policy

The public surface will be deliberately small. High-level functions (for
example `price`, `greeks`, `implied_volatility`) will be exposed from the
package root or a small number of explicit modules. Internal helpers, solver
details, and numerical constants will remain private.

## Numerical testing strategy

Numerical behaviour will be verified by tests that:

- Compare against independently derived reference values or known closed-form
  limits.
- Use explicit relative and absolute tolerances documented alongside the test.
- Cover edge cases explicitly (for example behaviour at expiry, zero dividend
  yield, deep in/out of the money).
- Are deterministic and reproducible across runs and platforms.

## Optional dependency isolation

Visualisation and interactivity dependencies (for example plotting or notebook
libraries) will be optional and confined to demonstration code. The core will
not require them at import time or runtime.

## Error and invalid-input representation

Invalid inputs will be represented explicitly through raised exceptions with
clear messages, including which input failed validation. The library will not
return sentinel values or silently clamp inputs.

## Status

None of the modules above exist yet beyond the package metadata and `py.typed`
marker. See [ROADMAP.md](../ROADMAP.md) for the staged plan.
