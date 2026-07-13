"""Internal numerical helpers for BlackScholesLab.

These helpers are mathematically pure and depend only on the Python standard
library. They are intentionally kept internal so that future modules (for
example Greeks or implied volatility) can reuse them without exposing
implementation details in the public API.
"""

from __future__ import annotations

import math


def norm_cdf(x: float) -> float:
    """Standard normal cumulative distribution function.

    Implemented with :func:`math.erf`:

        N(x) = 0.5 * (1 + erf(x / sqrt(2)))

    Args:
        x: Input value (any finite real number).

    Returns:
        The probability that a standard normal random variable is less than
        or equal to ``x``.
    """
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
