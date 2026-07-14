"""Tests for the BlackScholesLab command-line interface.

These tests invoke :func:`blackscholeslab.cli.main` directly and, where useful,
confirm stdout/stderr separation, exit codes, and deterministic JSON output.
"""

from __future__ import annotations

import json
import sys
from typing import Any, cast
from unittest import mock

import pytest

from blackscholeslab import cli

ABS_TOL = 1e-10
REL_TOL = 1e-9


def _run(argv: list[str]) -> tuple[int, str, str]:
    """Run ``main`` capturing stdout/stderr, returning (code, out, err)."""
    import io

    out_buf = io.StringIO()
    err_buf = io.StringIO()
    with mock.patch("sys.stdout", out_buf), mock.patch("sys.stderr", err_buf):
        code = cli.main(argv)
    return code, out_buf.getvalue(), err_buf.getvalue()


def _parse_json(text: str) -> dict[str, Any]:
    return cast("dict[str, Any]", json.loads(text))


# --------------------------------------------------------------------------- #
# Price
# --------------------------------------------------------------------------- #


def test_price_call_reference() -> None:
    code, out, err = _run(
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
    assert err == ""
    data = _parse_json(out)
    assert data["command"] == "price"
    assert data["option_type"] == "call"
    # Independent reference price computed with the same core API.
    from blackscholeslab import BlackScholesInputs, OptionType, price_european

    expected = price_european(
        BlackScholesInputs(100.0, 100.0, 1.0, 0.05, 0.20, 0.02),
        OptionType.CALL,
    )
    assert data["price"] == pytest.approx(expected, abs=ABS_TOL)


def test_price_put_reference() -> None:
    code, out, err = _run(
        [
            "price",
            "--type",
            "put",
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
    data = _parse_json(out)
    assert data["option_type"] == "put"
    from blackscholeslab import BlackScholesInputs, OptionType, price_european

    expected = price_european(
        BlackScholesInputs(100.0, 100.0, 1.0, 0.05, 0.20, 0.02),
        OptionType.PUT,
    )
    assert data["price"] == pytest.approx(expected, abs=ABS_TOL)


def test_price_dividend_paying_case() -> None:
    _, out, _ = _run(
        [
            "price",
            "--type",
            "call",
            "--spot",
            "100",
            "--strike",
            "100",
            "--time",
            "0.5",
            "--rate",
            "0.03",
            "--volatility",
            "0.25",
            "--dividend-yield",
            "0.01",
            "--json",
        ]
    )
    data = _parse_json(out)
    assert data["price"] > 0


def test_price_expiry_boundary() -> None:
    _, out, _ = _run(
        [
            "price",
            "--type",
            "call",
            "--spot",
            "120",
            "--strike",
            "100",
            "--time",
            "0",
            "--rate",
            "0.05",
            "--volatility",
            "0.20",
            "--json",
        ]
    )
    data = _parse_json(out)
    # At expiry, price equals intrinsic payoff = max(S - K, 0) = 20.
    assert data["price"] == pytest.approx(20.0, abs=ABS_TOL)


def test_price_zero_volatility_boundary() -> None:
    _, out, _ = _run(
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
            "0",
            "--json",
        ]
    )
    data = _parse_json(out)
    # Deterministic discounted payoff; must not error.
    assert data["price"] >= 0


def test_price_malformed_values_exit_2() -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(
            [
                "price",
                "--type",
                "call",
                "--spot",
                "abc",
                "--strike",
                "100",
                "--time",
                "1",
                "--rate",
                "0.05",
                "--volatility",
                "0.20",
            ]
        )
    assert exc.value.code == 2


def test_price_negative_finite_rate_yield_accepted() -> None:
    _, out, _ = _run(
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
            "-0.02",
            "--volatility",
            "0.20",
            "--dividend-yield",
            "-0.01",
            "--json",
        ]
    )
    data = _parse_json(out)
    assert data["price"] >= 0


# --------------------------------------------------------------------------- #
# Greeks
# --------------------------------------------------------------------------- #


def test_greeks_call_reference() -> None:
    _, out, _ = _run(
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
            "0.30",
            "--dividend-yield",
            "0.02",
            "--json",
        ]
    )
    data = _parse_json(out)
    assert data["command"] == "greeks"
    assert data["option_type"] == "call"
    for key in ("delta", "gamma", "vega", "theta", "rho", "dividend_rho"):
        assert key in data
    # Raw units: vega must not be divided by 100.
    assert data["vega"] > 1.0


