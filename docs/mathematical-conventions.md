# Mathematical conventions

This document records the mathematical conventions used by the implemented
Black-Scholes-Merton European pricing core, implied-volatility solver, payoff
analysis, and pre-expiry scenario analysis in BlackScholesLab. Items marked
**Unresolved** concern future capabilities and are not settled by this
implementation.

## Market inputs

| Symbol | Meaning | Unit | Notes |
| ------ | ------- | ---- | ----- |
| `S` | Spot price of the underlying | currency | Must be strictly positive. |
| `K` | Strike price | currency | Must be strictly positive. |
| `T` | Time to expiry | years | Must be non-negative. `T = 0` means at expiry. |
| `r` | Continuously compounded risk-free rate | decimal per year | May be negative (finite). |
| `q` | Continuously compounded dividend yield | decimal per year | Defaults to `0`. May be negative (finite). |
| `sigma` | Annualised volatility | decimal per year | Must be non-negative. `0` selects the deterministic path. |

### Spot price
`S` is the current price of the underlying asset, expressed in the same currency
as `K`. It must be strictly positive.

### Strike price
`K` is the agreed exercise price. It must be strictly positive.

### Time to expiry
`T` is measured in **years** as a non-negative real number. A value of
`T = 0` places the option at expiry, where pricing reduces to the intrinsic
payoff.

### Continuously compounded risk-free rate
`r` is the annual risk-free rate under continuous compounding. The toolkit
assumes continuous compounding throughout; discrete compounding conventions are
out of scope. `r` must be finite and may be negative in unusual markets.

### Continuous dividend yield
`q` is the annual continuous dividend yield of the underlying. It defaults to
`0` when omitted, representing a non-dividend-paying asset. `q` must be finite
and may be negative.

### Annualised volatility
`sigma` is the annualised standard deviation of the underlying return, expressed
as a decimal (for example `0.20` for 20%). It must be non-negative. A value of
`sigma = 0` is explicitly supported and selects the deterministic
discounted-payoff path rather than the regular d1/d2 formula.

## Option types

The toolkit prices **European** options only. European options may be exercised
solely at expiry.

- **European call**: right to buy the underlying at `K` at expiry.
- **European put**: right to sell the underlying at `K` at expiry.

American exercise, barriers, and other exotic features are out of scope.

## Standard normal cumulative distribution function

The standard normal CDF `N(x)` is implemented internally with `math.erf`:

```
N(x) = 0.5 * (1 + erf(x / sqrt(2)))
```

It is a pure standard-library helper and is not part of the public API.

## Black-Scholes-Merton formulas (European, continuous dividend yield)

For `T > 0` and `sigma > 0`:

```
d1 = [ ln(S / K) + (r - q + 0.5 * sigma^2) * T ] / (sigma * sqrt(T))

d2 = d1 - sigma * sqrt(T)
```

Call price:

```
C = S * exp(-q * T) * N(d1) - K * exp(-r * T) * N(d2)
```

Put price:

```
P = K * exp(-r * T) * N(-d2) - S * exp(-q * T) * N(-d1)
```

where `N` is the standard normal CDF.

## Behaviour at expiry

When `T = 0`, the option value equals its intrinsic payoff:

- Call: `max(S - K, 0)`
- Put: `max(K - S, 0)`

At expiry, `r`, `q`, and `sigma` do not affect the result. This is tested as a
hard boundary condition.

## Zero-volatility behaviour

When `sigma = 0` and `T > 0`, the regular d1/d2 formula would divide by zero.
Instead, the exact deterministic discounted payoff is used:

Call:

```
max( S * exp(-q * T) - K * exp(-r * T), 0 )
```

Put:

```
max( K * exp(-r * T) - S * exp(-q * T), 0 )
```

Zero volatility is supported explicitly; the implementation does **not** replace
it with an epsilon.

## Implied volatility

The `implied_volatility` solver recovers the annualised volatility `sigma` that
makes `price_european` match an observed `market_price`. It is deterministic and
reuses `price_european` as its single pricing oracle; it never reimplements the
pricing formula.

