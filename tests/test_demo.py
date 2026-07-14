"""Tests for the BlackScholesLab interactive demonstration.

Two layers are covered:

1. Direct, deterministic tests of ``demo.helpers`` (no Streamlit required).
2. Headless application tests using ``streamlit.testing.v1.AppTest``.

The AppTest layer verifies that the demonstration calls the existing public
core APIs and surfaces expected domain errors without crashing.
"""

from __future__ import annotations

from math import isclose
from pathlib import Path

import pytest

import blackscholeslab as bsl
from blackscholeslab import (
    ExpiryScenarioResult,
    OptionGreeks,
    OptionScenario,
    OptionType,
    ScenarioPriceResult,
)
from demo.helpers import (
    ScenarioSpec,
    break_even_price,
    default_scenario_specs,
    expiry_chart_data,
    expiry_rows,
    format_number,
    inclusive_grid,
    option_type_from_label,
    scenario_rows,
)

APP_PATH = Path(__file__).resolve().parent.parent / "demo" / "app.py"

from streamlit.testing.v1 import AppTest  # noqa: E402


# --------------------------------------------------------------------------- #
# Helper: inclusive_grid
# --------------------------------------------------------------------------- #
def test_app_module_imports_cleanly() -> None:
    import demo.app as _app_module

    assert hasattr(_app_module, "main")


def test_inclusive_grid_exact_endpoints_two_points() -> None:
    grid = inclusive_grid(0.0, 10.0, 2)
    assert grid == (0.0, 10.0)
    assert grid[0] == 0.0
    assert grid[-1] == 10.0


def test_inclusive_grid_exact_endpoints_51_points() -> None:
    grid = inclusive_grid(50.0, 150.0, 51)
    assert len(grid) == 51
    assert grid[0] == 50.0
    assert grid[-1] == 150.0


def test_inclusive_grid_ascending() -> None:
    grid = inclusive_grid(1.0, 2.0, 11)
    assert all(grid[i] < grid[i + 1] for i in range(len(grid) - 1))


def test_inclusive_grid_deterministic() -> None:
    first = inclusive_grid(0.0, 1.0, 20)
    second = inclusive_grid(0.0, 1.0, 20)
    assert first == second


def test_inclusive_grid_zero_start() -> None:
    grid = inclusive_grid(0.0, 5.0, 6)
    assert grid[0] == 0.0
    assert len(grid) == 6


def test_inclusive_grid_rejects_points_less_than_two() -> None:
    with pytest.raises(ValueError):
        inclusive_grid(0.0, 1.0, 1)


def test_inclusive_grid_rejects_equal_bounds() -> None:
    with pytest.raises(ValueError):
        inclusive_grid(1.0, 1.0, 5)


def test_inclusive_grid_rejects_reversed_bounds() -> None:
    with pytest.raises(ValueError):
        inclusive_grid(10.0, 1.0, 5)


def test_inclusive_grid_rejects_negative_start() -> None:
    with pytest.raises(ValueError):
        inclusive_grid(-1.0, 5.0, 5)


def test_inclusive_grid_rejects_nan() -> None:
    with pytest.raises(ValueError):
        inclusive_grid(float("nan"), 5.0, 5)


def test_inclusive_grid_rejects_infinity() -> None:
    with pytest.raises(ValueError):
        inclusive_grid(0.0, float("inf"), 5)


def test_inclusive_grid_rejects_bool_points() -> None:
    with pytest.raises(TypeError):
        inclusive_grid(0.0, 5.0, True)


def test_inclusive_grid_rejects_string_bounds() -> None:
    with pytest.raises(TypeError):
        inclusive_grid("0", 5.0, 5)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# Helper: option_type_from_label
# --------------------------------------------------------------------------- #
def test_option_label_mapping_call() -> None:
    assert option_type_from_label("Call") is OptionType.CALL
    assert option_type_from_label("call") is OptionType.CALL


def test_option_label_mapping_put() -> None:
    assert option_type_from_label("Put") is OptionType.PUT
    assert option_type_from_label("put") is OptionType.PUT


def test_option_label_mapping_rejects_arbitrary() -> None:
    with pytest.raises(ValueError):
        option_type_from_label("banana")


def test_option_label_mapping_rejects_non_string() -> None:
    with pytest.raises(TypeError):
        option_type_from_label(None)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# Helper: break_even_price