def test_greeks_put_reference() -> None:
    _, out, _ = _run(
        [
            "greeks",
            "--type",
            "put",
            "--spot",
            "100",
            "--strike",
            "100",
            "--time",
            "1",
            "--rate",
            "0.05",
            "--volatility",
            "0.30",
            "--dividend-yield",
            "0.02",
            "--json",
        ]
    )
    data = _parse_json(out)
    assert data["option_type"] == "put"
    assert data["delta"] < 0


def test_greeks_json_key_set_exact() -> None:
    _, out, _ = _run(
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
            "0.30",
            "--json",
        ]
    )
    data = _parse_json(out)
    assert set(data.keys()) == {
        "command",
        "option_type",
        "delta",
        "gamma",
        "vega",
        "theta",
        "rho",
        "dividend_rho",
    }


def test_greeks_zero_time_rejected_exit_2() -> None:
    code, _, err = _run(
        [
            "greeks",
            "--type",
            "call",
            "--spot",
            "100",
            "--strike",
            "100",
            "--time",
            "0",
            "--rate",
            "0.05",
            "--volatility",
            "0.30",
        ]
    )
    assert code == 2
    assert err.startswith("error:")


def test_greeks_zero_volatility_rejected_exit_2() -> None:
    code, _, err = _run(
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
            "0",
        ]
    )
    assert code == 2
    assert err.startswith("error:")


# --------------------------------------------------------------------------- #
# Implied volatility
# --------------------------------------------------------------------------- #


def test_implied_volatility_call_recovers_0_20() -> None:
    _, out, _ = _run(
        [
            "implied-volatility",
            "--type",
            "call",
            "--market-price",
            "10.450583572185565",
            "--spot",
            "100",
            "--strike",
            "100",
            "--time",
            "1",
            "--rate",
            "0.05",
            "--dividend-yield",
            "0",
            "--json",
        ]
    )
    data = _parse_json(out)
    assert data["implied_volatility"] == pytest.approx(0.20, abs=1e-9)


def test_implied_volatility_put_recovers_0_20() -> None:
    from blackscholeslab import (
        BlackScholesInputs,
        OptionType,
        price_european,
    )

    market = price_european(
        BlackScholesInputs(100.0, 100.0, 1.0, 0.05, 0.20, 0.0),
        OptionType.PUT,
    )
    _, out, _ = _run(
        [
            "implied-volatility",
            "--type",
            "put",
            "--market-price",
            str(market),
            "--spot",
            "100",
            "--strike",
            "100",
            "--time",
            "1",
            "--rate",
            "0.05",
            "--dividend-yield",
            "0",
            "--json",
        ]
    )
    data = _parse_json(out)
    assert data["implied_volatility"] == pytest.approx(0.20, abs=1e-9)


