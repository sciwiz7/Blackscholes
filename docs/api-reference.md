# Public API reference

This document lists every symbol exported from `blackscholeslab.__all__`. Each
entry states its exact name, category, purpose, parameters or fields, return
type, validation behaviour, relevant exceptions, important boundary behaviour,
and a small usage example or cross-link.

> The public surface is intentionally small. Internal helpers
> (`validate_inputs`, `validate_real_number`, `norm_cdf`, `_norm_pdf`,
> `_price_at_volatility`, `_no_arbitrage_bounds`, `_validate_solver_controls`)
> are private and are **not** part of this API. API stability is **not**
> promised before the first stable release (`1.0.0`).

## `OptionType` — enum

- **Category:** enum
- **Purpose:** identifies the type of a European option.
- **Members:** `OptionType.CALL` (`"call"`), `OptionType.PUT` (`"put"`).
- **Validation:** arbitrary strings, numbers, `None`, or booleans are rejected
  by the pricing/Greek/solver functions (`TypeError`).
- **Example:**

  ```python
  from blackscholeslab import OptionType
  option_type = OptionType.CALL
  ```

## `BlackScholesInputs` — model

- **Category:** model (frozen dataclass)
- **Purpose:** immutable, typed pricing inputs.
- **Fields:**
  - `spot: float` — current underlying price; strictly positive.
  - `strike: float` — exercise price; strictly positive.
  - `time_to_expiry: float` — time to expiry in years; non-negative (`0` = at expiry).
  - `risk_free_rate: float` — continuously compounded annual rate; finite, may be negative.
  - `volatility: float` — annualised volatility as a decimal; non-negative (`0` = deterministic path).
  - `dividend_yield: float` — continuously compounded annual dividend yield; finite, may be negative; default `0.0`.
- **Return type:** the instance itself.
- **Validation:** every field is validated on construction. `TypeError` for wrong
  types (bool, str, None, complex); `ValueError` for non-finite, non-positive
  `spot`/`strike`, negative `time_to_expiry`/`volatility`, or out-of-domain values.
- **Boundary behaviour:** at `time_to_expiry == 0` the price equals the intrinsic
  payoff; at `volatility == 0` (positive time) the deterministic discounted payoff
  is used.
- **Example:**

  ```python
  from blackscholeslab import BlackScholesInputs
  inputs = BlackScholesInputs(spot=100.0, strike=100.0, time_to_expiry=1.0,
                               risk_free_rate=0.05, volatility=0.20, dividend_yield=0.02)
  ```

## `price_european` — function

- **Category:** function
- **Purpose:** price a European option under Black-Scholes-Merton.
- **Parameters:** `inputs: BlackScholesInputs`, `option_type: OptionType`.
- **Return type:** `float` (the option price).
- **Exceptions:** `TypeError` if `option_type` is not a valid `OptionType`.
- **Boundary behaviour:** at expiry returns the intrinsic payoff; at zero
  volatility returns the exact deterministic discounted payoff; otherwise uses
  the standard d1/d2 formulas with continuous dividend yield.
- **Cross-link:** [pricing-and-greeks tutorial](tutorials/pricing-and-greeks.md),
  [mathematical conventions](mathematical-conventions.md).
- **Example:**

  ```python
  from blackscholeslab import price_european, OptionType
  price = price_european(inputs, OptionType.CALL)
  ```

## `OptionGreeks` — model

- **Category:** model (frozen dataclass)
- **Purpose:** immutable result model for the six analytical Greeks.
- **Fields:** `delta: float`, `gamma: float`, `vega: float`, `theta: float`,
  `rho: float`, `dividend_rho: float`. All are raw-unit values (see below).
- **Return type:** the instance itself.
- **Units / scaling:** delta = price change per 1 unit of spot; gamma = delta
  change per 1 unit of spot; vega = price change per **1.0** absolute change in
  volatility; theta = price change per **one year** of calendar time; rho =
  price change per **1.0** absolute change in rate; dividend rho = price change
  per **1.0** absolute change in yield. None are divided by 100 or 365.
- **Example:** produced by `greeks_european` (see below).

## `greeks_european` — function

- **Category:** function
- **Purpose:** compute the six analytical Greeks for a European option.
- **Parameters:** `inputs: BlackScholesInputs`, `option_type: OptionType`.
- **Return type:** `OptionGreeks`.
- **Exceptions:** `TypeError` for an invalid `option_type`; `ValueError` if
  `time_to_expiry == 0` or `volatility == 0` (Greeks are undefined there).
