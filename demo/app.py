"""Optional, educational Streamlit demonstration for BlackScholesLab.

This application is a thin, browser-based view over the existing public
BlackScholesLab APIs. It performs no financial mathematics of its own: every
price, Greek, implied volatility, payoff, and scenario value is produced by the
authoritative core functions. The demonstration:

- uses only the existing public BlackScholesLab APIs;
- contains no duplicated financial formulas;
- makes no network calls and uses no live market data;
- requires no account or authentication and stores no user data;
- provides no financial recommendations;
- preserves the project's deterministic behaviour;
- surfaces expected domain errors clearly without raw tracebacks.

Launch with: ``streamlit run demo/app.py``
"""

from __future__ import annotations

import streamlit as st

from blackscholeslab import (
    BlackScholesInputs,
    ExpiryScenarioResult,
    ImpliedVolatilityInputs,
    OptionGreeks,
    OptionScenario,
    OptionType,
    ScenarioPriceResult,
    evaluate_expiry_scenarios,
    evaluate_price_scenarios,
    greeks_european,
    implied_volatility,
    price_european,
)
from demo.helpers import (
    break_even_price,
    default_scenario_specs,
    expiry_chart_data,
    expiry_rows,
    format_number,
    inclusive_grid,
    option_type_from_label,
    scenario_rows,
)

EXPECTED_ERRORS = (TypeError, ValueError, RuntimeError, OverflowError)

GREEK_UNIT_NOTE = (
    "Units are raw and not divided by 100 or 365. Vega is the price change for an "
    "absolute 1.0 change in volatility. Rho and dividend rho are for an absolute "
    "1.0 change in rate or yield. Theta is annual (per one year of calendar time)."
)

SIDEBAR_EXPLANATION = (
    "All rates and volatility are annualised decimal units. For example, "
    "0.20 volatility means 20% and 0.05 rate means 5%. Values are not converted "
    "from percentages automatically."
)


def show_expected_error(error: Exception) -> None:
    """Render an expected user/domain error without a raw traceback."""
    st.error(f"Calculation could not be completed: {error}")


def build_base_inputs() -> tuple[BlackScholesInputs | None, OptionType | None, str | None]:
    """Build the shared base inputs and option type from the sidebar widgets.

    Returns:
        A tuple of ``(inputs, option_type, error_message)``. When construction
        fails, ``inputs`` and ``option_type`` are ``None`` and ``error_message``
        explains the failure.
    """
    try:
        option_type = option_type_from_label(st.session_state["opt_type"])
        inputs = BlackScholesInputs(
            spot=float(st.session_state["base_spot"]),
            strike=float(st.session_state["base_strike"]),
            time_to_expiry=float(st.session_state["base_time"]),
            risk_free_rate=float(st.session_state["base_rate"]),
            volatility=float(st.session_state["base_vol"]),
            dividend_yield=float(st.session_state["base_div"]),
        )
    except EXPECTED_ERRORS as exc:
        return None, None, str(exc)
    return inputs, option_type, None


def render_sidebar() -> None:
    """Render the shared base-option assumptions in the sidebar."""
    st.sidebar.header("Base option assumptions")
    st.sidebar.selectbox(
        "Option type",
        options=["Call", "Put"],
        index=0,
        key="opt_type",
    )
    st.sidebar.number_input("Spot price", min_value=0.0, value=100.0, step=1.0, key="base_spot")
    st.sidebar.number_input("Strike price", min_value=0.0, value=100.0, step=1.0, key="base_strike")
    st.sidebar.number_input(
        "Time to expiry (years)", min_value=0.0, value=1.0, step=0.1, key="base_time"
    )
    st.sidebar.number_input(
        "Risk-free rate (annualised decimal)",
        value=0.05,
        step=0.01,
        key="base_rate",
    )
    st.sidebar.number_input(
        "Volatility (annualised decimal)", min_value=0.0, value=0.20, step=0.01, key="base_vol"
    )
    st.sidebar.number_input(
        "Dividend yield (annualised decimal)", value=0.02, step=0.01, key="base_div"
    )
    st.sidebar.caption(SIDEBAR_EXPLANATION)