def test_implied_volatility_dividend_case_recovers_0_30() -> None:
    from blackscholeslab import (
        BlackScholesInputs,
        OptionType,
        price_european,
    )

    market = price_european(
        BlackScholesInputs(100.0, 100.0, 1.0, 0.05, 0.30, 0.02),
        OptionType.CALL,
    )
    _, out, _ = _run(
        [
            "implied-volatility",
            "--type",
            "call",
            "--market-price",
            str(market),
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
    data = _parse_json(out)
    assert data["implied_volatility"] == pytest.approx(0.30, abs=1e-9)


def test_implied_volatility_arbitrage_bound_error_exit_2() -> None:
    code, _, err = _run(
        [
            "implied-volatility",
            "--type",
            "call",
            "--market-price",
            "0.0001",
            "--spot",
            "100",
            "--strike",
            "100",
            "--time",
            "1",
            "--rate",
            "0.05",
        ]
    )
    assert code == 2
    assert err.startswith("error:")


def test_implied_volatility_forced_non_convergence_exit_3() -> None:
    from blackscholeslab import BlackScholesInputs, OptionType, price_european

    market = price_european(
        BlackScholesInputs(100.0, 100.0, 1.0, 0.05, 0.20, 0.0),
        OptionType.CALL,
    )
    code, _, err = _run(
        [
            "implied-volatility",
            "--type",
            "call",
            "--market-price",
            str(market),
            "--spot",
            "100",
            "--strike",
            "100",
            "--time",
            "1",
            "--rate",
            "0.05",
            "--max-iterations",
            "1",
        ]
    )
    assert code == 3
    assert err.startswith("error:")


def test_implied_volatility_solver_controls_passed() -> None:
    _, out, _ = _run(
        [
            "implied-volatility",
            "--type",
            "call",
            "--market-price",
            "10.450583572185565",
            "--spot",
            "100",
            "--strike",
            "100",
            "--time",
            "1",
            "--rate",
            "0.05",
            "--price-tolerance",
            "1e-12",
            "--volatility-tolerance",
            "1e-14",
            "--max-iterations",
            "500",
            "--initial-upper-volatility",
            "1.0",
            "--max-volatility",
            "5.0",
            "--json",
        ]
    )
    data = _parse_json(out)
    assert data["implied_volatility"] == pytest.approx(0.20, abs=1e-11)


def test_implied_volatility_json_only_documented_keys() -> None:
    _, out, _ = _run(
        [
            "implied-volatility",
            "--type",
            "call",
            "--market-price",
            "10.450583572185565",
            "--spot",
            "100",
            "--strike",
            "100",
            "--time",
            "1",
            "--rate",
            "0.05",
            "--json",
        ]
    )
    data = _parse_json(out)
    assert set(data.keys()) == {"command", "option_type", "implied_volatility"}


# --------------------------------------------------------------------------- #
# Payoff and expiry P&L
# --------------------------------------------------------------------------- #


def test_payoff_call() -> None:
    _, out, _ = _run(
        ["payoff", "--type", "call", "--underlying-price", "120", "--strike", "100", "--json"]
    )
    data = _parse_json(out)
    assert data["payoff"] == pytest.approx(20.0, abs=ABS_TOL)


def test_payoff_put() -> None:
    _, out, _ = _run(
        ["payoff", "--type", "put", "--underlying-price", "80", "--strike", "100", "--json"]
    )
    data = _parse_json(out)
    assert data["payoff"] == pytest.approx(20.0, abs=ABS_TOL)


def test_expiry_pnl_call() -> None:
    _, out, _ = _run(
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
    data = _parse_json(out)
    assert data["profit_loss"] == pytest.approx(13.0, abs=ABS_TOL)


def test_expiry_pnl_put() -> None:
    _, out, _ = _run(
        [
            "expiry-pnl",
            "--type",
            "put",
            "--underlying-price",
            "80",
            "--strike",
            "100",
            "--premium",
            "6",
            "--json",
        ]
    )
    data = _parse_json(out)
    assert data["profit_loss"] == pytest.approx(14.0, abs=ABS_TOL)


def test_expiry_pnl_break_even() -> None:
    _, out, _ = _run(
        [
            "expiry-pnl",
            "--type",
            "call",
            "--underlying-price",
            "107",
            "--strike",
            "100",
            "--premium",
            "7",
            "--json",
        ]
    )
    data = _parse_json(out)
    assert data["profit_loss"] == pytest.approx(0.0, abs=ABS_TOL)


def test_expiry_pnl_invalid_premium_exit_2() -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(
            [
                "expiry-pnl",
                "--type",
                "call",
                "--underlying-price",
                "120",
                "--strike",
                "100",
                "--premium",
                "abc",
            ]
        )
    assert exc.value.code == 2


def test_expiry_pnl_invalid_underlying_price_exit_2() -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(
            [
                "expiry-pnl",
                "--type",
                "call",
                "--underlying-price",
                "abc",
                "--strike",
                "100",
                "--premium",
                "7",
            ]
        )
    assert exc.value.code == 2


# --------------------------------------------------------------------------- #
# Expiry scenarios
# --------------------------------------------------------------------------- #


def test_expiry_scenarios_call_rows() -> None:
    _, out, _ = _run(
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
    data = _parse_json(out)
    assert data["option_type"] == "call"
    rows = data["results"]
    assert [r["underlying_price"] for r in rows] == [80.0, 100.0, 107.0, 120.0]
    assert [r["payoff"] for r in rows] == [0.0, 0.0, 7.0, 20.0]
    assert [r["profit_loss"] for r in rows] == [-7.0, -7.0, 0.0, 13.0]


def test_expiry_scenarios_put_rows() -> None:
    _, out, _ = _run(
        [
            "expiry-scenarios",
            "--type",
            "put",
            "--strike",
            "100",
            "--premium",
            "6",
            "--underlying-prices",
            "80",
            "120",
            "--json",
        ]
    )
    data = _parse_json(out)
    rows = data["results"]
    assert [r["payoff"] for r in rows] == [20.0, 0.0]
    assert [r["profit_loss"] for r in rows] == [14.0, -6.0]


def test_expiry_scenarios_order_preserved() -> None:
    _, out, _ = _run(
        [
            "expiry-scenarios",
            "--type",
            "call",
            "--strike",
            "100",
            "--underlying-prices",
            "120",
            "80",
            "100",
            "--json",
        ]
    )
    data = _parse_json(out)
    assert [r["underlying_price"] for r in data["results"]] == [120.0, 80.0, 100.0]


def test_expiry_scenarios_duplicates_preserved() -> None:
    _, out, _ = _run(
        [
            "expiry-scenarios",
            "--type",
            "call",
            "--strike",
            "100",
            "--underlying-prices",
            "100",
            "100",
            "100",
            "--json",
        ]
    )
    data = _parse_json(out)
    assert len(data["results"]) == 3


def test_expiry_scenarios_human_output() -> None:
    code, out, err = _run(
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
        ]
    )
    assert code == 0
    assert err == ""
    lines = out.strip().splitlines()
    assert lines[0] == "Underlying price | Payoff | Profit/loss"
    assert lines[1] == "80 | 0 | -7"
    assert lines[4] == "120 | 20 | 13"


def test_expiry_scenarios_malformed_item_exit_2() -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(
            [
                "expiry-scenarios",
                "--type",
                "call",
                "--strike",
                "100",
                "--underlying-prices",
                "80",
                "abc",
            ]
        )
    assert exc.value.code == 2


# --------------------------------------------------------------------------- #
# Price scenarios
# --------------------------------------------------------------------------- #


def _price_scenarios_json(argv: list[str]) -> dict[str, Any]:
    _, out, _ = _run(argv)
    return _parse_json(out)


def test_price_scenarios_one_scenario() -> None:
    data = _price_scenarios_json(
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
            "110,1,0.20,0.05,0.02,spot-up",
            "--json",
        ]
    )
    assert len(data["results"]) == 1
    assert data["results"][0]["label"] == "spot-up"
    assert data["results"][0]["spot"] == pytest.approx(110.0, abs=ABS_TOL)


def test_price_scenarios_several() -> None:
    data = _price_scenarios_json(
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
            "110,1,0.20,0.05,0.02,a",
            "--scenario",
            "90,0.5,0.30,0.03,0.01,b",
            "--json",
        ]
    )
    assert len(data["results"]) == 2


def test_price_scenarios_put() -> None:
    data = _price_scenarios_json(
        [
            "price-scenarios",
            "--type",
            "put",
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
            "--scenario",
            "110,1,0.20,0.05,0.02",
            "--json",
        ]
    )
    assert data["option_type"] == "put"


def test_price_scenarios_labels_and_null_label() -> None:
    data = _price_scenarios_json(
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
            "--scenario",
            "110,1,0.20,0.05,0.02,named",
            "--scenario",
            "90,1,0.20,0.05,0.02",
            "--json",
        ]
    )
    assert data["results"][0]["label"] == "named"
    assert data["results"][1]["label"] is None


