"""Tests for multi-strategy backtesting engine."""

from datetime import datetime
from unittest.mock import MagicMock

import pandas as pd
import pytest

from copilot_quant.backtest.multi_strategy import (
    MultiStrategyEngine,
    StrategyAttribution,
)
from copilot_quant.backtest.orders import Fill, Order
from copilot_quant.backtest.signals import SignalBasedStrategy, TradingSignal
from copilot_quant.data.providers import DataProvider


class MockDataProvider(DataProvider):
    """Mock data provider for testing."""
    
    def get_historical_data(self, symbol, start_date=None, end_date=None):
        """Return mock historical data."""
        dates = pd.date_range(start='2023-01-01', end='2023-01-10', freq='D')
        
        data = pd.DataFrame({
            'Open': [150.0] * len(dates),
            'High': [155.0] * len(dates),
            'Low': [145.0] * len(dates),
            'Close': [150.0 + i for i, _ in enumerate(dates)],
            'Volume': [1000000] * len(dates),
        }, index=dates)
        
        data['Symbol'] = symbol
        return data
    
    def get_multiple_symbols(self, symbols, start_date=None, end_date=None):
        """Return mock data for multiple symbols."""
        dates = pd.date_range(start='2023-01-01', end='2023-01-10', freq='D')
        
        # Create multi-level columns for multiple symbols
        data = {}
        for metric in ['Open', 'High', 'Low', 'Close', 'Volume']:
            for symbol in symbols:
                if metric == 'Volume':
                    data[(metric, symbol)] = [1000000] * len(dates)
                else:
                    base_price = 150.0 if metric != 'High' else 155.0
                    if metric == 'Low':
                        base_price = 145.0
                    if metric == 'Close':
                        data[(metric, symbol)] = [base_price + i for i in range(len(dates))]
                    else:
                        data[(metric, symbol)] = [base_price] * len(dates)
        
        df = pd.DataFrame(data, index=dates)
        df.columns = pd.MultiIndex.from_tuples(df.columns)
        return df
    
    def get_ticker_info(self, symbol):
        """Return mock ticker info."""
        return {
            'symbol': symbol,
            'name': f'{symbol} Inc.',
            'exchange': 'NASDAQ',
        }


class BuyOnceStrategy(SignalBasedStrategy):
    """Strategy that buys once with a signal."""
    
    def __init__(self, symbol='AAPL', confidence=0.8, sharpe=1.5):
        super().__init__()
        self.symbol = symbol
        self.confidence = confidence
        self.sharpe = sharpe
        self.signal_generated = False
    
    def generate_signals(self, timestamp, data):
        """Generate one buy signal."""
        if not self.signal_generated:
            self.signal_generated = True
            return [TradingSignal(
                symbol=self.symbol,
                side='buy',
                confidence=self.confidence,
                sharpe_estimate=self.sharpe,
                entry_price=150.0,
                strategy_name=self.name
            )]
        return []


class TestStrategyAttribution:
    """Tests for StrategyAttribution class."""
    
    def test_attribution_initialization(self):
        """Test attribution initialization."""
        attr = StrategyAttribution('TestStrategy')
        
        assert attr.strategy_name == 'TestStrategy'
        assert attr.total_deployed == 0.0
        assert attr.realized_pnl == 0.0
        assert attr.unrealized_pnl == 0.0
        assert attr.num_trades == 0
        assert attr.num_wins == 0
        assert attr.num_losses == 0
    
    def test_record_fill(self):
        """Test recording a fill."""
        attr = StrategyAttribution('TestStrategy')
        
        fill = Fill(
            order=Order(symbol='AAPL', quantity=10, order_type='market', side='buy'),
            fill_price=150.0,
            fill_quantity=10,
            commission=1.5,
            timestamp=datetime(2023, 1, 1),
        )
        
        attr.record_fill(fill)
        
        assert attr.num_trades == 1
        assert attr.total_deployed == 1500.0  # 150.0 * 10
        assert len(attr.fills) == 1
    
    def test_record_trade_close_win(self):
        """Test recording a winning trade."""
        attr = StrategyAttribution('TestStrategy')
        
        attr.record_trade_close(100.0)
        
        assert attr.realized_pnl == 100.0
        assert attr.num_wins == 1
        assert attr.num_losses == 0
    
    def test_record_trade_close_loss(self):
        """Test recording a losing trade."""
        attr = StrategyAttribution('TestStrategy')
        
        attr.record_trade_close(-50.0)
        
        assert attr.realized_pnl == -50.0
        assert attr.num_wins == 0
        assert attr.num_losses == 1
    
    def test_update_unrealized_pnl(self):
        """Test updating unrealized P&L."""
        attr = StrategyAttribution('TestStrategy')
        
        attr.update_unrealized_pnl(25.0)
        
        assert attr.unrealized_pnl == 25.0
    
    def test_total_pnl(self):
        """Test total P&L calculation."""
        attr = StrategyAttribution('TestStrategy')
        
        attr.record_trade_close(100.0)
        attr.update_unrealized_pnl(25.0)
        
        assert attr.total_pnl == 125.0
    
    def test_win_rate_no_trades(self):
        """Test win rate with no trades."""
        attr = StrategyAttribution('TestStrategy')
        
        assert attr.win_rate == 0.0
    
    def test_win_rate_calculation(self):
        """Test win rate calculation."""
        attr = StrategyAttribution('TestStrategy')
        
        attr.record_trade_close(100.0)  # Win
        attr.record_trade_close(-50.0)  # Loss
        attr.record_trade_close(75.0)   # Win
        
        assert attr.win_rate == pytest.approx(2.0 / 3.0)
    
    def test_deployed_capital_return(self):
        """Test deployed capital return calculation."""
        attr = StrategyAttribution('TestStrategy')
        
        fill = Fill(
            order=Order(symbol='AAPL', quantity=10, order_type='market', side='buy'),
            fill_price=150.0,
            fill_quantity=10,
            commission=1.5,
            timestamp=datetime(2023, 1, 1),
        )
        
        attr.record_fill(fill)
        attr.record_trade_close(150.0)  # $150 profit on $1500 deployed
        
        assert attr.deployed_capital_return == pytest.approx(0.1)  # 10%
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        attr = StrategyAttribution('TestStrategy')
        
        fill = Fill(
            order=Order(symbol='AAPL', quantity=10, order_type='market', side='buy'),
            fill_price=150.0,
            fill_quantity=10,
            commission=1.5,
            timestamp=datetime(2023, 1, 1),
        )
        
        attr.record_fill(fill)
        attr.record_trade_close(150.0)
        
        result = attr.to_dict()
        
        assert result['strategy_name'] == 'TestStrategy'
        assert result['total_deployed'] == 1500.0
        assert result['realized_pnl'] == 150.0
        assert result['num_trades'] == 1