def render_price_tab(inputs: BlackScholesInputs, option_type: OptionType) -> None:
    """Render the Price tab."""
    st.subheader("European option price")
    try:
        price = price_european(inputs, option_type)
        st.metric("Option price", format_number(price))
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Option type", option_type.value)
        col_b.metric("Spot", format_number(inputs.spot))
        col_c.metric("Strike", format_number(inputs.strike))
        col_d, col_e, col_f = st.columns(3)
        col_d.metric("Time to expiry", format_number(inputs.time_to_expiry))
        col_e.metric("Volatility", format_number(inputs.volatility))
        col_f.metric("Risk-free rate", format_number(inputs.risk_free_rate))
        st.metric("Dividend yield", format_number(inputs.dividend_yield))
        st.caption(
            "At expiry the price equals the intrinsic payoff. At zero volatility before "
            "expiry, the deterministic discounted boundary is used. The model assumes a "
            "European option with continuous compounding."
        )
    except EXPECTED_ERRORS as exc:
        show_expected_error(exc)


def render_greeks_tab(inputs: BlackScholesInputs, option_type: OptionType) -> None:
    """Render the Greeks tab."""
    st.subheader("Analytical Greeks")
    try:
        greeks: OptionGreeks = greeks_european(inputs, option_type)
        col1, col2, col3 = st.columns(3)
        col1.metric("Delta", format_number(greeks.delta))
        col2.metric("Gamma", format_number(greeks.gamma))
        col3.metric("Vega", format_number(greeks.vega))
        col4, col5, col6 = st.columns(3)
        col4.metric("Theta", format_number(greeks.theta))
        col5.metric("Rho", format_number(greeks.rho))
        col6.metric("Dividend rho", format_number(greeks.dividend_rho))
        st.caption(GREEK_UNIT_NOTE)
        st.caption(
            "Greeks require positive time to expiry and positive volatility. When the "
            "base assumptions set either to zero, the core API rejects the request and "
            "the result is shown as a domain error rather than a fabricated value."
        )
    except EXPECTED_ERRORS as exc:
        show_expected_error(exc)


def render_implied_volatility_tab(inputs: BlackScholesInputs, option_type: OptionType) -> None:
    """Render the Implied volatility tab."""
    st.subheader("Implied volatility")
    st.markdown("Solve for the annualised implied volatility implied by an observed price.")

    market_default = 0.0
    try:
        market_default = price_european(inputs, option_type)
    except EXPECTED_ERRORS:
        market_default = 0.0

    market_price = st.number_input(
        "Observed market price",
        min_value=0.0,
        value=float(market_default),
        step=0.1,
        key="iv_market_price",
    )
    c1, c2 = st.columns(2)
    price_tol = c1.number_input(
        "Price tolerance",
        min_value=1e-14,
        value=1e-10,
        step=1e-10,
        format="%.1e",
        key="iv_price_tol",
    )
    vol_tol = c2.number_input(
        "Volatility tolerance",
        min_value=1e-14,
        value=1e-12,
        step=1e-12,
        format="%.1e",
        key="iv_vol_tol",
    )
    c3, c4, c5 = st.columns(3)
    max_iter = int(
        c3.number_input("Maximum iterations", min_value=1, value=200, step=1, key="iv_max_iter")
    )
    init_upper = c4.number_input(
        "Initial upper volatility", min_value=1e-6, value=0.5, step=0.1, key="iv_initial_upper"
    )
    max_vol = c5.number_input(
        "Maximum volatility", min_value=1e-6, value=10.0, step=0.5, key="iv_max_vol"
    )

    try:
        iv_inputs = ImpliedVolatilityInputs(
            market_price=float(market_price),
            spot=inputs.spot,
            strike=inputs.strike,
            time_to_expiry=inputs.time_to_expiry,
            risk_free_rate=inputs.risk_free_rate,
            dividend_yield=inputs.dividend_yield,
        )
        solved = implied_volatility(
            iv_inputs,
            option_type,
            price_tolerance=float(price_tol),
            volatility_tolerance=float(vol_tol),
            max_iterations=max_iter,
            initial_upper_volatility=float(init_upper),
            max_volatility=float(max_vol),
        )
    except EXPECTED_ERRORS as exc:
        show_expected_error(exc)
        return

    st.metric("Implied volatility (annualised decimal)", format_number(solved))
    st.metric("Implied volatility (percent)", format_number(solved * 100.0, precision=4))
    st.caption(
        "The percent value is the decimal result multiplied by 100 purely for display. "
        "The value passed back into the pricing API is the raw decimal."
    )

    try:
        repriced = price_european(
            BlackScholesInputs(
                spot=inputs.spot,
                strike=inputs.strike,
                time_to_expiry=inputs.time_to_expiry,
                risk_free_rate=inputs.risk_free_rate,
                volatility=solved,
                dividend_yield=inputs.dividend_yield,
            ),
            option_type,
        )
        residual = repriced - float(market_price)
        c6, c7 = st.columns(2)
        c6.metric("Repriced option value", format_number(repriced))
        c7.metric("Absolute repricing residual", format_number(abs(residual)))
    except EXPECTED_ERRORS as exc:
        show_expected_error(exc)

    st.caption(
        "No-arbitrage policy: below the lower bound the price is invalid; equal to the "
        "lower bound the implied volatility is exactly zero; at or above the upper bound "
        "no finite implied volatility exists. The solver is the single source of truth."
    )


