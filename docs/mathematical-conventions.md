# Mathematical conventions

This document records the **intended** mathematical conventions for
BlackScholesLab. The formulas and numerical routines that follow these
conventions are not implemented yet; this document is a specification to be
verified during the numerical implementation stage.

Conventions in this document are design intentions. Items marked
**Unresolved** must be confirmed against references during implementation and
unit testing.

## Market inputs

| Symbol | Meaning | Unit | Notes |
| ------ | ------- | ---- | ----- |
| `S` | Spot price of the underlying | currency | Must be strictly positive. |
| `K` | Strike price | currency | Must be strictly positive. |
| `T` | Time to expiry | years | Must be non-negative. `T = 0` means at expiry. |
| `r` | Continuously compounded risk-free rate | decimal per year | May be negative in unusual markets. |
| `q` | Continuously compounded dividend yield | decimal per year | Defaults to `0`. |
| `sigma` | Annualised volatility | decimal per year | Must be strictly positive. |

### Spot price
`S` is the current price of the underlying asset, expressed in the same
currency as `K`. It must be strictly positive.

### Strike price
`K` is the agreed exercise price. It must be strictly positive.

### Time to expiry
`T` is measured in **years** as a positive real number, or exactly `0` at
expiry. A value of `T = 0` places the option at expiry, where pricing reduces
to the intrinsic payoff.

### Continuously compounded risk-free rate
`r` is the annual risk-free rate under continuous compounding. The toolkit
assumes continuous compounding throughout; discrete compounding conventions
are out of scope.

### Continuous dividend yield
`q` is the annual continuous dividend yield of the underlying. It defaults to
`0` when omitted, representing a non-dividend-paying asset.

### Annualised volatility
`sigma` is the annualised standard deviation of the underlying return,
expressed as a decimal (for example `0.20` for 20%). It must be strictly
positive. A non-positive volatility is mathematically invalid for the
Black-Scholes model.

## Option types

The toolkit targets **European** options only. European options may be
exercised solely at expiry.

- **European call**: right to buy the underlying at `K` at expiry.
- **European put**: right to sell the underlying at `K` at expiry.

American exercise, barriers, and other exotic features are out of scope for
the current plan.

## Calendar-day versus trading-day assumptions

Time to expiry `T` is expressed in calendar years. **Unresolved:** whether
volatility and rate inputs should be internally adjusted for trading-day
counts, and whether day-count conventions (for example actual/365) will be
exposed. This must be decided and documented during implementation, with tests
covering the chosen convention.

## Planned Greek units and signs

Greeks are sensitivities of the option price to model inputs. The intended
definitions are listed below; signs follow standard quantitative-finance
conventions. **Unresolved:** exact scaling of vega and theta (per 1.00 change
in volatility versus per 1 percentage point, and per year versus per calendar
day) must be fixed during implementation and stated explicitly.

| Greek | Sensitivity to | Intended sign for calls | Intended sign for puts |
| ----- | -------------- | ----------------------- | ---------------------- |
| Delta | underlying price | positive | negative |
| Gamma | underlying price (2nd order) | positive | positive |
| Vega  | volatility | positive | positive |
| Theta | time | typically negative | typically negative |
| Rho   | risk-free rate | positive | negative |

## Behaviour at expiry

At `T = 0` the option value equals its intrinsic payoff:

- Call: `max(S - K, 0)`
- Put: `max(K - S, 0)`

Behaviour at expiry will be tested as a hard boundary condition, including the
continuity of price and Greek limits as `T -> 0`.

## Invalid-input handling

Invalid inputs will be rejected explicitly before any numerical computation:

- Non-finite values (`NaN`, `inf`) are rejected.
- `S <= 0`, `K <= 0`, `sigma <= 0` are rejected.
- `T < 0` is rejected.
- Domain violations raise a typed exception naming the offending input.

The library will not return sentinel values such as `NaN` to represent invalid
states.

## Floating-point comparison and tolerance policy

Numerical results will be compared using a combined absolute and relative
tolerance. **Unresolved:** the default tolerances for pricing and Greeks will
be chosen during implementation based on reference values and machine
precision, and documented in the tests. Comparisons will avoid exact equality
on floating-point results.

## Numerical edge cases requiring implementation-stage verification

These cases must be explicitly verified when the numerical routines are
implemented:

- `T -> 0` (at expiry) and the limit `T -> 0+`.
- `sigma` very small but positive (near-deterministic limit).
- Deep in-the-money and deep out-of-the-money limits.
- `q = 0` and `q > 0` (with and without dividends).
- Large `T` (long-dated options).
- Stability of the implied-volatility solver near-at-the-money and at the
  boundaries of the price domain.

## References

Each implemented formula and Greek must be accompanied by a citation or
derivation reference in code comments and tests. References will be collected
in the implementation-stage documentation.
