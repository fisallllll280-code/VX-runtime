"""Offline, deterministic primitives for VX Financial Intelligence.

Research-only utilities. This module does not fetch market data, predict prices,
connect to a broker, or place orders.
"""
from __future__ import annotations

from math import isfinite
from typing import Iterable, Sequence


def validate_close_series(values: Iterable[float]) -> tuple[float, ...]:
    """Return validated positive finite close prices in chronological order."""
    prices = tuple(float(value) for value in values)
    if len(prices) < 2:
        raise ValueError("at least two chronological close prices are required")
    if any(not isfinite(value) or value <= 0 for value in prices):
        raise ValueError("close prices must be finite and greater than zero")
    return prices


def simple_returns(close_prices: Iterable[float]) -> tuple[float, ...]:
    """Calculate simple close-to-close returns; input must be chronological."""
    prices = validate_close_series(close_prices)
    return tuple((prices[i] / prices[i - 1]) - 1.0 for i in range(1, len(prices)))


def max_drawdown(equity_curve: Iterable[float]) -> float:
    """Return maximum peak-to-trough drawdown as a non-positive fraction."""
    values = tuple(float(value) for value in equity_curve)
    if not values:
        raise ValueError("equity curve cannot be empty")
    if any(not isfinite(value) or value <= 0 for value in values):
        raise ValueError("equity values must be finite and greater than zero")
    peak = values[0]
    worst = 0.0
    for value in values:
        peak = max(peak, value)
        worst = min(worst, value / peak - 1.0)
    return worst


def risk_capped_quantity(
    *,
    equity: float,
    risk_fraction: float,
    entry_price: float,
    stop_price: float,
    max_notional_fraction: float = 1.0,
) -> float:
    """Calculate a long-position quantity bounded by risk and notional caps.

    This is an educational sizing primitive, not a recommendation to trade.
    Fees, slippage, gaps, liquidity, taxes, FX conversion, and instrument
    multipliers are intentionally not inferred and must be modelled separately.
    """
    numbers = (equity, risk_fraction, entry_price, stop_price, max_notional_fraction)
    if any(not isfinite(float(x)) for x in numbers):
        raise ValueError("all inputs must be finite")
    if equity <= 0 or entry_price <= 0 or stop_price <= 0:
        raise ValueError("equity and prices must be greater than zero")
    if not 0 < risk_fraction <= 1:
        raise ValueError("risk_fraction must be in (0, 1]")
    if not 0 < max_notional_fraction <= 1:
        raise ValueError("max_notional_fraction must be in (0, 1]")
    if stop_price >= entry_price:
        raise ValueError("long-position stop_price must be below entry_price")

    risk_per_unit = entry_price - stop_price
    risk_limited_quantity = (equity * risk_fraction) / risk_per_unit
    notional_limited_quantity = (equity * max_notional_fraction) / entry_price
    return max(0.0, min(risk_limited_quantity, notional_limited_quantity))


def enforce_drawdown_limit(equity_curve: Sequence[float], limit_fraction: float) -> bool:
    """Return True only when observed drawdown remains within the declared limit."""
    if not isfinite(float(limit_fraction)) or not 0 < limit_fraction < 1:
        raise ValueError("limit_fraction must be in (0, 1)")
    return max_drawdown(equity_curve) >= -limit_fraction