def test_price_scenarios_empty_string_label() -> None:
    data = _price_scenarios_json(
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
            "--scenario",
            "110,1,0.20,0.05,0.02,",
            "--json",
        ]
    )
    assert data["results"][0]["label"] == ""


def test_price_scenarios_duplicate_scenarios() -> None:
    data = _price_scenarios_json(
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
            "--scenario",
            "110,1,0.20,0.05,0.02,dup",
            "--scenario",
            "110,1,0.20,0.05,0.02,dup",
            "--json",
        ]
    )
    assert len(data["results"]) == 2


def test_price_scenarios_input_order() -> None:
    data = _price_scenarios_json(
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
            "--scenario",
            "90,1,0.20,0.05,0.02,first",
            "--scenario",
            "110,1,0.20,0.05,0.02,second",
            "--json",
        ]
    )
    assert [r["label"] for r in data["results"]] == ["first", "second"]


def test_price_scenarios_zero_base_percentage_none() -> None:
    data = _price_scenarios_json(
        [
            "price-scenarios",
            "--type",
            "call",
            "--spot",
            "100",
            "--strike",
            "200",
            "--time",
            "0",
            "--rate",
            "0.05",
            "--volatility",
            "0.20",
            "--scenario",
            "110,1,0.20,0.05,0.02,up",
            "--json",
        ]
    )
    # Base at expiry with spot <= strike -> base price exactly 0 -> None.
    assert data["results"][0]["percentage_change"] is None


