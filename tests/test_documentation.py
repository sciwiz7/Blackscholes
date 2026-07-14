"""Documentation, tutorial, example, and CLAIM validation for BlackScholesLab.

These tests use only the Python standard library. They verify that:

- every local Markdown link in the repository documentation resolves;
- the API reference documents every public symbol in ``blackscholeslab.__all__``;
- the worked examples run successfully and produce deterministic output;
- the documented CLI commands execute and return expected, accurate results;
- the project is explicitly described as unreleased and is never claimed to be on
  PyPI / published;
- no secrets, no absolute local paths, and no duplicated financial formulas appear
  in the examples;
- every Python snippet embedded in the documentation compiles.

The tests never require network access, third-party Markdown tooling, or a
published package.
"""

from __future__ import annotations

import importlib.util
import io
import json
import re
from pathlib import Path

import blackscholeslab
from blackscholeslab import cli

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
TUTORIALS_DIR = DOCS_DIR / "tutorials"
EXAMPLES_DIR = REPO_ROOT / "examples"

DOC_FILES = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "CHANGELOG.md",
    REPO_ROOT / "examples" / "README.md",
    DOCS_DIR / "index.md",
    DOCS_DIR / "api-reference.md",
    DOCS_DIR / "architecture.md",
    DOCS_DIR / "development.md",
    DOCS_DIR / "mathematical-conventions.md",
    *sorted(TUTORIALS_DIR.glob("*.md")),
]

LINK_RE = re.compile(r"\]\(([^)]+)\)")
PYTHON_BLOCK_RE = re.compile(r"```python\n(.*?)```", re.DOTALL)

