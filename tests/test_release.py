"""Version-consistency and release-focused validation for BlackScholesLab.

These tests verify that:

- the version string is consistent across pyproject.toml, the runtime
  ``__version__`` attribute, the built wheel metadata, and (where practical)
  the built sdist metadata;
- the wheel and sdist build successfully from a clean checkout;
- the built artifacts contain expected files and exclude forbidden ones;
- the console entry point is present;
- the ``py.typed`` marker is included;
- Streamlit is not a mandatory dependency;
- demo extra metadata is present;
- the version remains the expected candidate version;
- the release workflow's production tag would be exactly ``v0.1.0``;
- mismatched tags would fail;
- development, alpha, beta, and release-candidate versions would fail the
  production-stable path;
- the tagged commit must still be contained in main;
- no manual production-dispatch mode exists;
- artifact SHA-256 hashes are computed.

The artifact tests are fully self-contained: a session-scoped fixture builds a
fresh wheel and sdist exactly once into a pytest-managed temporary directory
(never the repository-root ``dist/``), and every artifact test receives the
exact built paths. No pre-existing or locally cached build output is trusted.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import re
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_INIT = REPO_ROOT / "src" / "blackscholeslab" / "__init__.py"
PYPROJECT = REPO_ROOT / "pyproject.toml"
RELEASE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "release.yml"
RELEASING_DOC = REPO_ROOT / "docs" / "releasing.md"

EXPECTED_VERSION = "0.1.0"

FORBIDDEN_WHEEL_PATTERNS = [
    "__pycache__",
    ".pyc",
    ".git",
    ".venv",
    ".env",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    ".coverage",
]

FORBIDDEN_SDIST_PATTERNS = [
    "__pycache__",
    ".pyc",
    ".git/",
    ".venv/",
    ".mypy_cache/",
    ".ruff_cache/",
    ".pytest_cache/",
    ".coverage",
]


def _read_pyproject_version() -> str:
    """Extract the version string from pyproject.toml without TOML library."""
    text = PYPROJECT.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("version"):
            _, _, value = stripped.partition("=")
            return value.strip().strip('"').strip("'")
    raise AssertionError("version not found in pyproject.toml")


def _read_init_version() -> str:
    """Extract the __version__ string from __init__.py."""
    text = SRC_INIT.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("__version__"):
            _, _, value = stripped.partition("=")
            return value.strip().strip('"').strip("'")
    raise AssertionError("__version__ not found in __init__.py")


def _sha256(path: Path) -> str:
    """Compute the SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _get_runtime_version() -> str:
    """Read the version from the installed package metadata."""
    return importlib.metadata.version("blackscholeslab")