def test_price_scenarios_malformed_field_count_exit_2() -> None:
    code, _, err = _run(
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
            "--scenario",
            "110,1,0.20,0.05",
            "--json",
        ]
    )
    assert code == 2
    assert "scenario 0" in err


def test_price_scenarios_malformed_numeric_field_exit_2() -> None:
    code, _, err = _run(
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
            "--scenario",
            "110,abc,0.20,0.05,0.02,bad",
            "--json",
        ]
    )
    assert code == 2
    assert "scenario 0" in err


def test_price_scenarios_extra_field_rejected_exit_2() -> None:
    code, _, err = _run(
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
            "--scenario",
            "110,1,0.20,0.05,0.02,label,extra",
            "--json",
        ]
    )
    assert code == 2
    assert "scenario 0" in err


def test_price_scenarios_invalid_value_reports_index_exit_2() -> None:
    code, _, err = _run(
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
            "--scenario=-1,1,0.20,0.05,0.02,bad",
            "--json",
        ]
    )
    assert code == 2
    assert "scenario 0" in err


def test_price_scenarios_json_fields_exact() -> None:
    data = _price_scenarios_json(
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
            "110,1,0.20,0.05,0.02,spot-up",
            "--json",
        ]
    )
    result = data["results"][0]
    assert set(result.keys()) == {
        "label",
        "spot",
        "time_to_expiry",
        "volatility",
        "risk_free_rate",
        "dividend_yield",
        "option_price",
        "price_change",
        "percentage_change",
    }


