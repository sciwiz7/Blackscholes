"""Foundation-level tests for the BlackScholesLab package.

These tests verify the package metadata and importability only. They do NOT
test any mathematical functionality, because none has been implemented yet.
"""

from __future__ import annotations

import importlib.metadata
import importlib.util

import blackscholeslab

EXPECTED_VERSION = "0.1.0"


def test_package_imports() -> None:
    assert importlib.util.find_spec("blackscholeslab") is not None
    assert blackscholeslab is not None


def test_version_exists_and_matches() -> None:
    assert isinstance(blackscholeslab.__version__, str)
    assert blackscholeslab.__version__ == EXPECTED_VERSION


def test_public_metadata_exists() -> None:
    assert hasattr(blackscholeslab, "__author__")
    assert hasattr(blackscholeslab, "__license__")
    assert blackscholeslab.__author__ == "Amrut Deshmukh"
    assert blackscholeslab.__license__ == "MIT"


def test_distribution_version_matches() -> None:
    installed = importlib.metadata.version("blackscholeslab")
    assert installed == EXPECTED_VERSION