# --------------------------------------------------------------------------- #
def test_break_even_call() -> None:
    assert break_even_price(OptionType.CALL, 100.0, 7.0) == 107.0


def test_break_even_put() -> None:
    assert break_even_price(OptionType.PUT, 100.0, 7.0) == 93.0


def test_break_even_put_negative_is_not_clamped() -> None:
    # A premium larger than the strike yields a negative break-even; the helper
    # returns the arithmetic result honestly rather than clamping to zero.
    assert break_even_price(OptionType.PUT, 100.0, 150.0) == -50.0


def test_break_even_rejects_negative_premium() -> None:
    with pytest.raises(ValueError):
        break_even_price(OptionType.CALL, 100.0, -1.0)


# --------------------------------------------------------------------------- #
# Helper: format_number
# --------------------------------------------------------------------------- #
def test_format_number_stable() -> None:
    assert format_number(0.2) == "0.2"
    assert format_number(123.456789, precision=3) == "123"


# --------------------------------------------------------------------------- #
# Helper: row construction and ordering
# --------------------------------------------------------------------------- #
def test_expiry_rows_ordering() -> None:
    results = (
        ExpiryScenarioResult(80.0, 0.0, -7.0),
        ExpiryScenarioResult(100.0, 0.0, -7.0),
        ExpiryScenarioResult(120.0, 20.0, 13.0),
    )
    rows = expiry_rows(results)
    assert [r["Underlying price"] for r in rows] == [80.0, 100.0, 120.0]
    assert rows[2]["Profit/Loss"] == 13.0


def test_expiry_chart_data_ordering() -> None:
    results = (
        ExpiryScenarioResult(80.0, 0.0, -7.0),
        ExpiryScenarioResult(100.0, 0.0, -7.0),
        ExpiryScenarioResult(120.0, 20.0, 13.0),
    )
    data = expiry_chart_data(results)
    assert data["Underlying price"] == [80.0, 100.0, 120.0]
    assert len(data["Payoff"]) == 3


def test_scenario_rows_ordering_and_none_percentage() -> None:
    scenarios = [
        OptionScenario(
            spot=100.0, time_to_expiry=1.0, volatility=0.2, risk_free_rate=0.05, label="Base"
        ),
        OptionScenario(
            spot=90.0, time_to_expiry=1.0, volatility=0.2, risk_free_rate=0.05, label=None
        ),
        OptionScenario(
            spot=50.0, time_to_expiry=1.0, volatility=0.2, risk_free_rate=0.05, label="Zero base"
        ),
    ]
    results = (
        ScenarioPriceResult(scenarios[0], 10.0, 0.0, 0.0),
        ScenarioPriceResult(scenarios[1], 5.0, -5.0, -0.5),
        ScenarioPriceResult(scenarios[2], 0.0, -10.0, None),
    )
    rows = scenario_rows(results)
    assert [r["Scenario"] for r in rows] == [1, 2, 3]
    assert rows[0]["Label"] == "Base"
    assert rows[1]["Label"] == ""
    assert rows[2]["Percentage change"] == "undefined"


def test_default_scenario_specs_three() -> None:
    specs: list[ScenarioSpec] = default_scenario_specs(100.0, 1.0, 0.2, 0.05, 0.02, 3)
    assert len(specs) == 3
    assert specs[0].label == "Downside"
    assert isclose(specs[0].spot, 90.0)
    assert specs[1].label == "Base"
    assert isclose(specs[1].spot, 100.0)
    assert specs[2].label == "Upside"
    assert isclose(specs[2].spot, 110.0)


def test_default_scenario_specs_five() -> None:
    specs: list[ScenarioSpec] = default_scenario_specs(100.0, 1.0, 0.2, 0.05, 0.02, 5)
    assert len(specs) == 5
    assert specs[3].label == "Scenario 4"
    assert specs[4].label == "Scenario 5"


def test_default_scenario_specs_rejects_out_of_range() -> None:
    with pytest.raises(ValueError):
        default_scenario_specs(100.0, 1.0, 0.2, 0.05, 0.02, 0)


