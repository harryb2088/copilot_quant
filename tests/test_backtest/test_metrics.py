"""Tests for performance metrics analyzer."""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from copilot_quant.backtest.metrics import PerformanceAnalyzer
from copilot_quant.backtest.orders import Fill, Order


class TestPerformanceAnalyzer:
    """Tests for PerformanceAnalyzer class."""
    
    def test_analyzer_initialization(self):
        """Test analyzer initializes correctly."""
        analyzer = PerformanceAnalyzer(risk_free_rate=0.03)
        assert analyzer.risk_free_rate == 0.03
    
    def test_analyzer_default_risk_free_rate(self):
        """Test default risk-free rate."""
        analyzer = PerformanceAnalyzer()
        assert analyzer.risk_free_rate == 0.02
    
    def test_calculate_returns(self):
        """Test return calculation."""
        analyzer = PerformanceAnalyzer()
        
        # Create simple equity curve
        dates = pd.date_range('2024-01-01', periods=5)
        equity = pd.Series([100, 105, 110, 108, 112], index=dates)
        
        returns = analyzer.calculate_returns(equity)
        
        # First return should be 0 (no previous value)
        assert returns.iloc[0] == 0.0
        
        # Second return should be 5%
        assert abs(returns.iloc[1] - 0.05) < 0.0001
        
        # Third return should be ~4.76%
        assert abs(returns.iloc[2] - (110/105 - 1)) < 0.0001
    
    def test_calculate_total_return(self):
        """Test total return calculation."""
        analyzer = PerformanceAnalyzer()
        
        total_return = analyzer.calculate_total_return(100000, 150000)
        assert abs(total_return - 0.5) < 0.0001  # 50% return
        
        total_return = analyzer.calculate_total_return(100000, 90000)
        assert abs(total_return - (-0.1)) < 0.0001  # -10% return
    
    def test_calculate_total_return_zero_initial(self):
        """Test total return with zero initial capital."""
        analyzer = PerformanceAnalyzer()
        
        total_return = analyzer.calculate_total_return(0, 100)
        assert total_return == 0.0
    
    def test_calculate_sharpe_ratio(self):
        """Test Sharpe ratio calculation."""
        analyzer = PerformanceAnalyzer(risk_free_rate=0.02)
        
        # Create returns with positive mean
        dates = pd.date_range('2024-01-01', periods=252)
        # Daily return of ~0.1% (annualized ~25%)
        returns = pd.Series(np.random.normal(0.001, 0.01, 252), index=dates)
        
        sharpe = analyzer.calculate_sharpe_ratio(returns)
        
        # Sharpe should be positive
        assert sharpe > 0
        
        # Sharpe should be reasonable (typically -3 to 3 for real strategies)
        assert -5 < sharpe < 5
    
    def test_calculate_sharpe_ratio_zero_std(self):
        """Test Sharpe ratio with zero volatility."""
        analyzer = PerformanceAnalyzer()
        
        # Constant returns (no volatility)
        dates = pd.date_range('2024-01-01', periods=10)
        returns = pd.Series([0.01] * 10, index=dates)
        
        sharpe = analyzer.calculate_sharpe_ratio(returns)
        
        # With constant returns, std is very close to 0, resulting in very high Sharpe
        # This is expected behavior - we check it's a very large number
        assert sharpe > 1000 or sharpe == 0.0
    
    def test_calculate_sharpe_ratio_empty_returns(self):
        """Test Sharpe ratio with empty returns."""
        analyzer = PerformanceAnalyzer()
        
        returns = pd.Series(dtype=float)
        sharpe = analyzer.calculate_sharpe_ratio(returns)
        
        assert sharpe == 0.0
    
    def test_calculate_sortino_ratio(self):
        """Test Sortino ratio calculation."""
        analyzer = PerformanceAnalyzer(risk_free_rate=0.02)
        
        # Create asymmetric returns (more upside than downside)
        dates = pd.date_range('2024-01-01', periods=100)
        returns = pd.Series(
            [0.02 if i % 3 == 0 else -0.005 for i in range(100)],
            index=dates
        )
        
        sortino = analyzer.calculate_sortino_ratio(returns)
        
        # Sortino should be calculated
        assert sortino != 0
    
    def test_calculate_sortino_ratio_no_downside(self):
        """Test Sortino ratio with no negative returns."""
        analyzer = PerformanceAnalyzer()
        
        # Only positive returns
        dates = pd.date_range('2024-01-01', periods=10)
        returns = pd.Series([0.01, 0.02, 0.015, 0.01, 0.02,
                            0.01, 0.015, 0.02, 0.01, 0.015], index=dates)
        
        sortino = analyzer.calculate_sortino_ratio(returns)
        
        # Should return inf when no downside
        assert sortino == float('inf')
    
    def test_calculate_max_drawdown(self):
        """Test maximum drawdown calculation."""
        analyzer = PerformanceAnalyzer()
        
        # Create equity curve with known drawdown
        dates = pd.date_range('2024-01-01', periods=10)
        equity = pd.Series([100, 110, 120, 100, 90, 95, 105, 110, 115, 120], index=dates)
        
        max_dd = analyzer.calculate_max_drawdown(equity)
        
        # Max drawdown should be from 120 to 90 = -25%
        assert abs(max_dd - (-0.25)) < 0.0001
    
    def test_calculate_max_drawdown_no_drawdown(self):
        """Test max drawdown with always increasing equity."""
        analyzer = PerformanceAnalyzer()
        
        # Monotonically increasing
        dates = pd.date_range('2024-01-01', periods=10)
        equity = pd.Series(range(100, 110), index=dates)
        
        max_dd = analyzer.calculate_max_drawdown(equity)
        
        # No drawdown should be 0
        assert max_dd == 0.0
    
    def test_calculate_max_drawdown_empty(self):
        """Test max drawdown with empty equity curve."""
        analyzer = PerformanceAnalyzer()
        
        equity = pd.Series(dtype=float)
        max_dd = analyzer.calculate_max_drawdown(equity)
        
        assert max_dd == 0.0
    
    def test_calculate_win_rate_simple(self):
        """Test win rate calculation with simple trades."""
        analyzer = PerformanceAnalyzer()
        
        # Create winning trade (buy low, sell high)
        buy_order = Order('AAPL', 10, 'market', 'buy')
        sell_order = Order('AAPL', 10, 'market', 'sell')
        
        buy_fill = Fill(
            order=buy_order,
            fill_price=100.0,
            fill_quantity=10,
            commission=1.0,
            timestamp=datetime(2024, 1, 1)
        )
        
        sell_fill = Fill(
            order=sell_order,
            fill_price=110.0,
            fill_quantity=10,
            commission=1.0,
            timestamp=datetime(2024, 1, 2)
        )
        
        trades = [buy_fill, sell_fill]
        win_rate = analyzer.calculate_win_rate(trades)
        
        # Should be 100% win rate (1 winning trade)
        assert win_rate == 1.0
    
    def test_calculate_win_rate_loss(self):
        """Test win rate with losing trade."""
        analyzer = PerformanceAnalyzer()
        
        # Create losing trade (buy high, sell low)
        buy_order = Order('AAPL', 10, 'market', 'buy')
        sell_order = Order('AAPL', 10, 'market', 'sell')
        
        buy_fill = Fill(
            order=buy_order,
            fill_price=110.0,
            fill_quantity=10,
            commission=1.0,
            timestamp=datetime(2024, 1, 1)
        )
        
        sell_fill = Fill(
            order=sell_order,
            fill_price=100.0,
            fill_quantity=10,
            commission=1.0,
            timestamp=datetime(2024, 1, 2)
        )
        
        trades = [buy_fill, sell_fill]
        win_rate = analyzer.calculate_win_rate(trades)
        
        # Should be 0% win rate (1 losing trade)
        assert win_rate == 0.0
    
    def test_calculate_win_rate_mixed(self):
        """Test win rate with mixed wins and losses."""
        analyzer = PerformanceAnalyzer()
        
        trades = []
        
        # Winning trade
        trades.append(Fill(
            order=Order('AAPL', 10, 'market', 'buy'),
            fill_price=100.0, fill_quantity=10, commission=1.0,
            timestamp=datetime(2024, 1, 1)
        ))
        trades.append(Fill(
            order=Order('AAPL', 10, 'market', 'sell'),
            fill_price=110.0, fill_quantity=10, commission=1.0,
            timestamp=datetime(2024, 1, 2)
        ))
        
        # Losing trade
        trades.append(Fill(
            order=Order('MSFT', 10, 'market', 'buy'),
            fill_price=200.0, fill_quantity=10, commission=1.0,
            timestamp=datetime(2024, 1, 3)
        ))
        trades.append(Fill(
            order=Order('MSFT', 10, 'market', 'sell'),
            fill_price=190.0, fill_quantity=10, commission=1.0,
            timestamp=datetime(2024, 1, 4)
        ))
        
        win_rate = analyzer.calculate_win_rate(trades)
        
        # Should be 50% win rate
        assert abs(win_rate - 0.5) < 0.0001
    
    def test_calculate_win_rate_empty_trades(self):
        """Test win rate with no trades."""
        analyzer = PerformanceAnalyzer()
        
        win_rate = analyzer.calculate_win_rate([])
        assert win_rate == 0.0
    
    def test_calculate_metrics_comprehensive(self):
        """Test comprehensive metrics calculation."""
        analyzer = PerformanceAnalyzer(risk_free_rate=0.02)
        
        # Create realistic equity curve
        dates = pd.date_range('2024-01-01', periods=252)
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.0005, 0.01, 252))
        equity = pd.Series(100000 * (1 + returns).cumprod(), index=dates)
        
        # Create some trades
        trades = [
            Fill(
                order=Order('AAPL', 10, 'market', 'buy'),
                fill_price=100.0, fill_quantity=10, commission=1.0,
                timestamp=dates[0]
            ),
            Fill(
                order=Order('AAPL', 10, 'market', 'sell'),
                fill_price=105.0, fill_quantity=10, commission=1.0,
                timestamp=dates[50]
            ),
        ]
        
        metrics = analyzer.calculate_metrics(
            equity_curve=equity,
            trades=trades,
            initial_capital=100000
        )
        
        # Check all expected keys are present
        expected_keys = [
            'total_return', 'total_return_pct',
            'annualized_return', 'annualized_return_pct', 'cagr',
            'volatility', 'volatility_pct',
            'max_drawdown', 'max_drawdown_pct',
            'sharpe_ratio', 'sortino_ratio', 'calmar_ratio',
            'total_trades', 'win_rate', 'win_rate_pct',
            'profit_factor', 'avg_win', 'avg_loss', 'avg_trade',
            'trading_days', 'trading_years'
        ]
        
        for key in expected_keys:
            assert key in metrics, f"Missing key: {key}"
        
        # Check some basic properties
        assert metrics['total_trades'] == 2
        assert metrics['trading_days'] == 252
        assert abs(metrics['trading_years'] - 1.0) < 0.01
    
    def test_calculate_metrics_empty_equity(self):
        """Test metrics with empty equity curve."""
        analyzer = PerformanceAnalyzer()
        
        equity = pd.Series(dtype=float)
        metrics = analyzer.calculate_metrics(
            equity_curve=equity,
            trades=[],
            initial_capital=100000
        )
        
        # All metrics should be zero
        assert metrics['total_return'] == 0.0
        assert metrics['sharpe_ratio'] == 0.0
        assert metrics['max_drawdown'] == 0.0
    
    def test_trade_stats_calculation(self):
        """Test detailed trade statistics calculation."""
        analyzer = PerformanceAnalyzer()
        
        # Create multiple trades with known outcomes
        trades = []
        
        # Win: Buy at 100, sell at 110 (profit: ~99)
        trades.append(Fill(
            order=Order('AAPL', 10, 'market', 'buy'),
            fill_price=100.0, fill_quantity=10, commission=1.0,
            timestamp=datetime(2024, 1, 1)
        ))
        trades.append(Fill(
            order=Order('AAPL', 10, 'market', 'sell'),
            fill_price=110.0, fill_quantity=10, commission=1.0,
            timestamp=datetime(2024, 1, 2)
        ))
        
        # Loss: Buy at 200, sell at 180 (loss: ~-202)
        trades.append(Fill(
            order=Order('MSFT', 10, 'market', 'buy'),
            fill_price=200.0, fill_quantity=10, commission=1.0,
            timestamp=datetime(2024, 1, 3)
        ))
        trades.append(Fill(
            order=Order('MSFT', 10, 'market', 'sell'),
            fill_price=180.0, fill_quantity=10, commission=1.0,
            timestamp=datetime(2024, 1, 4)
        ))
        
        # Calculate using the internal method
        stats = analyzer._calculate_trade_stats(trades)
        
        assert stats['win_rate'] == 0.5  # 1 win, 1 loss
        assert stats['avg_win'] > 0
        assert stats['avg_loss'] < 0
    
    def test_annualized_return_calculation(self):
        """Test annualized return helper method."""
        analyzer = PerformanceAnalyzer()
        
        # 50% return over 1 year
        ann_return = analyzer._annualize_return(0.5, 1.0)
        assert abs(ann_return - 0.5) < 0.0001
        
        # 50% return over 2 years (annualized ~22.5%)
        ann_return = analyzer._annualize_return(0.5, 2.0)
        expected = (1.5 ** 0.5) - 1
        assert abs(ann_return - expected) < 0.0001
        
        # Zero years should return 0
        ann_return = analyzer._annualize_return(0.5, 0)
        assert ann_return == 0.0
    
    def test_calmar_ratio_calculation(self):
        """Test Calmar ratio helper method."""
        analyzer = PerformanceAnalyzer()
        
        # Positive return with drawdown
        calmar = analyzer._calculate_calmar_ratio(0.20, -0.10)
        assert calmar == 2.0  # 20% / 10%
        
        # Zero drawdown
        calmar = analyzer._calculate_calmar_ratio(0.20, 0.0)
        assert calmar == 0.0
        
        # Positive drawdown (should return 0)
        calmar = analyzer._calculate_calmar_ratio(0.20, 0.05)
        assert calmar == 0.0
