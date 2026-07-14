"""BlackScholesLab: a transparent and carefully tested Black-Scholes toolkit.

The development version implements the European option pricing core:

- :class:`BlackScholesInputs` — immutable, typed pricing inputs.
- :class:`OptionType` — call/put enumeration.
- :func:`price_european` — analytical European call and put pricing.
- :class:`ImpliedVolatilityInputs` — immutable, typed market inputs.
- :func:`implied_volatility` — deterministic implied-volatility solver.
- :func:`intrinsic_payoff` — intrinsic expiry payoff for European options.
- :func:`expiry_profit_loss` — expiry profit and loss after a paid premium.
- :func:`evaluate_expiry_scenarios` — ordered expiry payoff/P&L evaluation.
- :func:`evaluate_price_scenarios` — pre-expiry scenario repricing.
"""

from __future__ import annotations

from blackscholeslab.greeks import OptionGreeks, greeks_european
from blackscholeslab.implied_volatility import ImpliedVolatilityInputs, implied_volatility
from blackscholeslab.models import BlackScholesInputs, OptionType
from blackscholeslab.payoff import (
    ExpiryScenarioResult,
    evaluate_expiry_scenarios,
    expiry_profit_loss,
    intrinsic_payoff,
)
from blackscholeslab.pricing import price_european
from blackscholeslab.scenarios import (
    OptionScenario,
    ScenarioPriceResult,
    evaluate_price_scenarios,
)

__version__ = "0.1.0"
__author__ = "Amrut Deshmukh"
__license__ = "MIT"

__all__ = [
    "BlackScholesInputs",
    "OptionType",
    "price_european",
    "OptionGreeks",
    "greeks_european",
    "ImpliedVolatilityInputs",
    "implied_volatility",
    "ExpiryScenarioResult",
    "OptionScenario",
    "ScenarioPriceResult",
    "intrinsic_payoff",
    "expiry_profit_loss",
    "evaluate_expiry_scenarios",
    "evaluate_price_scenarios",
    "__version__",
    "__author__",
    "__license__",
]