### Market price

`market_price` is the observed European option price (currency). It is a single
scalar and must be non-negative.

### Annualised decimal volatility output

The solver returns `sigma` as an **annualised decimal** volatility (for example
`0.20` for 20%), expressed in calendar years. No percentage scaling is applied
to the output, and the value is not rounded.

### European no-arbitrage bounds

For `S = spot`, `K = strike`, `T = time_to_expiry`, `r = risk_free_rate`,
`q = dividend_yield`:

```
discounted_spot   = S * exp(-q * T)
discounted_strike = K * exp(-r * T)
```

Call bounds:

```
lower_call = max(discounted_spot - discounted_strike, 0)
upper_call = discounted_spot
```

Put bounds:

```
lower_put = max(discounted_strike - discounted_spot, 0)
upper_put = discounted_strike
```

The solver validates `market_price` before solving:

- If `market_price` is below the applicable lower bound, `ValueError` is raised.
  A below-lower-bound price is never reinterpreted as zero volatility.
- If `market_price` equals the lower bound, the solver returns exactly `0.0`
  (the zero-volatility deterministic price).
- If `market_price` is at or above the upper bound, `ValueError` is raised
  because no finite implied volatility produces that price.

### Zero-volatility lower-bound interpretation

The lower bound is the exact deterministic price of the option when `sigma = 0`
with positive time to expiry. It is the minimum attainable European price and
corresponds to `sigma = 0`.

### Infinite-volatility upper-bound interpretation

The upper bound is approached only as `sigma -> infinity`. Equality with the
upper bound therefore has no finite solution, which is why it is rejected rather
than clamped.

### Time-to-expiry requirement

Implied volatility requires strictly positive `T`. At `T = 0` the option is at
expiry and its value is the intrinsic payoff, which is independent of
volatility, so `ImpliedVolatilityInputs` rejects `T <= 0`.

### Tolerance meanings

- `price_tolerance` (default `1e-10`): absolute price tolerance. Bisection stops
  when `|price(midpoint) - market_price| <= price_tolerance`.
- `volatility_tolerance` (default `1e-12`): absolute volatility-interval
  tolerance. Bisection also stops when `upper_volatility - lower_volatility <=
  volatility_tolerance`, returning the midpoint of the final interval.

Both must be finite, strictly positive real numbers.

### Maximum-volatility policy

`initial_upper_volatility` (default `0.5`) seeds the upper bracket. If the price
at that volatility is still below `market_price`, the upper bound is doubled
repeatedly, never exceeding `max_volatility` (default `10.0`). If the price at
`max_volatility` is still below `market_price`, `ValueError` is raised; the
solver never silently returns `max_volatility`. `initial_upper_volatility` must
not exceed `max_volatility`.

### Non-convergence policy

Bisection runs for at most `max_iterations` (default `200`) iterations. If it
does not satisfy the price or volatility tolerance within that limit, a
`RuntimeError` is raised; the solver never returns an unconverged value.

### IEEE-754 limitations

The implementation uses IEEE 754 double precision. Extremely small positive
volatilities may be numerically indistinguishable from the zero-volatility lower
bound in floating-point arithmetic; the solver does not special-case such cases
beyond the exact lower-bound equality check. No arbitrary clamps or epsilons are
applied to prices or volatilities.

## Intrinsic payoff

The intrinsic payoff of a European option at expiry is the amount received on
exercise, ignoring any premium paid. It is never negative:

```
Call:  max(S - K, 0)
Put:   max(K - S, 0)
```

`S` (underlying price) must be a finite real number and must be `>= 0`; a zero
underlying price is valid (it yields a zero call payoff and a `K` put payoff).
`K` (strike) must be finite and strictly positive. `intrinsic_payoff` does not
price the option and does not depend on `r`, `q`, `sigma`, or `T`.

## Long-option expiry profit and loss

The expiry profit and loss of a **long** option is the intrinsic payoff minus
the premium paid for one option unit:

```
expiry_profit_loss = intrinsic_payoff(...) - premium
```

