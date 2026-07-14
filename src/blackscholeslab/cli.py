"""Command-line interface for BlackScholesLab.

This module is a thin, deterministic command-line interface over the existing
core analytics. It depends only on the standard library and on the public core
API; it never reimplements pricing, Greek, implied-volatility, payoff, or
scenario calculations.

Design constraints:

- Use only the standard library (``argparse``, ``json``, ``sys``) plus the
  public core API.
- Parse arguments, translate ``call``/``put`` into :class:`OptionType`, build
  the existing typed input models, invoke the existing public functions, and
  format output.
- Support a stable human-readable text mode and a deterministic JSON mode.
- Map expected user errors to stable exit codes (``2`` for ``TypeError``/
  ``ValueError``, ``3`` for ``RuntimeError`` from the solver).

The core modules must never import this CLI; the dependency direction is
strictly CLI -> core.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence

from blackscholeslab import (
    BlackScholesInputs,
    ImpliedVolatilityInputs,
    OptionScenario,
    OptionType,
    evaluate_expiry_scenarios,
    evaluate_price_scenarios,
    expiry_profit_loss,
    greeks_european,
    implied_volatility,
    intrinsic_payoff,
    price_european,
)

_OPTION_TYPE_BY_NAME: dict[str, OptionType] = {
    "call": OptionType.CALL,
    "put": OptionType.PUT,
}

_EXPECTED_OPTION_TYPES = ["call", "put"]


def _parse_option_type(value: str) -> OptionType:
    """Map a lowercase ``call``/``put`` string to an :class:`OptionType`."""
    option_type = _OPTION_TYPE_BY_NAME.get(value)
    if option_type is None:
        raise ValueError(f"invalid option type: {value!r} (expected 'call' or 'put')")
    return option_type


def _fmt_float(value: float) -> str:
    """Return a stable, locale-independent human-readable representation.

    The underlying calculation is never rounded; this helper only controls how a
    raw ``float`` is printed for humans.
    """
    return format(value, ".12g")


def _print_json(payload: dict[str, object]) -> None:
    """Print exactly one deterministic JSON object to stdout."""
    print(json.dumps(payload, sort_keys=True, allow_nan=False))


def _add_common_pricing_args(parser: argparse.ArgumentParser) -> None:
    """Add the shared pricing inputs (spot, strike, time, rate, volatility)."""
    parser.add_argument("--type", required=True, choices=_EXPECTED_OPTION_TYPES)
    parser.add_argument("--spot", required=True, type=float)
    parser.add_argument("--strike", required=True, type=float)
    parser.add_argument("--time", required=True, type=float)
    parser.add_argument("--rate", required=True, type=float)
    parser.add_argument("--volatility", required=True, type=float)
    parser.add_argument("--dividend-yield", type=float, default=0.0)
    parser.add_argument("--json", action="store_true")


def _cmd_price(args: argparse.Namespace) -> int:
    """Handle the ``price`` subcommand."""
    option_type = _parse_option_type(args.type)
    inputs = BlackScholesInputs(
        spot=args.spot,
        strike=args.strike,
        time_to_expiry=args.time,
        risk_free_rate=args.rate,
        volatility=args.volatility,
        dividend_yield=args.dividend_yield,
    )
    price = price_european(inputs, option_type)

    if args.json:
        _print_json(
            {
                "command": "price",
                "option_type": args.type,
                "price": price,
            }
        )
    else:
        print(f"Option type: {args.type}")
        print(f"Price: {_fmt_float(price)}")
    return 0


def _cmd_greeks(args: argparse.Namespace) -> int:
    """Handle the ``greeks`` subcommand."""
    option_type = _parse_option_type(args.type)
    inputs = BlackScholesInputs(
        spot=args.spot,
        strike=args.strike,
        time_to_expiry=args.time,
        risk_free_rate=args.rate,
        volatility=args.volatility,
        dividend_yield=args.dividend_yield,
    )
    greeks = greeks_european(inputs, option_type)

    if args.json:
        _print_json(
            {
                "command": "greeks",
                "option_type": args.type,
                "delta": greeks.delta,
                "gamma": greeks.gamma,
                "vega": greeks.vega,
                "theta": greeks.theta,
                "rho": greeks.rho,
                "dividend_rho": greeks.dividend_rho,
            }
        )
    else:
        print(f"Option type: {args.type}")
        print(f"Delta: {_fmt_float(greeks.delta)}")
        print(f"Gamma: {_fmt_float(greeks.gamma)}")
        print(f"Vega: {_fmt_float(greeks.vega)}")
        print(f"Theta: {_fmt_float(greeks.theta)}")
        print(f"Rho: {_fmt_float(greeks.rho)}")
        print(f"Dividend rho: {_fmt_float(greeks.dividend_rho)}")
    return 0


def _cmd_implied_volatility(args: argparse.Namespace) -> int:
    """Handle the ``implied-volatility`` subcommand."""
    option_type = _parse_option_type(args.type)
    inputs = ImpliedVolatilityInputs(
        market_price=args.market_price,
        spot=args.spot,
        strike=args.strike,
        time_to_expiry=args.time,
        risk_free_rate=args.rate,
        dividend_yield=args.dividend_yield,
    )
    implied_vol = implied_volatility(
        inputs,
        option_type,
        price_tolerance=args.price_tolerance,
        volatility_tolerance=args.volatility_tolerance,
        max_iterations=args.max_iterations,
        initial_upper_volatility=args.initial_upper_volatility,
        max_volatility=args.max_volatility,
    )

    if args.json:
        _print_json(
            {
                "command": "implied-volatility",
                "option_type": args.type,
                "implied_volatility": implied_vol,
            }
        )
    else:
        print(f"Option type: {args.type}")
        print(f"Implied volatility: {_fmt_float(implied_vol)}")
    return 0


def _cmd_payoff(args: argparse.Namespace) -> int:
    """Handle the ``payoff`` subcommand."""
    option_type = _parse_option_type(args.type)
    payoff = intrinsic_payoff(
        underlying_price=args.underlying_price,
        strike=args.strike,
        option_type=option_type,
    )

    if args.json:
        _print_json(
            {
                "command": "payoff",
                "option_type": args.type,
                "payoff": payoff,
            }
        )
    else:
        print(f"Option type: {args.type}")
        print(f"Payoff: {_fmt_float(payoff)}")
    return 0


def _cmd_expiry_pnl(args: argparse.Namespace) -> int:
    """Handle the ``expiry-pnl`` subcommand."""
    option_type = _parse_option_type(args.type)
    profit_loss = expiry_profit_loss(
        underlying_price=args.underlying_price,
        strike=args.strike,
        option_type=option_type,
        premium=args.premium,
    )

    if args.json:
        _print_json(
            {
                "command": "expiry-pnl",
                "option_type": args.type,
                "profit_loss": profit_loss,
            }
        )
    else:
        print(f"Option type: {args.type}")
        print(f"Profit/loss: {_fmt_float(profit_loss)}")
    return 0


def _cmd_expiry_scenarios(args: argparse.Namespace) -> int:
    """Handle the ``expiry-scenarios`` subcommand."""
    option_type = _parse_option_type(args.type)
    results = evaluate_expiry_scenarios(
        args.underlying_prices,
        args.strike,
        option_type,
        premium=args.premium,
    )

    if args.json:
        payload_results = [
            {
                "underlying_price": result.underlying_price,
                "payoff": result.payoff,
                "profit_loss": result.profit_loss,
            }
            for result in results
        ]
        _print_json(
            {
                "command": "expiry-scenarios",
                "option_type": args.type,
                "results": payload_results,
            }
        )
    else:
        print("Underlying price | Payoff | Profit/loss")
        for result in results:
            print(
                f"{_fmt_float(result.underlying_price)} | "
                f"{_fmt_float(result.payoff)} | "
                f"{_fmt_float(result.profit_loss)}"
            )
    return 0


def _parse_scenarios(raw_scenarios: list[str]) -> list[OptionScenario]:
    """Parse repeatable ``--scenario`` string arguments into scenarios.

    Each scenario is ``spot,time,volatility,rate,dividend_yield[,label]`` with
    exactly five or six comma-separated fields. Commas inside labels are not
    supported. Malformed scenarios report their zero-based index.
    """
    parsed: list[OptionScenario] = []
    for index, raw in enumerate(raw_scenarios):
        parts = raw.split(",")
        if len(parts) not in (5, 6):
            raise ValueError(
                f"scenario {index} must have 5 or 6 comma-separated fields, got {len(parts)}"
            )
        try:
            spot = float(parts[0])
            time_to_expiry = float(parts[1])
            volatility = float(parts[2])
            risk_free_rate = float(parts[3])
            dividend_yield = float(parts[4])
        except ValueError:
            raise ValueError(f"scenario {index} has an invalid numeric field") from None
        label = parts[5] if len(parts) == 6 else None
        try:
            scenario = OptionScenario(
                spot=spot,
                time_to_expiry=time_to_expiry,
                volatility=volatility,
                risk_free_rate=risk_free_rate,
                dividend_yield=dividend_yield,
                label=label,
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(f"scenario {index}: {exc}") from exc
        parsed.append(scenario)
    return parsed


def _cmd_price_scenarios(args: argparse.Namespace) -> int:
    """Handle the ``price-scenarios`` subcommand."""
    option_type = _parse_option_type(args.type)
    base_inputs = BlackScholesInputs(
        spot=args.spot,
        strike=args.strike,
        time_to_expiry=args.time,
        risk_free_rate=args.rate,
        volatility=args.volatility,
        dividend_yield=args.dividend_yield,
    )
    scenarios = _parse_scenarios(args.scenario)
    results = evaluate_price_scenarios(base_inputs, option_type, scenarios)

    if args.json:
        payload_results = [
            {
                "label": result.scenario.label,
                "spot": result.scenario.spot,
                "time_to_expiry": result.scenario.time_to_expiry,
                "volatility": result.scenario.volatility,
                "risk_free_rate": result.scenario.risk_free_rate,
                "dividend_yield": result.scenario.dividend_yield,
                "option_price": result.option_price,
                "price_change": result.price_change,
                "percentage_change": result.percentage_change,
            }
            for result in results
        ]
        _print_json(
            {
                "command": "price-scenarios",
                "option_type": args.type,
                "results": payload_results,
            }
        )
    else:
        for index, result in enumerate(results):
            label_text = result.scenario.label if result.scenario.label is not None else "none"
            if result.percentage_change is None:
                percentage_text = "undefined"
            else:
                percentage_text = _fmt_float(result.percentage_change)
            print(f"Scenario {index} (label={label_text})")
            print(f"  Option price: {_fmt_float(result.option_price)}")
            print(f"  Price change: {_fmt_float(result.price_change)}")
            print(f"  Percentage change: {percentage_text}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="blackscholeslab",
        description="BlackScholesLab command-line interface for option analytics.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    price_parser = subparsers.add_parser("price", help="Price a European option.")
    _add_common_pricing_args(price_parser)
    price_parser.set_defaults(handler=_cmd_price)

    greeks_parser = subparsers.add_parser(
        "greeks", help="Compute analytical Greeks for a European option."
    )
    _add_common_pricing_args(greeks_parser)
    greeks_parser.set_defaults(handler=_cmd_greeks)

    iv_parser = subparsers.add_parser(
        "implied-volatility", help="Solve for implied volatility from a market price."
    )
    iv_parser.add_argument("--type", required=True, choices=_EXPECTED_OPTION_TYPES)
    iv_parser.add_argument("--market-price", required=True, type=float)
    iv_parser.add_argument("--spot", required=True, type=float)
    iv_parser.add_argument("--strike", required=True, type=float)
    iv_parser.add_argument("--time", required=True, type=float)
    iv_parser.add_argument("--rate", required=True, type=float)
    iv_parser.add_argument("--dividend-yield", type=float, default=0.0)
    iv_parser.add_argument("--price-tolerance", type=float, default=1e-10)
    iv_parser.add_argument("--volatility-tolerance", type=float, default=1e-12)
    iv_parser.add_argument("--max-iterations", type=int, default=200)
    iv_parser.add_argument("--initial-upper-volatility", type=float, default=0.5)
    iv_parser.add_argument("--max-volatility", type=float, default=10.0)
    iv_parser.add_argument("--json", action="store_true")
    iv_parser.set_defaults(handler=_cmd_implied_volatility)

    payoff_parser = subparsers.add_parser(
        "payoff", help="Compute the intrinsic expiry payoff of a European option."
    )
    payoff_parser.add_argument("--type", required=True, choices=_EXPECTED_OPTION_TYPES)
    payoff_parser.add_argument("--underlying-price", required=True, type=float)
    payoff_parser.add_argument("--strike", required=True, type=float)
    payoff_parser.add_argument("--json", action="store_true")
    payoff_parser.set_defaults(handler=_cmd_payoff)

    pnl_parser = subparsers.add_parser(
        "expiry-pnl", help="Compute expiry profit/loss for a long European option."
    )
    pnl_parser.add_argument("--type", required=True, choices=_EXPECTED_OPTION_TYPES)
    pnl_parser.add_argument("--underlying-price", required=True, type=float)
    pnl_parser.add_argument("--strike", required=True, type=float)
    pnl_parser.add_argument("--premium", required=True, type=float)
    pnl_parser.add_argument("--json", action="store_true")
    pnl_parser.set_defaults(handler=_cmd_expiry_pnl)

    expiry_scenarios_parser = subparsers.add_parser(
        "expiry-scenarios",
        help="Evaluate expiry payoff and profit/loss across underlying prices.",
    )
    expiry_scenarios_parser.add_argument("--type", required=True, choices=_EXPECTED_OPTION_TYPES)
    expiry_scenarios_parser.add_argument("--strike", required=True, type=float)
    expiry_scenarios_parser.add_argument("--premium", type=float, default=0.0)
    expiry_scenarios_parser.add_argument(
        "--underlying-prices", required=True, nargs="+", type=float
    )
    expiry_scenarios_parser.add_argument("--json", action="store_true")
    expiry_scenarios_parser.set_defaults(handler=_cmd_expiry_scenarios)

    price_scenarios_parser = subparsers.add_parser(
        "price-scenarios",
        help="Reprice a European option under pre-expiry scenario assumptions.",
    )
    _add_common_pricing_args(price_scenarios_parser)
    price_scenarios_parser.add_argument(
        "--scenario",
        required=True,
        action="append",
        metavar="SPOT,TIME,VOLATILITY,RATE,DIVIDEND_YIELD[,LABEL]",
        help=(
            "A repeatable scenario encoded as five or six comma-separated fields: "
            "spot, time_to_expiry, volatility, risk_free_rate, dividend_yield, "
            "and an optional label. At least one scenario is required."
        ),
    )
    price_scenarios_parser.set_defaults(handler=_cmd_price_scenarios)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the ``blackscholeslab`` command.

    Args:
        argv: Optional argument vector (defaults to ``sys.argv[1:]``).

    Returns:
        ``0`` on success, ``2`` for expected ``TypeError``/``ValueError`` input
        errors, and ``3`` for a ``RuntimeError`` raised by the implied-volatility
        solver on non-convergence.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    handler: Callable[[argparse.Namespace], int] = args.handler
    try:
        return handler(args)
    except (TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        # Only the implied-volatility solver failure is mapped to exit code 3.
        # An unexpected RuntimeError from another command is re-raised so it
        # remains distinguishable as an internal failure and is not silently
        # reported as implied-volatility non-convergence.
        if args.command == "implied-volatility":
            print(f"error: {exc}", file=sys.stderr)
            return 3
        raise


if __name__ == "__main__":
    raise SystemExit(main())
