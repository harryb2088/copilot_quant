"""
Trading signal system for signal-based portfolio allocation.

This module provides the TradingSignal class and SignalBasedStrategy base class
for implementing signal-based trading strategies that compete for capital based
on signal quality rather than pre-allocated capital pods.
"""

from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import pandas as pd

from copilot_quant.backtest.strategy import Strategy


@dataclass
class TradingSignal:
    """
    Represents a trading signal with quality metrics.
    
    Attributes:
        symbol: Ticker symbol (e.g., 'AAPL', 'SPY')
        side: Order side ('buy' or 'sell')
        confidence: Signal confidence level (0.0 to 1.0)
        sharpe_estimate: Estimated Sharpe ratio for this trade
        entry_price: Expected entry price
        stop_loss: Optional stop loss price
        take_profit: Optional take profit price
        strategy_name: Name of strategy generating this signal
    """
    symbol: str
    side: str  # 'buy' or 'sell'
    confidence: float  # 0.0 to 1.0
    sharpe_estimate: float
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    strategy_name: str = ""
    
    def __post_init__(self):
        """Validate signal after initialization."""
        if self.side not in ['buy', 'sell']:
            raise ValueError(f"Invalid side: {self.side}. Must be 'buy' or 'sell'")
        
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Invalid confidence: {self.confidence}. Must be between 0.0 and 1.0")
        
        if self.entry_price <= 0:
            raise ValueError(f"Invalid entry_price: {self.entry_price}. Must be positive")
        
        if self.stop_loss is not None and self.stop_loss <= 0:
            raise ValueError(f"Invalid stop_loss: {self.stop_loss}. Must be positive")
        
        if self.take_profit is not None and self.take_profit <= 0:
            raise ValueError(f"Invalid take_profit: {self.take_profit}. Must be positive")
    
    @property
    def quality_score(self) -> float:
        """
        Calculate signal quality score for ranking.
        
        Combines confidence and estimated Sharpe ratio to determine signal quality.
        Higher scores indicate better quality signals that deserve more capital.
        
        Returns:
            Quality score (0.0 to 1.0)
        """
        # Normalize Sharpe estimate (cap at 2.0 for scoring purposes)
        normalized_sharpe = min(self.sharpe_estimate / 2.0, 1.0)
        
        # Combine confidence and Sharpe estimate
        return self.confidence * normalized_sharpe


class SignalBasedStrategy(Strategy):
    """
    Base class for strategies that generate TradingSignal objects.
    
    Unlike traditional strategies that return Order objects, signal-based
    strategies return TradingSignal objects with quality metrics. The
    MultiStrategyEngine uses these quality metrics to dynamically size
    positions and allocate capital to the best signals.
    
    Subclasses must implement generate_signals() instead of on_data().
    
    Example:
        >>> class MeanReversionSignals(SignalBasedStrategy):
        ...     def generate_signals(self, timestamp, data):
        ...         signals = []
        ...         # Analyze data and generate signals
        ...         if condition_met:
        ...             signals.append(TradingSignal(
        ...                 symbol='AAPL',
        ...                 side='buy',
        ...                 confidence=0.8,
        ...                 sharpe_estimate=1.5,
        ...                 entry_price=150.0,
        ...                 strategy_name=self.name
        ...             ))
        ...         return signals
    """
    
    @abstractmethod
    def generate_signals(
        self,
        timestamp: datetime,
        data: pd.DataFrame
    ) -> List[TradingSignal]:
        """
        Generate trading signals based on market data.
        
        This is the main strategy logic that analyzes market data and
        produces TradingSignal objects with quality metrics.
        
        Args:
            timestamp: Current timestamp in the backtest
            data: DataFrame with current and historical market data
                  Index: DatetimeIndex
                  Columns: Multi-level (Metric, Symbol) or Symbol-specific
        
        Returns:
            List of TradingSignal objects. Return empty list for no signals.
        
        Note:
            Avoid look-ahead bias - only use data available up to timestamp.
        """
        pass
    
    def on_data(self, timestamp: datetime, data: pd.DataFrame) -> List:
        """
        Internal method - do not override.
        
        This method is called by BacktestEngine but should not be used
        directly in SignalBasedStrategy subclasses. Override generate_signals()
        instead.
        
        Returns:
            Empty list (signals are generated via generate_signals())
        """
        # Signal-based strategies don't use on_data directly
        # They use generate_signals() which is called by MultiStrategyEngine
        return []
