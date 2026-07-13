# Contributing to BlackScholesLab

Thank you for your interest in contributing. This document explains how to set
up a development environment and what is expected of contributions.

## Development setup

A Python 3.11+ environment is required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Branch naming

Use descriptive branch names with a short prefix:

- `feature/<short-description>` for new capabilities
- `fix/<short-description>` for bug fixes
- `docs/<short-description>` for documentation changes
- `chore/<short-description>` for tooling or maintenance

## Testing requirements

- All changes must include or update tests where applicable.
- Run `pytest` and ensure coverage does not regress without justification.
- Mathematical changes require tests with explicit reference values and
  documented tolerances.

## Formatting and linting

- Code must pass `ruff format --check .` and `ruff check .`.
- Run `ruff format .` to apply formatting before committing.

## Type checking

- Code must pass `mypy` in strict mode.

## Commit expectations

- Keep commits focused and descriptive.
- Do not commit generated environments (`.venv`), build output (`dist`,
  `build`), or caches.
- Do not commit secrets or confidential data.

## Pull-request expectations

- Open pull requests against `main`.
- Complete the pull-request checklist, including the quality commands above.
- Describe the motivation and the change clearly.
- Link related issues where relevant.

## Mathematical changes

Changes to calculations or numerical routines require:

- A reference (textbook, paper, or explicit derivation) cited in code comments
  and the pull request.
- Tests comparing results against independent reference values.
- Explicit tolerances for floating-point comparisons.
- Notes on edge cases and behaviour at expiry.

## Reporting numerical disagreements

If you believe a calculation is incorrect, please open an issue and include:

- The inputs used.
- The result you observed.
- The expected result and its source or reference.
- Your Python version and operating system.

Disagreements are resolved by reference to documented mathematical sources and
reproducible tests, not by assertion.

## Prohibited content

Do not commit credentials, tokens, private keys, personal filesystem paths,
or any confidential data. Review your diff before pushing.
