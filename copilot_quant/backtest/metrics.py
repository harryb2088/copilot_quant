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
        # Calculate returns without forward-filling missing values
        # The fillna(0) handles the first NaN value from pct_change
        try:
            # Pandas >= 2.1 requires explicit fill_method
            return equity_curve.pct_change(fill_method=None).fillna(0)
        except TypeError:
            # Older pandas versions don't have fill_method parameter
            return equity_curve.pct_change().fillna(0)
    
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
    
    def calculate_portfolio_metrics(
        self,
        portfolio_history: pd.DataFrame,
        positions: Dict,
        initial_capital: float
    ) -> Dict:
        """
        Calculate portfolio-level metrics from portfolio history.
        
        This method computes institutional metrics including cash allocation,
        exposure, leverage, and position concentration.
        
        Args:
            portfolio_history: DataFrame with columns:
                - timestamp: datetime index
                - portfolio_value: total portfolio value
                - cash: cash balance
                - positions_value: total positions value
                - num_positions: number of open positions
            positions: Dictionary of current positions {symbol: Position}
            initial_capital: Starting capital
        
        Returns:
            Dictionary containing portfolio-level metrics
        """
        if portfolio_history.empty:
            return self._empty_portfolio_metrics()
        
        latest = portfolio_history.iloc[-1]
        
        # Cash metrics
        cash_balance = latest.get('cash', 0)
        portfolio_value = latest.get('portfolio_value', initial_capital)
        positions_value = latest.get('positions_value', 0)
        
        cash_allocation = cash_balance / portfolio_value if portfolio_value > 0 else 0.0
        
        # Exposure metrics
        # Gross exposure = sum of absolute position values
        # Net exposure = sum of signed position values (long - short)
        long_value = 0
        short_value = 0
        
        for position in positions.values():
            market_value = abs(position.quantity * position.avg_entry_price)
            if position.quantity > 0:
                long_value += market_value
            elif position.quantity < 0:
                short_value += market_value
        
        gross_exposure = (long_value + short_value) / portfolio_value if portfolio_value > 0 else 0.0
        net_exposure = (long_value - short_value) / portfolio_value if portfolio_value > 0 else 0.0
        long_exposure = long_value / portfolio_value if portfolio_value > 0 else 0.0
        short_exposure = short_value / portfolio_value if portfolio_value > 0 else 0.0
        
        # Leverage ratio
        leverage_ratio = gross_exposure + cash_allocation
        
        # Position concentration
        num_positions = len([p for p in positions.values() if p.quantity != 0])
        
        if num_positions > 0 and portfolio_value > 0:
            position_sizes = [
                abs(p.quantity * p.avg_entry_price) / portfolio_value 
                for p in positions.values() if p.quantity != 0
            ]
            largest_position = max(position_sizes) if position_sizes else 0.0
            avg_position_size = np.mean(position_sizes) if position_sizes else 0.0
            
            # Top 5 concentration
            sorted_sizes = sorted(position_sizes, reverse=True)
            top_5_concentration = sum(sorted_sizes[:5]) if len(sorted_sizes) >= 5 else sum(sorted_sizes)
        else:
            largest_position = 0.0
            avg_position_size = 0.0
            top_5_concentration = 0.0
        
        return {
            # Cash metrics
            'cash_balance': cash_balance,
            'cash_allocation': cash_allocation,
            'cash_allocation_pct': cash_allocation * 100,
            
            # Exposure metrics
            'gross_exposure': gross_exposure,
            'gross_exposure_pct': gross_exposure * 100,
            'net_exposure': net_exposure,
            'net_exposure_pct': net_exposure * 100,
            'long_exposure': long_exposure,
            'long_exposure_pct': long_exposure * 100,
            'short_exposure': short_exposure,
            'short_exposure_pct': short_exposure * 100,
            
            # Leverage
            'leverage_ratio': leverage_ratio,
            
            # Position metrics
            'num_positions': num_positions,
            'largest_position': largest_position,
            'largest_position_pct': largest_position * 100,
            'avg_position_size': avg_position_size,
            'avg_position_size_pct': avg_position_size * 100,
            'top_5_concentration': top_5_concentration,
            'top_5_concentration_pct': top_5_concentration * 100,
            
            # Portfolio value
            'portfolio_value': portfolio_value,
            'positions_value': positions_value,
        }
    
    def calculate_turnover(
        self,
        trades: List[Fill],
        avg_portfolio_value: float,
        period_days: int = 30
    ) -> float:
        """
        Calculate portfolio turnover rate.
        
        Turnover measures how frequently the portfolio is traded.
        Formula: (Total Trade Value / Avg Portfolio Value) / (Days / 365)
        
        Args:
            trades: List of all trade fills
            avg_portfolio_value: Average portfolio value over the period
            period_days: Number of days in the measurement period
        
        Returns:
            Annual turnover rate as decimal (e.g., 0.45 = 45% annual turnover)
        """
        if not trades or avg_portfolio_value == 0 or period_days == 0:
            return 0.0
        
        # Calculate total trade value (buys + sells)
        total_trade_value = sum(
            abs(fill.fill_price * fill.fill_quantity) 
            for fill in trades
        )
        
        # Annualize the turnover
        annualization_factor = 365.0 / period_days
        turnover = (total_trade_value / avg_portfolio_value) * annualization_factor
        
        return turnover
    
    def calculate_var(
        self,
        returns: pd.Series,
        confidence_level: float = 0.95,
        portfolio_value: float = 1000000
    ) -> float:
        """
        Calculate Value at Risk (VaR) using historical simulation.
        
        VaR estimates the maximum expected loss at a given confidence level.
        
        Args:
            returns: Series of period returns
            confidence_level: Confidence level (e.g., 0.95 for 95%)
            portfolio_value: Current portfolio value
        
        Returns:
            VaR in dollars (negative value represents potential loss)
        """
        if len(returns) == 0:
            return 0.0
        
        # Calculate the percentile
        var_percentile = 1 - confidence_level
        var_return = np.percentile(returns, var_percentile * 100)
        
        # Convert to dollar value
        var_dollars = var_return * portfolio_value
        
        return var_dollars
    
    def calculate_cvar(
        self,
        returns: pd.Series,
        confidence_level: float = 0.95,
        portfolio_value: float = 1000000
    ) -> float:
        """
        Calculate Conditional Value at Risk (CVaR), also known as Expected Shortfall.
        
        CVaR is the expected loss given that the loss exceeds VaR.
        
        Args:
            returns: Series of period returns
            confidence_level: Confidence level (e.g., 0.95 for 95%)
            portfolio_value: Current portfolio value
        
        Returns:
            CVaR in dollars (negative value represents expected tail loss)
        """
        if len(returns) == 0:
            return 0.0
        
        # Calculate VaR threshold
        var_percentile = 1 - confidence_level
        var_threshold = np.percentile(returns, var_percentile * 100)
        
        # Calculate mean of returns below VaR threshold
        tail_returns = returns[returns <= var_threshold]
        
        if len(tail_returns) == 0:
            return var_threshold * portfolio_value
        
        cvar_return = tail_returns.mean()
        cvar_dollars = cvar_return * portfolio_value
        
        return cvar_dollars
    
    def calculate_beta(
        self,
        portfolio_returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> float:
        """
        Calculate portfolio beta relative to a benchmark.
        
        Beta measures the portfolio's sensitivity to benchmark movements.
        Beta = Covariance(Portfolio, Benchmark) / Variance(Benchmark)
        
        Args:
            portfolio_returns: Series of portfolio returns
            benchmark_returns: Series of benchmark returns (e.g., SPY)
        
        Returns:
            Beta coefficient (1.0 = same volatility as benchmark)
        """
        if len(portfolio_returns) == 0 or len(benchmark_returns) == 0:
            return 0.0
        
        # Align the series
        aligned = pd.DataFrame({
            'portfolio': portfolio_returns,
            'benchmark': benchmark_returns
        }).dropna()
        
        if len(aligned) < 2:
            return 0.0
        
        # Calculate covariance and variance
        covariance = aligned['portfolio'].cov(aligned['benchmark'])
        benchmark_variance = aligned['benchmark'].var()
        
        if benchmark_variance == 0:
            return 0.0
        
        beta = covariance / benchmark_variance
        
        return beta
    
    def calculate_drawdown_duration(self, equity_curve: pd.Series) -> Dict:
        """
        Calculate drawdown duration metrics.
        
        Args:
            equity_curve: Time series of portfolio values
        
        Returns:
            Dictionary with drawdown duration metrics
        """
        if len(equity_curve) == 0:
            return {
                'max_drawdown_duration_days': 0,
                'avg_drawdown_duration_days': 0.0,
                'current_drawdown_duration_days': 0,
                'underwater_periods': 0
            }
        
        # Calculate running maximum
        running_max = equity_curve.expanding().max()
        
        # Identify underwater periods (when below peak)
        is_underwater = equity_curve < running_max
        
        # Find continuous underwater periods
        underwater_periods = []
        current_duration = 0
        
        for underwater in is_underwater:
            if underwater:
                current_duration += 1
            else:
                if current_duration > 0:
                    underwater_periods.append(current_duration)
                    current_duration = 0
        
        # Add final period if still underwater
        if current_duration > 0:
            underwater_periods.append(current_duration)
        
        max_duration = max(underwater_periods) if underwater_periods else 0
        avg_duration = np.mean(underwater_periods) if underwater_periods else 0.0
        num_periods = len(underwater_periods)
        
        # Current drawdown duration
        current_dd_duration = current_duration
        
        return {
            'max_drawdown_duration_days': max_duration,
            'avg_drawdown_duration_days': avg_duration,
            'current_drawdown_duration_days': current_dd_duration,
            'underwater_periods': num_periods
        }
    
    def _empty_portfolio_metrics(self) -> Dict:
        """Return empty portfolio metrics when no data available."""
        return {
            'cash_balance': 0.0,
            'cash_allocation': 0.0,
            'cash_allocation_pct': 0.0,
            'gross_exposure': 0.0,
            'gross_exposure_pct': 0.0,
            'net_exposure': 0.0,
            'net_exposure_pct': 0.0,
            'long_exposure': 0.0,
            'long_exposure_pct': 0.0,
            'short_exposure': 0.0,
            'short_exposure_pct': 0.0,
            'leverage_ratio': 0.0,
            'num_positions': 0,
            'largest_position': 0.0,
            'largest_position_pct': 0.0,
            'avg_position_size': 0.0,
            'avg_position_size_pct': 0.0,
            'top_5_concentration': 0.0,
            'top_5_concentration_pct': 0.0,
            'portfolio_value': 0.0,
            'positions_value': 0.0,
        }
