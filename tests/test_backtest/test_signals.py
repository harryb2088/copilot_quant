"""Tests for signal-based trading system."""

from datetime import datetime

import pandas as pd
import pytest

from copilot_quant.backtest.signals import SignalBasedStrategy, TradingSignal


class TestTradingSignal:
    """Tests for TradingSignal class."""
    
    def test_valid_signal_creation(self):
        """Test creating a valid signal."""
        signal = TradingSignal(
            symbol='AAPL',
            side='buy',
            confidence=0.8,
            sharpe_estimate=1.5,
            entry_price=150.0,
            strategy_name='TestStrategy'
        )
        
        assert signal.symbol == 'AAPL'
        assert signal.side == 'buy'
        assert signal.confidence == 0.8
        assert signal.sharpe_estimate == 1.5
        assert signal.entry_price == 150.0
        assert signal.strategy_name == 'TestStrategy'
    
    def test_signal_with_stop_loss_take_profit(self):
        """Test signal with stop loss and take profit."""
        signal = TradingSignal(
            symbol='AAPL',
            side='sell',
            confidence=0.6,
            sharpe_estimate=1.2,
            entry_price=150.0,
            stop_loss=145.0,
            take_profit=155.0,
            strategy_name='TestStrategy'
        )
        
        assert signal.stop_loss == 145.0
        assert signal.take_profit == 155.0
    
    def test_invalid_side(self):
        """Test that invalid side raises ValueError."""
        with pytest.raises(ValueError, match="Invalid side"):
            TradingSignal(
                symbol='AAPL',
                side='invalid',
                confidence=0.8,
                sharpe_estimate=1.5,
                entry_price=150.0
            )
    
    def test_invalid_confidence_too_low(self):
        """Test that confidence below 0 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid confidence"):
            TradingSignal(
                symbol='AAPL',
                side='buy',
                confidence=-0.1,
                sharpe_estimate=1.5,
                entry_price=150.0
            )
    
    def test_invalid_confidence_too_high(self):
        """Test that confidence above 1 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid confidence"):
            TradingSignal(
                symbol='AAPL',
                side='buy',
                confidence=1.5,
                sharpe_estimate=1.5,
                entry_price=150.0
            )
    
    def test_invalid_entry_price(self):
        """Test that invalid entry price raises ValueError."""
        with pytest.raises(ValueError, match="Invalid entry_price"):
            TradingSignal(
                symbol='AAPL',
                side='buy',
                confidence=0.8,
                sharpe_estimate=1.5,
                entry_price=-10.0
            )
    
    def test_quality_score_calculation(self):
        """Test quality score calculation."""
        # Test with normal values
        signal1 = TradingSignal(
            symbol='AAPL',
            side='buy',
            confidence=0.8,
            sharpe_estimate=1.0,
            entry_price=150.0
        )
        # Quality = confidence * min(sharpe/2, 1) = 0.8 * min(1.0/2, 1) = 0.8 * 0.5 = 0.4
        assert signal1.quality_score == pytest.approx(0.4)
        
        # Test with high Sharpe
        signal2 = TradingSignal(
            symbol='AAPL',
            side='buy',
            confidence=0.8,
            sharpe_estimate=3.0,
            entry_price=150.0
        )
        # Quality = confidence * min(sharpe/2, 1) = 0.8 * min(3.0/2, 1) = 0.8 * 1.0 = 0.8
        assert signal2.quality_score == pytest.approx(0.8)
        
        # Test with very high Sharpe (capped at 2.0)
        signal3 = TradingSignal(
            symbol='AAPL',
            side='buy',
            confidence=1.0,
            sharpe_estimate=5.0,
            entry_price=150.0
        )
        # Quality = confidence * min(sharpe/2, 1) = 1.0 * min(5.0/2, 1) = 1.0 * 1.0 = 1.0
        assert signal3.quality_score == pytest.approx(1.0)
    
    def test_quality_score_with_low_confidence(self):
        """Test quality score with low confidence."""
        signal = TradingSignal(
            symbol='AAPL',
            side='buy',
            confidence=0.2,
            sharpe_estimate=2.0,
            entry_price=150.0
        )
        # Quality = 0.2 * min(2.0/2, 1) = 0.2 * 1.0 = 0.2
        assert signal.quality_score == pytest.approx(0.2)
    
    def test_quality_score_edge_cases(self):
        """Test quality score edge cases."""
        # Zero confidence
        signal1 = TradingSignal(
            symbol='AAPL',
            side='buy',
            confidence=0.0,
            sharpe_estimate=2.0,
            entry_price=150.0
        )
        assert signal1.quality_score == pytest.approx(0.0)
        
        # Zero Sharpe
        signal2 = TradingSignal(
            symbol='AAPL',
            side='buy',
            confidence=1.0,
            sharpe_estimate=0.0,
            entry_price=150.0
        )
        assert signal2.quality_score == pytest.approx(0.0)
        
        # Both max
        signal3 = TradingSignal(
            symbol='AAPL',
            side='buy',
            confidence=1.0,
            sharpe_estimate=2.0,
            entry_price=150.0
        )
        assert signal3.quality_score == pytest.approx(1.0)