def render_expiry_payoff_tab(inputs: BlackScholesInputs, option_type: OptionType) -> None:
    """Render the Expiry payoff tab."""
    st.subheader("Expiry payoff and long-option profit/loss")

    premium_default = 0.0
    try:
        premium_default = price_european(inputs, option_type)
    except EXPECTED_ERRORS:
        premium_default = 0.0

    premium = st.number_input(
        "Premium paid per option unit",
        min_value=0.0,
        value=float(premium_default),
        step=0.1,
        key="payoff_premium",
    )
    c1, c2, c3 = st.columns(3)
    min_underlying = float(
        c1.number_input(
            "Minimum expiry underlying price",
            min_value=0.0,
            value=float(max(0.0, inputs.spot * 0.5)) if inputs is not None else 0.0,
            step=1.0,
            key="payoff_min",
        )
    )
    max_underlying = float(
        c2.number_input(
            "Maximum expiry underlying price",
            min_value=0.0,
            value=float(inputs.spot * 1.5) if inputs is not None else 150.0,
            step=1.0,
            key="payoff_max",
        )
    )
    points = int(
        c3.number_input(
            "Number of evaluation points",
            min_value=2,
            max_value=501,
            value=51,
            step=1,
            key="payoff_points",
        )
    )

    try:
        grid = inclusive_grid(min_underlying, max_underlying, points)
    except EXPECTED_ERRORS as exc:
        show_expected_error(exc)
        return

    try:
        results: tuple[ExpiryScenarioResult, ...] = evaluate_expiry_scenarios(
            grid, inputs.strike, option_type, premium=float(premium)
        )
    except EXPECTED_ERRORS as exc:
        show_expected_error(exc)
        return

    st.table(expiry_rows(results))
    st.line_chart(expiry_chart_data(results))

    if option_type is OptionType.CALL:
        max_loss = f"-{format_number(float(premium))}"
    else:
        max_loss = f"-{format_number(float(premium))}"
    st.markdown(f"**Maximum loss (long option):** {max_loss} per unit (the premium paid).")

    try:
        break_even = break_even_price(option_type, inputs.strike, float(premium))
        if option_type is OptionType.CALL:
            st.markdown(
                f"**Break-even underlying price:** {format_number(break_even)} "
                f"(strike {format_number(inputs.strike)} + premium "
                f"{format_number(float(premium))})."
            )
        else:
            st.markdown(
                f"**Break-even underlying price:** {format_number(break_even)} "
                f"(strike {format_number(inputs.strike)} - premium "
                f"{format_number(float(premium))})."
            )
    except EXPECTED_ERRORS as exc:
        show_expected_error(exc)

    st.caption(
        "This is one long option unit. No quantity or contract multiplier is assumed. "
        "No transaction cost or tax is included. The premium is treated as the amount "
        "paid. Payoff and profit/loss values come from the public payoff APIs; the "
        "break-even figure is educational arithmetic only."
    )


