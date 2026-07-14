# Tutorial: interactive demonstration

BlackScholesLab includes an optional, browser-based Streamlit demonstration
(`demo/`). It is an educational view over the existing public core APIs: it
performs **no financial mathematics of its own** and makes **no network calls**,
uses **no live market data**, requires **no account or authentication**, and
stores **no user data**.

## Installation

The demonstration depends only on Streamlit, isolated in the `demo` extra so the
core runtime dependencies remain empty:

```bash
python -m pip install -e ".[dev,demo]"
```

or, to also get the development tools:

```bash
python -m pip install -e ".[dev,demo]"
```

## Launch

```bash
streamlit run demo/app.py
```

Telemetry (usage statistics) is disabled in `.streamlit/config.toml`; the
configuration contains no secrets or deployment credentials and no permissive
cross-origin or security settings. The demonstration is intended to run
**locally** and is **not** hosted publicly anywhere.

## What you see

The app renders **five tabs**:

1. **Price** — European call and put prices from `price_european`.
2. **Greeks** — the six analytical Greeks (delta, gamma, vega, annual theta, rho,
   dividend rho) from `greeks_european`.
3. **Implied volatility** — implied volatility solving from `implied_volatility`,
   with the annualised decimal result, an explicitly labelled percent display,
   the repriced value, and the absolute repricing residual.
4. **Expiry payoff** — intrinsic payoff and long-option profit/loss from
   `evaluate_expiry_scenarios`, with a deterministic inclusive grid, an ordered
   table, a native line chart, and maximum-loss / break-even explanations.
5. **Scenario analysis** — pre-expiry scenario repricing from
   `evaluate_price_scenarios`, with the strike fixed from the base option.

## Sidebar inputs

All calculations share a base set of assumptions entered in the sidebar:

- Option type (Call / Put)
- Spot price
- Strike price
- Time to expiry (years)
- Risk-free rate (annualised decimal)
- Volatility (annualised decimal)
- Dividend yield (annualised decimal)

**Annualised decimal units.** Every rate and volatility input is an annualised
decimal (for example `0.05` is a 5% rate and `0.20` is 20% volatility). The
demonstration does not accept percentage strings and does not scale inputs.

## Raw Greek units

The Greeks tab shows the same raw decimal units as `greeks_european`:

- vega is the price change for an absolute `1.0` change in volatility;
- rho and dividend rho are for an absolute `1.0` change in rate or yield;
- theta is annual (per one year of calendar time).

Values are **not** divided by 100 or 365.

## Implied-volatility controls

The Implied volatility tab exposes the public solver defaults and lets you
adjust the price tolerance, volatility tolerance, maximum iterations, initial
upper volatility, and maximum volatility. The percent value shown is the decimal
result multiplied by `100` purely for display; the value passed back into the
pricing API remains the raw decimal.

## Long-option premium interpretation

The Expiry payoff tab treats the premium as the amount paid for **one option
unit**: no contract multiplier or position quantity is assumed, no discounting
is applied, and short positions are not inferred. The break-even underlying price
(`strike ± premium`) is explanatory arithmetic only.

## Scenario ordering and percentage change

In the Scenario analysis tab, scenario order and duplicates are preserved, the
strike stays fixed from the base option, and the percentage change is a decimal
return (`price_change / base_price`). When the base option price is exactly
`0.0`, the demonstration displays `undefined` rather than substituting zero or
infinity.

## Expected-error presentation

Expected user/domain errors (`TypeError`, `ValueError`, `RuntimeError` from
implied-volatility non-convergence, and `OverflowError` from extreme
standard-library exponentials) are caught and shown as concise `st.error`
messages without raw tracebacks. Unexpected internal failures remain visible
during development and testing.

## Limitations

- The demonstration is **local-only** and is **not** hosted publicly.
- It provides **no financial recommendations** and uses **no live or historical
  market data**; all inputs are supplied by you through the interface.
- It must not be used for trading or investment decisions without independent
  verification.

> **Educational only.** BlackScholesLab is not financial advice.
