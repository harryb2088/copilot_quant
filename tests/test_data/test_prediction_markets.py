"""Tests for prediction market providers.

TESTING APPROACH - MOCK-FIRST STRATEGY
======================================

All tests in this file use mocks to avoid external API calls. This ensures:
1. Tests run in CI/CD environments with firewall restrictions
2. Tests are fast and deterministic
3. Tests don't depend on external service availability

The following APIs are mocked to avoid firewall blocks:
- gamma-api.polymarket.com (Polymarket)
- api.elections.kalshi.com (Kalshi)
- www.predictit.org (PredictIt)
- www.metaculus.com (Metaculus)

RUNNING LIVE API TESTS (OPTIONAL)
==================================

To test against live APIs locally (when needed):
1. Mark tests with @pytest.mark.live_api decorator
2. Run with: pytest -m live_api tests/test_data/test_prediction_markets.py

By default, live_api tests are skipped in CI/CD to prevent firewall issues.

Mock data generators are available in:
tests/test_data/mock_prediction_markets/mock_data.py
"""

from unittest.mock import Mock, patch
import pandas as pd
import pytest
from datetime import datetime

from copilot_quant.data.prediction_markets import (
    PolymarketProvider,
    KalshiProvider,
    PredictItProvider,
    MetaculusProvider,
    PredictionMarketStorage,
)
from tests.test_data.mock_prediction_markets.mock_data import (
    generate_mock_polymarket_markets,
    generate_mock_polymarket_price_data,
    generate_mock_kalshi_markets,
    generate_mock_kalshi_price_data,
    generate_mock_predictit_markets,
    generate_mock_predictit_contract_data,
    generate_mock_metaculus_markets,
    generate_mock_metaculus_prediction_data,
)


class TestPolymarketProvider:
    """Tests for Polymarket data provider.
    
    NOTE: All tests use mocks. To add live API tests in the future:
    1. Add @pytest.mark.live_api decorator to the test
    2. Remove the @patch decorator and make real API calls
    3. Run with: pytest -m live_api
    """

    @pytest.fixture
    def provider(self):
        """Create a PolymarketProvider instance."""
        return PolymarketProvider()

    def test_provider_initialization(self, provider):
        """Test that provider initializes correctly."""
        assert provider.name == "Polymarket"
        assert provider.base_url == "https://clob.polymarket.com"
        assert provider.gamma_url == "https://gamma-api.polymarket.com"

    @patch('requests.Session.get')
    def test_list_markets_returns_dataframe(self, mock_get, provider):
        """Test that list_markets returns a DataFrame."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                'condition_id': 'mock_123',
                'question': 'Test Question?',
                'category': 'Test',
                'end_date_iso': '2024-12-31T23:59:59Z',
                'active': True,
                'volume': 1000.0,
                'liquidity': 500.0,
            }
        ]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        markets = provider.list_markets(limit=10)
        
        assert isinstance(markets, pd.DataFrame)
        assert not markets.empty
        assert 'market_id' in markets.columns
        assert 'title' in markets.columns

    @patch('requests.Session.get')
    def test_list_markets_handles_empty_response(self, mock_get, provider):
        """Test that list_markets handles empty API response."""
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        markets = provider.list_markets()
        
        assert isinstance(markets, pd.DataFrame)
        assert markets.empty

    @patch('requests.Session.get')
    def test_get_market_details(self, mock_get, provider):
        """Test getting market details."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'condition_id': 'mock_123',
            'question': 'Test Question?',
            'description': 'Test description',
            'category': 'Test',
            'outcomes': ['Yes', 'No'],
            'tokens': [{'token_id': 'token_1'}],
            'volume': 1000.0,
            'liquidity': 500.0,
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        details = provider.get_market_details('mock_123')
        
        assert isinstance(details, dict)
        assert details['market_id'] == 'mock_123'
        assert details['title'] == 'Test Question?'

    def test_normalize_market_name(self, provider):
        """Test market name normalization."""
        name = provider.normalize_market_name("Will BTC reach $100k?")
        assert isinstance(name, str)
        assert name == "will_btc_reach_100k"


