"""
Backtesting module for strategy testing and validation.

This module provides the core backtesting engine and supporting classes
for testing trading strategies against historical market data.
"""

from copilot_quant.backtest.engine import BacktestEngine
from copilot_quant.backtest.metrics import PerformanceAnalyzer
from copilot_quant.backtest.orders import Fill, Order, Position
from copilot_quant.backtest.results import BacktestResult
from copilot_quant.backtest.strategy import Strategy

# Interface definitions for advanced use cases
from copilot_quant.backtest.interfaces import (
    BacktestConfig,
    BrokerConfig,
    IBroker,
    IDataFeed,
    IPerformanceAnalyzer,
    IPortfolioManager,
    IResultsTracker,
    IStrategy,
)

__all__ = [
    # Core classes
    "BacktestEngine",
    "Strategy",
    "Order",
    "Fill",
    "Position",
    "BacktestResult",
    "PerformanceAnalyzer",
    # Interface definitions
    "IDataFeed",
    "IBroker",
    "IPortfolioManager",
    "IPerformanceAnalyzer",
    "IResultsTracker",
    "IStrategy",
    "BacktestConfig",
    "BrokerConfig",
]
