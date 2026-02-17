"""
Strategy base class for backtesting.

This module provides the abstract base class that all trading strategies inherit from.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

import pandas as pd

from copilot_quant.backtest.orders import Order


class Strategy(ABC):
    """
    Abstract base class for trading strategies.
    
    All custom strategies must inherit from this class and implement
    the on_data method. Optional callbacks can be overridden for additional
    functionality.
    
    Example:
        >>> class BuyAndHold(Strategy):
        ...     def initialize(self):
        ...         self.invested = False
        ...     
        ...     def on_data(self, timestamp, data):
        ...         if not self.invested:
        ...             self.invested = True
        ...             return [Order(symbol='SPY', quantity=100, 
        ...                          order_type='market', side='buy')]
        ...         return []
    """
    
    def __init__(self):
        """Initialize strategy."""
        self.name = self.__class__.__name__
    
    @abstractmethod
    def on_data(self, timestamp: datetime, data: pd.DataFrame) -> List[Order]:
        """
        Called on each new data point during backtesting.
        
        This is the main strategy logic that determines what orders to place
        based on the current market data.
        
        Args:
            timestamp: Current timestamp in the backtest
            data: DataFrame with current and historical market data
                  Index: DatetimeIndex
                  Columns: Multi-level (Metric, Symbol) or Symbol-specific
        
        Returns:
            List of Order objects to execute. Return empty list for no orders.
        
        Note:
            Avoid look-ahead bias - only use data available up to timestamp.
        """
        pass
    
    def on_fill(self, fill) -> None:
        """
        Called when an order is filled.
        
        Override this method to track fills or adjust strategy state.
        
        Args:
            fill: Fill object containing order execution details
        """
        pass
    
    def initialize(self) -> None:
        """
        Called before backtest starts.
        
        Override this method to initialize strategy state, indicators, etc.
        """
        pass
    
    def finalize(self) -> None:
        """
        Called after backtest ends.
        
        Override this method to perform cleanup or final calculations.
        """
        pass
    
    def __repr__(self) -> str:
        """String representation of strategy."""
        return f"{self.name}()"