# --------------------------------------------------------------------------- #
# Core-delegation: the demo calls the existing public APIs
# --------------------------------------------------------------------------- #
def test_demo_delegates_to_public_apis(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, int] = {}

    def spy_price(*_args: object, **_kwargs: object) -> float:
        calls["price"] = calls.get("price", 0) + 1
        return 1.0

    def spy_greeks(*_args: object, **_kwargs: object) -> OptionGreeks:
        calls["greeks"] = calls.get("greeks", 0) + 1
        return OptionGreeks(delta=0.0, gamma=0.0, vega=0.0, theta=0.0, rho=0.0, dividend_rho=0.0)

    def spy_iv(*_args: object, **_kwargs: object) -> float:
        calls["iv"] = calls.get("iv", 0) + 1
        return 0.2

    def spy_expiry(*_args: object, **_kwargs: object) -> tuple[ExpiryScenarioResult, ...]:
        calls["expiry"] = calls.get("expiry", 0) + 1
        return (ExpiryScenarioResult(1.0, 0.0, -1.0),)

    def spy_scenarios(*_args: object, **_kwargs: object) -> tuple[ScenarioPriceResult, ...]:
        calls["scenarios"] = calls.get("scenarios", 0) + 1
        scenario = OptionScenario(spot=1.0, time_to_expiry=1.0, volatility=0.2, risk_free_rate=0.05)
        return (ScenarioPriceResult(scenario, 1.0, 0.0, 0.0),)

    monkeypatch.setattr(bsl, "price_european", spy_price)
    monkeypatch.setattr(bsl, "greeks_european", spy_greeks)
    monkeypatch.setattr(bsl, "implied_volatility", spy_iv)
    monkeypatch.setattr(bsl, "evaluate_expiry_scenarios", spy_expiry)
    monkeypatch.setattr(bsl, "evaluate_price_scenarios", spy_scenarios)

    at = AppTest.from_file(str(APP_PATH)).run()
    assert len(at.exception) == 0
    assert calls.get("price", 0) >= 1
    assert calls.get("greeks", 0) >= 1
    assert calls.get("iv", 0) >= 1
    assert calls.get("expiry", 0) >= 1
    assert calls.get("scenarios", 0) >= 1


# --------------------------------------------------------------------------- #
# AppTest smoke tests
# --------------------------------------------------------------------------- #
def test_application_starts_without_uncaught_exception() -> None:
    at = AppTest.from_file(str(APP_PATH)).run()
    assert len(at.exception) == 0


def test_title_present() -> None:
    at = AppTest.from_file(str(APP_PATH)).run()
    assert "BlackScholesLab" in [t.value for t in at.title]


def test_educational_warning_present() -> None:
    at = AppTest.from_file(str(APP_PATH)).run()
    joined = " ".join(w.value for w in at.warning).lower()
    assert "not financial advice" in joined
    assert "educational" in joined


def test_default_pricing_produces_result() -> None:
    at = AppTest.from_file(str(APP_PATH)).run()
    labels = [m.label for m in at.metric]
    assert "Option price" in labels
    price = [m for m in at.metric if m.label == "Option price"][0]
    assert price.value not in (None, "")


def test_default_greeks_produce_metrics() -> None:
    at = AppTest.from_file(str(APP_PATH)).run()
    greek_labels = {"Delta", "Gamma", "Vega", "Theta", "Rho", "Dividend rho"}
    rendered = {m.label for m in at.metric}
    assert greek_labels.issubset(rendered)


def test_five_tabs_exist() -> None:
    at = AppTest.from_file(str(APP_PATH)).run()
    labels = [t.label for t in at.tabs]
    assert labels == [
        "Price",
        "Greeks",
        "Implied volatility",
        "Expiry payoff",
        "Scenario analysis",
    ]


def test_shared_base_widgets_exist_with_defaults() -> None:
    at = AppTest.from_file(str(APP_PATH)).run()
    keys = {w.key for w in at.number_input} | {w.key for w in at.selectbox}
    for expected in {
        "opt_type",
        "base_spot",
        "base_strike",
        "base_time",
        "base_rate",
        "base_vol",
        "base_div",
    }:
        assert expected in keys
    assert at.selectbox(key="opt_type").value == "Call"
    assert at.number_input(key="base_spot").value == 100.0
    assert at.number_input(key="base_strike").value == 100.0
    assert at.number_input(key="base_time").value == 1.0
    assert at.number_input(key="base_rate").value == 0.05
    assert at.number_input(key="base_vol").value == 0.20
    assert at.number_input(key="base_div").value == 0.02


def test_switch_to_put_reruns_without_exception() -> None:
    at = AppTest.from_file(str(APP_PATH)).run()
    at.selectbox(key="opt_type").set_value("Put")
    at.run()
    assert len(at.exception) == 0
    option_type_metric = [m for m in at.metric if m.label == "Option type"][0]
    assert option_type_metric.value == "put"


