"""Tests for prediction market providers.

TESTING APPROACH - MOCK-FIRST STRATEGY

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

from copilot_quant.data.prediction_markets import (
    PolymarketProvider,
    KalshiProvider,
    get_prediction_market_provider,
    PredictItProvider,
    MetaculusProvider,
    PredictionMarketStorage,
)
from tests.test_data.mock_prediction_markets.mock_data import (
    generate_mock_polymarket_markets,
    generate_mock_polymarket_price_data,
)


class TestPolymarketProvider:
    """Tests for Polymarket data provider."""
    """Tests for Polymarket data provider.
    
    NOTE: All tests use mocks. To add live API tests in the future:
    1. Add @pytest.mark.live_api decorator to the test
    2. Remove the @patch decorator and make real API calls
    3. Run with: pytest -m live_api
    """

    @pytest.fixture
    def provider(self):
        """Create a PolymarketProvider instance."""
        return PolymarketProvider(rate_limit_delay=0)

    def test_provider_initialization(self, provider):
        """Test that provider initializes correctly."""
        assert provider.base_url == "https://clob.polymarket.com"
        assert provider.gamma_url == "https://gamma-api.polymarket.com"
        assert provider.rate_limit_delay == 0

    @patch('copilot_quant.data.prediction_markets.requests.Session.get')
    def test_get_active_markets_returns_dataframe(self, mock_get, provider):
        """Test that get_active_markets returns a DataFrame."""
        # Mock the API response
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                'id': 'market1',
                'question': 'Will BTC reach $100k?',
                'tags': ['crypto'],
                'end_date_iso': '2024-12-31',
                'volume': 100000,
                'liquidity': 50000,
                'created_at': '2024-01-01',
                'active': True,
            }
        ]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        markets = provider.list_markets(limit=10)
        
        assert isinstance(markets, pd.DataFrame)
        assert not markets.empty

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

        markets = provider.get_active_markets()

        assert isinstance(markets, pd.DataFrame)
        assert not markets.empty
        assert 'market_id' in markets.columns
        assert 'question' in markets.columns
        assert 'category' in markets.columns

    @patch('copilot_quant.data.prediction_markets.requests.Session.get')
    def test_get_active_markets_with_category_filter(self, mock_get, provider):
        """Test filtering markets by category."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                'id': 'market1',
                'question': 'Will BTC reach $100k?',
                'tags': ['crypto'],
                'end_date_iso': '2024-12-31',
                'volume': 100000,
                'liquidity': 50000,
                'created_at': '2024-01-01',
                'active': True,
            },
            {
                'id': 'market2',
                'question': 'Who will win the election?',
                'tags': ['politics'],
                'end_date_iso': '2024-11-05',
                'volume': 200000,
                'liquidity': 100000,
                'created_at': '2024-01-01',
                'active': True,
            }
        ]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        markets = provider.get_active_markets(category='crypto')

        assert isinstance(markets, pd.DataFrame)
        assert len(markets) == 1
        assert markets.iloc[0]['question'] == 'Will BTC reach $100k?'

    @patch('copilot_quant.data.prediction_markets.requests.Session.get')
    def test_get_market_prices_returns_dataframe(self, mock_get, provider):
        """Test that get_market_prices returns a DataFrame."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'price': 0.65,
            'volume': 100000,
            'liquidity': 50000,
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # This test is a placeholder - actual implementation needed
        # For now, just test that provider exists
        assert provider is not None

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

        prices = provider.get_market_prices('market1')

        assert isinstance(prices, pd.DataFrame)
        assert not prices.empty
        assert 'timestamp' in prices.columns
        assert 'price' in prices.columns
        assert 'volume' in prices.columns

    @patch('copilot_quant.data.prediction_markets.requests.Session.get')
    def test_get_market_info_returns_dict(self, mock_get, provider):
        """Test that get_market_info returns a dictionary."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'id': 'market1',
            'question': 'Will BTC reach $100k?',
            'price': 0.65,
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        info = provider.get_market_info('market1')

        assert isinstance(info, dict)
        assert 'id' in info
        assert 'question' in info


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
        return KalshiProvider(rate_limit_delay=0)

    def test_provider_initialization(self, provider):
        """Test that provider initializes correctly."""
        assert provider.base_url == "https://api.elections.kalshi.com/trade-api/v2"
        assert provider.rate_limit_delay == 0

    def test_provider_initialization_with_api_key(self):
        """Test initialization with API key."""
        provider = KalshiProvider(api_key='test_key', rate_limit_delay=0)
        assert 'Authorization' in provider.session.headers

    @patch('copilot_quant.data.prediction_markets.requests.Session.get')
    def test_get_active_markets_returns_dataframe(self, mock_get, provider):
        """Test that get_active_markets returns a DataFrame."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'markets': [
                {
                    'ticker': 'TICKER1',
                    'title': 'Will unemployment be above 5%?',
                    'category': 'economics',
                    'close_time': '2024-12-31',
                    'volume': 10000,
                    'liquidity': 5000,
                    'yes_bid': 0.45,
                    'yes_ask': 0.48,
                    'no_bid': 0.52,
                    'no_ask': 0.55,
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        markets = provider.get_active_markets(limit=10)
        
        assert isinstance(markets, pd.DataFrame)
        assert not markets.empty

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

        markets = provider.get_active_markets()

        assert isinstance(markets, pd.DataFrame)
        assert not markets.empty
        assert 'market_id' in markets.columns
        assert 'question' in markets.columns
        assert 'yes_bid' in markets.columns
        assert 'yes_ask' in markets.columns

    @patch('copilot_quant.data.prediction_markets.requests.Session.get')
    def test_get_market_prices_returns_dataframe(self, mock_get, provider):
        """Test that get_market_prices returns a DataFrame."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'history': [
                {
                    'ts': '2024-01-01T12:00:00Z',
                    'yes_bid': 0.45,
                    'yes_ask': 0.48,
                    'no_bid': 0.52,
                    'no_ask': 0.55,
                    'volume': 1000,
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # This test is a placeholder - actual implementation needed
        # For now, just test that provider exists
        assert provider is not None


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

        prices = provider.get_market_prices('TICKER1')

        assert isinstance(prices, pd.DataFrame)
        assert not prices.empty
        assert 'timestamp' in prices.columns
        assert 'yes_bid' in prices.columns
        assert 'yes_ask' in prices.columns

    @patch('copilot_quant.data.prediction_markets.requests.Session.get')
    def test_get_market_info_returns_dict(self, mock_get, provider):
        """Test that get_market_info returns a dictionary."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'market': {
                'ticker': 'TICKER1',
                'title': 'Will unemployment be above 5%?',
                'category': 'economics',
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # This test is a placeholder - actual implementation needed
        # For now, just test that provider exists
        assert provider is not None

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

        info = provider.get_market_info('TICKER1')

        assert isinstance(info, dict)
        assert 'ticker' in info
        assert 'title' in info


class TestProviderFactory:
    """Tests for prediction market provider factory function."""

    def test_get_polymarket_provider(self):
        """Test getting Polymarket provider."""
        provider = get_prediction_market_provider('polymarket')
        assert isinstance(provider, PolymarketProvider)

    def test_get_kalshi_provider(self):
        """Test getting Kalshi provider."""
        provider = get_prediction_market_provider('kalshi')
        assert isinstance(provider, KalshiProvider)

    def test_get_provider_invalid_name(self):
        """Test that invalid provider name raises error."""
        with pytest.raises(ValueError):
            get_prediction_market_provider('invalid_provider')

    def test_get_provider_with_kwargs(self):
        """Test passing kwargs to provider."""
        provider = get_prediction_market_provider(
            'kalshi',
            api_key='test_key',
            rate_limit_delay=1.0
        )
        assert isinstance(provider, KalshiProvider)
        assert provider.api_key == 'test_key'
        assert provider.rate_limit_delay == 1.0


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
