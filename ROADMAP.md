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

**Status: Planned**

- Delta, gamma, vega, theta, and rho.
- Documented units, signs, and tolerances.
- Reference-tested values.

## Stage 4 — Implied volatility

**Status: Planned**

- Deterministic root-finding against observed prices.
- Bounded, well-tested solver behaviour.

## Stage 5 — Payoff and scenario analysis

**Status: Planned**

- Intrinsic payoff evaluation.
- Batched scenario evaluation across input grids.

## Stage 6 — Command-line interface

**Status: Planned**

- A thin CLI exposing selected core functionality.
- Strictly dependent on the core, never the reverse.

## Stage 7 — Interactive demonstration

**Status: Planned**

- An optional, dependency-isolated demonstration for education.
- No impact on the importable core.

## Stage 8 — Documentation and tutorials

**Status: Planned**

- Usage tutorials, worked examples, and reference documentation.
- Expanded mathematical references.

## Stage 9 — First stable release

**Status: Planned**

- Semantic versioning `1.0.0` once the core is complete, tested, and reviewed.
- Published on a package index with full documentation.

## Notes

European call and put pricing is implemented in the development version but the
project remains unreleased and is not available from PyPI. Progress will be
tracked through issues and pull requests against the repository.
