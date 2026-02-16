"""Tests for prediction market providers module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime

from copilot_quant.data.prediction_markets import (
    PolymarketProvider,
    KalshiProvider,
    get_prediction_market_provider,
)


class TestPolymarketProvider:
    """Tests for Polymarket data provider."""

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
    """Tests for Kalshi data provider."""

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
