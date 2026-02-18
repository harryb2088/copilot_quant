"""
Backtest results and analysis.

This module provides classes for storing and analyzing backtest results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from copilot_quant.backtest.orders import Fill


@dataclass
class BacktestResult:
    """
    Stores and provides access to backtest outcomes.
    
    Attributes:
        strategy_name: Name of the strategy that was tested
        start_date: Start date of the backtest
        end_date: End date of the backtest
        initial_capital: Starting capital
        final_capital: Ending capital (cash + positions)
        total_return: Total return as a decimal (e.g., 0.15 = 15%)
        trades: List of all fills executed during backtest
        portfolio_history: DataFrame with portfolio value over time
        positions_history: DataFrame with position details over time
    """
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    trades: List[Fill] = field(default_factory=list)
    portfolio_history: pd.DataFrame = field(default_factory=pd.DataFrame)
    positions_history: pd.DataFrame = field(default_factory=pd.DataFrame)
    
    def get_trade_log(self) -> pd.DataFrame:
        """
        Return DataFrame of all trades.
        
        Returns:
            DataFrame with columns:
                - timestamp: Time of fill
                - symbol: Symbol traded
                - side: 'buy' or 'sell'
                - quantity: Quantity filled
                - price: Fill price
                - commission: Commission paid
                - total_cost: Total cost including commission
        """
        if not self.trades:
            return pd.DataFrame(columns=[
                'timestamp', 'symbol', 'side', 'quantity', 
                'price', 'commission', 'total_cost'
            ])
        
        trade_data = []
        for fill in self.trades:
            trade_data.append({
                'timestamp': fill.timestamp,
                'symbol': fill.order.symbol,
                'side': fill.order.side,
                'quantity': fill.fill_quantity,
                'price': fill.fill_price,
                'commission': fill.commission,
                'total_cost': fill.total_cost,
            })
        
        df = pd.DataFrame(trade_data)
        df = df.set_index('timestamp')
        return df
    
    def get_equity_curve(self) -> pd.Series:
        """
        Return time series of portfolio values.
        
        Returns:
            Series with DatetimeIndex and portfolio values
        """
        if self.portfolio_history.empty:
            return pd.Series(dtype=float)
        
        if 'portfolio_value' in self.portfolio_history.columns:
            return self.portfolio_history['portfolio_value']
        
        return pd.Series(dtype=float)
    
    def get_summary_stats(self, risk_free_rate: float = 0.02) -> Dict:
        """
        Calculate comprehensive summary statistics for the backtest.
        
        This method computes all performance metrics including returns,
        risk metrics (Sharpe, Sortino, drawdown), and trade statistics.
        
        Args:
            risk_free_rate: Annual risk-free rate for Sharpe/Sortino (default: 2%)
        
        Returns:
            Dictionary with comprehensive performance metrics including:
                - Basic stats (dates, capital, returns)
                - Risk metrics (Sharpe, Sortino, volatility, max drawdown)
                - Trade statistics (count, win rate, profit factor)
        """
        # Import here to avoid circular dependency
        from copilot_quant.backtest.metrics import PerformanceAnalyzer
        
        # Basic stats
        stats = {
            'strategy_name': self.strategy_name,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'duration_days': (self.end_date - self.start_date).days,
            'initial_capital': self.initial_capital,
            'final_capital': self.final_capital,
            'total_return': self.total_return,
            'total_return_pct': self.total_return * 100,
            'total_trades': len(self.trades),
        }
        
        # Calculate commission totals if we have trades
        if self.trades:
            trade_log = self.get_trade_log()
            stats['total_commission'] = trade_log['commission'].sum()
            stats['buy_trades'] = len(trade_log[trade_log['side'] == 'buy'])
            stats['sell_trades'] = len(trade_log[trade_log['side'] == 'sell'])
        
        # Calculate advanced metrics using PerformanceAnalyzer
        equity_curve = self.get_equity_curve()
        if not equity_curve.empty:
            analyzer = PerformanceAnalyzer(risk_free_rate=risk_free_rate)
            metrics = analyzer.calculate_metrics(
                equity_curve=equity_curve,
                trades=self.trades,
                initial_capital=self.initial_capital
            )
            
            # Merge advanced metrics into stats
            stats.update(metrics)
        
        return stats
    
    def get_performance_metrics(self, risk_free_rate: float = 0.02) -> Dict:
        """
        Get detailed performance metrics.
        
        This is a convenience method that returns the same metrics as
        get_summary_stats() but with a more descriptive name.
        
        Args:
            risk_free_rate: Annual risk-free rate for Sharpe/Sortino (default: 2%)
        
        Returns:
            Dictionary with comprehensive performance metrics
        """
        return self.get_summary_stats(risk_free_rate=risk_free_rate)
    
    @property
    def metrics(self) -> Dict:
        """
        Get performance metrics as a property for convenience.
        
        Returns:
            Dictionary with comprehensive performance metrics
        """
        return self.get_summary_stats()
    
    @property
    def equity_curve(self) -> pd.Series:
        """
        Get equity curve as a property for convenience.
        
        Returns:
            Series with DatetimeIndex and portfolio values
        """
        return self.get_equity_curve()
    
    def __repr__(self) -> str:
        """String representation of backtest result."""
        return (
            f"BacktestResult(strategy={self.strategy_name}, "
            f"return={self.total_return:.2%}, "
            f"trades={len(self.trades)})"
        )