class TestKalshiProvider:
    """Tests for Kalshi data provider.
    
    NOTE: All tests use mocks. To add live API tests in the future:
    1. Add @pytest.mark.live_api decorator to the test
    2. Remove the @patch decorator and make real API calls
    3. Run with: pytest -m live_api
    """

    @pytest.fixture
    def provider(self):
        """Create a KalshiProvider instance."""
        return KalshiProvider()

    def test_provider_initialization(self, provider):
        """Test that provider initializes correctly."""
        assert provider.name == "Kalshi"
        assert provider.api_key is None

    def test_provider_initialization_with_api_key(self):
        """Test that provider initializes with API key."""
        provider = KalshiProvider(api_key="test_key")
        assert provider.api_key == "test_key"
        assert 'Authorization' in provider.session.headers

    @patch('requests.Session.get')
    def test_list_markets_returns_dataframe(self, mock_get, provider):
        """Test that list_markets returns a DataFrame."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'events': [
                {
                    'event_ticker': 'INX',
                    'category': 'Finance',
                    'markets': [
                        {
                            'ticker': 'INX-24DEC31-T5000',
                            'title': 'S&P 500 above 5000',
                            'status': 'open',
                            'volume': 50000.0,
                        }
                    ]
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        markets = provider.list_markets(limit=10)
        
        assert isinstance(markets, pd.DataFrame)
        assert not markets.empty
        assert 'market_id' in markets.columns


class TestPredictItProvider:
    """Tests for PredictIt data provider.
    
    NOTE: All tests use mocks. To add live API tests in the future:
    1. Add @pytest.mark.live_api decorator to the test
    2. Remove the @patch decorator and make real API calls
    3. Run with: pytest -m live_api
    """

    @pytest.fixture
    def provider(self):
        """Create a PredictItProvider instance."""
        return PredictItProvider()

    def test_provider_initialization(self, provider):
        """Test that provider initializes correctly."""
        assert provider.name == "PredictIt"
        assert provider.base_url == "https://www.predictit.org/api/marketdata"

    @patch('requests.Session.get')
    def test_list_markets_returns_dataframe(self, mock_get, provider):
        """Test that list_markets returns a DataFrame."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'markets': [
                {
                    'id': 7890,
                    'name': 'Test Market',
                    'url': 'politics/test',
                    'dateEnd': '2024-12-31T23:59:59',
                    'status': 'Open',
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        markets = provider.list_markets(limit=10)
        
        assert isinstance(markets, pd.DataFrame)
        assert not markets.empty
        assert 'market_id' in markets.columns

    @patch('copilot_quant.data.prediction_markets.predictit.PredictItProvider.get_market_details')
    def test_get_market_data_returns_dataframe(self, mock_get_details, provider):
        """Test that get_market_data returns contract data."""
        mock_get_details.return_value = {
            'contracts': [
                {
                    'id': 12345,
                    'name': 'Yes',
                    'lastTradePrice': 0.52,
                    'bestBuyYesCost': 0.53,
                    'bestBuyNoCost': 0.48,
                    'bestSellYesCost': 0.54,
                    'bestSellNoCost': 0.47,
                }
            ]
        }

        data = provider.get_market_data('7890')
        
        assert isinstance(data, pd.DataFrame)
        assert not data.empty


class TestMetaculusProvider:
    """Tests for Metaculus data provider.
    
    NOTE: All tests use mocks. To add live API tests in the future:
    1. Add @pytest.mark.live_api decorator to the test
    2. Remove the @patch decorator and make real API calls
    3. Run with: pytest -m live_api
    """

    @pytest.fixture
    def provider(self):
        """Create a MetaculusProvider instance."""
        return MetaculusProvider()

    def test_provider_initialization(self, provider):
        """Test that provider initializes correctly."""
        assert provider.name == "Metaculus"
        assert provider.base_url == "https://www.metaculus.com/api2"

    @patch('requests.Session.get')
    def test_list_markets_returns_dataframe(self, mock_get, provider):
        """Test that list_markets returns a DataFrame."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'results': [
                {
                    'id': 10001,
                    'title': 'Test Question',
                    'category': 'AI',
                    'close_time': '2030-01-01T00:00:00Z',
                    'status': 'open',
                    'number_of_predictions': 450,
                    'community_prediction': {'q2': 0.35},
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        markets = provider.list_markets(limit=10)
        
        assert isinstance(markets, pd.DataFrame)
        assert not markets.empty
        assert 'market_id' in markets.columns
        assert 'community_prediction' in markets.columns


class TestPredictionMarketStorage:
    """Tests for PredictionMarketStorage."""

    @pytest.fixture
    def csv_storage(self, tmp_path):
        """Create a CSV storage instance."""
        return PredictionMarketStorage(
            storage_type='csv',
            base_path=str(tmp_path / 'prediction_markets')
        )

    @pytest.fixture
    def sqlite_storage(self, tmp_path):
        """Create a SQLite storage instance."""
        return PredictionMarketStorage(
            storage_type='sqlite',
            db_path=str(tmp_path / 'markets.db')
        )

    def test_csv_storage_initialization(self, csv_storage):
        """Test CSV storage initialization."""
        assert csv_storage.storage_type == 'csv'
        assert csv_storage.base_path.exists()

    def test_sqlite_storage_initialization(self, sqlite_storage):
        """Test SQLite storage initialization."""
        assert sqlite_storage.storage_type == 'sqlite'
        from pathlib import Path
        assert Path(sqlite_storage.db_path).exists()

    def test_invalid_storage_type_raises_error(self, tmp_path):
        """Test that invalid storage type raises error."""
        with pytest.raises(ValueError):
            PredictionMarketStorage(
                storage_type='invalid',
                base_path=str(tmp_path)
            )

    def test_save_and_load_markets_csv(self, csv_storage):
        """Test saving and loading markets to CSV."""
        markets = generate_mock_polymarket_markets()
        csv_storage.save_markets('polymarket', markets)
        
        loaded = csv_storage.load_markets('polymarket')
        assert isinstance(loaded, pd.DataFrame)
        assert len(loaded) == len(markets)

    def test_save_and_load_markets_sqlite(self, sqlite_storage):
        """Test saving and loading markets to SQLite."""
        markets = generate_mock_polymarket_markets()
        sqlite_storage.save_markets('polymarket', markets)
        
        loaded = sqlite_storage.load_markets('polymarket')
        assert isinstance(loaded, pd.DataFrame)
        assert len(loaded) == len(markets)

    def test_save_and_load_market_data_csv(self, csv_storage):
        """Test saving and loading market data to CSV."""
        data = generate_mock_polymarket_price_data()
        csv_storage.save_market_data('polymarket', 'mock_123', data)
        
        loaded = csv_storage.load_market_data('polymarket', 'mock_123')
        assert isinstance(loaded, pd.DataFrame)
        assert len(loaded) == len(data)

    def test_save_and_load_market_data_sqlite(self, sqlite_storage):
        """Test saving and loading market data to SQLite."""
        data = generate_mock_polymarket_price_data()
        sqlite_storage.save_market_data('polymarket', 'mock_123', data)
        
        loaded = sqlite_storage.load_market_data('polymarket', 'mock_123')
        assert isinstance(loaded, pd.DataFrame)
        assert len(loaded) == len(data)

    def test_load_nonexistent_markets_returns_empty(self, csv_storage):
        """Test that loading nonexistent markets returns empty DataFrame."""
        loaded = csv_storage.load_markets('nonexistent')
        assert isinstance(loaded, pd.DataFrame)
        assert loaded.empty

    def test_normalize_filename(self, csv_storage):
        """Test filename normalization."""
        normalized = csv_storage._normalize_filename("Market-ID/123:456")
        assert isinstance(normalized, str)
        assert '/' not in normalized
        assert ':' not in normalized