def test_price_scenarios_percentage_change_decimal() -> None:
    data = _price_scenarios_json(
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
            "110,1,0.20,0.05,0.02,spot-up",
            "--json",
        ]
    )
    # percentage_change is a decimal ratio, not multiplied by 100.
    assert data["results"][0]["percentage_change"] < 1.0


# --------------------------------------------------------------------------- #
# Human-readable (non-JSON) mode
# --------------------------------------------------------------------------- #


def test_price_human_mode() -> None:
    code, out, err = _run(
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
        ]
    )
    assert code == 0
    assert err == ""
    assert "Option type: call" in out
    assert out.startswith("Option type: call")
    assert "Price:" in out


def test_greeks_human_mode() -> None:
    code, out, err = _run(
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
            "0.30",
            "--dividend-yield",
            "0.02",
        ]
    )
    assert code == 0
    assert "Delta:" in out
    assert "Gamma:" in out
    assert "Vega:" in out
    assert "Theta:" in out
    assert "Rho:" in out
    assert "Dividend rho:" in out


def test_implied_volatility_human_mode() -> None:
    code, out, err = _run(
        [
            "implied-volatility",
            "--type",
            "call",
            "--market-price",
            "10.450583572185565",
            "--spot",
            "100",
            "--strike",
            "100",
            "--time",
            "1",
            "--rate",
            "0.05",
        ]
    )
    assert code == 0
    assert "Implied volatility:" in out


def test_payoff_human_mode() -> None:
    code, out, err = _run(
        ["payoff", "--type", "call", "--underlying-price", "120", "--strike", "100"]
    )
    assert code == 0
    assert "Option type: call" in out
    assert "Payoff: 20" in out


def test_expiry_pnl_human_mode() -> None:
    code, out, err = _run(
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
        ]
    )
    assert code == 0
    assert "Profit/loss: 13" in out


def test_price_scenarios_human_mode() -> None:
    code, out, err = _run(
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
            "110,1,0.20,0.05,0.02,spot-up",
        ]
    )
    assert code == 0
    assert "Scenario 0 (label=spot-up)" in out
    assert "Option price:" in out
    assert "Price change:" in out
    assert "Percentage change:" in out


def test_price_scenarios_human_mode_undefined_percentage() -> None:
    code, out, err = _run(
        [
            "price-scenarios",
            "--type",
            "call",
            "--spot",
            "100",
            "--strike",
            "200",
            "--time",
            "0",
            "--rate",
            "0.05",
            "--volatility",
            "0.20",
            "--scenario",
            "110,1,0.20,0.05,0.02,up",
        ]
    )
    assert code == 0
    assert "Percentage change: undefined" in out


def test_parse_option_type_helper() -> None:
    from blackscholeslab import OptionType

    assert cli._parse_option_type("call") is OptionType.CALL
    assert cli._parse_option_type("put") is OptionType.PUT
    with pytest.raises(ValueError):
        cli._parse_option_type("CALL")


# --------------------------------------------------------------------------- #
# CLI meta
# --------------------------------------------------------------------------- #


def test_no_subcommand_exit_2() -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main([])
    assert exc.value.code == 2


def test_invalid_subcommand_exit_2() -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["bogus"])
    assert exc.value.code == 2


def test_help_exits_0() -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])
    assert exc.value.code == 0


@pytest.mark.parametrize(
    "command",
    [
        "price",
        "greeks",
        "implied-volatility",
        "payoff",
        "expiry-pnl",
        "expiry-scenarios",
        "price-scenarios",
    ],
)
def test_subcommand_help_exits_0(command: str) -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main([command, "--help"])
    assert exc.value.code == 0


def test_invalid_option_type_exit_2() -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(
            [
                "price",
                "--type",
                "CALL",
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
            ]
        )
    assert exc.value.code == 2


def test_missing_required_args_exit_2() -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["price", "--type", "call"])
    assert exc.value.code == 2


