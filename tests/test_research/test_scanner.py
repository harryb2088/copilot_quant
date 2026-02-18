"""Tests for SecurityScanner class."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from copilot_quant.research.scanner import SecurityScanner


class TestSecurityScannerInitialization:
    """Tests for SecurityScanner initialization."""
    
    def test_initialization_with_local_source(self):
        """Test that scanner initializes correctly with local data source."""
        scanner = SecurityScanner(data_source='local')
        assert scanner.data_source == 'local'
        assert scanner.df is not None
        assert isinstance(scanner.df, pd.DataFrame)
    
    def test_initialization_with_yfinance_source(self):
        """Test that scanner initializes correctly with yfinance data source."""
        scanner = SecurityScanner(data_source='yfinance')
        assert scanner.data_source == 'yfinance'
        assert scanner.df is None
    
    def test_initialization_with_invalid_source(self):
        """Test that invalid data source raises ValueError."""
        with pytest.raises(ValueError, match="Invalid data_source"):
            SecurityScanner(data_source='invalid_source')
    
    def test_local_universe_has_tickers(self):
        """Test that local universe loads with ticker data."""
        scanner = SecurityScanner(data_source='local')
        assert len(scanner.df) > 0
        assert 'ticker' in scanner.df.columns
        assert 'sector' in scanner.df.columns
        assert 'market_cap' in scanner.df.columns
        assert 'asset_type' in scanner.df.columns


class TestSecurityScannerFind:
    """Tests for SecurityScanner.find() method."""
    
    @pytest.fixture
    def mock_scanner(self):
        """Create a SecurityScanner with mocked data."""
        scanner = SecurityScanner(data_source='local')
        
        # Replace with mock data
        scanner.df = pd.DataFrame([
            {
                'ticker': 'AAPL',
                'name': 'Apple Inc.',
                'sector': 'Technology',
                'industry': 'Consumer Electronics',
                'market_cap': 3000000000000,  # $3T
                'avg_volume': 50000000,
                'volatility': 0.25,
                'dividend_yield': 0.005,
                'asset_type': 'equity',
            },
            {
                'ticker': 'MSFT',
                'name': 'Microsoft Corporation',
                'sector': 'Technology',
                'industry': 'Software',
                'market_cap': 2800000000000,  # $2.8T
                'avg_volume': 30000000,
                'volatility': 0.22,
                'dividend_yield': 0.008,
                'asset_type': 'equity',
            },
            {
                'ticker': 'JNJ',
                'name': 'Johnson & Johnson',
                'sector': 'Healthcare',
                'industry': 'Pharmaceuticals',
                'market_cap': 400000000000,  # $400B
                'avg_volume': 8000000,
                'volatility': 0.18,
                'dividend_yield': 0.028,
                'asset_type': 'equity',
            },
            {
                'ticker': 'SPY',
                'name': 'SPDR S&P 500 ETF',
                'sector': None,
                'industry': None,
                'market_cap': 500000000000,  # $500B
                'avg_volume': 80000000,
                'volatility': 0.15,
                'dividend_yield': 0.015,
                'asset_type': 'etf',
            },
            {
                'ticker': 'NVDA',
                'name': 'NVIDIA Corporation',
                'sector': 'Technology',
                'industry': 'Semiconductors',
                'market_cap': 1500000000000,  # $1.5T
                'avg_volume': 40000000,
                'volatility': 0.45,
                'dividend_yield': 0.001,
                'asset_type': 'equity',
            },
        ])
        
        return scanner
    
    def test_find_returns_dataframe(self, mock_scanner):
        """Test that find() returns a DataFrame by default."""
        results = mock_scanner.find()
        assert isinstance(results, pd.DataFrame)
    
    def test_find_returns_json_when_requested(self, mock_scanner):
        """Test that find() returns JSON format when as_json=True."""
        results = mock_scanner.find(as_json=True)
        assert isinstance(results, list)
        assert all(isinstance(item, dict) for item in results)
    
    def test_find_filter_by_sector(self, mock_scanner):
        """Test filtering by sector."""
        results = mock_scanner.find(sector='Technology')
        assert len(results) == 3
        assert all(results['sector'] == 'Technology')
        assert set(results['ticker']) == {'AAPL', 'MSFT', 'NVDA'}
    
    def test_find_filter_by_industry(self, mock_scanner):
        """Test filtering by industry."""
        results = mock_scanner.find(industry='Software')
        assert len(results) == 1
        assert results.iloc[0]['ticker'] == 'MSFT'
    
    def test_find_filter_by_market_cap_min(self, mock_scanner):
        """Test filtering by minimum market cap."""
        results = mock_scanner.find(market_cap_min=1e12)  # $1T
        assert len(results) == 3
        assert set(results['ticker']) == {'AAPL', 'MSFT', 'NVDA'}
    
    def test_find_filter_by_market_cap_max(self, mock_scanner):
        """Test filtering by maximum market cap."""
        results = mock_scanner.find(market_cap_max=5e11)  # $500B
        assert len(results) == 2
        assert set(results['ticker']) == {'JNJ', 'SPY'}
    
    def test_find_filter_by_market_cap_range(self, mock_scanner):
        """Test filtering by market cap range."""
        results = mock_scanner.find(
            market_cap_min=4e11,  # $400B
            market_cap_max=6e11,  # $600B
        )
        assert len(results) == 2
        assert set(results['ticker']) == {'JNJ', 'SPY'}
    
    def test_find_filter_by_avg_volume(self, mock_scanner):
        """Test filtering by average volume."""
        results = mock_scanner.find(avg_volume_min=30000000)
        assert len(results) == 4
        assert set(results['ticker']) == {'AAPL', 'MSFT', 'SPY', 'NVDA'}
    
    def test_find_filter_by_volatility_max(self, mock_scanner):
        """Test filtering by maximum volatility."""
        results = mock_scanner.find(volatility_max=0.20)
        assert len(results) == 2
        assert set(results['ticker']) == {'JNJ', 'SPY'}
    
    def test_find_filter_by_volatility_min(self, mock_scanner):
        """Test filtering by minimum volatility."""
        results = mock_scanner.find(volatility_min=0.40)
        assert len(results) == 1
        assert results.iloc[0]['ticker'] == 'NVDA'
    
    def test_find_filter_by_asset_type_equity(self, mock_scanner):
        """Test filtering by asset type - equity."""
        results = mock_scanner.find(asset_type='equity')
        assert len(results) == 4
        assert all(results['asset_type'] == 'equity')
    
    def test_find_filter_by_asset_type_etf(self, mock_scanner):
        """Test filtering by asset type - ETF."""
        results = mock_scanner.find(asset_type='etf')
        assert len(results) == 1
        assert results.iloc[0]['ticker'] == 'SPY'
    
    def test_find_filter_by_dividend_yield_min(self, mock_scanner):
        """Test filtering by minimum dividend yield."""
        results = mock_scanner.find(dividend_yield_min=0.01)
        assert len(results) == 2
        assert set(results['ticker']) == {'JNJ', 'SPY'}
    
    def test_find_filter_by_dividend_yield_max(self, mock_scanner):
        """Test filtering by maximum dividend yield."""
        results = mock_scanner.find(dividend_yield_max=0.01)
        assert len(results) == 3
        assert set(results['ticker']) == {'AAPL', 'MSFT', 'NVDA'}
    
    def test_find_multiple_filters_combined(self, mock_scanner):
        """Test combining multiple filters."""
        results = mock_scanner.find(
            sector='Technology',
            market_cap_min=2e12,  # $2T
            volatility_max=0.30,
        )
        assert len(results) == 2
        assert set(results['ticker']) == {'AAPL', 'MSFT'}
    
    def test_find_with_specific_tickers(self, mock_scanner):
        """Test filtering to specific tickers."""
        results = mock_scanner.find(tickers=['AAPL', 'JNJ'])
        assert len(results) == 2
        assert set(results['ticker']) == {'AAPL', 'JNJ'}
    
    def test_find_with_exclude_tickers(self, mock_scanner):
        """Test excluding specific tickers."""
        results = mock_scanner.find(exclude_tickers=['AAPL', 'MSFT'])
        assert len(results) == 3
        assert set(results['ticker']) == {'JNJ', 'SPY', 'NVDA'}
    
    def test_find_raises_error_when_no_matches(self, mock_scanner):
        """Test that find() raises ValueError when no securities match."""
        with pytest.raises(ValueError, match="No securities match"):
            mock_scanner.find(market_cap_min=1e15)  # $1000T - impossible
    
    def test_find_complex_scenario(self, mock_scanner):
        """Test a complex real-world filtering scenario."""
        # Find large-cap tech stocks with low volatility and decent dividends
        results = mock_scanner.find(
            sector='Technology',
            market_cap_min=1e12,
            volatility_max=0.30,
            dividend_yield_min=0.005,
        )
        assert len(results) == 2
        assert set(results['ticker']) == {'AAPL', 'MSFT'}


class TestSecurityScannerYFinanceMode:
    """Tests for SecurityScanner with yfinance data source."""
    
    @patch('copilot_quant.research.scanner.yf.Ticker')
    @patch('copilot_quant.research.scanner.get_sp500_tickers')
    def test_find_with_yfinance_source(self, mock_get_tickers, mock_yf_ticker):
        """Test finding securities with yfinance data source."""
        # Mock S&P 500 tickers
        mock_get_tickers.return_value = ['AAPL', 'MSFT']
        
        # Mock yfinance responses
        mock_aapl_info = {
            'longName': 'Apple Inc.',
            'sector': 'Technology',
            'industry': 'Consumer Electronics',
            'marketCap': 3000000000000,
            'averageVolume': 50000000,
            'dividendYield': 0.005,
            'quoteType': 'EQUITY',
        }
        
        mock_msft_info = {
            'longName': 'Microsoft Corporation',
            'sector': 'Technology',
            'industry': 'Software',
            'marketCap': 2800000000000,
            'averageVolume': 30000000,
            'dividendYield': 0.008,
            'quoteType': 'EQUITY',
        }
        
        # Configure mock to return different info for each ticker
        def get_ticker_info(ticker):
            mock = MagicMock()
            if ticker == 'AAPL':
                mock.info = mock_aapl_info
            else:
                mock.info = mock_msft_info
            mock.history.return_value = pd.DataFrame()  # Empty history
            return mock
        
        mock_yf_ticker.side_effect = get_ticker_info
        
        # Create scanner and search
        scanner = SecurityScanner(data_source='yfinance')
        results = scanner.find(sector='Technology')
        
        assert len(results) == 2
        assert all(results['sector'] == 'Technology')
    
    @patch('copilot_quant.research.scanner.yf.Ticker')
    def test_fetch_live_data_option(self, mock_yf_ticker):
        """Test fetch_live_data option with local scanner."""
        # Mock yfinance response
        mock_info = {
            'longName': 'Test Corp',
            'sector': 'Technology',
            'marketCap': 1000000000,
            'quoteType': 'EQUITY',
        }
        
        mock_ticker = MagicMock()
        mock_ticker.info = mock_info
        mock_ticker.history.return_value = pd.DataFrame()
        mock_yf_ticker.return_value = mock_ticker
        
        # Create scanner with local source
        scanner = SecurityScanner(data_source='local')
        
        # Search with fetch_live_data=True
        results = scanner.find(
            tickers=['TEST'],
            fetch_live_data=True,
        )
        
        assert len(results) == 1
        assert results.iloc[0]['ticker'] == 'TEST'


class TestSecurityScannerHelperMethods:
    """Tests for SecurityScanner helper methods."""
    
    def test_determine_asset_type_etf(self):
        """Test determining asset type for ETF."""
        scanner = SecurityScanner(data_source='local')
        info = {'quoteType': 'ETF'}
        assert scanner._determine_asset_type(info) == 'etf'
    
    def test_determine_asset_type_equity(self):
        """Test determining asset type for equity."""
        scanner = SecurityScanner(data_source='local')
        info = {'quoteType': 'EQUITY'}
        assert scanner._determine_asset_type(info) == 'equity'
    
    def test_determine_asset_type_default(self):
        """Test determining asset type with missing quoteType."""
        scanner = SecurityScanner(data_source='local')
        info = {}
        assert scanner._determine_asset_type(info) == 'equity'
    
    @patch('copilot_quant.research.scanner.yf.Ticker')
    def test_fetch_ticker_data_with_volatility(self, mock_yf_ticker):
        """Test fetching ticker data calculates volatility."""
        # Mock historical data for volatility calculation
        hist_data = pd.DataFrame({
            'Close': [100, 102, 101, 103, 105, 104, 106, 108, 107, 109,
                      110, 108, 111, 113, 112, 114, 116, 115, 117, 119,
                      118, 120, 122, 121, 123] * 2,  # 50 days of data
        })
        
        mock_ticker = MagicMock()
        mock_ticker.info = {
            'longName': 'Test Corp',
            'sector': 'Technology',
            'marketCap': 1000000000,
            'quoteType': 'EQUITY',
        }
        mock_ticker.history.return_value = hist_data
        mock_yf_ticker.return_value = mock_ticker
        
        scanner = SecurityScanner(data_source='local')
        data = scanner._fetch_ticker_data('TEST')
        
        assert data['volatility'] is not None
        assert isinstance(data['volatility'], (int, float))
    
    @patch('copilot_quant.research.scanner.yf.Ticker')
    def test_fetch_ticker_data_handles_errors(self, mock_yf_ticker):
        """Test that fetch_ticker_data handles errors gracefully."""
        # Mock to raise exception
        mock_yf_ticker.side_effect = Exception("API Error")
        
        scanner = SecurityScanner(data_source='local')
        data = scanner._fetch_ticker_data('INVALID')
        
        # Should return data with None values instead of crashing
        assert data['ticker'] == 'INVALID'
        assert data['name'] is None
        assert data['sector'] is None


@pytest.mark.integration
class TestSecurityScannerIntegration:
    """Integration tests that may require network access."""
    
    def test_scanner_with_real_sp500_data(self):
        """Test scanner with real S&P 500 data."""
        scanner = SecurityScanner(data_source='local')
        
        # Should have loaded S&P 500 tickers
        assert len(scanner.df) > 50
        assert 'AAPL' in scanner.df['ticker'].values
        assert 'MSFT' in scanner.df['ticker'].values
    
    def test_find_all_equities(self):
        """Test finding all equities in universe."""
        scanner = SecurityScanner(data_source='local')
        results = scanner.find(asset_type='equity')
        
        # S&P 500 is all equities
        assert len(results) > 50
