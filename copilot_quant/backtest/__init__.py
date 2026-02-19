"""
Backtesting module for strategy testing and validation.

This module provides the core backtesting engine and supporting classes
for testing trading strategies against historical market data.
"""

# Lazy imports to avoid circular dependencies

__all__ = [
    # Core classes
    "BacktestEngine",
    "LiveStrategyEngine",
    "MultiStrategyEngine",
    "Strategy",
    "SignalBasedStrategy",
    "TradingSignal",
    "StrategyAttribution",
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


def __getattr__(name):
    """Lazy load attributes to avoid circular imports"""
    if name == 'BacktestEngine':
        from copilot_quant.backtest.engine import BacktestEngine
        return BacktestEngine
    elif name == 'PerformanceAnalyzer':
        from copilot_quant.backtest.metrics import PerformanceAnalyzer
        return PerformanceAnalyzer
    elif name == 'MultiStrategyEngine':
        from copilot_quant.backtest.multi_strategy import MultiStrategyEngine
        return MultiStrategyEngine
    elif name == 'StrategyAttribution':
        from copilot_quant.backtest.multi_strategy import StrategyAttribution
        return StrategyAttribution
    elif name == 'Fill':
        from copilot_quant.backtest.orders import Fill
        return Fill
    elif name == 'Order':
        from copilot_quant.backtest.orders import Order
        return Order
    elif name == 'Position':
        from copilot_quant.backtest.orders import Position
        return Position
    elif name == 'BacktestResult':
        from copilot_quant.backtest.results import BacktestResult
        return BacktestResult
    elif name == 'SignalBasedStrategy':
        from copilot_quant.backtest.signals import SignalBasedStrategy
        return SignalBasedStrategy
    elif name == 'TradingSignal':
        from copilot_quant.backtest.signals import TradingSignal
        return TradingSignal
    elif name == 'Strategy':
        from copilot_quant.backtest.strategy import Strategy
        return Strategy
    elif name == 'LiveStrategyEngine':
        from copilot_quant.backtest.live_engine import LiveStrategyEngine
        return LiveStrategyEngine
    elif name == 'BacktestConfig':
        from copilot_quant.backtest.interfaces import BacktestConfig
        return BacktestConfig
    elif name == 'BrokerConfig':
        from copilot_quant.backtest.interfaces import BrokerConfig
        return BrokerConfig
    elif name == 'IBroker':
        from copilot_quant.backtest.interfaces import IBroker
        return IBroker
    elif name == 'IDataFeed':
        from copilot_quant.backtest.interfaces import IDataFeed
        return IDataFeed
    elif name == 'IPerformanceAnalyzer':
        from copilot_quant.backtest.interfaces import IPerformanceAnalyzer
        return IPerformanceAnalyzer
    elif name == 'IPortfolioManager':
        from copilot_quant.backtest.interfaces import IPortfolioManager
        return IPortfolioManager
    elif name == 'IResultsTracker':
        from copilot_quant.backtest.interfaces import IResultsTracker
        return IResultsTracker
    elif name == 'IStrategy':
        from copilot_quant.backtest.interfaces import IStrategy
        return IStrategy
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
