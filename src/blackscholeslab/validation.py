"""Reusable input validation for BlackScholesLab.

Validation helpers reject malformed or mathematically invalid inputs before any
numerical computation. The conventions are:

- Booleans are never accepted as financial numbers.
- Strings, ``None``, and complex values are rejected.
- Every numeric input must be a real, finite number.
- ``spot`` and ``strike`` must be strictly positive.
- ``time_to_expiry`` and ``volatility`` must be non-negative.
- ``risk_free_rate`` and ``dividend_yield`` must be finite but may be negative.

Type errors (wrong type) raise :class:`TypeError`; invalid values raise
:class:`ValueError`. Messages name the offending input.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from blackscholeslab.models import OptionType


def validate_real_number(
    value: Any,
    name: str,
    *,
    allow_negative: bool,
    allow_zero: bool,
) -> None:
    """Validate a single real-number input field.

    Args:
        value: The candidate value.
        name: Human-readable field name used in error messages.
        allow_negative: Whether negative finite values are permitted.
        allow_zero: Whether a zero value is permitted.

    Raises:
        TypeError: If ``value`` is not a real number (bool, str, None, complex,
            or another unsupported type).
        ValueError: If ``value`` is non-finite (NaN or infinite), negative when
            not allowed, or zero when not allowed.
    """
    if value is None:
        raise TypeError(f"{name} must be a real number, got None")
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a real number, not a bool")
    if isinstance(value, str):
        raise TypeError(f"{name} must be a real number, not a string")
    if isinstance(value, complex):
        raise TypeError(f"{name} must be a real number, not a complex value")
    if not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a real number, got {type(value).__name__}")
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite, got {value!r}")
    if value < 0 and not allow_negative:
        raise ValueError(f"{name} must be non-negative, got {value!r}")
    if value == 0 and not allow_zero:
        raise ValueError(f"{name} must be strictly positive, got {value!r}")


def validate_inputs(inputs: Any) -> None:
    """Validate every numeric field of a :class:`BlackScholesInputs` instance.

    Raises:
        TypeError: If ``inputs`` is not a :class:`BlackScholesInputs`, or if any
            field has the wrong type.
        ValueError: If any field has an invalid value.
    """
    from blackscholeslab.models import BlackScholesInputs

    if not isinstance(inputs, BlackScholesInputs):
        raise TypeError(
            f"inputs must be a BlackScholesInputs instance, got {type(inputs).__name__}"
        )

    validate_real_number(inputs.spot, "spot", allow_negative=False, allow_zero=False)
    validate_real_number(inputs.strike, "strike", allow_negative=False, allow_zero=False)
    validate_real_number(
        inputs.time_to_expiry, "time_to_expiry", allow_negative=False, allow_zero=True
    )
    validate_real_number(
        inputs.risk_free_rate, "risk_free_rate", allow_negative=True, allow_zero=True
    )
    validate_real_number(inputs.volatility, "volatility", allow_negative=False, allow_zero=True)
    validate_real_number(
        inputs.dividend_yield, "dividend_yield", allow_negative=True, allow_zero=True
    )


def validate_option_type(option_type: Any) -> OptionType:
    """Validate and return ``option_type`` as a :class:`OptionType`.

    Args:
        option_type: Candidate option type.

    Returns:
        The validated :class:`OptionType` member.

    Raises:
        TypeError: If ``option_type`` is not a valid :class:`OptionType`.
    """
    from blackscholeslab.models import OptionType

    if not isinstance(option_type, OptionType):
        raise TypeError(
            f"option_type must be OptionType.CALL or OptionType.PUT, got {option_type!r}"
        )
    return option_type
