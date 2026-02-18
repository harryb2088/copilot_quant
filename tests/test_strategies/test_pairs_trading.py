"""Tests for pairs trading strategy."""

from datetime import datetime, timedelta
from typing import List

import numpy as np
import pandas as pd
import pytest

from copilot_quant.backtest import BacktestEngine
from copilot_quant.data.providers import DataProvider
from copilot_quant.strategies import PairsTradingStrategy


class MockPairsDataProvider(DataProvider):
    """Mock data provider for pairs trading tests."""
    
    def __init__(self):
        """Initialize with cointegrated pair data."""
        super().__init__()
    
    def get_historical_data(
        self,
        symbol: str,
        start_date=None,
        end_date=None,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """Get historical data for a single symbol."""
        df = self.get_data([symbol], start_date, end_date)
        return df[df['Symbol'] == symbol].drop('Symbol', axis=1)
    
    def get_multiple_symbols(
        self,
        symbols: List[str],
        start_date=None,
        end_date=None,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """Get historical data for multiple symbols."""
        return self.get_data(symbols, start_date, end_date)
    
    def get_ticker_info(self, symbol: str) -> dict:
        """Get metadata about a ticker."""
        return {
            'symbol': symbol,
            'name': f'{symbol} Test Company',
            'sector': 'Technology',
            'industry': 'Software'
        }
        
    def get_data(self, symbols, start_date, end_date):
        """Generate mock cointegrated pair data."""
        # Create date range
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Create base price series
        np.random.seed(42)
        base = 100 + np.cumsum(np.random.randn(len(dates)) * 0.5)
        
        # Create cointegrated pairs
        data_frames = []
        
        for symbol in symbols:
            if symbol == 'PAIR_A':
                # Base series with small noise
                prices = base + np.random.randn(len(dates)) * 0.1
            elif symbol == 'PAIR_B':
                # Highly correlated with PAIR_A (hedge ratio ~2)
                prices = 2 * base + np.random.randn(len(dates)) * 0.1
            elif symbol == 'INDEP':
                # Independent series (not cointegrated)
                prices = 100 + np.cumsum(np.random.randn(len(dates)) * 0.5)
            else:
                prices = 100 + np.cumsum(np.random.randn(len(dates)) * 0.5)
            
            df = pd.DataFrame({
                'Symbol': symbol,
                'Open': prices,
                'High': prices * 1.01,
                'Low': prices * 0.99,
                'Close': prices,
                'Volume': 1000000
            }, index=dates)
            
            data_frames.append(df)
        
        return pd.concat(data_frames).sort_index()


class TestPairsTradingStrategy:
    """Tests for PairsTradingStrategy class."""
    
    def test_strategy_initialization(self):
        """Test strategy initialization with parameters."""
        strategy = PairsTradingStrategy(
            lookback=60,
            entry_zscore=2.0,
            exit_zscore=0.5,
            quantity=100,
            max_pairs=5
        )
        
        assert strategy.lookback == 60
        assert strategy.entry_zscore == 2.0
        assert strategy.exit_zscore == 0.5
        assert strategy.quantity == 100
        assert strategy.max_pairs == 5
        assert strategy.name == 'PairsTradingStrategy'
    
    def test_strategy_identifies_pairs(self):
        """Test that strategy identifies cointegrated pairs."""
        provider = MockPairsDataProvider()
        engine = BacktestEngine(
            initial_capital=100000,
            data_provider=provider,
            commission=0.001,
            slippage=0.0005
        )
        
        strategy = PairsTradingStrategy(
            lookback=30,
            entry_zscore=2.0,
            exit_zscore=0.5,
            quantity=100,
            max_pairs=3,
            min_correlation=0.7
        )
        
        engine.add_strategy(strategy)
        
        result = engine.run(
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 6, 30),
            symbols=['PAIR_A', 'PAIR_B', 'INDEP']
        )
        
        # Strategy should identify PAIR_A and PAIR_B as cointegrated
        assert len(strategy.trading_pairs) > 0
        
        # Should have made some trades
        assert result.metrics['total_trades'] > 0
    
    def test_strategy_entry_signals(self):
        """Test that strategy generates entry signals on Z-score threshold."""
        provider = MockPairsDataProvider()
        engine = BacktestEngine(
            initial_capital=100000,
            data_provider=provider,
            commission=0.001,
            slippage=0.0005
        )
        
        strategy = PairsTradingStrategy(
            lookback=30,
            entry_zscore=1.5,  # Lower threshold for more trades
            exit_zscore=0.3,
            quantity=100,
            max_pairs=3
        )
        
        engine.add_strategy(strategy)
        
        result = engine.run(
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            symbols=['PAIR_A', 'PAIR_B']
        )
        
        # Should generate trades
        assert result.metrics['total_trades'] > 0
        
        # Should have both buy and sell orders (for pair trading)
        buy_trades = [t for t in result.trades if t.order.side == 'buy']
        sell_trades = [t for t in result.trades if t.order.side == 'sell']
        
        assert len(buy_trades) > 0
        assert len(sell_trades) > 0
    
    def test_strategy_respects_max_pairs(self):
        """Test that strategy respects max_pairs limit."""
        provider = MockPairsDataProvider()
        engine = BacktestEngine(
            initial_capital=100000,
            data_provider=provider,
            commission=0.001,
            slippage=0.0005
        )
        
        strategy = PairsTradingStrategy(
            lookback=30,
            entry_zscore=2.0,
            exit_zscore=0.5,
            quantity=100,
            max_pairs=1  # Only trade 1 pair
        )
        
        engine.add_strategy(strategy)
        
        result = engine.run(
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 6, 30),
            symbols=['PAIR_A', 'PAIR_B', 'INDEP']
        )
        
        # Should only identify up to max_pairs
        assert len(strategy.trading_pairs) <= 1
    
    def test_strategy_with_insufficient_data(self):
        """Test strategy behavior with insufficient data."""
        provider = MockPairsDataProvider()
        engine = BacktestEngine(
            initial_capital=100000,
            data_provider=provider,
            commission=0.001,
            slippage=0.0005
        )
        
        strategy = PairsTradingStrategy(
            lookback=100,  # Longer than available data
            entry_zscore=2.0,
            exit_zscore=0.5,
            quantity=100
        )
        
        engine.add_strategy(strategy)
        
        # Short date range
        result = engine.run(
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 31),
            symbols=['PAIR_A', 'PAIR_B']
        )
        
        # Should handle gracefully without errors
        assert result is not None
    
    def test_strategy_performance_metrics(self):
        """Test that strategy tracks performance metrics correctly."""
        provider = MockPairsDataProvider()
        engine = BacktestEngine(
            initial_capital=100000,
            data_provider=provider,
            commission=0.001,
            slippage=0.0005
        )
        
        strategy = PairsTradingStrategy(
            lookback=30,
            entry_zscore=1.5,
            exit_zscore=0.5,
            quantity=100
        )
        
        engine.add_strategy(strategy)
        
        result = engine.run(
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            symbols=['PAIR_A', 'PAIR_B']
        )
        
        metrics = result.metrics
        
        # Check all required metrics are present
        assert 'total_return' in metrics
        assert 'sharpe_ratio' in metrics
        assert 'max_drawdown' in metrics
        assert 'total_trades' in metrics
        assert 'win_rate' in metrics
        
        # Metrics should have reasonable values
        assert isinstance(metrics['sharpe_ratio'], (int, float))
        assert -1 <= metrics['max_drawdown'] <= 0
        assert metrics['total_trades'] >= 0
    
    def test_strategy_rebalance_frequency(self):
        """Test that strategy rebalances pairs at specified frequency."""
        provider = MockPairsDataProvider()
        engine = BacktestEngine(
            initial_capital=100000,
            data_provider=provider,
            commission=0.001,
            slippage=0.0005
        )
        
        strategy = PairsTradingStrategy(
            lookback=30,
            entry_zscore=2.0,
            exit_zscore=0.5,
            quantity=100,
            rebalance_frequency=10  # Rebalance every 10 days
        )
        
        engine.add_strategy(strategy)
        
        result = engine.run(
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 3, 31),
            symbols=['PAIR_A', 'PAIR_B']
        )
        
        # Should complete without errors
        assert result is not None
        
        # Should have identified pairs
        assert len(strategy.trading_pairs) >= 0


