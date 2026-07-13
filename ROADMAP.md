# Roadmap

This roadmap describes the planned stages for BlackScholesLab. Stages are
marked as **Completed**, **In progress**, or **Planned** to distinguish actual
state from future intent. The project does not yet implement any mathematical
functionality.

## Stage 1 — Repository foundation

**Status: In progress**

- `src`-based package layout.
- Packaging with `pyproject.toml` and a standards-compliant build backend.
- Development tooling: Ruff, mypy, pytest, pytest-cov.
- CI workflow on Python 3.11 and 3.12.
- Documentation: architecture, mathematical conventions, development guide.
- Community documents: README, LICENSE, CONTRIBUTING, CODE_OF_CONDUCT,
  SECURITY, GOVERNANCE, and this roadmap.
- Foundation-level tests.

## Stage 2 — European call and put pricing

**Status: Planned**

- Option data models and option-type definitions.
- Input validation.
- Analytical pricing for European call and put options.
- Behaviour at expiry and edge-case verification.

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

No mathematical feature listed above is implemented yet. Progress will be
tracked through issues and pull requests against the repository.
