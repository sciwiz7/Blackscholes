# Examples

This directory holds runnable usage examples for BlackScholesLab. Each example is
a self-contained, deterministic Python script that exercises only the public core
API (`blackscholeslab.__all__`). They contain no network or file I/O, no
randomness, and no duplicated financial formulas.

| Script | What it shows |
| ------ | ------------- |
| `pricing_and_greeks.py` | European call/put pricing with dividends, expiry and zero-volatility boundaries, finite negative rates/yields, and all six analytical Greeks. |
| `implied_volatility.py` | Building an `ImpliedVolatilityInputs` snapshot, solving for implied volatility, repricing, the absolute residual, and the zero-volatility lower bound. |
| `payoff_and_scenarios.py` | Intrinsic payoff, long-option expiry P&L, ordered expiry scenarios, and fixed-strike pre-expiry scenario repricing (including the `None` percentage-change case). |

Run any example directly:

```bash
python examples/pricing_and_greeks.py
python examples/implied_volatility.py
python examples/payoff_and_scenarios.py
```

Each script defines a `main()` function with a `__main__` guard, so it can also be
imported without executing. The examples are executed and checked for
deterministic output by `tests/test_documentation.py`.
