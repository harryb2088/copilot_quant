"""
Tests for IBKR Live Market Data Feed

These tests use mocking to avoid requiring an actual IBKR connection.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from copilot_quant.brokers.live_market_data import IBKRLiveDataFeed


class TestIBKRLiveDataFeed(unittest.TestCase):
    """Test cases for IBKRLiveDataFeed"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Patch IB class to avoid actual connection
        self.ib_patcher = patch('copilot_quant.brokers.live_market_data.IB')
        self.mock_ib_class = self.ib_patcher.start()
        self.mock_ib = MagicMock()
        self.mock_ib_class.return_value = self.mock_ib
        
        # Mock connection status
        self.mock_ib.isConnected.return_value = False
        
    def tearDown(self):
        """Clean up after tests"""
        self.ib_patcher.stop()
    
    def test_initialization(self):
        """Test feed initialization with various configurations"""
        # Test default initialization
        feed = IBKRLiveDataFeed()
        self.assertEqual(feed.paper_trading, True)
        self.assertEqual(feed.host, '127.0.0.1')
        self.assertEqual(feed.port, 7497)  # Paper TWS
        self.assertEqual(feed.client_id, 1)
        
        # Test with custom parameters
        feed = IBKRLiveDataFeed(
            paper_trading=False,
            host='192.168.1.100',
            port=7496,
            client_id=5
        )
        self.assertEqual(feed.paper_trading, False)
        self.assertEqual(feed.host, '192.168.1.100')
        self.assertEqual(feed.port, 7496)
        self.assertEqual(feed.client_id, 5)
    
    def test_port_auto_detection(self):
        """Test automatic port detection based on trading mode"""
        # Paper TWS
        feed = IBKRLiveDataFeed(paper_trading=True, use_gateway=False)
        self.assertEqual(feed.port, 7497)
        
        # Live TWS
        feed = IBKRLiveDataFeed(paper_trading=False, use_gateway=False)
        self.assertEqual(feed.port, 7496)
        
        # Paper Gateway
        feed = IBKRLiveDataFeed(paper_trading=True, use_gateway=True)
        self.assertEqual(feed.port, 4002)
        
        # Live Gateway
        feed = IBKRLiveDataFeed(paper_trading=False, use_gateway=True)
        self.assertEqual(feed.port, 4001)
    
    def test_connect_success(self):
        """Test successful connection"""
        feed = IBKRLiveDataFeed()
        
        # Mock successful connection
        self.mock_ib.isConnected.return_value = True
        
        result = feed.connect(retry_count=1)
        
        self.assertTrue(result)
        self.assertTrue(feed.is_connected())
        self.mock_ib.connect.assert_called_once()
    
    def test_connect_failure(self):
        """Test connection failure"""
        feed = IBKRLiveDataFeed()
        
        # Mock connection failure
        self.mock_ib.isConnected.return_value = False
        
        result = feed.connect(retry_count=1)
        
        self.assertFalse(result)
        self.assertFalse(feed.is_connected())
    
    def test_connect_retry(self):
        """Test connection retry logic"""
        feed = IBKRLiveDataFeed()
        
        # Mock first attempt fails, second succeeds
        self.mock_ib.isConnected.side_effect = [False, True]
        
        with patch('copilot_quant.brokers.live_market_data.time.sleep'):
            result = feed.connect(retry_count=2)
        
        self.assertTrue(result)
        self.assertEqual(self.mock_ib.connect.call_count, 2)
    
    def test_subscribe_not_connected(self):
        """Test subscription when not connected"""
        feed = IBKRLiveDataFeed()
        
        results = feed.subscribe(['AAPL', 'MSFT'])
        
        self.assertEqual(results, {'AAPL': False, 'MSFT': False})
    
    def test_subscribe_success(self):
        """Test successful subscription to market data"""
        feed = IBKRLiveDataFeed()
        feed._connected = True
        self.mock_ib.isConnected.return_value = True
        
        # Mock contract qualification
        mock_contract = Mock()
        mock_contract.symbol = 'AAPL'
        self.mock_ib.qualifyContracts.return_value = [mock_contract]
        
        # Mock market data request with proper event support
        mock_ticker = Mock()
        mock_event = MagicMock()
        mock_event.__iadd__ = Mock(return_value=mock_event)
        mock_ticker.updateEvent = mock_event
        self.mock_ib.reqMktData.return_value = mock_ticker
        
        results = feed.subscribe(['AAPL'])
        
        self.assertEqual(results, {'AAPL': True})
        self.assertIn('AAPL', feed._subscriptions)
        self.mock_ib.reqMktData.assert_called_once()
    
    def test_subscribe_with_callback(self):
        """Test subscription with callback function"""
        feed = IBKRLiveDataFeed()
        feed._connected = True
        self.mock_ib.isConnected.return_value = True
        
        # Mock contract qualification
        mock_contract = Mock()
        self.mock_ib.qualifyContracts.return_value = [mock_contract]
        
        # Mock market data request with proper event support
        mock_ticker = Mock()
        mock_event = MagicMock()
        mock_event.__iadd__ = Mock(return_value=mock_event)
        mock_ticker.updateEvent = mock_event
        self.mock_ib.reqMktData.return_value = mock_ticker
        
        # Create callback
        callback = Mock()
        
        results = feed.subscribe(['AAPL'], callback=callback)
        
        self.assertEqual(results, {'AAPL': True})
        self.assertIn(callback, feed._callbacks['AAPL'])
    
    def test_subscribe_contract_qualification_failure(self):
        """Test subscription when contract qualification fails"""
        feed = IBKRLiveDataFeed()
        feed._connected = True
        self.mock_ib.isConnected.return_value = True
        
        # Mock failed contract qualification
        self.mock_ib.qualifyContracts.return_value = []
        
        results = feed.subscribe(['INVALID'])
        
        self.assertEqual(results, {'INVALID': False})
        self.assertNotIn('INVALID', feed._subscriptions)
    
    def test_unsubscribe_success(self):
        """Test successful unsubscription"""
        feed = IBKRLiveDataFeed()
        feed._connected = True
        self.mock_ib.isConnected.return_value = True
        
        # Setup subscription
        mock_contract = Mock()
        feed._subscriptions['AAPL'] = mock_contract
        feed._latest_data['AAPL'] = {'last': 150.0}
        feed._callbacks['AAPL'] = [Mock()]
        
        results = feed.unsubscribe(['AAPL'])
        
        self.assertEqual(results, {'AAPL': True})
        self.assertNotIn('AAPL', feed._subscriptions)
        self.assertNotIn('AAPL', feed._latest_data)
        self.assertNotIn('AAPL', feed._callbacks)
        self.mock_ib.cancelMktData.assert_called_once_with(mock_contract)
    
    def test_unsubscribe_not_subscribed(self):
        """Test unsubscribing from symbol not subscribed to"""
        feed = IBKRLiveDataFeed()
        feed._connected = True
        self.mock_ib.isConnected.return_value = True
        
        results = feed.unsubscribe(['AAPL'])
        
        self.assertEqual(results, {'AAPL': False})
    
    def test_get_latest_price(self):
        """Test getting latest price for a symbol"""
        feed = IBKRLiveDataFeed()
        
        # Setup latest data
        feed._latest_data['AAPL'] = {
            'last': 150.50,
            'bid': 150.45,
            'ask': 150.55
        }
        
        price = feed.get_latest_price('AAPL')
        
        self.assertEqual(price, 150.50)
    
    def test_get_latest_price_fallback(self):
        """Test price fallback when last is not available"""
        feed = IBKRLiveDataFeed()
        
        # Only close price available
        feed._latest_data['AAPL'] = {'close': 150.00}
        price = feed.get_latest_price('AAPL')
        self.assertEqual(price, 150.00)
        
        # Only bid price available
        feed._latest_data['MSFT'] = {'bid': 300.00}
        price = feed.get_latest_price('MSFT')
        self.assertEqual(price, 300.00)
    
    def test_get_latest_price_no_data(self):
        """Test getting price when no data available"""
        feed = IBKRLiveDataFeed()
        
        price = feed.get_latest_price('AAPL')
        
        self.assertIsNone(price)
    
    def test_get_latest_data(self):
        """Test getting full latest data for a symbol"""
        feed = IBKRLiveDataFeed()
        
        test_data = {
            'last': 150.50,
            'bid': 150.45,
            'ask': 150.55,
            'volume': 1000000
        }
        feed._latest_data['AAPL'] = test_data
        
        data = feed.get_latest_data('AAPL')
        
        self.assertEqual(data, test_data)
        # Verify it's a copy
        self.assertIsNot(data, feed._latest_data['AAPL'])
    
    @patch('copilot_quant.brokers.live_market_data.util')
    def test_get_historical_bars_success(self, mock_util):
        """Test successful historical data download"""
        feed = IBKRLiveDataFeed()
        feed._connected = True
        self.mock_ib.isConnected.return_value = True
        
        # Mock contract qualification
        mock_contract = Mock()
        self.mock_ib.qualifyContracts.return_value = [mock_contract]
        
        # Mock historical data
        mock_bars = [Mock() for _ in range(30)]
        self.mock_ib.reqHistoricalData.return_value = mock_bars
        
        # Mock DataFrame conversion
        test_df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=30),
            'open': np.random.uniform(100, 110, 30),
            'high': np.random.uniform(110, 120, 30),
            'low': np.random.uniform(90, 100, 30),
            'close': np.random.uniform(100, 110, 30),
            'volume': np.random.randint(1000000, 5000000, 30)
        })
        mock_util.df.return_value = test_df.copy()
        
        df = feed.get_historical_bars('AAPL', duration='1 M', bar_size='1 day')
        
        self.assertIsNotNone(df)
        self.assertGreater(len(df), 0)
        self.mock_ib.reqHistoricalData.assert_called_once()
    
    def test_get_historical_bars_not_connected(self):
        """Test historical data request when not connected"""
        feed = IBKRLiveDataFeed()
        
        df = feed.get_historical_bars('AAPL')
        
        self.assertIsNone(df)
    
    def test_get_historical_bars_contract_failure(self):
        """Test historical data when contract qualification fails"""
        feed = IBKRLiveDataFeed()
        feed._connected = True
        self.mock_ib.isConnected.return_value = True
        
        # Mock failed contract qualification
        self.mock_ib.qualifyContracts.return_value = []
        
        df = feed.get_historical_bars('INVALID')
        
        self.assertIsNone(df)
    
    def test_normalize_historical_data(self):
        """Test data normalization"""
        feed = IBKRLiveDataFeed()
        
        # Create test DataFrame
        df = pd.DataFrame({
            'Date': pd.date_range('2024-01-01', periods=5),
            'Open': [100, 101, 102, 103, 104],
            'High': [105, 106, 107, 108, 109],
            'Low': [95, 96, 97, 98, 99],
            'Close': [102, 103, 104, 105, 106],
            'Volume': [1000000, 1100000, 1200000, 1300000, 1400000]
        })
        
        normalized = feed._normalize_historical_data(df, 'AAPL')
        
        # Check column names are lowercase
        self.assertIn('open', normalized.columns)
        self.assertIn('high', normalized.columns)
        self.assertIn('close', normalized.columns)
        
        # Check symbol added
        self.assertIn('symbol', normalized.columns)
        self.assertTrue((normalized['symbol'] == 'AAPL').all())
        
        # Check date is index
        self.assertIsInstance(normalized.index, pd.DatetimeIndex)
    
    def test_ticker_update_handling(self):
        """Test handling of ticker updates"""
        feed = IBKRLiveDataFeed()
        
        # Create mock ticker
        mock_ticker = Mock()
        mock_ticker.time = datetime.now()
        mock_ticker.bid = 150.45
        mock_ticker.ask = 150.55
        mock_ticker.last = 150.50
        mock_ticker.close = 150.00
        mock_ticker.volume = 1000000
        mock_ticker.bidSize = 100
        mock_ticker.askSize = 200
        mock_ticker.high = 151.00
        mock_ticker.low = 149.00
        mock_ticker.open = 150.00
        
        feed._on_ticker_update('AAPL', mock_ticker)
        
        # Check data was stored
        self.assertIn('AAPL', feed._latest_data)
        data = feed._latest_data['AAPL']
        self.assertEqual(data['last'], 150.50)
        self.assertEqual(data['bid'], 150.45)
        self.assertEqual(data['ask'], 150.55)
        self.assertEqual(data['volume'], 1000000)
    
    def test_ticker_update_with_callback(self):
        """Test ticker update triggers callback"""
        feed = IBKRLiveDataFeed()
        
        # Setup callback
        callback = Mock()
        feed._callbacks['AAPL'].append(callback)
        
        # Create mock ticker
        mock_ticker = Mock()
        mock_ticker.time = datetime.now()
        mock_ticker.last = 150.50
        mock_ticker.bid = 150.45
        mock_ticker.ask = 150.55
        mock_ticker.close = None
        mock_ticker.volume = None
        mock_ticker.bidSize = None
        mock_ticker.askSize = None
        mock_ticker.high = None
        mock_ticker.low = None
        mock_ticker.open = None
        
        feed._on_ticker_update('AAPL', mock_ticker)
        
        # Check callback was called
        self.assertTrue(callback.called)
        call_args = callback.call_args[0]
        self.assertEqual(call_args[0], 'AAPL')
        self.assertIn('last', call_args[1])
    
    def test_error_handling(self):
        """Test error event handling"""
        feed = IBKRLiveDataFeed()
        
        # Test various error codes
        feed._on_error(1, 2104, "Market data farm connection is OK", None)
        feed._on_error(1, 200, "No security definition found", None)
        feed._on_error(1, 10197, "Delayed market data", None)
        feed._on_error(1, 502, "Couldn't connect", None)
    
    def test_disconnect_event_handling(self):
        """Test disconnect event handling"""
        feed = IBKRLiveDataFeed()
        feed._connected = True
        feed._subscriptions['AAPL'] = Mock()
        feed._latest_data['AAPL'] = {'last': 150.0}
        
        feed._on_disconnect()
        
        self.assertFalse(feed._connected)
        self.assertEqual(len(feed._subscriptions), 0)
        self.assertEqual(len(feed._latest_data), 0)
    
    def test_reconnect_success(self):
        """Test successful reconnection"""
        feed = IBKRLiveDataFeed()
        
        # Setup existing subscriptions
        feed._subscriptions['AAPL'] = Mock()
        callback = Mock()
        feed._callbacks['AAPL'] = [callback]
        
        # Mock reconnection
        self.mock_ib.isConnected.return_value = True
        
        # Mock re-subscription
        mock_contract = Mock()
        self.mock_ib.qualifyContracts.return_value = [mock_contract]
        mock_ticker = Mock()
        mock_ticker.updateEvent = Mock()
        self.mock_ib.reqMktData.return_value = mock_ticker
        
        with patch('copilot_quant.brokers.live_market_data.time.sleep'):
            result = feed.reconnect()
        
        self.assertTrue(result)
        self.assertTrue(feed.is_connected())
    
    def test_disconnect(self):
        """Test disconnection"""
        feed = IBKRLiveDataFeed()
        feed._connected = True
        self.mock_ib.isConnected.return_value = True
        
        # Setup subscriptions
        feed._subscriptions['AAPL'] = Mock()
        feed._subscriptions['MSFT'] = Mock()
        
        feed.disconnect()
        
        self.assertFalse(feed._connected)
        self.assertEqual(len(feed._subscriptions), 0)
        self.mock_ib.disconnect.assert_called_once()
    
    def test_get_subscribed_symbols(self):
        """Test getting list of subscribed symbols"""
        feed = IBKRLiveDataFeed()
        
        feed._subscriptions['AAPL'] = Mock()
        feed._subscriptions['MSFT'] = Mock()
        feed._subscriptions['GOOGL'] = Mock()
        
        symbols = feed.get_subscribed_symbols()
        
        self.assertEqual(set(symbols), {'AAPL', 'MSFT', 'GOOGL'})
    
    def test_context_manager(self):
        """Test using feed as context manager"""
        self.mock_ib.isConnected.return_value = True
        
        with IBKRLiveDataFeed() as feed:
            self.assertTrue(feed.is_connected())
        
        self.mock_ib.connect.assert_called()
        self.mock_ib.disconnect.assert_called()


if __name__ == '__main__':
    unittest.main()
