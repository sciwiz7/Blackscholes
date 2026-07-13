# Mathematical conventions

This document records the mathematical conventions used by the implemented
Black-Scholes-Merton European pricing core in BlackScholesLab. Items marked
**Unresolved** concern future capabilities (Greeks, implied volatility) and are
not settled by this implementation.

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

## Greek units and signs (Unresolved)

Greeks are not implemented in this stage. The intended definitions and
**Unresolved** scaling questions are recorded for later work:

- **Vega scaling**: per 1.00 change in volatility versus per 1 percentage point.
- **Theta scaling**: per year versus per calendar day.
- **Rho scaling**: per 1.00 change in rate versus per 1 percentage point.
- Sign conventions for Greeks are not yet implemented and remain unresolved.

## References

The implemented formulas follow the standard Black-Scholes-Merton European
option pricing model with continuous dividend yield. Reference test values are
computed independently from the closed-form formulas using `math.erf` and are
documented in the test suite with their derivation.