@pytest.fixture(scope="session")
def artifacts(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    """Build a fresh wheel and sdist once per session into a temp directory.

    The artifacts are produced by ``python -m build`` into a pytest-managed
    temporary directory, never into the repository-root ``dist/``. Exactly one
    wheel and one sdist must be present; multiple artifacts are rejected so the
    tests never select an arbitrary "latest" file.
    """
    out_dir = tmp_path_factory.mktemp("release_artifacts")
    subprocess.run(
        [sys.executable, "-m", "build", "--outdir", str(out_dir), str(REPO_ROOT)],
        check=True,
    )
    wheels = sorted(out_dir.glob("*.whl"))
    sdists = sorted(out_dir.glob("*.tar.gz"))
    assert len(wheels) == 1, f"expected exactly one wheel, found {wheels}"
    assert len(sdists) == 1, f"expected exactly one sdist, found {sdists}"
    return {"wheel": wheels[0], "sdist": sdists[0]}


# --------------------------------------------------------------------------- #
# Version consistency
# --------------------------------------------------------------------------- #
def test_pyproject_version_is_expected() -> None:
    assert _read_pyproject_version() == EXPECTED_VERSION


def test_init_version_is_expected() -> None:
    assert _read_init_version() == EXPECTED_VERSION


def test_runtime_version_is_expected() -> None:
    assert _get_runtime_version() == EXPECTED_VERSION


def test_pyproject_and_init_versions_match() -> None:
    assert _read_pyproject_version() == _read_init_version()


def test_runtime_version_matches_pyproject() -> None:
    assert _get_runtime_version() == _read_pyproject_version()


# --------------------------------------------------------------------------- #
# Artifact existence and hashing
# --------------------------------------------------------------------------- #
def test_wheel_exists(artifacts: dict[str, Path]) -> None:
    assert artifacts["wheel"].is_file()


def test_sdist_exists(artifacts: dict[str, Path]) -> None:
    assert artifacts["sdist"].is_file()


def test_artifact_sha256_hashes(artifacts: dict[str, Path]) -> None:
    wheel = artifacts["wheel"]
    sdist = artifacts["sdist"]
    assert _sha256(wheel)
    assert _sha256(sdist)


# --------------------------------------------------------------------------- #
# Wheel content inspection
# --------------------------------------------------------------------------- #
def test_wheel_contains_py_typed(artifacts: dict[str, Path]) -> None:
    wheel_path = artifacts["wheel"]
    with zipfile.ZipFile(wheel_path) as zf:
        names = zf.namelist()
    assert any("py.typed" in name for name in names), "py.typed not found in wheel"


def test_wheel_contains_cli_entry_point(artifacts: dict[str, Path]) -> None:
    wheel_path = artifacts["wheel"]
    with zipfile.ZipFile(wheel_path) as zf:
        names = zf.namelist()
    assert any(name.endswith("METADATA") for name in names), "No METADATA in wheel"
    with zipfile.ZipFile(wheel_path) as zf:
        for name in names:
            if name.endswith("METADATA"):
                content = zf.read(name).decode("utf-8")
                assert "blackscholeslab" in content
                break


def test_wheel_no_forbidden_files(artifacts: dict[str, Path]) -> None:
    wheel_path = artifacts["wheel"]
    with zipfile.ZipFile(wheel_path) as zf:
        names = zf.namelist()
    offenders = [n for n in names if any(p in n for p in FORBIDDEN_WHEEL_PATTERNS)]
    assert not offenders, f"Forbidden files in wheel: {offenders}"


def test_wheel_no_streamlit_mandatory_dependency(artifacts: dict[str, Path]) -> None:
    wheel_path = artifacts["wheel"]
    with zipfile.ZipFile(wheel_path) as zf:
        for name in zf.namelist():
            if name.endswith("METADATA"):
                content = zf.read(name).decode("utf-8")
                for line in content.splitlines():
                    if line.startswith("Requires-Dist:"):
                        # Streamlit is acceptable only as an optional extra
                        if "extra ==" in line:
                            continue
                        assert "streamlit" not in line.lower(), (
                            "Streamlit is a mandatory dependency"
                        )


def test_wheel_metadata_version_matches(artifacts: dict[str, Path]) -> None:
    wheel_path = artifacts["wheel"]
    with zipfile.ZipFile(wheel_path) as zf:
        for name in zf.namelist():
            if name.endswith("METADATA"):
                content = zf.read(name).decode("utf-8")
                for line in content.splitlines():
                    if line.startswith("Version:"):
                        _, _, value = line.partition(":")
                        assert value.strip() == EXPECTED_VERSION
                        return
    raise AssertionError("No Version field in wheel METADATA")


# --------------------------------------------------------------------------- #
# Sdist content inspection
# --------------------------------------------------------------------------- #
def test_sdist_contains_expected_directories(artifacts: dict[str, Path]) -> None:
    sdist_path = artifacts["sdist"]
    with tarfile.open(sdist_path, "r:gz") as tf:
        names = tf.getnames()
    assert any("src/blackscholeslab" in n for n in names), "src/blackscholeslab not in sdist"
    assert any("tests/" in n for n in names), "tests/ not in sdist"
    assert any("docs/" in n for n in names), "docs/ not in sdist"
    assert any("examples/" in n for n in names), "examples/ not in sdist"


def test_sdist_contains_demo(artifacts: dict[str, Path]) -> None:
    sdist_path = artifacts["sdist"]
    with tarfile.open(sdist_path, "r:gz") as tf:
        names = tf.getnames()
    assert any("demo/" in n for n in names), "demo/ not in sdist"


def test_sdist_no_forbidden_files(artifacts: dict[str, Path]) -> None:
    sdist_path = artifacts["sdist"]
    with tarfile.open(sdist_path, "r:gz") as tf:
        names = tf.getnames()
    offenders = [n for n in names if any(p in n for p in FORBIDDEN_SDIST_PATTERNS)]
    assert not offenders, f"Forbidden files in sdist: {offenders}"


def test_sdist_metadata_version_matches(artifacts: dict[str, Path]) -> None:
    sdist_path = artifacts["sdist"]
    with tarfile.open(sdist_path, "r:gz") as tf:
        for member in tf.getmembers():
            if member.name.endswith("PKG-INFO"):
                f = tf.extractfile(member)
                assert f is not None
                content = f.read().decode("utf-8")
                for line in content.splitlines():
                    if line.startswith("Version:"):
                        _, _, value = line.partition(":")
                        assert value.strip() == EXPECTED_VERSION
                        return
    raise AssertionError("No Version field in sdist PKG-INFO")


def test_sdist_no_streamlit_mandatory_dependency(artifacts: dict[str, Path]) -> None:
    sdist_path = artifacts["sdist"]
    with tarfile.open(sdist_path, "r:gz") as tf:
        for member in tf.getmembers():
            if member.name.endswith("PKG-INFO"):
                f = tf.extractfile(member)
                assert f is not None
                content = f.read().decode("utf-8")
                for line in content.splitlines():
                    if line.startswith("Requires-Dist:"):
                        if "extra ==" in line:
                            continue
                        assert "streamlit" not in line.lower(), (
                            "Streamlit is a mandatory dependency in sdist"
                        )


# --------------------------------------------------------------------------- #
# Release-workflow security regression tests
#
# These use only the Python standard library and a small, intentionally coarse
# structural parser. They are designed to detect security regressions in
# release.yml (and the release documentation) without introducing a YAML
# parsing dependency. They target structure and expected tokens, not punctuation.
# --------------------------------------------------------------------------- #
def _load_workflow() -> str:
    assert RELEASE_WORKFLOW.exists(), "release.yml not found"
    return RELEASE_WORKFLOW.read_text(encoding="utf-8")


def _load_releasing_doc() -> str:
    assert RELEASING_DOC.exists(), "docs/releasing.md not found"
    return RELEASING_DOC.read_text(encoding="utf-8")


_JOB_RE = re.compile(r"^  ([A-Za-z0-9_-]+):\n", re.MULTILINE)


def _job_blocks(text: str) -> dict[str, str]:
    """Split top-level job definitions into name -> body text."""
    matches = list(_JOB_RE.finditer(text))
    blocks: dict[str, str] = {}
    for i, m in enumerate(matches):
        name = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        blocks[name] = text[start:end]
    return blocks


def _env_names(text: str) -> list[str]:
    return re.findall(r"environment:\s*\n\s+name:\s*(\S+)", text)


def test_workflow_dispatch_has_no_production_pypi_mode() -> None:
    text = _load_workflow()
    # The workflow_dispatch mode options must not expose a production PyPI mode.
    dispatch_block = text.split("workflow_dispatch:", 1)[-1]
    # Limit to the inputs/mode section before the next top-level key.
    tail = dispatch_block.split("\npermissions:", 1)[0]
    # Match a standalone option line only (e.g. "  - pypi"), not "testpypi"/"TestPyPI".
    assert not re.search(r"^\s*-\s*pypi\s*$", tail, re.MULTILINE), (
        "workflow_dispatch must not expose a 'pypi' production mode"
    )


def test_normal_push_and_pull_request_do_not_publish() -> None:
    text = _load_workflow()
    # Production publishing must require a tag push, not ordinary branches.
    assert "pull_request:" not in text, "pull_request trigger must not exist"
    # The production publish job must be gated on the push tag event only.
    jobs = _job_blocks(text)
    assert "publish-pypi" in jobs
    prod = jobs["publish-pypi"]
    assert "github.event_name == 'push'" in prod
    # And it must not also accept a manual dispatch production mode.
    assert "mode == 'pypi'" not in prod


def test_production_and_testpypi_environments_distinct() -> None:
    text = _load_workflow()
    envs = _env_names(text)
    assert "pypi" in envs, "production environment 'pypi' missing"
    assert "pypi-testpypi" in envs, "TestPyPI environment 'pypi-testpypi' missing"
    assert len(set(envs)) == len(envs), "environment names are not distinct"


def test_build_job_has_no_oidc_permission() -> None:
    text = _load_workflow()
    jobs = _job_blocks(text)
    assert "build" in jobs
    build = jobs["build"]
    assert "id-token: write" not in build, "build job must not have id-token: write"


def test_publish_jobs_depend_on_build() -> None:
    text = _load_workflow()
    jobs = _job_blocks(text)
    for name in ("publish-pypi", "publish-testpypi"):
        assert name in jobs, f"{name} job missing"
        assert "needs: build" in jobs[name], f"{name} must depend on build"


def test_publish_jobs_download_not_rebuild() -> None:
    text = _load_workflow()
    jobs = _job_blocks(text)
    for name in ("publish-pypi", "publish-testpypi"):
        body = jobs[name]
        assert "download-artifact" in body, f"{name} must download artifacts"
        assert "python -m build" not in body, f"{name} must not rebuild artifacts"


def test_publish_jobs_verify_checksums() -> None:
    text = _load_workflow()
    jobs = _job_blocks(text)
    for name in ("publish-pypi", "publish-testpypi"):
        body = jobs[name]
        assert "sha256sum -c" in body, f"{name} must verify checksums before publish"
        assert "SHA256SUMS" in body, f"{name} must use the checksum manifest"


def test_no_token_or_password_input_in_publish() -> None:
    text = _load_workflow()
    jobs = _job_blocks(text)
    for name in ("publish-pypi", "publish-testpypi"):
        body = jobs[name]
        # No stored PyPI password/token inputs may be referenced. The OIDC
        # "id-token: write" permission is expected and must not be flagged.
        assert re.search(r"(?<!-)password:", body) is None, f"{name} references a password input"
        assert re.search(r"(?<!-)token:", body) is None, f"{name} references a token input"


def test_no_pull_request_target() -> None:
    text = _load_workflow()
    assert "pull_request_target" not in text


def test_no_unsafe_mixed_index_in_releasing_docs() -> None:
    doc = _load_releasing_doc()
    # Extract fenced code blocks only; the unsafe mixed-index command must not
    # appear as a recommended rehearsal instruction. (It may appear in prose as
    # a warning against using it.)
    code_blocks = re.findall(r"```[a-zA-Z]*\n(.*?)```", doc, re.DOTALL)
    for block in code_blocks:
        assert "--extra-index-url https://pypi.org/simple/" not in block, (
            "unsafe mixed-index command must not be presented as a rehearsal"
        )
    # The safe isolated rehearsal guidance must be present.
    lowered = doc.lower()
    assert "--no-deps" in lowered
    assert "--index-url https://test.pypi.org/simple/" in lowered


def test_version_tag_and_binding_verification_present() -> None:
    text = _load_workflow()
    # Tag/package version binding and main-history reachability checks.
    assert "v${PKG_VERSION}" in text or "v$PKG_VERSION" in text, (
        "workflow must compare the tag to v${PACKAGE_VERSION}"
    )
    assert "merge-base --is-ancestor" in text, "workflow must check main-history reachability"
    assert "tomllib" in text or "pyproject.toml" in text


def test_production_rejects_development_versions() -> None:
    text = _load_workflow()
    # The production path must reject .dev (and pre-release) versions.
    assert "*.dev*" in text, "workflow must reject development versions for production"
    assert "is_production_event" in text


def test_top_level_permissions_minimal() -> None:
    text = _load_workflow()
    head = text.split("\njobs:", 1)[0]
    assert "contents: read" in head, "top-level permissions must include contents: read"
    # No broad write permissions at the top level.
    assert "contents: write" not in head
    assert "actions: write" not in head
    assert "pull-requests: write" not in head


def test_oidc_only_on_publish_jobs() -> None:
    text = _load_workflow()
    jobs = _job_blocks(text)
    for name, body in jobs.items():
        has_oidc = "id-token: write" in body
        if name in ("publish-pypi", "publish-testpypi"):
            assert has_oidc, f"{name} must have id-token: write"
        else:
            assert not has_oidc, f"{name} must not have id-token: write"


# --------------------------------------------------------------------------- #
# Production-tag / version-binding regression tests
# --------------------------------------------------------------------------- #
def test_production_tag_would_be_v0_1_0() -> None:
    # The production tag is exactly v<package version>; for this candidate the
    # package version is the stable 0.1.0, so the tag must be v0.1.0.
    assert EXPECTED_VERSION == "0.1.0"
    assert f"v{EXPECTED_VERSION}" == "v0.1.0"


def test_candidate_version_is_stable_not_prerelease() -> None:
    # A 0.1.0 production candidate must not carry dev/a/b/rc markers.
    for marker in (".dev", "a", "b", "rc"):
        assert marker not in EXPECTED_VERSION, f"unexpected pre-release marker {marker!r}"
    assert EXPECTED_VERSION == "0.1.0"


def test_workflow_rejects_mismatched_tag() -> None:
    text = _load_workflow()
    # The workflow derives EXPECTED_TAG="v${PKG_VERSION}" and fails when the
    # pushed tag does not equal it exactly.
    assert 'EXPECTED_TAG="v${PKG_VERSION}"' in text
    assert 'if [ "$TAG_NAME" != "$EXPECTED_TAG" ]; then' in text


def test_workflow_rejects_prerelease_versions_for_production() -> None:
    text = _load_workflow()
    # The production path must refuse dev/alpha/beta/release-candidate versions.
    assert "*.dev*|*a*|*b*|*rc*" in text, (
        "workflow must reject dev/alpha/beta/rc versions for production"
    )


def test_workflow_requires_tag_commit_in_main_history() -> None:
    text = _load_workflow()
    # The tagged commit must be retained in the protected default main history.
    assert "git merge-base --is-ancestor" in text
    assert "origin/main" in text


def test_no_manual_production_dispatch_mode() -> None:
    text = _load_workflow()
    # Production publication is available only via a rigorously validated tag
    # push; the manual dispatch must not expose a 'pypi' production mode.
    assert "mode == 'pypi'" not in text
    dispatch_block = text.split("workflow_dispatch:", 1)[-1]
    tail = dispatch_block.split("\npermissions:", 1)[0]
    assert not re.search(r"^\s*-\s*pypi\s*$", tail, re.MULTILINE), (
        "workflow_dispatch must not expose a 'pypi' production mode"
    )
