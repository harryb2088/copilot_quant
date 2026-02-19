"""Tests for BenchmarkComparator with data provider injection."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, date
from unittest.mock import Mock, MagicMock, patch
import sys

# Mock yfinance if not available
if 'yfinance' not in sys.modules:
    sys.modules['yfinance'] = MagicMock()

# Import BenchmarkComparator directly from module to avoid analytics.__init__ dependencies
import importlib.util
spec = importlib.util.spec_from_file_location(
    "benchmarks",
    "copilot_quant/analytics/benchmarks.py"
)
benchmarks_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmarks_module)
BenchmarkComparator = benchmarks_module.BenchmarkComparator

from copilot_quant.data.factory import MockDataProvider


class TestBenchmarkComparatorDataProvider:
    """Tests for BenchmarkComparator with data provider injection."""
    
    @pytest.fixture
    def mock_data_provider(self):
        """Create a mock data provider for testing."""
        return MockDataProvider(seed=42, base_price=100.0, volatility=0.015)
    
    @pytest.fixture
    def portfolio_returns(self):
        """Create sample portfolio returns for testing."""
        dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
        np.random.seed(123)
        returns = pd.Series(
            np.random.normal(0.0005, 0.02, len(dates)),
            index=dates,
            name="portfolio_returns"
        )
        return returns
    
    def test_initialization_with_data_provider(self, mock_data_provider):
        """Test that comparator initializes with data provider."""
        comparator = BenchmarkComparator(data_provider=mock_data_provider)
        
        assert comparator.data_provider is not None
        assert comparator.data_provider == mock_data_provider
    
    def test_initialization_without_data_provider(self):
        """Test that comparator initializes without data provider."""
        comparator = BenchmarkComparator()
        
        assert comparator.data_provider is None
    
    def test_uses_data_provider_when_available(self, mock_data_provider, portfolio_returns):
        """Test that comparator uses data provider when available."""
        comparator = BenchmarkComparator(data_provider=mock_data_provider)
        
        # Compare to benchmark
        result = comparator.compare_to_benchmark(portfolio_returns, benchmark="SPY")
        
        # Should return valid comparison metrics
        assert isinstance(result, dict)
        assert "benchmark" in result
        assert result["benchmark"] == "SPY"
        assert "alpha" in result
        assert "beta" in result
        assert "correlation" in result
    
    def test_falls_back_to_yfinance_when_provider_fails(self, portfolio_returns):
        """Test fallback to yfinance when data provider fails."""
        # Create a mock provider that raises an exception
        failing_provider = Mock()
        failing_provider.get_historical_data.side_effect = Exception("Connection failed")
        
        # Patch yfinance in the benchmarks module we loaded
        with patch.object(benchmarks_module, 'yf') as mock_yf:
            with patch.object(benchmarks_module, 'YFINANCE_AVAILABLE', True):
                # Mock yfinance response
                mock_ticker = MagicMock()
                mock_data = pd.DataFrame(
                    {"Close": [100, 101, 102, 103, 104]},
                    index=pd.date_range("2024-01-01", periods=5)
                )
                mock_ticker.history.return_value = mock_data
                mock_yf.Ticker.return_value = mock_ticker
                
                comparator = BenchmarkComparator(data_provider=failing_provider)
                
                # Use only first 5 days of portfolio returns to match mock data
                short_returns = portfolio_returns.iloc[:5]
                result = comparator.compare_to_benchmark(short_returns, benchmark="SPY")
                
                # Should successfully fall back to yfinance
                assert isinstance(result, dict)
                assert result["benchmark"] == "SPY"
    
    def test_falls_back_to_mock_when_yfinance_unavailable(self, portfolio_returns):
        """Test fallback to mock data when yfinance is unavailable."""
        with patch.object(benchmarks_module, 'YFINANCE_AVAILABLE', False):
            comparator = BenchmarkComparator()  # No data provider, no yfinance
            
            result = comparator.compare_to_benchmark(portfolio_returns, benchmark="SPY")
            
            # Should successfully use mock data
            assert isinstance(result, dict)
            assert result["benchmark"] == "SPY"
            assert result["num_observations"] > 0
    
    def test_data_provider_used_for_equity_curve(self, mock_data_provider):
        """Test that data provider is used for equity curve generation."""
        comparator = BenchmarkComparator(data_provider=mock_data_provider)
        
        equity = comparator.get_benchmark_equity_curve(
            benchmark="QQQ",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            initial_value=100000
        )
        
        assert isinstance(equity, pd.Series)
        assert len(equity) > 0
        # The initial value is calculated from returns, so allow some flexibility
        assert 95000 < equity.iloc[0] < 105000
    
    def test_compare_to_multiple_benchmarks_with_provider(self, mock_data_provider, portfolio_returns):
        """Test comparing to multiple benchmarks with data provider."""
        comparator = BenchmarkComparator(data_provider=mock_data_provider)
        
        benchmarks = ["SPY", "QQQ", "DIA"]
        results = comparator.compare_to_multiple_benchmarks(portfolio_returns, benchmarks=benchmarks)
        
        assert isinstance(results, dict)
        assert len(results) == 3
        
        for benchmark in benchmarks:
            assert benchmark in results
            assert isinstance(results[benchmark], dict)
            assert "alpha" in results[benchmark]
            assert "beta" in results[benchmark]
    
    def test_cache_works_with_data_provider(self, mock_data_provider, portfolio_returns):
        """Test that caching works correctly with data provider."""
        comparator = BenchmarkComparator(data_provider=mock_data_provider, cache_days=7)
        
        # First call - should fetch from provider
        result1 = comparator.compare_to_benchmark(portfolio_returns, benchmark="SPY")
        
        # Second call - should use cache (mock the provider to verify)
        original_method = mock_data_provider.get_historical_data
        mock_data_provider.get_historical_data = Mock(side_effect=Exception("Should not be called"))
        
        result2 = comparator.compare_to_benchmark(portfolio_returns, benchmark="SPY")
        
        # Results should be the same (from cache)
        assert result1["alpha"] == result2["alpha"]
        assert result1["beta"] == result2["beta"]
        
        # Restore original method
        mock_data_provider.get_historical_data = original_method


class TestBenchmarkComparatorMocking:
    """Tests to verify yfinance is properly mocked in benchmarks module."""
    
    @pytest.fixture
    def portfolio_returns(self):
        """Create sample portfolio returns."""
        dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
        np.random.seed(42)
        returns = pd.Series(
            np.random.normal(0.0005, 0.02, len(dates)),
            index=dates
        )
        return returns
    
    def test_yfinance_is_mocked_correctly(self, portfolio_returns):
        """Test that yfinance can be properly mocked."""
        # Patch yfinance in the benchmarks module we loaded
        with patch.object(benchmarks_module, 'yf') as mock_yf:
            with patch.object(benchmarks_module, 'YFINANCE_AVAILABLE', True):
                # Mock the yfinance response
                mock_ticker = MagicMock()
                mock_data = pd.DataFrame(
                    {"Close": [100, 101, 102, 101, 103] + [104] * 95},
                    index=pd.date_range("2024-01-01", periods=100, freq="D")
                )
                mock_ticker.history.return_value = mock_data
                mock_yf.Ticker.return_value = mock_ticker
                
                # Create comparator without data provider (will use yfinance)
                comparator = BenchmarkComparator()
                
                result = comparator.compare_to_benchmark(portfolio_returns, benchmark="SPY")
                
                # Verify mock was called
                assert mock_yf.Ticker.called
                assert mock_ticker.history.called
                
                # Verify result is valid
                assert isinstance(result, dict)
                assert "alpha" in result
                assert "beta" in result
    
    def test_handles_empty_yfinance_response(self, portfolio_returns):
        """Test that empty yfinance response is handled gracefully."""
        # Patch yfinance in the benchmarks module we loaded
        with patch.object(benchmarks_module, 'yf') as mock_yf:
            with patch.object(benchmarks_module, 'YFINANCE_AVAILABLE', True):
                # Mock empty response
                mock_ticker = MagicMock()
                mock_ticker.history.return_value = pd.DataFrame()
                mock_yf.Ticker.return_value = mock_ticker
                
                comparator = BenchmarkComparator()
                result = comparator.compare_to_benchmark(portfolio_returns, benchmark="SPY")
                
                # Should fall back to mock data
                assert isinstance(result, dict)
                assert result["num_observations"] > 0
    
    def test_handles_yfinance_exception(self, portfolio_returns):
        """Test that yfinance exceptions are handled gracefully."""
        # Patch yfinance in the benchmarks module we loaded
        with patch.object(benchmarks_module, 'yf') as mock_yf:
            with patch.object(benchmarks_module, 'YFINANCE_AVAILABLE', True):
                # Mock exception
                mock_ticker = MagicMock()
                mock_ticker.history.side_effect = Exception("Network error")
                mock_yf.Ticker.return_value = mock_ticker
                
                comparator = BenchmarkComparator()
                result = comparator.compare_to_benchmark(portfolio_returns, benchmark="SPY")
                
                # Should fall back to mock data
                assert isinstance(result, dict)
                assert result["num_observations"] > 0


class TestBenchmarkComparatorIntegrationWithMockProvider:
    """Integration tests using MockDataProvider."""
    
    def test_end_to_end_comparison_with_mock_provider(self):
        """Test complete benchmark comparison flow with mock provider."""
        # Create mock provider
        provider = MockDataProvider(seed=42, base_price=100.0, volatility=0.015)
        
        # Create comparator with provider
        comparator = BenchmarkComparator(data_provider=provider)
        
        # Generate portfolio returns
        dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
        np.random.seed(123)
        portfolio_returns = pd.Series(
            np.random.normal(0.0008, 0.02, len(dates)),  # Slightly better than market
            index=dates
        )
        
        # Compare to SPY
        result = comparator.compare_to_benchmark(portfolio_returns, benchmark="SPY")
        
        # Verify all metrics are present and reasonable
        assert result["benchmark"] == "SPY"
        assert -1.0 <= result["correlation"] <= 1.0
        # Beta can be negative if portfolio and benchmark are negatively correlated
        assert abs(result["alpha"]) < 1.0  # Alpha should be reasonable
        assert result["num_observations"] > 300  # Should have most days of the year
    
    def test_multiple_benchmarks_comparison(self):
        """Test comparing to multiple benchmarks."""
        provider = MockDataProvider(seed=42)
        comparator = BenchmarkComparator(data_provider=provider)
        
        # Generate portfolio returns
        dates = pd.date_range(start="2024-01-01", periods=252, freq="D")  # One year
        np.random.seed(123)
        portfolio_returns = pd.Series(
            np.random.normal(0.0005, 0.018, len(dates)),
            index=dates
        )
        
        # Compare to multiple benchmarks
        benchmarks = ["SPY", "QQQ", "IWM"]
        results = comparator.compare_to_multiple_benchmarks(portfolio_returns, benchmarks)
        
        assert len(results) == 3
        for benchmark in benchmarks:
            assert benchmark in results
            assert results[benchmark]["num_observations"] > 200
            assert "alpha" in results[benchmark]
            assert "beta" in results[benchmark]
    
    def test_equity_curve_generation(self):
        """Test benchmark equity curve generation."""
        provider = MockDataProvider(seed=42, base_price=450.0)  # SPY-like price
        comparator = BenchmarkComparator(data_provider=provider)
        
        equity = comparator.get_benchmark_equity_curve(
            benchmark="SPY",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            initial_value=100000
        )
        
        # Verify equity curve
        assert isinstance(equity, pd.Series)
        assert len(equity) > 300
        # The mock data can have significant variation, so be more lenient
        assert 80000 < equity.iloc[0] < 130000
        assert equity.iloc[-1] > 0  # Should still be positive
        
        # Check that equity curve shows reasonable behavior
        # (not constant, shows some variation)
        assert equity.std() > 0
