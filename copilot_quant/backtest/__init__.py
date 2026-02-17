"""
Backtesting module for strategy testing and validation.

This module provides the core backtesting engine and supporting classes
for testing trading strategies against historical market data.
"""

from copilot_quant.backtest.engine import BacktestEngine
from copilot_quant.backtest.orders import Fill, Order, Position
from copilot_quant.backtest.results import BacktestResult
from copilot_quant.backtest.strategy import Strategy

__all__ = [
    "BacktestEngine",
    "Strategy",
    "Order",
    "Fill",
    "Position",
    "BacktestResult",
]