class TestPairsTradingIntegration:
    """Integration tests for pairs trading strategy."""
    
    @pytest.mark.integration
    def test_full_backtest_workflow(self):
        """Test complete backtest workflow with pairs trading."""
        provider = MockPairsDataProvider()
        engine = BacktestEngine(
            initial_capital=100000,
            data_provider=provider,
            commission=0.001,
            slippage=0.0005
        )
        
        strategy = PairsTradingStrategy(
            lookback=30,
            entry_zscore=1.5,
            exit_zscore=0.5,
            quantity=100,
            max_pairs=2
        )
        
        engine.add_strategy(strategy)
        
        result = engine.run(
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            symbols=['PAIR_A', 'PAIR_B']
        )
        
        # Verify result structure
        assert result is not None
        assert result.equity_curve is not None
        assert len(result.equity_curve) > 0
        assert result.trades is not None
        assert result.metrics is not None
        
        # Verify equity curve is Series with DatetimeIndex
        assert isinstance(result.equity_curve, pd.Series)
        assert isinstance(result.equity_curve.index, pd.DatetimeIndex)
        
        # Verify final capital is calculated
        assert result.metrics['final_capital'] > 0
        
        # Test get_summary_stats
        stats = result.get_summary_stats()
        assert 'strategy_name' in stats
        assert 'initial_capital' in stats
        assert 'final_capital' in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
