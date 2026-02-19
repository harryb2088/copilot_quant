"""Tests for data provider factory and MockDataProvider."""

import pytest
import pandas as pd
from datetime import datetime, timedelta

from copilot_quant.data.factory import MockDataProvider, create_data_provider


class TestMockDataProvider:
    """Tests for MockDataProvider."""
    
    @pytest.fixture
    def provider(self):
        """Create a MockDataProvider instance."""
        return MockDataProvider(seed=42, base_price=100.0, volatility=0.02)
    
    def test_initialization(self, provider):
        """Test that provider initializes correctly."""
        assert provider.name == "Mock Data Provider"
        assert provider.seed == 42
        assert provider.base_price == 100.0
        assert provider.volatility == 0.02
    
    def test_get_historical_data_returns_dataframe(self, provider):
        """Test that get_historical_data returns a DataFrame."""
        data = provider.get_historical_data(
            "AAPL",
            start_date="2024-01-01",
            end_date="2024-01-31",
        )
        
        assert isinstance(data, pd.DataFrame)
        assert len(data) > 0
    
    def test_get_historical_data_has_ohlcv_columns(self, provider):
        """Test that historical data contains OHLCV columns."""
        data = provider.get_historical_data(
            "AAPL",
            start_date="2024-01-01",
            end_date="2024-01-31",
        )
        
        expected_columns = ["Open", "High", "Low", "Close", "Volume"]
        for col in expected_columns:
            assert col in data.columns, f"Missing column: {col}"
    
    def test_get_historical_data_has_datetime_index(self, provider):
        """Test that historical data has DatetimeIndex."""
        data = provider.get_historical_data(
            "AAPL",
            start_date="2024-01-01",
            end_date="2024-01-31",
        )
        
        assert isinstance(data.index, pd.DatetimeIndex)
    
    def test_get_historical_data_default_dates(self, provider):
        """Test that default dates work (1 year ago to today)."""
        data = provider.get_historical_data("MSFT")
        
        # Should have approximately 365 days of data
        assert len(data) >= 350
        assert len(data) <= 380
    
    def test_get_historical_data_ohlc_relationships(self, provider):
        """Test that OHLC data maintains proper relationships."""
        data = provider.get_historical_data(
            "GOOGL",
            start_date="2024-01-01",
            end_date="2024-01-31",
        )
        
        # High should be >= Close
        assert (data["High"] >= data["Close"]).all()
        
        # Low should be <= Close
        assert (data["Low"] <= data["Close"]).all()
        
        # High should be >= Low
        assert (data["High"] >= data["Low"]).all()
        
        # High should be >= Open
        assert (data["High"] >= data["Open"]).all()
        
        # Low should be <= Open
        assert (data["Low"] <= data["Open"]).all()
    
    def test_get_historical_data_volume_positive(self, provider):
        """Test that volume is always positive."""
        data = provider.get_historical_data(
            "TSLA",
            start_date="2024-01-01",
            end_date="2024-01-31",
        )
        
        assert (data["Volume"] > 0).all()
    
    def test_get_historical_data_different_symbols_different_data(self, provider):
        """Test that different symbols generate different data."""
        data1 = provider.get_historical_data("AAPL", start_date="2024-01-01", end_date="2024-01-10")
        data2 = provider.get_historical_data("MSFT", start_date="2024-01-01", end_date="2024-01-10")
        
        # Data should be different for different symbols
        assert not data1["Close"].equals(data2["Close"])
    
    def test_get_historical_data_same_symbol_reproducible(self, provider):
        """Test that same symbol generates reproducible data."""
        data1 = provider.get_historical_data("AAPL", start_date="2024-01-01", end_date="2024-01-10")
        data2 = provider.get_historical_data("AAPL", start_date="2024-01-01", end_date="2024-01-10")
        
        # Same symbol should produce same data
        assert data1["Close"].equals(data2["Close"])
    
    def test_get_multiple_symbols(self, provider):
        """Test getting data for multiple symbols."""
        symbols = ["AAPL", "MSFT", "GOOGL"]
        data = provider.get_multiple_symbols(
            symbols,
            start_date="2024-01-01",
            end_date="2024-01-31",
        )
        
        assert isinstance(data, pd.DataFrame)
        assert not data.empty
        
        # Should have multi-level columns
        if len(symbols) > 1:
            assert isinstance(data.columns, pd.MultiIndex)
    
    def test_get_multiple_symbols_empty_list(self, provider):
        """Test that empty symbol list returns empty DataFrame."""
        data = provider.get_multiple_symbols([])
        
        assert isinstance(data, pd.DataFrame)
        assert data.empty
    
    def test_get_ticker_info(self, provider):
        """Test getting ticker information."""
        info = provider.get_ticker_info("AAPL")
        
        assert isinstance(info, dict)
        assert "symbol" in info
        assert info["symbol"] == "AAPL"
        assert "longName" in info
        assert "sector" in info
        assert "marketCap" in info
    
    def test_different_seeds_different_data(self):
        """Test that different seeds produce different data."""
        provider1 = MockDataProvider(seed=42)
        provider2 = MockDataProvider(seed=123)
        
        data1 = provider1.get_historical_data("AAPL", start_date="2024-01-01", end_date="2024-01-10")
        data2 = provider2.get_historical_data("AAPL", start_date="2024-01-01", end_date="2024-01-10")
        
        # Different seeds should produce different data
        assert not data1["Close"].equals(data2["Close"])
    
    def test_custom_base_price(self):
        """Test that custom base price is respected."""
        provider = MockDataProvider(seed=42, base_price=500.0)
        data = provider.get_historical_data("TSLA", start_date="2024-01-01", end_date="2024-01-02")
        
        # First open should be close to base price
        assert abs(data["Open"].iloc[0] - 500.0) < 50.0  # Allow some variation
    
    def test_datetime_inputs(self, provider):
        """Test that datetime objects work as inputs."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)
        
        data = provider.get_historical_data("AAPL", start_date=start, end_date=end)
        
        assert len(data) > 0
        assert data.index[0].date() >= start.date()
        assert data.index[-1].date() <= end.date()


class TestCreateDataProviderFactory:
    """Tests for create_data_provider factory function."""
    
    def test_create_mock_provider(self):
        """Test creating a mock data provider."""
        provider = create_data_provider("mock")
        
        assert isinstance(provider, MockDataProvider)
    
    def test_create_mock_provider_with_params(self):
        """Test creating a mock provider with custom parameters."""
        provider = create_data_provider("mock", seed=123, base_price=200.0, volatility=0.03)
        
        assert isinstance(provider, MockDataProvider)
        assert provider.seed == 123
        assert provider.base_price == 200.0
        assert provider.volatility == 0.03
    
    def test_create_backtest_provider(self):
        """Test creating a backtest provider (yfinance)."""
        try:
            from copilot_quant.data.providers import YFinanceProvider
            
            provider = create_data_provider("backtest")
            
            assert isinstance(provider, YFinanceProvider)
        except ImportError:
            # yfinance not available - should raise ImportError
            with pytest.raises(ImportError, match="yfinance"):
                create_data_provider("backtest")
    
    def test_create_provider_case_insensitive(self):
        """Test that mode is case-insensitive."""
        provider1 = create_data_provider("MOCK")
        provider2 = create_data_provider("Mock")
        provider3 = create_data_provider("mock")
        
        assert all(isinstance(p, MockDataProvider) for p in [provider1, provider2, provider3])
    
    def test_create_provider_invalid_mode(self):
        """Test that invalid mode raises ValueError."""
        with pytest.raises(ValueError, match="Unknown mode"):
            create_data_provider("invalid_mode")
    
    def test_mock_provider_works_end_to_end(self):
        """Test that mock provider can be used end-to-end."""
        provider = create_data_provider("mock", seed=42)
        
        # Fetch data
        data = provider.get_historical_data("SPY", start_date="2024-01-01", end_date="2024-01-31")
        
        # Verify it's usable
        assert len(data) > 0
        assert "Close" in data.columns
        assert data["Close"].notna().all()
        
        # Calculate returns
        returns = data["Close"].pct_change().dropna()
        assert len(returns) > 0


class TestMockProviderRealisticData:
    """Tests to verify mock data is realistic enough for testing."""
    
    def test_prices_are_positive(self):
        """Test that all prices are positive."""
        provider = MockDataProvider(seed=42, base_price=100.0)
        data = provider.get_historical_data("AAPL", start_date="2024-01-01", end_date="2024-12-31")
        
        assert (data["Open"] > 0).all()
        assert (data["High"] > 0).all()
        assert (data["Low"] > 0).all()
        assert (data["Close"] > 0).all()
    
    def test_returns_are_reasonable(self):
        """Test that returns are within reasonable bounds."""
        provider = MockDataProvider(seed=42, base_price=100.0, volatility=0.02)
        data = provider.get_historical_data("MSFT", start_date="2024-01-01", end_date="2024-12-31")
        
        returns = data["Close"].pct_change().dropna()
        
        # Most daily returns should be within ±10%
        assert (returns.abs() < 0.10).sum() / len(returns) > 0.90
    
    def test_data_has_realistic_volatility(self):
        """Test that generated data has realistic volatility."""
        provider = MockDataProvider(seed=42, base_price=100.0, volatility=0.02)
        data = provider.get_historical_data("SPY", start_date="2024-01-01", end_date="2024-12-31")
        
        returns = data["Close"].pct_change().dropna()
        actual_vol = returns.std()
        
        # Should be close to specified volatility (within 50%)
        assert abs(actual_vol - 0.02) / 0.02 < 0.5
    
    def test_data_can_be_used_for_strategy_testing(self):
        """Test that mock data is suitable for strategy backtesting."""
        provider = MockDataProvider(seed=42, base_price=100.0)
        data = provider.get_historical_data("AAPL", start_date="2024-01-01", end_date="2024-12-31")
        
        # Calculate simple moving averages (common strategy indicator)
        data["SMA_20"] = data["Close"].rolling(window=20).mean()
        data["SMA_50"] = data["Close"].rolling(window=50).mean()
        
        # Should be able to identify crossovers
        sma_data = data.dropna()
        assert len(sma_data) > 0
        
        # Check for at least one crossover
        crosses = (sma_data["SMA_20"] > sma_data["SMA_50"]).astype(int).diff().abs().sum()
        assert crosses > 0  # Should have some crossovers in a year