- **Boundary behaviour:** requires positive time to expiry and positive
  volatility; the base case must be valid Black-Scholes-Merton inputs.
- **Cross-link:** [pricing-and-greeks tutorial](tutorials/pricing-and-greeks.md),
  [mathematical conventions](mathematical-conventions.md).
- **Example:**

  ```python
  from blackscholeslab import greeks_european, OptionType
  greeks = greeks_european(inputs, OptionType.CALL)
  ```

## `ImpliedVolatilityInputs` — model

- **Category:** model (frozen dataclass)
- **Purpose:** immutable, typed market inputs for implied-volatility solving.
- **Fields:**
  - `market_price: float` — observed European option price; non-negative.
  - `spot: float` — strictly positive.
  - `strike: float` — strictly positive.
  - `time_to_expiry: float` — time to expiry in years; **strictly positive**
    (implied volatility is undefined at expiry).
  - `risk_free_rate: float` — finite, may be negative.
  - `dividend_yield: float` — finite, may be negative; default `0.0`.
- **Return type:** the instance itself.
- **Validation:** `TypeError`/`ValueError` for malformed or out-of-domain fields.
- **Example:**

  ```python
  from blackscholeslab import ImpliedVolatilityInputs
  iv_inputs = ImpliedVolatilityInputs(market_price=9.227005508154036, spot=100.0,
                                       strike=100.0, time_to_expiry=1.0,
                                       risk_free_rate=0.05, dividend_yield=0.02)
  ```

## `implied_volatility` — function

- **Category:** function
- **Purpose:** solve for the annualised implied volatility of a European option.
- **Parameters:**
  - `inputs: ImpliedVolatilityInputs`
  - `option_type: OptionType`
  - `price_tolerance: float = 1e-10` — absolute price tolerance.
  - `volatility_tolerance: float = 1e-12` — absolute volatility-interval tolerance.
  - `max_iterations: int = 200` — maximum bisection iterations.
  - `initial_upper_volatility: float = 0.5` — initial upper bracket (≤ `max_volatility`).
  - `max_volatility: float = 10.0` — maximum volatility before bracketing stops.
- **Return type:** `float` (annualised decimal volatility; not rounded).
- **Exceptions:** `TypeError` for wrong types; `ValueError` for invalid controls,
  an out-of-bounds `market_price`, or a market price above `max_volatility`;
  `RuntimeError` on non-convergence within `max_iterations`.
- **Boundary behaviour:** returns exactly `0.0` when `market_price` equals the
  zero-volatility lower bound; raises `ValueError` below the lower bound or at/above
  the upper bound; reuses `price_european` as the single pricing oracle.
- **Cross-link:** [implied-volatility tutorial](tutorials/implied-volatility.md),
  [mathematical conventions](mathematical-conventions.md).
- **Example:**

  ```python
  from blackscholeslab import implied_volatility, OptionType
  vol = implied_volatility(iv_inputs, OptionType.CALL)
  ```

## `ExpiryScenarioResult` — model

- **Category:** model (frozen dataclass)
- **Purpose:** immutable result of an expiry payoff/P&L evaluation for one price.
- **Fields:** `underlying_price: float`, `payoff: float`, `profit_loss: float`.
- **Return type:** the instance itself.
- **Cross-link:** produced by `evaluate_expiry_scenarios`.

## `intrinsic_payoff` — function

- **Category:** function
- **Purpose:** intrinsic expiry payoff of a European option.
- **Parameters:** `underlying_price: float` (≥ 0), `strike: float` (> 0),
  `option_type: OptionType`.
- **Return type:** `float` (non-negative).
- **Exceptions:** `TypeError`/`ValueError` for invalid types or non-finite /
  negative `underlying_price` / non-positive `strike`.
- **Definition:** call `max(S - K, 0)`; put `max(K - S, 0)`.
- **Cross-link:** [payoff-and-scenarios tutorial](tutorials/payoff-and-scenarios.md).
- **Example:**

  ```python
  from blackscholeslab import intrinsic_payoff, OptionType
  payoff = intrinsic_payoff(underlying_price=120.0, strike=100.0, option_type=OptionType.CALL)
  ```

## `expiry_profit_loss` — function

- **Category:** function
- **Purpose:** expiry profit and loss of a long European option.
- **Parameters:** `underlying_price: float`, `strike: float`, `option_type: OptionType`,
  `premium: float` (≥ 0, the amount paid for one unit).
- **Return type:** `float` (`intrinsic_payoff(...) - premium`).
- **Exceptions:** `TypeError`/`ValueError` for invalid inputs or a negative premium.
- **Semantics:** long option, one unit, no discounting, no multiplier, no inferred
  short position; minimum P&L is `-premium`.