Conventions:

- `premium` is the amount paid to acquire one option unit. It must be a finite
  real number and must be `>= 0`.
- No discounting is applied inside this function; the premium is compared
  directly to the intrinsic payoff at expiry.
- No contract multiplier or position quantity is assumed; the result is per
  single option unit.
- Short positions are never inferred and the premium sign is never silently
  changed. For a long option, the minimum profit and loss is `-premium`.
- The break-even underlying price is `K + premium` for a call and `K - premium`
  for a put.

## Scenario analysis

`evaluate_price_scenarios` reprices a European option under pre-expiry scenario
assumptions. The strike is taken from the base case and remains fixed across
scenarios; only spot, time to expiry, volatility, risk-free rate, and dividend
yield vary per scenario. Each scenario price is produced by `price_european`, so
the pricing core remains the single source of truth.

### Scenario fields

- `spot` (`S`) must be strictly positive.
- `time_to_expiry` (`T`) must be non-negative; `T = 0` places the option at
  expiry.
- `volatility` (`sigma`) must be non-negative; `sigma = 0` selects the
  deterministic discounted-payoff path.
- `risk_free_rate` (`r`) must be finite and may be negative.
- `dividend_yield` (`q`) must be finite and may be negative; it defaults to `0`.
- `label` is an optional `str` (or `None`); an empty string is permitted and is
  treated as a present-but-empty label.

### Absolute and percentage change

For each scenario, with the base option price `P0` and the scenario option price
`P1`:

```
price_change     = P1 - P0
percentage_change = price_change / P0
```

`percentage_change` is a **decimal** return (for example `0.1` means a 10%
increase); users may multiply by 100 for percentage points. It is **not**
multiplied by 100 internally and is not clamped.

When the base price `P0` is exactly `0.0`, `percentage_change` is `None`. The
implementation does not return `inf`, does not substitute `0`, and does not use
an epsilon denominator.

### Order and duplicate preservation

`evaluate_price_scenarios` preserves the order of the supplied scenarios and
preserves duplicate scenarios exactly. The input iterable is consumed once; no
implicit grid or de-duplication is performed, and the result is an immutable
tuple. `evaluate_expiry_scenarios` follows the same policy for underlying prices.

### Boundary behaviour inherited from price_european

Because scenarios are repriced with `price_european`, all boundary behaviour is
inherited unchanged: at `T = 0` the price equals the intrinsic payoff, and at
`sigma = 0` (with `T > 0`) the exact deterministic discounted payoff is used.
The scenario module does not reimplement or override these rules.

## Invalid-input handling

Invalid inputs are rejected explicitly before any numerical computation:

- Booleans are **never** accepted as financial numbers (`True`/`False` are
  rejected even where `1`/`0` would be valid).
- Strings, `None`, and complex values are rejected by type.
- Non-finite values (`NaN`, `+inf`, `-inf`) are rejected.
- `S <= 0` and `K <= 0` are rejected (strictly positive).
- `T < 0` and `sigma < 0` are rejected.
- `T = 0` and `sigma = 0` are allowed.
- `r` and `q` must be finite but may be negative; they are not required to be
  non-negative.
- Invalid `option_type` values (arbitrary strings, numbers, `None`, booleans)
  are rejected by `price_european`.

Type errors raise `TypeError`; invalid values raise `ValueError`. Messages name
the offending input. The library does not return sentinel values such as `NaN`
to represent invalid states, and it does not silently coerce malformed input.

## Floating-point comparison and tolerance policy

Numerical results are compared using `pytest.approx` with a combined absolute
tolerance of `1e-10` and a relative tolerance of `1e-9` for ordinary reference
cases. Exact equality is used only where the result is mathematically exact,
such as intrinsic value at expiry.

Comparisons avoid exact equality on general floating-point results.

## Known numerical limitations

- The implementation uses IEEE 754 double precision via the standard library.
  Extreme combinations of inputs (for example very large `S` or `K` with very
  long `T`) may encounter floating-point overflow in `math.exp` or loss of
  precision, which Python surfaces as exceptions or finite but imprecise values.