def test_zero_time_shows_greeks_domain_error() -> None:
    at = AppTest.from_file(str(APP_PATH)).run()
    at.number_input(key="base_time").set_value(0.0)
    at.run()
    assert len(at.exception) == 0
    assert any("greeks_european" in e.value for e in at.error)


def test_zero_volatility_shows_greeks_domain_error() -> None:
    at = AppTest.from_file(str(APP_PATH)).run()
    at.number_input(key="base_vol").set_value(0.0)
    at.run()
    assert len(at.exception) == 0
    assert any("greeks_european" in e.value for e in at.error)


def test_valid_implied_volatility_produces_result() -> None:
    at = AppTest.from_file(str(APP_PATH)).run()
    labels = [m.label for m in at.metric]
    assert "Implied volatility (annualised decimal)" in labels
    iv = [m for m in at.metric if m.label == "Implied volatility (annualised decimal)"][0]
    assert iv.value not in (None, "")


def test_invalid_market_price_shows_error() -> None:
    at = AppTest.from_file(str(APP_PATH)).run()
    at.number_input(key="iv_market_price").set_value(0.0)
    at.run()
    assert len(at.exception) == 0
    assert any("no-arbitrage" in e.value or "lower bound" in e.value for e in at.error)


def test_payoff_grid_controls_produce_ordered_output() -> None:
    at = AppTest.from_file(str(APP_PATH)).run()
    assert at.number_input(key="payoff_min").value == 50.0
    assert at.number_input(key="payoff_max").value == 150.0
    assert at.number_input(key="payoff_points").value == 51


def test_scenario_controls_produce_ordered_output() -> None:
    at = AppTest.from_file(str(APP_PATH)).run()
    labels = [
        at.text_input(key="scenario_0_label").value,
        at.text_input(key="scenario_1_label").value,
        at.text_input(key="scenario_2_label").value,
    ]
    assert labels == ["Downside", "Base", "Upside"]
    assert at.number_input(key="scenario_0_spot").value == pytest.approx(90.0)
    assert at.number_input(key="scenario_1_spot").value == pytest.approx(100.0)
    assert at.number_input(key="scenario_2_spot").value == pytest.approx(110.0)
    assert at.number_input(key="scenario_count").value == 3


def test_zero_base_percentage_change_renders_undefined() -> None:
    at = AppTest.from_file(str(APP_PATH)).run()
    at.number_input(key="base_time").set_value(0.0)
    at.number_input(key="base_spot").set_value(10.0)
    at.number_input(key="base_strike").set_value(100.0)
    at.run()
    assert len(at.exception) == 0
    scenario_table = None
    for table in at.table:
        if "Percentage change" in list(table.value.columns):
            scenario_table = table.value
            break
    assert scenario_table is not None
    assert "undefined" in scenario_table["Percentage change"].tolist()


def test_no_traceback_for_expected_errors() -> None:
    at = AppTest.from_file(str(APP_PATH)).run()
    at.number_input(key="base_vol").set_value(0.0)
    at.run()
    assert len(at.exception) == 0
    assert all("Traceback" not in e.value for e in at.error)


def test_zero_volatility_price_produces_result() -> None:
    at = AppTest.from_file(str(APP_PATH)).run()
    at.number_input(key="base_vol").set_value(0.0)
    at.run()
    assert len(at.exception) == 0
    price = [m for m in at.metric if m.label == "Option price"]
    assert price and price[0].value not in (None, "")


def test_implied_volatility_solver_failure_shows_error() -> None:
    at = AppTest.from_file(str(APP_PATH)).run()
    at.number_input(key="iv_max_iter").set_value(1)
    at.number_input(key="iv_market_price").set_value(10.0)
    at.run()
    assert len(at.exception) == 0
    assert any("Calculation could not be completed" in e.value for e in at.error)


def test_finite_negative_rate_accepted() -> None:
    at = AppTest.from_file(str(APP_PATH)).run()
    at.number_input(key="base_rate").set_value(-0.05)
    at.run()
    assert len(at.exception) == 0
    price = [m for m in at.metric if m.label == "Option price"]
    assert price and price[0].value not in (None, "")


