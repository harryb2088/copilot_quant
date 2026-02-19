"""Tests for data providers module."""

from unittest.mock import patch, MagicMock
import sys

import pandas as pd
import pytest

# Mock yfinance if not available
if 'yfinance' not in sys.modules:
    sys.modules['yfinance'] = MagicMock()

from copilot_quant.data.providers import (
    YFinanceProvider,
    get_data_provider,
    YFINANCE_AVAILABLE,
)


class TestYFinanceProvider:
    """Tests for Yahoo Finance data provider."""

    @pytest.fixture
    def provider(self):
        """Create a YFinanceProvider instance."""
        # Temporarily set YFINANCE_AVAILABLE to True for tests
        with patch('copilot_quant.data.providers.YFINANCE_AVAILABLE', True):
            provider = YFinanceProvider.__new__(YFinanceProvider)
            provider.name = "Yahoo Finance (yfinance)"
            return provider

    def test_provider_initialization(self, provider):
        """Test that provider initializes correctly."""
        assert provider.name == "Yahoo Finance (yfinance)"

    @patch("copilot_quant.data.providers.yf.Ticker")
    def test_get_historical_data_returns_dataframe(self, mock_ticker, provider):
        """Test that get_historical_data returns a DataFrame."""
        # Mock the yfinance response
        mock_data = pd.DataFrame(
            {
                "Open": [100, 101, 102],
                "High": [105, 106, 107],
                "Low": [99, 100, 101],
                "Close": [104, 105, 106],
                "Volume": [1000000, 1100000, 1200000],
            },
            index=pd.date_range("2024-01-01", periods=3),
        )

        mock_ticker.return_value.history.return_value = mock_data

        data = provider.get_historical_data(
            "AAPL",
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        assert isinstance(data, pd.DataFrame)
        assert len(data) == 3

    @patch("copilot_quant.data.providers.yf.Ticker")
    def test_get_historical_data_has_expected_columns(self, mock_ticker, provider):
        """Test that historical data contains expected columns."""
        # Mock the yfinance response with expected columns
        mock_data = pd.DataFrame(
            {
                "Open": [100, 101, 102],
                "High": [105, 106, 107],
                "Low": [99, 100, 101],
                "Close": [104, 105, 106],
                "Volume": [1000000, 1100000, 1200000],
                "Dividends": [0, 0, 0],
                "Stock Splits": [0, 0, 0],
            },
            index=pd.date_range("2024-01-01", periods=3),
        )

        mock_ticker.return_value.history.return_value = mock_data

        data = provider.get_historical_data(
            "AAPL",
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        # Check for standard OHLCV columns
        expected_columns = ["Open", "High", "Low", "Close", "Volume"]
        for col in expected_columns:
            assert col in data.columns, f"Missing column: {col}"

    @patch("copilot_quant.data.providers.yf.Ticker")
    def test_get_historical_data_with_datetime_index(self, mock_ticker, provider):
        """Test that historical data has DatetimeIndex."""
        mock_data = pd.DataFrame(
            {
                "Open": [100, 101, 102],
                "High": [105, 106, 107],
                "Low": [99, 100, 101],
                "Close": [104, 105, 106],
                "Volume": [1000000, 1100000, 1200000],
            },
            index=pd.date_range("2024-01-01", periods=3),
        )

        mock_ticker.return_value.history.return_value = mock_data

        data = provider.get_historical_data(
            "AAPL",
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        assert isinstance(data.index, pd.DatetimeIndex)

    @patch("copilot_quant.data.providers.yf.download")
    def test_get_multiple_symbols(self, mock_download, provider):
        """Test downloading multiple symbols at once."""
        # Create mock multi-index DataFrame
        dates = pd.date_range("2024-01-01", periods=3)
        mock_data = pd.DataFrame(
            {
                ("Close", "AAPL"): [100, 101, 102],
                ("Close", "MSFT"): [200, 201, 202],
                ("Volume", "AAPL"): [1000000, 1100000, 1200000],
                ("Volume", "MSFT"): [2000000, 2100000, 2200000],
            },
            index=dates,
        )
        mock_data.columns = pd.MultiIndex.from_tuples(mock_data.columns)

        mock_download.return_value = mock_data

        symbols = ["AAPL", "MSFT"]
        data = provider.get_multiple_symbols(
            symbols,
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        assert isinstance(data, pd.DataFrame)
        assert not data.empty

    @patch("copilot_quant.data.providers.yf.Ticker")
    def test_get_ticker_info(self, mock_ticker, provider):
        """Test getting ticker information."""
        mock_ticker.return_value.info = {
            "longName": "Apple Inc.",
            "sector": "Technology",
            "marketCap": 3000000000000,
        }

        info = provider.get_ticker_info("AAPL")

        assert isinstance(info, dict)
        assert len(info) > 0
        assert info["longName"] == "Apple Inc."

    @patch("copilot_quant.data.providers.yf.Ticker")
    def test_get_sp500_index(self, mock_ticker, provider):
        """Test getting S&P500 index data."""
        mock_data = pd.DataFrame(
            {
                "Open": [4000, 4010, 4020],
                "High": [4050, 4060, 4070],
                "Low": [3990, 4000, 4010],
                "Close": [4040, 4050, 4060],
                "Volume": [1000000000, 1100000000, 1200000000],
            },
            index=pd.date_range("2024-01-01", periods=3),
        )

        mock_ticker.return_value.history.return_value = mock_data

        data = provider.get_sp500_index(
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        assert isinstance(data, pd.DataFrame)
        assert not data.empty


class TestProviderFactory:
    """Tests for provider factory function."""

    def test_get_data_provider_yfinance(self):
        """Test getting yfinance provider."""
        provider = get_data_provider("yfinance")
        assert isinstance(provider, YFinanceProvider)

    def test_get_data_provider_yahoo_alias(self):
        """Test that 'yahoo' alias works."""
        provider = get_data_provider("yahoo")
        assert isinstance(provider, YFinanceProvider)

    def test_get_data_provider_invalid_name(self):
        """Test that invalid provider name raises error."""
        with pytest.raises(ValueError):
            get_data_provider("invalid_provider")


@pytest.mark.integration
class TestYFinanceProviderIntegration:
    """Integration tests that require network access."""

    @pytest.fixture
    def provider(self):
        """Create a YFinanceProvider instance."""
        return YFinanceProvider()

    def test_download_real_data(self, provider):
        """Test downloading real data from Yahoo Finance."""
        # This test requires network access
        data = provider.get_historical_data(
            "AAPL",
            start_date="2024-01-01",
            end_date="2024-01-07",
        )

        # Should have roughly 5 trading days (accounting for holidays/weekends)
        assert len(data) >= 3
        assert len(data) <= 7

        # Verify data quality
        assert data["Close"].notna().all()
        assert (data["High"] >= data["Low"]).all()
        assert (data["High"] >= data["Close"]).all()
        assert (data["Low"] <= data["Close"]).all()
