"""
Performance metrics and analysis for backtesting.

This module provides comprehensive performance metrics calculation including
returns, risk metrics (Sharpe, Sortino), drawdown analysis, and trade statistics.
"""

from typing import Dict, List

import numpy as np
import pandas as pd

from copilot_quant.backtest.orders import Fill


class PerformanceAnalyzer:
    """
    Calculate comprehensive performance metrics for backtest results.
    
    This analyzer computes standard quantitative metrics including:
    - Total and annualized returns
    - Risk metrics (Sharpe ratio, Sortino ratio, volatility)
    - Drawdown analysis (maximum drawdown, drawdown duration)
    - Trade statistics (win rate, profit factor, average win/loss)
    
    Example:
        >>> analyzer = PerformanceAnalyzer(risk_free_rate=0.02)
        >>> metrics = analyzer.calculate_metrics(
        ...     equity_curve=equity_series,
        ...     trades=trade_list,
        ...     initial_capital=100000
        ... )
        >>> print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    """
    
    def __init__(self, risk_free_rate: float = 0.02):
        """
        Initialize performance analyzer.
        
        Args:
            risk_free_rate: Annual risk-free rate for Sharpe/Sortino calculations
                           (e.g., 0.02 = 2% annual rate)
        """
        self.risk_free_rate = risk_free_rate
    
    def calculate_metrics(
        self,
        equity_curve: pd.Series,
        trades: List[Fill],
        initial_capital: float
    ) -> Dict:
        """
        Calculate all performance metrics.
        
        Args:
            equity_curve: Time series of portfolio values
            trades: List of all trade fills
            initial_capital: Starting capital
        
        Returns:
            Dictionary containing all calculated metrics
        """
        if equity_curve.empty:
            return self._empty_metrics()
        
        final_capital = equity_curve.iloc[-1]
        returns = self.calculate_returns(equity_curve)
        
        # Time metrics
        days = len(equity_curve)
        years = days / 252 if days > 0 else 1
        
        # Return metrics
        total_return = self.calculate_total_return(initial_capital, final_capital)
        annualized_return = self._annualize_return(total_return, years)
        
        # Risk metrics
        max_dd = self.calculate_max_drawdown(equity_curve)
        sharpe = self.calculate_sharpe_ratio(returns)
        sortino = self.calculate_sortino_ratio(returns)
        calmar = self._calculate_calmar_ratio(annualized_return, max_dd)
        
        # Trade statistics
        trade_stats = self._calculate_trade_stats(trades)
        
        return {
            # Returns
            'total_return': total_return,
            'total_return_pct': total_return * 100,
            'annualized_return': annualized_return,
            'annualized_return_pct': annualized_return * 100,
            'cagr': annualized_return,
            
            # Risk metrics
            'volatility': returns.std() * np.sqrt(252) if len(returns) > 0 else 0.0,
            'volatility_pct': returns.std() * np.sqrt(252) * 100 if len(returns) > 0 else 0.0,
            'max_drawdown': max_dd,
            'max_drawdown_pct': max_dd * 100,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'calmar_ratio': calmar,
            
            # Trade statistics
            'total_trades': len(trades),
            'win_rate': trade_stats['win_rate'],
            'win_rate_pct': trade_stats['win_rate'] * 100,
            'profit_factor': trade_stats['profit_factor'],
            'avg_win': trade_stats['avg_win'],
            'avg_loss': trade_stats['avg_loss'],
            'avg_trade': trade_stats['avg_trade'],
            
            # Time metrics
            'trading_days': days,
            'trading_years': years,
        }
    
    def calculate_returns(self, equity_curve: pd.Series) -> pd.Series:
        """
        Calculate period-over-period returns.
        
        Args:
            equity_curve: Time series of portfolio values
        
        Returns:
            Series of period returns (daily if equity_curve is daily)
        """
        return equity_curve.pct_change(fill_method=None).fillna(0)
    
    def calculate_total_return(self, initial: float, final: float) -> float:
        """
        Calculate total return.
        
        Args:
            initial: Starting capital
            final: Ending capital
        
        Returns:
            Total return as decimal (e.g., 0.15 = 15%)
        """
        if initial == 0:
            return 0.0
        return (final - initial) / initial
    
    def calculate_sharpe_ratio(
        self,
        returns: pd.Series,
        risk_free_rate: float = None
    ) -> float:
        """
        Calculate Sharpe ratio (annualized).
        
        The Sharpe ratio measures risk-adjusted return by comparing
        excess returns to volatility.
        
        Formula: (Mean Return - Risk Free Rate) / Std Dev of Returns
        
        Args:
            returns: Series of period returns
            risk_free_rate: Annual risk-free rate (uses default if None)
        
        Returns:
            Annualized Sharpe ratio
        """
        if risk_free_rate is None:
            risk_free_rate = self.risk_free_rate
        
        if len(returns) == 0 or returns.std() == 0:
            return 0.0
        
        # Convert annual risk-free rate to daily
        daily_rf = risk_free_rate / 252
        
        # Calculate excess return
        excess_return = returns.mean() - daily_rf
        
        # Calculate Sharpe ratio and annualize
        sharpe = excess_return / returns.std()
        sharpe_annualized = sharpe * np.sqrt(252)
        
        return sharpe_annualized
    
    def calculate_sortino_ratio(
        self,
        returns: pd.Series,
        risk_free_rate: float = None
    ) -> float:
        """
        Calculate Sortino ratio (annualized).
        
        The Sortino ratio is similar to Sharpe but only penalizes
        downside volatility, making it more appropriate for strategies
        with asymmetric return distributions.
        
        Formula: (Mean Return - Risk Free Rate) / Downside Deviation
        
        Args:
            returns: Series of period returns
            risk_free_rate: Annual risk-free rate (uses default if None)
        
        Returns:
            Annualized Sortino ratio
        """
        if risk_free_rate is None:
            risk_free_rate = self.risk_free_rate
        
        if len(returns) == 0:
            return 0.0
        
        # Calculate downside returns only
        downside_returns = returns[returns < 0]
        
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            # No downside volatility - return high value if positive returns
            return float('inf') if returns.mean() > 0 else 0.0
        
        # Convert annual risk-free rate to daily
        daily_rf = risk_free_rate / 252
        
        # Calculate excess return
        excess_return = returns.mean() - daily_rf
        
        # Calculate Sortino ratio and annualize
        sortino = excess_return / downside_returns.std()
        sortino_annualized = sortino * np.sqrt(252)
        
        return sortino_annualized
    
    def calculate_max_drawdown(self, equity_curve: pd.Series) -> float:
        """
        Calculate maximum drawdown.
        
        Maximum drawdown is the largest peak-to-trough decline in
        portfolio value. It measures the worst-case loss an investor
        would have experienced.
        
        Args:
            equity_curve: Time series of portfolio values
        
        Returns:
            Maximum drawdown as decimal (e.g., -0.20 = -20% drawdown)
        """
        if len(equity_curve) == 0:
            return 0.0
        
        # Calculate running maximum (peak values)
        running_max = equity_curve.expanding().max()
        
        # Calculate drawdown at each point
        drawdown = (equity_curve - running_max) / running_max
        
        # Return maximum drawdown (most negative value)
        return drawdown.min()
    
    def calculate_win_rate(self, trades: List[Fill]) -> float:
        """
        Calculate win rate from completed trades.
        
        Win rate is the percentage of profitable round-trip trades
        (buy-sell pairs). This requires matching buys with sells.
        
        Args:
            trades: List of all trade fills
        
        Returns:
            Win rate as decimal (e.g., 0.60 = 60% win rate)
        """
        if not trades:
            return 0.0
        
        # Group trades by symbol to track round trips
        symbol_trades: Dict[str, List] = {}
        
        for fill in trades:
            symbol = fill.order.symbol
            if symbol not in symbol_trades:
                symbol_trades[symbol] = []
            symbol_trades[symbol].append(fill)
        
        # Analyze each symbol's trades
        wins = 0
        total_round_trips = 0
        
        for symbol, fills in symbol_trades.items():
            position_qty = 0
            entry_value = 0
            
            for fill in fills:
                if fill.order.side == 'buy':
                    # Opening or adding to position
                    position_qty += fill.fill_quantity
                    entry_value += fill.fill_price * fill.fill_quantity + fill.commission
                else:  # sell
                    # Closing or reducing position
                    if position_qty > 0:
                        # Calculate P&L for this round trip
                        exit_value = fill.fill_price * fill.fill_quantity - fill.commission
                        avg_entry = entry_value / position_qty if position_qty > 0 else 0
                        pnl = exit_value - (avg_entry * fill.fill_quantity)
                        
                        if pnl > 0:
                            wins += 1
                        
                        total_round_trips += 1
                        
                        # Update position
                        position_qty -= fill.fill_quantity
                        if position_qty > 0:
                            entry_value = avg_entry * position_qty
                        else:
                            entry_value = 0
        
        return wins / total_round_trips if total_round_trips > 0 else 0.0
    
    def _annualize_return(self, total_return: float, years: float) -> float:
        """Annualize a total return."""
        if years <= 0:
            return 0.0
        return (1 + total_return) ** (1 / years) - 1
    
    def _calculate_calmar_ratio(
        self,
        annualized_return: float,
        max_drawdown: float
    ) -> float:
        """
        Calculate Calmar ratio.
        
        Calmar ratio = Annualized Return / Absolute Max Drawdown
        """
        if max_drawdown == 0 or max_drawdown >= 0:
            return 0.0
        
        return annualized_return / abs(max_drawdown)
    
    def _calculate_trade_stats(self, trades: List[Fill]) -> Dict:
        """Calculate detailed trade statistics."""
        if not trades:
            return {
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'avg_trade': 0.0,
            }
        
        # Group trades by symbol for P&L calculation
        symbol_trades: Dict[str, List] = {}
        
        for fill in trades:
            symbol = fill.order.symbol
            if symbol not in symbol_trades:
                symbol_trades[symbol] = []
            symbol_trades[symbol].append(fill)
        
        # Calculate P&L for each round trip
        trade_pnls = []
        
        for symbol, fills in symbol_trades.items():
            position_qty = 0
            entry_value = 0
            
            for fill in fills:
                if fill.order.side == 'buy':
                    position_qty += fill.fill_quantity
                    entry_value += fill.fill_price * fill.fill_quantity + fill.commission
                else:  # sell
                    if position_qty > 0:
                        exit_value = fill.fill_price * fill.fill_quantity - fill.commission
                        avg_entry = entry_value / position_qty if position_qty > 0 else 0
                        pnl = exit_value - (avg_entry * fill.fill_quantity)
                        trade_pnls.append(pnl)
                        
                        position_qty -= fill.fill_quantity
                        if position_qty > 0:
                            entry_value = avg_entry * position_qty
                        else:
                            entry_value = 0
        
        if not trade_pnls:
            return {
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'avg_trade': 0.0,
            }
        
        # Calculate statistics
        winning_trades = [p for p in trade_pnls if p > 0]
        losing_trades = [p for p in trade_pnls if p < 0]
        
        win_rate = len(winning_trades) / len(trade_pnls) if trade_pnls else 0.0
        avg_win = np.mean(winning_trades) if winning_trades else 0.0
        avg_loss = np.mean(losing_trades) if losing_trades else 0.0
        avg_trade = np.mean(trade_pnls)
        
        # Profit factor = Gross Profit / Gross Loss
        gross_profit = sum(winning_trades) if winning_trades else 0.0
        gross_loss = abs(sum(losing_trades)) if losing_trades else 0.0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0
        
        return {
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'avg_trade': avg_trade,
        }
    
    def _empty_metrics(self) -> Dict:
        """Return empty metrics when no data available."""
        return {
            'total_return': 0.0,
            'total_return_pct': 0.0,
            'annualized_return': 0.0,
            'annualized_return_pct': 0.0,
            'cagr': 0.0,
            'volatility': 0.0,
            'volatility_pct': 0.0,
            'max_drawdown': 0.0,
            'max_drawdown_pct': 0.0,
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'calmar_ratio': 0.0,
            'total_trades': 0,
            'win_rate': 0.0,
            'win_rate_pct': 0.0,
            'profit_factor': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'avg_trade': 0.0,
            'trading_days': 0,
            'trading_years': 0.0,
        }