- **Example:**

  ```python
  from blackscholeslab import expiry_profit_loss, OptionType
  pnl = expiry_profit_loss(underlying_price=120.0, strike=100.0,
                           option_type=OptionType.CALL, premium=7.0)
  ```

## `evaluate_expiry_scenarios` — function

- **Category:** function
- **Purpose:** evaluate intrinsic payoff and expiry P&L over supplied underlying prices.
- **Parameters:** `underlying_prices: Iterable[float]`, `strike: float`,
  `option_type: OptionType`, `premium: float = 0.0`.
- **Return type:** `tuple[ExpiryScenarioResult, ...]` (immutable, in input order).
- **Exceptions:** `TypeError`/`ValueError` for an empty iterable, invalid items, or
  invalid scalars; an invalid item reports its zero-based index.
- **Boundary behaviour:** order and duplicate prices are preserved exactly; the
  iterable is consumed once.
- **Cross-link:** [payoff-and-scenarios tutorial](tutorials/payoff-and-scenarios.md).
- **Example:**

  ```python
  from blackscholeslab import evaluate_expiry_scenarios, OptionType
  results = evaluate_expiry_scenarios([80.0, 100.0, 120.0], 100.0, OptionType.CALL, premium=7.0)
  ```

## `OptionScenario` — model

- **Category:** model (frozen dataclass)
- **Purpose:** immutable pre-expiry scenario definition for one repricing.
- **Fields:** `spot: float` (> 0), `time_to_expiry: float` (≥ 0), `volatility: float`
  (≥ 0), `risk_free_rate: float` (finite, may be negative), `dividend_yield: float`
  (finite, may be negative; default `0.0`), `label: str | None` (optional).
- **Return type:** the instance itself.
- **Validation:** `TypeError`/`ValueError` for malformed fields; `label` must be a
  `str` or `None` (empty string allowed).
- **Example:** produced for `evaluate_price_scenarios`.

## `ScenarioPriceResult` — model

- **Category:** model (frozen dataclass)
- **Purpose:** immutable price result for one pre-expiry scenario.
- **Fields:** `scenario: OptionScenario`, `option_price: float`,
  `price_change: float` (`option_price - base_price`),
  `percentage_change: float | None` (decimal return; `None` when base price is `0.0`).
- **Return type:** the instance itself.
- **Cross-link:** produced by `evaluate_price_scenarios`.

## `evaluate_price_scenarios` — function

- **Category:** function
- **Purpose:** reprice a European option under pre-expiry scenario assumptions.
- **Parameters:** `base_inputs: BlackScholesInputs`, `option_type: OptionType`,
  `scenarios: Iterable[OptionScenario]`.
- **Return type:** `tuple[ScenarioPriceResult, ...]` (immutable, in input order).
- **Exceptions:** `TypeError`/`ValueError` for invalid `base_inputs`, an invalid
  `option_type`, an empty `scenarios`, or a non-`OptionScenario` item; `RuntimeError`
  re-raised from `price_european` for numerically invalid assumptions.
- **Boundary behaviour:** the strike is fixed from `base_inputs` across all
  scenarios; order and duplicates are preserved; `percentage_change` is `None`
  when the base price is exactly `0.0`; expiry and zero-volatility boundaries are
  inherited from `price_european`.
- **Cross-link:** [payoff-and-scenarios tutorial](tutorials/payoff-and-scenarios.md).
- **Example:**

  ```python
  from blackscholeslab import OptionScenario, evaluate_price_scenarios, OptionType
  scenarios = [OptionScenario(spot=110.0, time_to_expiry=1.0, volatility=0.20,
                              risk_free_rate=0.05, dividend_yield=0.02, label="up")]
  results = evaluate_price_scenarios(inputs, OptionType.CALL, scenarios)
  ```

## `__version__` — metadata

- **Category:** metadata (str)
- **Value:** `"0.1.0"` (release candidate; not yet published to PyPI).
- **Example:** `blackscholeslab.__version__`.

## `__author__` — metadata

- **Category:** metadata (str)
- **Value:** `"Amrut Deshmukh"`.

## `__license__` — metadata

- **Category:** metadata (str)
- **Value:** `"MIT"`.

## See also

- [Documentation index](index.md)
- [Architecture](architecture.md)
- [Mathematical conventions](mathematical-conventions.md)
- [Command-line tutorial](tutorials/command-line-interface.md)
- [Interactive-demo tutorial](tutorials/interactive-demo.md)
