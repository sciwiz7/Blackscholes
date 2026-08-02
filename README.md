# BlackScholesLab

A transparent and carefully tested Python toolkit for European option pricing,
analytical Greeks, implied-volatility calculation, and scenario analysis based on
the Black-Scholes framework. Every calculation is deterministic and reproducible,
and the mathematics is documented and inspectable.

> **Status: release candidate (`0.1.0`), not yet published.** The European call
> and put pricing core, analytical Greeks, implied-volatility solving, payoff and
> scenario analysis, a command-line interface, and an optional interactive
> Streamlit demonstration are implemented and tested. The project remains
> **unreleased** and **has not been published to PyPI**; publication is pending
> explicit human approval. Do not rely on it for calculations until a stable
> release is published.

## Implemented capabilities (release candidate)

- European call and put pricing (Black-Scholes-Merton, continuous dividend yield).
- Analytical Greeks: delta, gamma, vega, annual theta, rho, dividend rho.
- Implied-volatility solving with European no-arbitrage bounds and finite negative
  rates/yields.
- Payoff and scenario analysis: intrinsic payoff, long-option expiry P&L, signed
  multi-leg strategy payoff profiles, ordered expiry scenarios, and fixed-strike
  pre-expiry scenario repricing.
- A command-line interface (`blackscholeslab`) with human-readable and
  deterministic JSON output.
- An optional interactive Streamlit demonstration (`demo/`) over the public APIs.

## Payoff API scopes

BlackScholesLab intentionally separates three related payoff/scenario APIs:

- `evaluate_expiry_scenarios` evaluates one long European option across supplied
  expiry underlying prices. It returns `ExpiryScenarioResult` rows containing
  `underlying_price`, intrinsic `payoff`, and long-option `profit_loss`.
- `strategy_payoff` aggregates signed `OptionLeg` and `UnderlyingLeg` objects at
  one expiry spot. It returns one `PayoffPoint` containing `spot_at_expiry`,
  aggregate `gross_payoff`, and aggregate `net_profit`.
- `evaluate_strategy_profile` applies the same multi-leg strategy aggregation
  across caller-supplied expiry spot prices, preserving input order and
  duplicates.

The strategy APIs are expiry-only. They do not model dividends, financing costs,
borrow fees, transaction costs, taxes, margin mechanics, assignment, pre-expiry
pricing, charts, or contract multipliers.

## Requirements

- Python **3.11 or newer** (`requires-python = ">=3.11"`).

## Installation

There is no published release. Install from source.

```bash
# Core + development tools
python -m pip install -e ".[dev]"

# Also include the interactive demonstration (Streamlit is isolated in the demo extra)
python -m pip install -e ".[dev,demo]"
```

The core runtime dependencies remain empty; Streamlit is confined to the optional
`demo` extra.

## Minimal Python quick start

```python
from blackscholeslab import (
    BlackScholesInputs,
    OptionType,
    price_european,
)

inputs = BlackScholesInputs(
    spot=100.0,
    strike=100.0,
    time_to_expiry=1.0,
    risk_free_rate=0.05,
    volatility=0.20,
    dividend_yield=0.02,
)
call_price = price_european(inputs, OptionType.CALL)
put_price = price_european(inputs, OptionType.PUT)
```

Worked tutorials (Greeks, implied volatility, payoff, scenarios, CLI, demo):
see [docs/index.md](docs/index.md) and the linked tutorials.

## Minimal CLI quick start

```bash
blackscholeslab price \
  --type call \
  --spot 100 --strike 100 --time 1 --rate 0.05 --volatility 0.20 --dividend-yield 0.02
```

Every rate and volatility is an **annualised decimal** (`0.05` = 5%, `0.20` = 20%).
Add `--json` for deterministic JSON output.

## Interactive demonstration

```bash
streamlit run demo/app.py
```

The demonstration is a local, educational view over the public APIs. It makes no
network calls, uses no live market data, stores no user data, and provides no
financial recommendations. Telemetry is disabled in `.streamlit/config.toml`. See
[docs/tutorials/interactive-demo.md](docs/tutorials/interactive-demo.md).

## Tests

```bash
pytest
```

This runs the full suite with branch coverage (core and demo) and the
documentation validation tests.

## Documentation

- [Documentation index](docs/index.md)
- [API reference](docs/api-reference.md)
- [Tutorials](docs/index.md#tutorials)
- [Mathematical conventions](docs/mathematical-conventions.md)
- [Architecture](docs/architecture.md)
- [Development](docs/development.md)

## Limitations

- European options only; American exercise, barriers, and exotics are out of scope.
- No transaction costs, taxes, multipliers, margin, assignment, or exercise
  mechanics are modelled.
- The project is educational; it is **not** financial advice.

## Licence

BlackScholesLab is released under the [MIT Licence](LICENSE).

## Disclaimer

BlackScholesLab is educational and analytical software. It is **not** financial
advice and must not be used for trading or investment decisions without
independent verification. The authors accept no liability for any use of this
software.