class SimpleSignalStrategy(SignalBasedStrategy):
    """Simple test strategy that generates signals."""
    
    def __init__(self):
        super().__init__()
        self.signal_count = 0
    
    def generate_signals(self, timestamp, data):
        """Generate a simple signal."""
        self.signal_count += 1
        
        if self.signal_count == 1:
            return [TradingSignal(
                symbol='AAPL',
                side='buy',
                confidence=0.8,
                sharpe_estimate=1.5,
                entry_price=150.0,
                strategy_name=self.name
            )]
        
        return []


class TestSignalBasedStrategy:
    """Tests for SignalBasedStrategy class."""
    
    def test_strategy_is_abstract(self):
        """Test that SignalBasedStrategy cannot be instantiated directly."""
        with pytest.raises(TypeError):
            SignalBasedStrategy()
    
    def test_strategy_requires_generate_signals(self):
        """Test that subclasses must implement generate_signals."""
        class IncompleteStrategy(SignalBasedStrategy):
            pass
        
        with pytest.raises(TypeError):
            IncompleteStrategy()
    
    def test_simple_signal_generation(self):
        """Test simple signal generation."""
        strategy = SimpleSignalStrategy()
        strategy.initialize()
        
        # First call should generate signal
        signals = strategy.generate_signals(
            datetime(2023, 1, 1),
            pd.DataFrame({'Close': [150.0]})
        )
        
        assert len(signals) == 1
        assert signals[0].symbol == 'AAPL'
        assert signals[0].side == 'buy'
        assert signals[0].confidence == 0.8
        
        # Second call should not generate signal
        signals2 = strategy.generate_signals(
            datetime(2023, 1, 2),
            pd.DataFrame({'Close': [151.0]})
        )
        
        assert len(signals2) == 0
    
    def test_on_data_returns_empty_list(self):
        """Test that on_data returns empty list for signal-based strategies."""
        strategy = SimpleSignalStrategy()
        
        orders = strategy.on_data(
            datetime(2023, 1, 1),
            pd.DataFrame({'Close': [150.0]})
        )
        
        assert orders == []
    
    def test_strategy_callbacks(self):
        """Test that strategy callbacks work."""
        strategy = SimpleSignalStrategy()
        
        # Test initialize
        assert strategy.signal_count == 0
        strategy.initialize()
        
        # Test finalize
        strategy.finalize()  # Should not raise
    
    def test_signal_sets_strategy_name(self):
        """Test that generated signals can include strategy name."""
        strategy = SimpleSignalStrategy()
        strategy.initialize()
        
        signals = strategy.generate_signals(
            datetime(2023, 1, 1),
            pd.DataFrame({'Close': [150.0]})
        )
        
        assert signals[0].strategy_name == strategy.name


class MultiSignalStrategy(SignalBasedStrategy):
    """Strategy that generates multiple signals."""
    
    def generate_signals(self, timestamp, data):
        """Generate multiple signals."""
        return [
            TradingSignal(
                symbol='AAPL',
                side='buy',
                confidence=0.8,
                sharpe_estimate=1.5,
                entry_price=150.0,
                strategy_name=self.name
            ),
            TradingSignal(
                symbol='MSFT',
                side='buy',
                confidence=0.6,
                sharpe_estimate=1.2,
                entry_price=300.0,
                strategy_name=self.name
            ),
            TradingSignal(
                symbol='GOOGL',
                side='sell',
                confidence=0.7,
                sharpe_estimate=1.3,
                entry_price=140.0,
                strategy_name=self.name
            ),
        ]


class TestMultipleSignals:
    """Tests for strategies that generate multiple signals."""
    
    def test_multiple_signals_generation(self):
        """Test generation of multiple signals."""
        strategy = MultiSignalStrategy()
        
        signals = strategy.generate_signals(
            datetime(2023, 1, 1),
            pd.DataFrame({'Close': [150.0]})
        )
        
        assert len(signals) == 3
        assert signals[0].symbol == 'AAPL'
        assert signals[1].symbol == 'MSFT'
        assert signals[2].symbol == 'GOOGL'
    
    def test_signals_have_different_quality_scores(self):
        """Test that signals have different quality scores."""
        strategy = MultiSignalStrategy()
        
        signals = strategy.generate_signals(
            datetime(2023, 1, 1),
            pd.DataFrame({'Close': [150.0]})
        )
        
        # AAPL: 0.8 * min(1.5/2, 1) = 0.8 * 0.75 = 0.6
        assert signals[0].quality_score == pytest.approx(0.6)
        
        # MSFT: 0.6 * min(1.2/2, 1) = 0.6 * 0.6 = 0.36
        assert signals[1].quality_score == pytest.approx(0.36)
        
        # GOOGL: 0.7 * min(1.3/2, 1) = 0.7 * 0.65 = 0.455
        assert signals[2].quality_score == pytest.approx(0.455)
    
    def test_signals_can_be_sorted_by_quality(self):
        """Test that signals can be sorted by quality score."""
        strategy = MultiSignalStrategy()
        
        signals = strategy.generate_signals(
            datetime(2023, 1, 1),
            pd.DataFrame({'Close': [150.0]})
        )
        
        sorted_signals = sorted(signals, key=lambda s: s.quality_score, reverse=True)
        
        # AAPL should be first (0.6), then GOOGL (0.455), then MSFT (0.36)
        assert sorted_signals[0].symbol == 'AAPL'
        assert sorted_signals[1].symbol == 'GOOGL'
        assert sorted_signals[2].symbol == 'MSFT'