def test_malformed_number_exit_2() -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(
            [
                "price",
                "--type",
                "call",
                "--spot",
                "100",
                "--strike",
                "100",
                "--time",
                "not-a-number",
                "--rate",
                "0.05",
                "--volatility",
                "0.20",
            ]
        )
    assert exc.value.code == 2


def test_stderr_stdout_separation() -> None:
    code, out, err = _run(
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
            "--json",
        ]
    )
    assert code == 0
    assert err == ""
    # JSON object only on stdout.
    assert out.strip().startswith("{")


def test_error_writes_to_stderr_only() -> None:
    code, out, err = _run(
        [
            "greeks",
            "--type",
            "call",
            "--spot",
            "100",
            "--strike",
            "100",
            "--time",
            "0",
            "--rate",
            "0.05",
            "--volatility",
            "0.30",
        ]
    )
    assert code == 2
    assert out == ""
    assert err.startswith("error:")


def test_deterministic_repeated_output() -> None:
    argv = [
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
    _, out1, _ = _run(argv)
    _, out2, _ = _run(argv)
    assert out1 == out2


def test_json_parse_and_sorted_keys() -> None:
    _, out, _ = _run(
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
            "--json",
        ]
    )
    data = _parse_json(out)
    # json.dumps(sort_keys=True) yields key order: command, option_type, price.
    assert list(data.keys()) == ["command", "option_type", "price"]


def test_core_modules_do_not_import_cli() -> None:
    """Core modules must not import the CLI module.

    This is verified by static inspection of the core source so the test is not
    contaminated by this test module's own import of the CLI.
    """
    import re

    import blackscholeslab

    assert "cli" not in blackscholeslab.__all__

    core_dir = __import__("pathlib").Path(blackscholeslab.__file__).parent
    import_pattern = re.compile(r"^\s*(import\s+\S*cli|from\s+\S*cli\s+import)", re.MULTILINE)
    for path in sorted(core_dir.glob("*.py")):
        if path.name == "cli.py":
            continue
        text = path.read_text(encoding="utf-8")
        assert not import_pattern.search(text), f"{path.name} appears to import the CLI module"


def test_module_main_execution_runs_guard_and_exits() -> None:
    """Execute cli.py with __name__ == '__main__' and confirm the guard runs.

    This genuinely covers ``if __name__ == '__main__': raise SystemExit(main())``
    by running the module file directly as ``__main__`` via ``runpy.run_path``
    (loader-independent, so it works under both regular and editable installs
    and on all supported Python versions). pytest-cov tracks the executed lines;
    no coverage exclusion is used.
    """
    import runpy
    from pathlib import Path

    argv = [
        "blackscholeslab",
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
        "--json",
    ]
    with mock.patch.object(sys, "argv", argv):
        with pytest.raises(SystemExit) as exc:
            runpy.run_path(str(Path(cli.__file__).resolve()), run_name="__main__")
    # A valid command returns 0, surfaced through the guard as SystemExit(0).
    assert exc.value.code == 0


def test_module_main_execution_no_args_exits_2() -> None:
    """Running the module as __main__ with no args hits argparse (exit 2)."""
    import runpy
    from pathlib import Path

    with mock.patch.object(sys, "argv", ["blackscholeslab"]):
        with pytest.raises(SystemExit) as exc:
            runpy.run_path(str(Path(cli.__file__).resolve()), run_name="__main__")
    assert exc.value.code == 2


def test_unexpected_runtime_error_not_mapped_to_3() -> None:
    """A RuntimeError from a non-implied-volatility command must propagate.

    This guards against the broad ``except RuntimeError: return 3`` design flaw:
    an unexpected internal failure in another command must not be silently
    reported as implied-volatility non-convergence.
    """
    with mock.patch.object(cli, "price_european", side_effect=RuntimeError("internal boom")):
        with pytest.raises(RuntimeError):
            cli.main(
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
                ]
            )