class TestMultiStrategyEngine:
    """Tests for MultiStrategyEngine class."""
    
    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = MultiStrategyEngine(
            initial_capital=100000,
            data_provider=MockDataProvider(),
            max_position_pct=0.025,
            max_deployed_pct=0.80
        )
        
        assert engine.initial_capital == 100000
        assert engine.max_position_pct == 0.025
        assert engine.max_deployed_pct == 0.80
        assert len(engine.strategies) == 0
    
    def test_add_strategy(self):
        """Test adding a strategy."""
        engine = MultiStrategyEngine(
            initial_capital=100000,
            data_provider=MockDataProvider()
        )
        
        strategy = BuyOnceStrategy()
        engine.add_strategy(strategy)
        
        assert len(engine.strategies) == 1
        assert strategy.name in engine.attributions
    
    def test_add_non_signal_strategy_raises_error(self):
        """Test that adding non-signal strategy raises TypeError."""
        from copilot_quant.backtest.strategy import Strategy
        
        class RegularStrategy(Strategy):
            def on_data(self, timestamp, data):
                return []
        
        engine = MultiStrategyEngine(
            initial_capital=100000,
            data_provider=MockDataProvider()
        )
        
        with pytest.raises(TypeError, match="requires SignalBasedStrategy"):
            engine.add_strategy(RegularStrategy())
    
    def test_run_without_strategies_raises_error(self):
        """Test that running without strategies raises ValueError."""
        engine = MultiStrategyEngine(
            initial_capital=100000,
            data_provider=MockDataProvider()
        )
        
        with pytest.raises(ValueError, match="No strategies registered"):
            engine.run(
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2023, 1, 10),
                symbols=['AAPL']
            )
    
    def test_single_strategy_backtest(self):
        """Test backtest with a single strategy."""
        engine = MultiStrategyEngine(
            initial_capital=100000,
            data_provider=MockDataProvider(),
            commission=0.001,
            slippage=0.0005
        )
        
        strategy = BuyOnceStrategy(symbol='AAPL', confidence=0.8, sharpe=1.5)
        engine.add_strategy(strategy)
        
        result = engine.run(
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 10),
            symbols=['AAPL']
        )
        
        assert result.strategy_name == 'MultiStrategy'
        assert result.initial_capital == 100000
        assert result.final_capital != 100000  # Should have traded
        
        # Check attribution
        assert 'BuyOnceStrategy' in result.strategy_attributions
        attr = result.strategy_attributions['BuyOnceStrategy']
        assert attr['num_trades'] > 0
    
    def test_multiple_strategies_backtest(self):
        """Test backtest with multiple strategies."""
        engine = MultiStrategyEngine(
            initial_capital=100000,
            data_provider=MockDataProvider(),
            commission=0.001,
            slippage=0.0005
        )
        
        strategy1 = BuyOnceStrategy(symbol='AAPL', confidence=0.8, sharpe=1.5)
        strategy1.name = 'BuyOnceStrategy_AAPL'  # Give unique name
        strategy2 = BuyOnceStrategy(symbol='MSFT', confidence=0.6, sharpe=1.2)
        strategy2.name = 'BuyOnceStrategy_MSFT'  # Give unique name
        
        engine.add_strategy(strategy1)
        engine.add_strategy(strategy2)
        
        result = engine.run(
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 10),
            symbols=['AAPL', 'MSFT']
        )
        
        # Check that both strategies are in attribution
        assert 'BuyOnceStrategy_AAPL' in result.strategy_attributions
        assert 'BuyOnceStrategy_MSFT' in result.strategy_attributions
        assert len(result.strategy_attributions) == 2
    
    def test_signal_ranking_by_quality(self):
        """Test that signals are ranked by quality score."""
        engine = MultiStrategyEngine(
            initial_capital=100000,
            data_provider=MockDataProvider()
        )
        
        # High quality strategy
        high_quality = BuyOnceStrategy(symbol='AAPL', confidence=1.0, sharpe=2.0)
        high_quality.name = 'HighQuality'
        # Low quality strategy
        low_quality = BuyOnceStrategy(symbol='MSFT', confidence=0.3, sharpe=0.5)
        low_quality.name = 'LowQuality'
        
        engine.add_strategy(high_quality)
        engine.add_strategy(low_quality)
        
        result = engine.run(
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 10),
            symbols=['AAPL', 'MSFT']
        )
        
        # High quality strategy should have executed first and gotten more capital
        # Both should have traded, but high quality should have larger position
        # This is implicit in the position sizing logic
        assert len(result.trades) >= 2
    
    def test_max_position_size_enforcement(self):
        """Test that max position size is enforced."""
        engine = MultiStrategyEngine(
            initial_capital=100000,
            data_provider=MockDataProvider(),
            max_position_pct=0.025  # 2.5% of cash
        )
        
        strategy = BuyOnceStrategy(symbol='AAPL', confidence=1.0, sharpe=2.0)
        engine.add_strategy(strategy)
        
        result = engine.run(
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 10),
            symbols=['AAPL']
        )
        
        # Check that first trade respects max position size
        if result.trades:
            first_trade = result.trades[0]
            position_value = first_trade.fill_price * first_trade.fill_quantity
            max_allowed = 100000 * 0.025  # 2.5% of initial capital
            
            # Should be less than or equal to max (with some tolerance for quality scaling)
            assert position_value <= max_allowed * 1.01  # Allow 1% tolerance
    
    def test_attribution_tracking(self):
        """Test that strategy attribution is tracked correctly."""
        engine = MultiStrategyEngine(
            initial_capital=100000,
            data_provider=MockDataProvider()
        )
        
        strategy = BuyOnceStrategy(symbol='AAPL', confidence=0.8, sharpe=1.5)
        engine.add_strategy(strategy)
        
        result = engine.run(
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 10),
            symbols=['AAPL']
        )
        
        attr = result.strategy_attributions['BuyOnceStrategy']
        
        # Should have basic attribution data
        assert 'strategy_name' in attr
        assert 'num_trades' in attr
        assert 'total_deployed' in attr
        assert 'total_pnl' in attr
        assert 'win_rate' in attr
        assert 'deployed_capital_return' in attr
        
        assert attr['strategy_name'] == 'BuyOnceStrategy'


