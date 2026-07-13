"""BlackScholesLab: a transparent and carefully tested Black-Scholes toolkit.

The development version implements the European option pricing core:

- :class:`BlackScholesInputs` — immutable, typed pricing inputs.
- :class:`OptionType` — call/put enumeration.
- :func:`price_european` — analytical European call and put pricing.
"""

from __future__ import annotations

from blackscholeslab.greeks import OptionGreeks, greeks_european
from blackscholeslab.models import BlackScholesInputs, OptionType
from blackscholeslab.pricing import price_european

__version__ = "0.1.0.dev0"
__author__ = "Amrut Deshmukh"
__license__ = "MIT"

__all__ = [
    "BlackScholesInputs",
    "OptionType",
    "price_european",
    "OptionGreeks",
    "greeks_european",
    "__version__",
    "__author__",
    "__license__",
]
