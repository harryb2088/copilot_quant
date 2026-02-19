"""
Unit tests for LiveDataFeedAdapter

Tests the adapter implementation that bridges IDataFeed interface
with IBKR live market data feed.
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
import pandas as pd

from copilot_quant.brokers.live_data_adapter import LiveDataFeedAdapter


class TestLiveDataFeedAdapter(unittest.TestCase):
    """Test suite for LiveDataFeedAdapter"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock the underlying IBKRLiveDataFeed
        self.mock_live_feed_patcher = patch('copilot_quant.brokers.live_data_adapter.IBKRLiveDataFeed')
        self.mock_live_feed_class = self.mock_live_feed_patcher.start()
        self.mock_live_feed = MagicMock()
        self.mock_live_feed_class.return_value = self.mock_live_feed
        
        # Create adapter instance
        self.adapter = LiveDataFeedAdapter(
            paper_trading=True,
            enable_cache=True,
            cache_size=100
        )
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.mock_live_feed_patcher.stop()
    
    def test_initialization(self):
        """Test adapter initialization"""
        self.assertIsNotNone(self.adapter)
        self.assertTrue(self.adapter.enable_cache)
        self.assertEqual(self.adapter.cache_size, 100)
        self.assertFalse(self.adapter._is_fallback_mode)
    
    def test_connect_success(self):
        """Test successful connection"""
        self.mock_live_feed.connect.return_value = True
        
        result = self.adapter.connect(timeout=30, retry_count=3)
        
        self.assertTrue(result)
        self.assertFalse(self.adapter._is_fallback_mode)
        self.mock_live_feed.connect.assert_called_once_with(timeout=30, retry_count=3)
    
    def test_connect_failure(self):
        """Test connection failure"""
        self.mock_live_feed.connect.return_value = False
        
        result = self.adapter.connect()
        
        self.assertFalse(result)
    
    def test_is_connected(self):
        """Test connection status check"""
        self.mock_live_feed.is_connected.return_value = True
        
        result = self.adapter.is_connected()
        
        self.assertTrue(result)
        self.mock_live_feed.is_connected.assert_called_once()
    
    def test_reconnect_success(self):
        """Test successful reconnection"""
        self.mock_live_feed.reconnect.return_value = True
        
        result = self.adapter.reconnect(timeout=30)
        
        self.assertTrue(result)
        self.assertFalse(self.adapter._is_fallback_mode)
    
    def test_reconnect_failure_enters_fallback_mode(self):
        """Test reconnection failure enters fallback mode"""
        self.mock_live_feed.reconnect.return_value = False
        
        result = self.adapter.reconnect()
        
        self.assertFalse(result)
        self.assertTrue(self.adapter._is_fallback_mode)
    
    def test_get_historical_data_success(self):
        """Test successful historical data retrieval"""
        # Create mock data
        mock_data = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [105, 106, 107],
            'low': [99, 100, 101],
            'close': [103, 104, 105],
            'volume': [1000, 1100, 1200]
        }, index=pd.date_range('2024-01-01', periods=3))
        
        self.mock_live_feed.is_connected.return_value = True
        self.mock_live_feed.get_historical_bars.return_value = mock_data.copy()
        
        result = self.adapter.get_historical_data(
            symbol='AAPL',
            start_date=datetime(2024, 1, 1),
            interval='1d'
        )
        
        self.assertIsNotNone(result)
        self.assertFalse(result.empty)
        self.assertIn('Close', result.columns)
        self.assertEqual(len(result), 3)
    
    def test_get_historical_data_not_connected_reconnects(self):
        """Test historical data retrieval reconnects if not connected"""
        self.mock_live_feed.is_connected.return_value = False
        self.mock_live_feed.reconnect.return_value = True
        
        mock_data = pd.DataFrame({
            'close': [100]
        }, index=pd.date_range('2024-01-01', periods=1))
        
        self.mock_live_feed.get_historical_bars.return_value = mock_data
        
        result = self.adapter.get_historical_data('AAPL')
        
        self.mock_live_feed.reconnect.assert_called_once()
        self.assertIsNotNone(result)
    
    def test_get_historical_data_caches_data(self):
        """Test that historical data is cached"""
        mock_data = pd.DataFrame({
            'close': [100, 101, 102]
        }, index=pd.date_range('2024-01-01', periods=3))
        
        self.mock_live_feed.is_connected.return_value = True
        self.mock_live_feed.get_historical_bars.return_value = mock_data
        
        self.adapter.get_historical_data('AAPL')
        
        # Check cache
        cached_data = self.adapter.get_cached_data('AAPL')
        self.assertIsNotNone(cached_data)
        self.assertEqual(len(cached_data), 3)
    
    def test_get_historical_data_fallback_to_cache(self):
        """Test fallback to cached data on error"""
        # First, populate cache
        mock_data = pd.DataFrame({
            'close': [100, 101]
        }, index=pd.date_range('2024-01-01', periods=2))
        
        self.mock_live_feed.is_connected.return_value = True
        self.mock_live_feed.get_historical_bars.return_value = mock_data
        self.adapter.get_historical_data('AAPL')
        
        # Now simulate error
        self.mock_live_feed.get_historical_bars.side_effect = Exception("Connection error")
        
        result = self.adapter.get_historical_data('AAPL')
        
        # Should return cached data
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
    
    def test_get_multiple_symbols(self):
        """Test retrieving data for multiple symbols"""
        # Mock data for each symbol
        aapl_data = pd.DataFrame({
            'Close': [100, 101]
        }, index=pd.date_range('2024-01-01', periods=2))
        
        msft_data = pd.DataFrame({
            'Close': [200, 201]
        }, index=pd.date_range('2024-01-01', periods=2))
        
        def mock_get_historical_data(symbol, **kwargs):
            if symbol == 'AAPL':
                return aapl_data
            elif symbol == 'MSFT':
                return msft_data
            return pd.DataFrame()
        
        # Patch get_historical_data method
        with patch.object(self.adapter, 'get_historical_data', side_effect=mock_get_historical_data):
            result = self.adapter.get_multiple_symbols(['AAPL', 'MSFT'])
        
        self.assertIsNotNone(result)
        self.assertFalse(result.empty)
    
    def test_get_ticker_info(self):
        """Test getting ticker metadata"""
        info = self.adapter.get_ticker_info('AAPL')
        
        self.assertIsInstance(info, dict)
        self.assertEqual(info['symbol'], 'AAPL')
        self.assertIn('exchange', info)
    
    def test_subscribe(self):
        """Test subscribing to real-time data"""
        self.mock_live_feed.is_connected.return_value = True
        self.mock_live_feed.subscribe.return_value = {'AAPL': True, 'MSFT': True}
        
        results = self.adapter.subscribe(['AAPL', 'MSFT'])
        
        self.assertEqual(results, {'AAPL': True, 'MSFT': True})
        self.mock_live_feed.subscribe.assert_called_once_with(['AAPL', 'MSFT'])
    
    def test_subscribe_not_connected(self):
        """Test subscribing when not connected returns False"""
        self.mock_live_feed.is_connected.return_value = False
        
        results = self.adapter.subscribe(['AAPL'])
        
        self.assertEqual(results, {'AAPL': False})
    
    def test_unsubscribe(self):
        """Test unsubscribing from real-time data"""
        self.mock_live_feed.unsubscribe.return_value = {'AAPL': True}
        
        results = self.adapter.unsubscribe(['AAPL'])
        
        self.assertEqual(results, {'AAPL': True})
    
    def test_get_latest_price(self):
        """Test getting latest price"""
        self.mock_live_feed.get_latest_price.return_value = 150.25
        
        price = self.adapter.get_latest_price('AAPL')
        
        self.assertEqual(price, 150.25)
    
    def test_get_latest_bar(self):
        """Test getting latest bar"""
        mock_tick_data = {
            'open': 150.0,
            'high': 151.0,
            'low': 149.5,
            'last': 150.5,
            'volume': 1000,
            'time': datetime.now()
        }
        
        self.mock_live_feed.get_latest_data.return_value = mock_tick_data
        
        bar = self.adapter.get_latest_bar('AAPL')
        
        self.assertIsNotNone(bar)
        self.assertIn('Open', bar.index)
        self.assertIn('Close', bar.index)
        self.assertEqual(bar['Open'], 150.0)
        self.assertEqual(bar['Close'], 150.5)
    
    def test_get_latest_bar_no_data(self):
        """Test getting latest bar when no data available"""
        self.mock_live_feed.get_latest_data.return_value = {}
        
        bar = self.adapter.get_latest_bar('AAPL')
        
        self.assertIsNone(bar)
    
    def test_interval_conversion(self):
        """Test interval to bar size conversion"""
        self.assertEqual(self.adapter._convert_interval_to_bar_size('1m'), '1 min')
        self.assertEqual(self.adapter._convert_interval_to_bar_size('5m'), '5 mins')
        self.assertEqual(self.adapter._convert_interval_to_bar_size('1h'), '1 hour')
        self.assertEqual(self.adapter._convert_interval_to_bar_size('1d'), '1 day')
        self.assertEqual(self.adapter._convert_interval_to_bar_size('1w'), '1 week')
    
    def test_duration_calculation(self):
        """Test duration calculation from date range"""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 15)
        
        duration = self.adapter._calculate_duration(start, end)
        
        # 14 days
        self.assertEqual(duration, '14 D')
    
    def test_duration_calculation_months(self):
        """Test duration calculation for months"""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 3, 1)
        
        duration = self.adapter._calculate_duration(start, end)
        
        # ~60 days = 2 months
        self.assertEqual(duration, '2 M')
    
    def test_clear_cache_single_symbol(self):
        """Test clearing cache for single symbol"""
        # Populate cache
        self.adapter._bar_cache['AAPL'] = pd.DataFrame()
        self.adapter._bar_cache['MSFT'] = pd.DataFrame()
        
        self.adapter.clear_cache('AAPL')
        
        self.assertNotIn('AAPL', self.adapter._bar_cache)
        self.assertIn('MSFT', self.adapter._bar_cache)
    
    def test_clear_cache_all(self):
        """Test clearing all cache"""
        # Populate cache
        self.adapter._bar_cache['AAPL'] = pd.DataFrame()
        self.adapter._bar_cache['MSFT'] = pd.DataFrame()
        
        self.adapter.clear_cache()
        
        self.assertEqual(len(self.adapter._bar_cache), 0)
    
    def test_is_fallback_mode(self):
        """Test fallback mode detection"""
        self.assertFalse(self.adapter.is_fallback_mode())
        
        self.adapter._is_fallback_mode = True
        self.assertTrue(self.adapter.is_fallback_mode())
    
    def test_disconnect(self):
        """Test disconnection"""
        self.adapter.disconnect()
        
        self.mock_live_feed.disconnect.assert_called_once()
    
    def test_context_manager(self):
        """Test using adapter as context manager"""
        self.mock_live_feed.connect.return_value = True
        
        with self.adapter as adapter:
            self.assertIsNotNone(adapter)
        
        self.mock_live_feed.connect.assert_called()
        self.mock_live_feed.disconnect.assert_called()


if __name__ == '__main__':
    unittest.main()
