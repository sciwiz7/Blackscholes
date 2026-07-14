# Development

This guide explains how to set up a local development environment for
BlackScholesLab. The project is in early development; only the repository
foundation exists so far.

## Requirements

- Python 3.11 or newer
- `pip` (or an equivalent installer)
- Access to install development dependencies listed in `pyproject.toml`

## Create a virtual environment

A repository-local virtual environment named `.venv` is recommended and is
already ignored by Git.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows use `.venv\Scripts\activate`.

## Install the package with development dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

This installs the package in editable mode together with `pytest`,
`pytest-cov`, `ruff`, and `mypy`.

## Run the test suite with coverage

```bash
pytest
```

The configuration in `pyproject.toml` enables coverage reporting. A coverage
XML report (`coverage.xml`) is produced for CI.

## Lint and format

```bash
ruff check .
ruff format --check .
```

To apply formatting automatically:

```bash
ruff format .
```

## Type checking

```bash
mypy
```

The project uses `mypy` in strict mode. New code must pass type checking.

## Running the command-line interface

After installing with `python -m pip install -e ".[dev]"`, the `blackscholeslab`
console script is available on the path:

```bash
blackscholeslab --help
```

The CLI module can also be run directly from the source tree without installing,
using the repository-local `.venv` and `PYTHONPATH`:

```bash
PYTHONPATH=src .venv/bin/python -m blackscholeslab.cli --help
```

To verify the installed console entry point after building a wheel, install the
wheel into a clean virtual environment and run, for example:

```bash
blackscholeslab --help
blackscholeslab price --type call --spot 100 --strike 100 --time 1 --rate 0.05 --volatility 0.20
```

## Pre-commit

Optional local hooks are provided via `.pre-commit-config.yaml`:

```bash
pre-commit install
pre-commit run --all-files
```

## Building the package

```bash
python -m pip install build
python -m build
```

Artifacts are written to `dist/`, which is ignored by Git.

## Project layout

```
src/blackscholeslab/   # Package source (src-layout)
tests/                 # Test suite
docs/                  # Documentation
examples/              # Usage examples (planned)
.github/               # CI and templates
pyproject.toml         # Project metadata and tooling configuration
```

See [architecture.md](architecture.md) for the planned package structure and
[CONTRIBUTING.md](../CONTRIBUTING.md) for contribution expectations.