def render_scenario_tab(inputs: BlackScholesInputs, option_type: OptionType) -> None:
    """Render the Scenario analysis tab."""
    st.subheader("Pre-expiry scenario analysis")
    st.markdown(
        "Reprice the option under alternative assumptions. The strike stays fixed "
        "at the base value."
    )

    count = int(
        st.number_input(
            "Number of scenarios", min_value=1, max_value=5, value=3, step=1, key="scenario_count"
        )
    )

    specs = default_scenario_specs(
        base_spot=inputs.spot,
        base_time=inputs.time_to_expiry,
        base_volatility=inputs.volatility,
        base_rate=inputs.risk_free_rate,
        base_dividend=inputs.dividend_yield,
        count=count,
    )

    scenarios: list[OptionScenario] = []
    for index, spec in enumerate(specs):
        st.markdown(f"**Scenario {index + 1}**")
        c1, c2 = st.columns(2)
        label = c1.text_input("Label", value=spec.label, key=f"scenario_{index}_label")
        spot = float(
            c2.number_input(
                "Scenario spot",
                min_value=0.0,
                value=spec.spot,
                step=1.0,
                key=f"scenario_{index}_spot",
            )
        )
        c3, c4 = st.columns(2)
        time_to_expiry = float(
            c3.number_input(
                "Scenario time to expiry",
                min_value=0.0,
                value=spec.time_to_expiry,
                step=0.1,
                key=f"scenario_{index}_time",
            )
        )
        volatility = float(
            c4.number_input(
                "Scenario volatility",
                min_value=0.0,
                value=spec.volatility,
                step=0.01,
                key=f"scenario_{index}_vol",
            )
        )
        c5, c6 = st.columns(2)
        rate = float(
            c5.number_input(
                "Scenario risk-free rate",
                value=spec.risk_free_rate,
                step=0.01,
                key=f"scenario_{index}_rate",
            )
        )
        dividend = float(
            c6.number_input(
                "Scenario dividend yield",
                value=spec.dividend_yield,
                step=0.01,
                key=f"scenario_{index}_div",
            )
        )
        scenarios.append(
            OptionScenario(
                spot=spot,
                time_to_expiry=time_to_expiry,
                volatility=volatility,
                risk_free_rate=rate,
                dividend_yield=dividend,
                label=label,
            )
        )

    try:
        results: tuple[ScenarioPriceResult, ...] = evaluate_price_scenarios(
            inputs, option_type, scenarios
        )
    except EXPECTED_ERRORS as exc:
        show_expected_error(exc)
        return

    st.table(scenario_rows(results))
    st.caption(
        "The strike remains fixed from the base option. Scenario order and duplicate "
        "scenarios are preserved. Percentage change is a decimal return "
        "(price_change / base price); it is shown as 'undefined' when the base price "
        "is exactly zero."
    )


def main() -> None:
    """Render the BlackScholesLab interactive demonstration."""
    st.set_page_config(
        page_title="BlackScholesLab Interactive Demo",
        page_icon="📈",
        layout="wide",
    )

    st.title("BlackScholesLab")
    st.markdown(
        "An educational, browser-based demonstration of European-option analytics: "
        "prices, analytical Greeks, implied volatility, expiry payoff, and pre-expiry "
        "scenarios."
    )
    st.warning(
        "Educational demonstration only. Results are not financial advice and must not "
        "be used for trading or investment decisions without independent verification."
    )
    st.info(
        "Rates and volatility use annualised decimal units (for example 0.20 volatility "
        "means 20% and 0.05 rate means 5%)."
    )

    render_sidebar()
    inputs, option_type, base_error = build_base_inputs()
    if base_error is not None:
        st.error(f"Base assumptions are invalid: {base_error}")

    tab_price, tab_greeks, tab_iv, tab_payoff, tab_scenario = st.tabs(
        ["Price", "Greeks", "Implied volatility", "Expiry payoff", "Scenario analysis"]
    )

    with tab_price:
        if inputs is not None and option_type is not None:
            render_price_tab(inputs, option_type)
    with tab_greeks:
        if inputs is not None and option_type is not None:
            render_greeks_tab(inputs, option_type)
    with tab_iv:
        if inputs is not None and option_type is not None:
            render_implied_volatility_tab(inputs, option_type)
    with tab_payoff:
        if inputs is not None and option_type is not None:
            render_expiry_payoff_tab(inputs, option_type)
    with tab_scenario:
        if inputs is not None and option_type is not None:
            render_scenario_tab(inputs, option_type)


if __name__ == "__main__":
    main()
