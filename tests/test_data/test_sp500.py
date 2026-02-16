"""Tests for S&P500 utilities module."""

import pytest

from copilot_quant.data.sp500 import (
    DOW_30_TICKERS,
    FAANG,
    MAGNIFICENT_7,
    get_sp500_tickers,
)


class TestSP500Tickers:
    """Tests for S&P500 ticker functions."""

    def test_get_sp500_tickers_returns_list(self):
        """Test that get_sp500_tickers returns a list."""
        tickers = get_sp500_tickers(source="manual")
        assert isinstance(tickers, list)

    def test_get_sp500_tickers_not_empty(self):
        """Test that ticker list is not empty."""
        tickers = get_sp500_tickers(source="manual")
        assert len(tickers) > 0

    def test_get_sp500_tickers_contains_strings(self):
        """Test that all tickers are strings."""
        tickers = get_sp500_tickers(source="manual")
        assert all(isinstance(ticker, str) for ticker in tickers)

    def test_get_sp500_tickers_major_stocks(self):
        """Test that major stocks are in the list."""
        tickers = get_sp500_tickers(source="manual")

        # Check for major tech stocks
        major_stocks = ["AAPL", "MSFT", "GOOGL", "AMZN"]
        for stock in major_stocks:
            assert stock in tickers, f"{stock} should be in S&P500 list"

    def test_get_sp500_tickers_with_index(self):
        """Test including S&P500 index symbol."""
        tickers = get_sp500_tickers(include_index=True, source="manual")
        assert "^GSPC" in tickers

    def test_get_sp500_tickers_without_index(self):
        """Test excluding S&P500 index symbol."""
        tickers = get_sp500_tickers(include_index=False, source="manual")
        assert "^GSPC" not in tickers

    def test_get_sp500_tickers_sorted(self):
        """Test that tickers are sorted alphabetically."""
        tickers = get_sp500_tickers(source="manual")
        assert tickers == sorted(tickers)

    def test_invalid_source_raises_error(self):
        """Test that invalid source raises ValueError."""
        with pytest.raises(ValueError):
            get_sp500_tickers(source="invalid_source")


class TestPredefinedLists:
    """Tests for predefined ticker lists."""

    def test_faang_list(self):
        """Test FAANG ticker list."""
        assert len(FAANG) == 5
        assert "AAPL" in FAANG
        assert "META" in FAANG
        assert "AMZN" in FAANG
        assert "NFLX" in FAANG
        assert "GOOGL" in FAANG

    def test_magnificent_7_list(self):
        """Test Magnificent 7 ticker list."""
        assert len(MAGNIFICENT_7) == 7
        assert "AAPL" in MAGNIFICENT_7
        assert "MSFT" in MAGNIFICENT_7
        assert "GOOGL" in MAGNIFICENT_7
        assert "AMZN" in MAGNIFICENT_7
        assert "NVDA" in MAGNIFICENT_7
        assert "META" in MAGNIFICENT_7
        assert "TSLA" in MAGNIFICENT_7

    def test_dow_30_list(self):
        """Test Dow 30 ticker list."""
        assert len(DOW_30_TICKERS) == 30
        # Check a few major Dow components
        assert "AAPL" in DOW_30_TICKERS
        assert "MSFT" in DOW_30_TICKERS
        assert "JPM" in DOW_30_TICKERS


@pytest.mark.integration
class TestSP500Integration:
    """Integration tests that require network access."""

    def test_get_sp500_from_wikipedia(self):
        """Test fetching S&P500 list from Wikipedia."""
        tickers = get_sp500_tickers(source="wikipedia")

        # S&P500 should have ~500 stocks
        assert len(tickers) > 450
        assert len(tickers) < 550

        # Should include major stocks
        assert "AAPL" in tickers
        assert "MSFT" in tickers