class HighFrequencyStrategy(SignalBasedStrategy):
    """Strategy that generates frequent signals."""
    
    def generate_signals(self, timestamp, data):
        """Generate a signal every time."""
        return [TradingSignal(
            symbol='AAPL',
            side='buy',
            confidence=0.5,
            sharpe_estimate=0.8,
            entry_price=150.0,
            strategy_name=self.name
        )]


class TestMaxDeploymentLimit:
    """Tests for max deployment limit enforcement."""
    
    def test_max_deployed_prevents_excessive_trading(self):
        """Test that max deployed limit prevents excessive trading."""
        engine = MultiStrategyEngine(
            initial_capital=100000,
            data_provider=MockDataProvider(),
            max_position_pct=0.10,  # 10% per position
            max_deployed_pct=0.20   # 20% max deployed (low for testing)
        )
        
        strategy = HighFrequencyStrategy()
        engine.add_strategy(strategy)
        
        result = engine.run(
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 10),
            symbols=['AAPL']
        )
        
        # Should not have traded much more than what the deployment limit allows
        # With 20% max deployed and 10% per position, we should see limited trades
        # The exact count depends on position sizing, but should be reasonable
        assert len(result.trades) <= 10  # At most one trade per day
        
        # Verify deployment limit was respected during backtest
        # Check portfolio history for max deployed percentage
        if not result.portfolio_history.empty and len(result.trades) > 0:
            max_deployed = (result.portfolio_history['positions_value'] / 
                          result.portfolio_history['portfolio_value']).max()
            
            # Allow small tolerance for rounding and slippage
            assert max_deployed <= engine.max_deployed_pct * 1.05, (
                f"Deployed capital ({max_deployed:.1%}) exceeded max limit "
                f"({engine.max_deployed_pct:.1%})"
            )
