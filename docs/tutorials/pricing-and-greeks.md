# Tutorial: pricing and Greeks

This tutorial walks through European option pricing and the analytical Greeks
using only the public BlackScholesLab API. It assumes BlackScholesLab is
installed from source (see the [documentation index](../index.md) for
installation).

All snippets are runnable Python. Copy them into a file or run
`examples/pricing_and_greeks.py` directly.

## What you need to import

```python
from blackscholeslab import (
    BlackScholesInputs,
    OptionType,
    OptionGreeks,
    greeks_european,
    price_european,
)
```

`BlackScholesInputs` is an immutable, typed container for the market
assumptions. `OptionType` is the `CALL` / `PUT` enumeration. `price_european`
prices a European option, and `greeks_european` returns the six analytical
Greeks as an immutable `OptionGreeks` value.

## Constructing the inputs

```python
inputs = BlackScholesInputs(
    spot=100.0,
    strike=100.0,
    time_to_expiry=1.0,
    risk_free_rate=0.05,
    volatility=0.20,
    dividend_yield=0.02,
)
```

The fields are:

| Field | Meaning | Units |
| ----- | ------- | ----- |
| `spot` | Current underlying price | currency, must be strictly positive |
| `strike` | Exercise price | currency, must be strictly positive |
| `time_to_expiry` | Time to expiry | calendar years, non-negative (`0` = at expiry) |
| `risk_free_rate` | Continuously compounded risk-free rate | annualised **decimal** (may be negative) |
| `volatility` | Annualised volatility | annualised **decimal**, non-negative (`0` = deterministic path) |
| `dividend_yield` | Continuously compounded dividend yield | annualised **decimal** (may be negative, default `0.0`) |

Two conventions matter throughout BlackScholesLab:

- **Rates and volatility are annualised decimals**, not percentages. A 5% rate
  is `0.05` and 20% volatility is `0.20`. The library never scales a percentage
  string for you.
- **Time is in calendar years.** There is no automatic trading-day conversion.

Fields are validated on construction. Booleans, strings, `None`, complex
values, non-finite numbers, non-positive `spot`/`strike`, or negative
`time_to_expiry`/`volatility` raise `TypeError` or `ValueError`.

## Pricing a European call and put

```python
call_price = price_european(inputs, OptionType.CALL)
put_price = price_european(inputs, OptionType.PUT)
print(call_price, put_price)
```

For the inputs above the deterministic results are:

```
9.227005508154 6.33008062755
```

(The exact printed values depend on your platform's IEEE-754 double precision,
but they are deterministic for a given machine and Python build.)

## Pricing with dividends

The `dividend_yield` field makes the model a Black-Scholes-**Merton** model with
continuous dividend yield. With `dividend_yield=0.02` the prices above are lower
than the non-dividend case because the underlying's dividend reduces the
forward price. Setting `dividend_yield=0.0` recovers the standard
Black-Scholes call and put prices.

## Expiry pricing

At `time_to_expiry == 0` the price collapses to the intrinsic payoff; `rate`,
`dividend_yield`, and `volatility` no longer matter:

```python
at_expiry = BlackScholesInputs(
    spot=120.0,
    strike=100.0,
    time_to_expiry=0.0,
    risk_free_rate=0.05,
    volatility=0.20,
    dividend_yield=0.02,
)
print(price_european(at_expiry, OptionType.CALL))   # 20.0  (max(S - K, 0))
print(price_european(at_expiry, OptionType.PUT))    # 0.0   (max(K - S, 0))
```

## Zero-volatility pricing

At `volatility == 0` with positive time to expiry, the regular d1/d2 formula
would divide by zero. BlackScholesLab instead returns the exact deterministic
discounted payoff:

```python
zero_vol = BlackScholesInputs(
    spot=100.0,
    strike=100.0,
    time_to_expiry=1.0,
    risk_free_rate=0.05,
    volatility=0.0,
    dividend_yield=0.02,
)
print(price_european(zero_vol, OptionType.CALL))  # 2.896924880604
print(price_european(zero_vol, OptionType.PUT))   # 0.0
```

Zero volatility is supported explicitly; the library does not substitute an
epsilon.

## Finite negative rates and yields

`risk_free_rate` and `dividend_yield` may be finite and negative. This is
allowed by the model (for example, in unusual money-market conditions) and is
not rejected:

```python
negative_inputs = BlackScholesInputs(
    spot=100.0,
    strike=100.0,
    time_to_expiry=1.0,
    risk_free_rate=-0.02,
    volatility=0.20,
    dividend_yield=-0.01,
)
print(price_european(negative_inputs, OptionType.CALL))  # 7.5885657342637245 (deterministic)
```

## Analytical Greeks

`greeks_european` returns all six Greeks in one immutable `OptionGreeks` value.
Greeks require **positive** time to expiry and **positive** volatility; at
`time_to_expiry == 0` or `volatility == 0` the function raises `ValueError`
because several formulas divide by those quantities and delta/gamma become
ill-defined at expiry.

```python
call_greeks = greeks_european(inputs, OptionType.CALL)
put_greeks = greeks_european(inputs, OptionType.PUT)
print(call_greeks.delta, call_greeks.gamma, call_greeks.vega)
print(call_greeks.theta, call_greeks.rho, call_greeks.dividend_rho)
```

For the base case (`S=100, K=100, T=1, r=0.05, sigma=0.20, q=0.02`):

```
delta        = 0.586851146134764
gamma        = 0.018950578755008718
vega         = 37.901157510017434   (per 1.0 absolute change in volatility)
theta        = -5.0893189139983335  (per one year of calendar time)
rho          = 49.45810910532236    (per 1.0 absolute change in rate)
dividend_rho = -58.685114613476394  (per 1.0 absolute change in yield)
```

The put Greeks for the same inputs are:

```
delta        = -0.3933475271719913
gamma        = 0.018950578755008718
vega         = 37.901157510017434   (per 1.0 absolute change in volatility)
theta        = -2.2935691381082735  (per one year of calendar time)
rho          = -45.664833344749056  (per 1.0 absolute change in rate)
dividend_rho = 39.33475271719913    (per 1.0 absolute change in yield)
```

### Raw units — read this carefully

The Greeks are returned in **raw units**. They are **not** divided by 100 (for a
percentage point) or by 365 (for a day). Specifically:

- **Vega** is the price change for an **absolute 1.0** change in volatility.
  To get the change per one volatility *percentage point*, divide vega by 100.
- **Rho** is the price change for an **absolute 1.0** change in the risk-free
  rate. Divide by 100 for one rate percentage point.
- **Dividend rho** is the price change for an **absolute 1.0** change in the
  dividend yield. Divide by 100 for one yield percentage point.
- **Theta** is the price change per **one year** of calendar time passing. To
  approximate the change per calendar day, divide theta by 365.
- **Delta** is the price change per one unit of spot.
- **Gamma** is the delta change per one unit of spot.

`OptionGreeks` is a frozen dataclass, so the values cannot be changed after
computation. See the [API reference](../api-reference.md) and
[mathematical conventions](../mathematical-conventions.md) for the exact
definitions and sign conventions.

## Running the included example

The file `examples/pricing_and_greeks.py` reproduces every step above and prints
the same deterministic values:

```bash
python examples/pricing_and_greeks.py
```

## Where to go next

- [Implied volatility tutorial](implied-volatility.md)
- [Payoff and scenarios tutorial](payoff-and-scenarios.md)
- [Mathematical conventions](../mathematical-conventions.md)
- [API reference](../api-reference.md)

> **Educational only.** BlackScholesLab is not financial advice. Do not use it
> for trading or investment decisions without independent verification.