FORBIDDEN_CLAIM_SUBSTRINGS = [
    "pip install blackscholeslab",
    "is available from PyPI",
    "available on PyPI",
    "published on PyPI",
    "released on PyPI",
    "install from PyPI",
    "now available on PyPI",
]
SECRET_SUBSTRINGS = [
    "AKIA",
    "github_pat",
    "xoxb-",
    "client_secret",
    "api_key =",
]
ABSOLUTE_PATH_SUBSTRINGS = ["/Users/", "/home/", "C:\\"]
DUPLICATED_FORMULA_DEFINES = [
    "def price_european",
    "def greeks_european",
    "def implied_volatility",
    "def intrinsic_payoff",
    "def expiry_profit_loss",
    "def evaluate_expiry_scenarios",
    "def evaluate_price_scenarios",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _run_cli(args: list[str]) -> tuple[int, str]:
    """Invoke the CLI entry point and capture stdout without exiting."""
    import contextlib

    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = cli.main(args)
    return code, out.getvalue()


def _load_example(path: Path) -> object:
    spec = importlib.util.spec_from_file_location("doc_example_module", str(path))
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------- #
# Link resolution
# --------------------------------------------------------------------------- #
def test_local_markdown_links_resolve() -> None:
    broken = []
    for doc in DOC_FILES:
        if not doc.exists():
            continue
        base_dir = doc.parent
        for match in LINK_RE.finditer(_read(doc)):
            target = match.group(1).strip()
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path_part = target.split("#", 1)[0].split("?", 1)[0]
            if not path_part:
                continue
            resolved = (base_dir / path_part).resolve()
            if not resolved.exists():
                broken.append(f"{doc.relative_to(REPO_ROOT)} -> {target}")
    assert not broken, "Broken local links:\n" + "\n".join(broken)


# --------------------------------------------------------------------------- #
# API reference coverage
# --------------------------------------------------------------------------- #
def test_api_reference_covers_all_public_symbols() -> None:
    api_text = _read(DOCS_DIR / "api-reference.md")
    missing = [symbol for symbol in blackscholeslab.__all__ if f"`{symbol}`" not in api_text]
    assert not missing, f"API reference missing symbols: {missing}"


# --------------------------------------------------------------------------- #
# Examples run and are deterministic
# --------------------------------------------------------------------------- #
def test_examples_run_and_are_deterministic() -> None:
    examples = [
        EXAMPLES_DIR / "pricing_and_greeks.py",
        EXAMPLES_DIR / "implied_volatility.py",
        EXAMPLES_DIR / "payoff_and_scenarios.py",
    ]
    import contextlib

    for path in examples:
        module = _load_example(path)
        first = io.StringIO()
        with contextlib.redirect_stdout(first):
            module.main()  # type: ignore[attr-defined]
        second = io.StringIO()
        with contextlib.redirect_stdout(second):
            module.main()  # type: ignore[attr-defined]
        assert first.getvalue().strip(), f"{path.name} produced no output"
        assert first.getvalue() == second.getvalue(), f"{path.name} output is not deterministic"


def test_examples_do_not_redefine_core_math() -> None:
    for path in EXAMPLES_DIR.glob("*.py"):
        source = _read(path)
        redefined = [define for define in DUPLICATED_FORMULA_DEFINES if define in source]
        assert not redefined, f"{path.name} redefines core math: {redefined}"


def test_examples_are_import_safe() -> None:
    for path in EXAMPLES_DIR.glob("*.py"):
        source = _read(path)
        compile(source, str(path), "exec")


# --------------------------------------------------------------------------- #
# CLI commands execute and return accurate results
# --------------------------------------------------------------------------- #
def test_cli_price() -> None:
    code, out = _run_cli(
        [
            "price",
            "--type",
            "call",
            "--spot",
            "100",
            "--strike",
            "100",
            "--time",
            "1",
            "--rate",
            "0.05",
            "--volatility",
            "0.20",
            "--dividend-yield",
            "0.02",
            "--json",
        ]
    )
    assert code == 0
    data = json.loads(out)
    assert data["option_type"] == "call"
    assert abs(data["price"] - 9.227005508154) < 1e-9


def test_cli_greeks() -> None:
    code, out = _run_cli(
        [
            "greeks",
            "--type",
            "call",
            "--spot",
            "100",
            "--strike",
            "100",
            "--time",
            "1",
            "--rate",
            "0.05",
            "--volatility",
            "0.20",
            "--dividend-yield",
            "0.02",
            "--json",
        ]
    )
    assert code == 0
    data = json.loads(out)
    assert abs(data["delta"] - 0.586851146134764) < 1e-9
    assert abs(data["gamma"] - 0.018950578755008718) < 1e-9
    assert abs(data["vega"] - 37.901157510017434) < 1e-9
    assert abs(data["theta"] - -5.0893189139983335) < 1e-9
    assert abs(data["rho"] - 49.45810910532236) < 1e-9
    assert abs(data["dividend_rho"] - -58.685114613476394) < 1e-9


def test_cli_implied_volatility() -> None:
    code, out = _run_cli(
        [
            "implied-volatility",
            "--type",
            "call",
            "--market-price",
            "9.227005508154",
            "--spot",
            "100",
            "--strike",
            "100",
            "--time",
            "1",
            "--rate",
            "0.05",
            "--dividend-yield",
            "0.02",
            "--json",
        ]
    )
    assert code == 0
    data = json.loads(out)
    assert abs(data["implied_volatility"] - 0.20) < 1e-6


def test_cli_payoff() -> None:
    code, out = _run_cli(
        [
            "payoff",
            "--type",
            "call",
            "--underlying-price",
            "120",
            "--strike",
            "100",
            "--json",
        ]
    )
    assert code == 0
    data = json.loads(out)
    assert abs(data["payoff"] - 20.0) < 1e-12


def test_cli_expiry_pnl() -> None:
    code, out = _run_cli(
        [
            "expiry-pnl",
            "--type",
            "call",
            "--underlying-price",
            "120",
            "--strike",
            "100",
            "--premium",
            "7",
            "--json",
        ]
    )
    assert code == 0
    data = json.loads(out)
    assert abs(data["profit_loss"] - 13.0) < 1e-12


def test_cli_expiry_scenarios() -> None:
    code, out = _run_cli(
        [
            "expiry-scenarios",
            "--type",
            "call",
            "--strike",
            "100",
            "--premium",
            "7",
            "--underlying-prices",
            "80",
            "100",
            "107",
            "120",
            "--json",
        ]
    )
    assert code == 0
    data = json.loads(out)
    assert len(data["results"]) == 4
    last = data["results"][-1]
    assert abs(last["underlying_price"] - 120.0) < 1e-12
    assert abs(last["payoff"] - 20.0) < 1e-12
    assert abs(last["profit_loss"] - 13.0) < 1e-12


def test_cli_price_scenarios_and_percentage_change_policy() -> None:
    code, out = _run_cli(
        [
            "price-scenarios",
            "--type",
            "call",
            "--spot",
            "100",
            "--strike",
            "100",
            "--time",
            "1",
            "--rate",
            "0.05",
            "--volatility",
            "0.20",
            "--dividend-yield",
            "0.02",
            "--scenario",
            "80,1,0.20,0.05,0.02",
            "--scenario",
            "100,1,0.20,0.05,0.02",
            "--scenario",
            "120,1,0.20,0.05,0.02",
            "--json",
        ]
    )
    assert code == 0
    data = json.loads(out)
    assert len(data["results"]) == 3
    assert all("option_price" in row for row in data["results"])

    # When the base-case option price is zero (zero-volatility out-of-the-money
    # base), percentage_change must be reported as null to avoid division by zero.
    code_eq, out_eq = _run_cli(
        [
            "price-scenarios",
            "--type",
            "call",
            "--spot",
            "90",
            "--strike",
            "100",
            "--time",
            "1",
            "--rate",
            "0.05",
            "--volatility",
            "0.0",
            "--dividend-yield",
            "0.02",
            "--scenario",
            "90,1,0.20,0.05,0.02",
            "--json",
        ]
    )
    assert code_eq == 0
    eq_data = json.loads(out_eq)
    assert len(eq_data["results"]) == 1
    assert eq_data["results"][0]["percentage_change"] is None


# --------------------------------------------------------------------------- #
# Release / claim, secret, and path checks
# --------------------------------------------------------------------------- #
def test_no_release_or_pypi_claim() -> None:
    offenders = []
    for doc in DOC_FILES:
        if not doc.exists():
            continue
        text = _read(doc).lower()
        for forbidden in FORBIDDEN_CLAIM_SUBSTRINGS:
            if forbidden in text:
                offenders.append(f"{doc.relative_to(REPO_ROOT)}: {forbidden}")
    assert not offenders, "Found release/PyPI claims:\n" + "\n".join(offenders)


def test_key_docs_state_unreleased_status() -> None:
    readme = _read(REPO_ROOT / "README.md").lower()
    index = _read(DOCS_DIR / "index.md").lower()
    assert "unreleased" in readme or "development version" in readme
    assert "unreleased" in index or "development version" in index


def test_no_secrets_in_docs() -> None:
    offenders = []
    for doc in DOC_FILES:
        if not doc.exists():
            continue
        text = _read(doc)
        for secret in SECRET_SUBSTRINGS:
            if secret in text:
                offenders.append(f"{doc.relative_to(REPO_ROOT)}: {secret}")
    assert not offenders, "Found secret-like substrings:\n" + "\n".join(offenders)


def test_no_absolute_local_paths_in_docs() -> None:
    offenders = []
    for doc in DOC_FILES:
        if not doc.exists():
            continue
        text = _read(doc)
        for path_marker in ABSOLUTE_PATH_SUBSTRINGS:
            if path_marker in text:
                offenders.append(f"{doc.relative_to(REPO_ROOT)}: {path_marker}")
    assert not offenders, "Found absolute local paths:\n" + "\n".join(offenders)


def test_interactive_demo_is_local_only() -> None:
    demo_doc = _read(TUTORIALS_DIR / "interactive-demo.md")
    assert "no network calls" in demo_doc
    assert "no live market data" in demo_doc
    assert "not financial advice" in demo_doc.lower()


# --------------------------------------------------------------------------- #
# Embedded Python snippets compile
# --------------------------------------------------------------------------- #
def test_documentation_python_snippets_compile() -> None:
    import textwrap

    failures = []
    for doc in DOC_FILES:
        if not doc.exists():
            continue
        text = _read(doc)
        for index, match in enumerate(PYTHON_BLOCK_RE.finditer(text)):
            block = textwrap.dedent(match.group(1))
            try:
                compile(block, f"{doc.relative_to(REPO_ROOT)}:snippet{index}", "exec")
            except SyntaxError as exc:
                failures.append(f"{doc.relative_to(REPO_ROOT)} snippet {index}: {exc}")
    assert not failures, "Python snippets failed to compile:\n" + "\n".join(failures)