def test_finite_negative_dividend_yield_accepted() -> None:
    at = AppTest.from_file(str(APP_PATH)).run()
    at.number_input(key="base_div").set_value(-0.02)
    at.run()
    assert len(at.exception) == 0
    price = [m for m in at.metric if m.label == "Option price"]
    assert price and price[0].value not in (None, "")


# --------------------------------------------------------------------------- #
# Helper: additional validation branches
# --------------------------------------------------------------------------- #
def test_format_number_rejects_invalid_precision() -> None:
    with pytest.raises(TypeError):
        format_number(0.2, precision="x")  # type: ignore[arg-type]


def test_format_number_rejects_bool_precision() -> None:
    with pytest.raises(TypeError):
        format_number(0.2, precision=True)


def test_break_even_rejects_invalid_option_type() -> None:
    with pytest.raises(TypeError):
        break_even_price("CALL", 100.0, 7.0)  # type: ignore[arg-type]


def test_default_scenario_specs_rejects_non_int_count() -> None:
    with pytest.raises(TypeError):
        default_scenario_specs(100.0, 1.0, 0.2, 0.05, 0.02, "3")  # type: ignore[arg-type]


def test_default_scenario_specs_rejects_bool_count() -> None:
    with pytest.raises(TypeError):
        default_scenario_specs(100.0, 1.0, 0.2, 0.05, 0.02, True)


# --------------------------------------------------------------------------- #
# AppTest: invalid base assumptions
# --------------------------------------------------------------------------- #
def test_invalid_base_inputs_shows_error_and_skips_tabs() -> None:
    at = AppTest.from_file(str(APP_PATH)).run()
    # A zero spot makes the shared BlackScholesInputs invalid, so every tab must
    # skip its body and the base-error message must be shown.
    at.number_input(key="base_spot").set_value(0.0)
    at.run()
    assert len(at.exception) == 0
    assert any("Base assumptions are invalid" in e.value for e in at.error)
    price = [m for m in at.metric if m.label == "Option price"]
    assert price == []


def test_payoff_grid_min_greater_than_max_shows_error() -> None:
    at = AppTest.from_file(str(APP_PATH)).run()
    at.number_input(key="payoff_min").set_value(200.0)
    at.number_input(key="payoff_max").set_value(150.0)
    at.run()
    assert len(at.exception) == 0
    assert any("Calculation could not be completed" in e.value for e in at.error)


# --------------------------------------------------------------------------- #
# AppTest: widget state must not reset a user-edited derived default
# --------------------------------------------------------------------------- #
def test_edited_market_price_persists_across_unrelated_change() -> None:
    at = AppTest.from_file(str(APP_PATH)).run()
    at.number_input(key="iv_market_price").set_value(123.0)
    at.run()
    # Change an unrelated base widget; the user-edited market price must persist.
    at.number_input(key="base_spot").set_value(120.0)
    at.run()
    assert at.number_input(key="iv_market_price").value == 123.0


# --------------------------------------------------------------------------- #
# AppTest: every tab surfaces expected core errors without crashing
# --------------------------------------------------------------------------- #
def _boom(*_args: object, **_kwargs: object) -> object:
    raise ValueError("forced expected error")


def test_expected_errors_surfaced_price_and_iv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bsl, "price_european", _boom)
    at = AppTest.from_file(str(APP_PATH)).run()
    at.number_input(key="iv_market_price").set_value(10.0)
    at.run()
    assert len(at.exception) == 0
    assert len(at.error) >= 1
    assert all("Calculation could not be completed" in e.value for e in at.error)


def test_expected_errors_surfaced_payoff_expiry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bsl, "evaluate_expiry_scenarios", _boom)
    at = AppTest.from_file(str(APP_PATH)).run()
    assert len(at.exception) == 0
    assert len(at.error) >= 1
    assert all("Calculation could not be completed" in e.value for e in at.error)


def test_expected_errors_surfaced_payoff_break_even(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("demo.helpers.break_even_price", _boom)
    at = AppTest.from_file(str(APP_PATH)).run()
    assert len(at.exception) == 0
    assert len(at.error) >= 1
    assert all("Calculation could not be completed" in e.value for e in at.error)


def test_expected_errors_surfaced_scenario(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bsl, "evaluate_price_scenarios", _boom)
    at = AppTest.from_file(str(APP_PATH)).run()
    assert len(at.exception) == 0
    assert len(at.error) >= 1
    assert all("Calculation could not be completed" in e.value for e in at.error)
