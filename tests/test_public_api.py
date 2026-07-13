"""Tests for the public package API and top-level imports."""

from __future__ import annotations

import blackscholeslab


def test_public_imports_work() -> None:
    from blackscholeslab import (
        BlackScholesInputs,
        OptionType,
        price_european,
    )

    assert BlackScholesInputs is not None
    assert OptionType is not None
    assert callable(price_european)


def test_public_api_end_to_end() -> None:
    from blackscholeslab import (
        BlackScholesInputs,
        OptionType,
        price_european,
    )

    inputs = BlackScholesInputs(
        spot=42.0,
        strike=40.0,
        time_to_expiry=0.5,
        risk_free_rate=0.10,
        volatility=0.20,
    )
    call_price = price_european(inputs, OptionType.CALL)
    put_price = price_european(inputs, OptionType.PUT)
    assert call_price > 0.0
    assert put_price > 0.0


def test_undocumented_internal_helpers_not_exported() -> None:
    # Internal helpers must remain private; only the documented public surface
    # is exported.
    assert "validate_inputs" not in blackscholeslab.__all__
    assert "norm_cdf" not in blackscholeslab.__all__
    assert "price_european" in blackscholeslab.__all__


def test_version_unchanged() -> None:
    assert blackscholeslab.__version__ == "0.1.0.dev0"
