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

## Install the package with development and demonstration dependencies

The interactive demonstration (`demo/`) is optional and depends on Streamlit,
which is isolated in the `demo` extra so the core runtime dependencies remain
empty:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev,demo]"
```

This installs the development dependencies above plus Streamlit for the
demonstration. The core package does not import Streamlit or the demonstration.

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

## Running the interactive demonstration

After installing the development and demonstration extras, launch the
demonstration from the repository root:

```bash
streamlit run demo/app.py
```

The demonstration is a browser-based educational view over the existing public
core APIs. It makes no network calls, uses no live market data, and stores no
user data. Telemetry (usage statistics) is disabled in `.streamlit/config.toml`.

## Running the demonstration tests

The demonstration has headless application tests built with
`streamlit.testing.v1.AppTest` plus direct tests of `demo/helpers.py`:

```bash
pytest tests/test_demo.py
```

These verify startup without uncaught exceptions, the presence of the title and
non-advice warning, visible pricing and Greeks results, the five tabs, the
shared base widgets and their defaults, expected domain-error handling, and that
the demonstration calls the existing public core APIs (verified by monkeypatching)
without duplicating the underlying mathematics.

## Verifying the app without deployment

The demonstration can be verified headlessly without a browser or deployment
using AppTest, as above, or by launching Streamlit in headless mode and
confirming it starts and serves the script. Headless operation is configured in
`.streamlit/config.toml` (`[server] headless = true`), so no command-line flag
is required:

```bash
streamlit run demo/app.py
```

Stop the server after confirming startup; do not leave a Streamlit process
running.

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

## Running the examples

The `examples/` directory holds self-contained, deterministic scripts that exercise
only the public core API. Each has a `main()` function and a `__main__` guard, so
it can be run directly or imported:

```bash
python examples/pricing_and_greeks.py
python examples/implied_volatility.py
python examples/payoff_and_scenarios.py
```

The scripts contain no network or file I/O and no randomness, and they produce
deterministic output. They are also executed by `tests/test_documentation.py`.

## Validating the documentation

The documentation is validated through the ordinary test suite. Run the full suite
(which includes `tests/test_documentation.py`):

```bash
pytest
```

`tests/test_documentation.py` checks, among other things, that every local
Markdown link resolves, that every public `__all__` symbol appears in
`docs/api-reference.md`, that each example runs successfully and deterministically,
that the documented CLI commands execute, that no release/PyPI claim appears, and
that no absolute local paths or secrets appear. Do not add a third-party Markdown
parser; the checks use only the standard library.

## Supported Python versions

BlackScholesLab supports **Python 3.11 and 3.12** (`requires-python = ">=3.11"`).
Continuous integration runs the lint, type-check, and test matrix on both
versions. The core dependencies remain empty; Streamlit is isolated in the optional
`demo` extra.

## Contribution workflow

- Create a feature branch from `main` (for example `feature/<topic>`).
- Make focused, tested changes; keep core behaviour deterministic and documented.
- Run `ruff format .`, `ruff check .`, `mypy`, and `pytest` before opening a pull
  request.
- Keep coverage at 100% for the core and the demo (`--cov-branch` is enabled).
- See [CONTRIBUTING.md](../CONTRIBUTING.md) for the full expectations and the
  issue/PR templates.

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