- The standard normal CDF inherits the accuracy of `math.erf`.
- No arbitrary clamping is applied; behaviour at domain boundaries is governed
  by the explicit expiry and zero-volatility rules above.

## Calendar-day versus trading-day assumptions

Time to expiry `T` is expressed in calendar years. **Unresolved:** whether
volatility and rate inputs should be internally adjusted for trading-day counts,
and whether day-count conventions will be exposed. This remains a design
decision for a later stage.

## Greek units and signs

The analytical Greeks are implemented and documented below. All Greeks are
defined with specific units and signs as per the public API. The units are
consistent with the pricing conventions:

- **Delta**: price change per one-unit change in spot.
- **Gamma**: delta change per one-unit change in spot.
- **Vega**: price change per 1.0 absolute change in volatility.
- **Theta**: price change per one year of calendar time passing (negative for long options).
- **Rho**: price change per 1.0 absolute change in the risk-free rate.
- **Dividend rho**: price change per 1.0 absolute change in dividend yield.

Scaling notes:

- **Vega per one volatility percentage point** = vega / 100.
- **Rho per one interest-rate percentage point** = rho / 100.
- **Dividend rho per one yield percentage point** = dividend_rho / 100.
- No automatic division by 100 or 365 is performed. Users must scale manually
  if they need these units.

Sign conventions:

- Call delta is positive for calls in-the-money; put delta is negative for puts
  in-the-money.
- Gamma and vega are positive for calls and puts.
- Theta is negative for long options (time decay erodes option value).
- Rho is positive for calls and negative for puts.
- Dividend rho is negative for calls and positive for puts.

## Greek formulas

Let S = spot, K = strike, T = time_to_expiry, r = risk_free_rate,
q = dividend_yield, sigma = volatility, N = standard normal CDF, phi = standard
normal PDF.

First compute:

```
d1 = [ ln(S / K) + (r - q + 0.5 * sigma²) * T ] / (sigma * sqrt(T))
d2 = d1 - sigma * sqrt(T)
```

### Call Greeks

- **Call delta:** exp(-q * T) * N(d1)
- **Call gamma:** [exp(-q * T) * phi(d1)] / [S * sigma * sqrt(T)]
- **Call vega:** S * exp(-q * T) * phi(d1) * sqrt(T)
- **Call theta:**
  ```
  [-S * exp(-q * T) * phi(d1) * sigma] / [2 * sqrt(T)]
  - r * K * exp(-r * T) * N(d2) + q * S * exp(-q * T) * N(d1)
  ```
- **Call rho:** K * T * exp(-r * T) * N(d2)
- **Call dividend rho:** -S * T * exp(-q * T) * N(d1)

### Put Greeks

- **Put delta:** exp(-q * T) * [N(d1) - 1]
- **Put gamma:** [exp(-q * T) * phi(d1)] / [S * sigma * sqrt(T)]
- **Put vega:** S * exp(-q * T) * phi(d1) * sqrt(T)
- **Put theta:**
  ```
  [-S * exp(-q * T) * phi(d1) * sigma] / [2 * sqrt(T)]
  + r * K * exp(-r * T) * N(-d2) - q * S * exp(-q * T) * N(-d1)
  ```
- **Put rho:** -K * T * exp(-r * T) * N(-d2)
- **Put dividend rho:** S * T * exp(-q * T) * N(-d1)

## Domain restrictions

Greeks require positive time to expiry and positive volatility because:

- Delta may be discontinuous at expiry (T = 0).
- Gamma may become singular or distributional at expiry.
- Several formulas divide by volatility × sqrt(time).

When `time_to_expiry == 0` or `volatility == 0`, the `greeks_european` function
raises ValueError with a clear message. The library does not substitute arbitrary
epsilons or return sentinel values at those boundaries.

## References

The implemented formulas follow the standard Black-Scholes-Merton European
option pricing model with continuous dividend yield. Reference test values are
computed independently from the closed-form formulas using `math.erf` and are
documented in the test suite with their derivation.
