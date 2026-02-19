"""
Tests for IBKRBroker main class

These tests use mocking to avoid requiring an actual IBKR connection.
"""

import sys
from pathlib import Path

# Add project root to path (must be before other local imports)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest  # noqa: E402
import time  # noqa: E402
from unittest.mock import patch  # noqa: E402

from tests.mocks.mock_ib import MockIB, Stock, MarketOrder  # noqa: E402


# Import broker module to avoid circular dependency issues
def get_broker_class():
    """Helper to import IBKRBroker class"""
    import copilot_quant.brokers.interactive_brokers
    return copilot_quant.brokers.interactive_brokers.IBKRBroker


class TestIBKRBrokerInitialization:
    """Test cases for IBKRBroker initialization"""
    
    @patch('copilot_quant.brokers.connection_manager.IB')
    def test_initialization_defaults(self, mock_ib_class):
        """Test broker initialization with default parameters"""
        mock_ib = MockIB()
        mock_ib_class.return_value = mock_ib
        
        IBKRBroker = get_broker_class()
        broker = IBKRBroker()
        
        assert broker.paper_trading is True
        assert broker.use_gateway is False
        assert broker.connection_manager is not None
    
    @patch('copilot_quant.brokers.connection_manager.IB')
    def test_initialization_custom_params(self, mock_ib_class):
        """Test broker initialization with custom parameters"""
        mock_ib = MockIB()
        mock_ib_class.return_value = mock_ib
        
        IBKRBroker = get_broker_class()
        broker = IBKRBroker(
            paper_trading=False,
            host='192.168.1.100',
            port=7496,
            client_id=5,
            use_gateway=True
        )
        
        assert broker.paper_trading is False
        assert broker.use_gateway is True
        assert broker.connection_manager.host == '192.168.1.100'
        assert broker.connection_manager.port == 7496
        assert broker.connection_manager.client_id == 5
    
    @patch('copilot_quant.brokers.connection_manager.IB')
    def test_initialization_with_managers_disabled(self, mock_ib_class):
        """Test broker initialization with managers disabled"""
        mock_ib = MockIB()
        mock_ib_class.return_value = mock_ib
        
        IBKRBroker = get_broker_class()
        broker = IBKRBroker(
            enable_account_manager=False,
            enable_position_manager=False,
            enable_order_execution=False,
            enable_order_logging=False
        )
        
        assert broker._enable_account_manager is False
        assert broker._enable_position_manager is False
        assert broker._enable_order_execution is False
        assert broker._enable_order_logging is False


class TestIBKRBrokerConnection:
    """Test cases for IBKRBroker connection management"""
    
    @patch('copilot_quant.brokers.connection_manager.IB')
    def test_connect_success(self, mock_ib_class):
        """Test successful connection"""
        mock_ib = MockIB()
        mock_ib_class.return_value = mock_ib
        
        IBKRBroker = get_broker_class()
        broker = IBKRBroker()
        
        result = broker.connect()
        
        assert result is True
        assert broker.is_connected() is True
    
    @patch('copilot_quant.brokers.connection_manager.IB')
    def test_connect_failure(self, mock_ib_class):
        """Test connection failure"""
        mock_ib = MockIB()
        mock_ib.set_connection_fail_count(10)  # Always fail
        mock_ib_class.return_value = mock_ib
        
        IBKRBroker = get_broker_class()
        broker = IBKRBroker()
        
        result = broker.connect(retry_count=2)
        
        assert result is False
        assert broker.is_connected() is False
    
    @patch('copilot_quant.brokers.connection_manager.IB')
    def test_connect_initializes_managers(self, mock_ib_class):
        """Test that connection initializes managers"""
        mock_ib = MockIB()
        mock_ib_class.return_value = mock_ib
        
        IBKRBroker = get_broker_class()
        broker = IBKRBroker(
            enable_account_manager=True,
            enable_position_manager=True,
            enable_order_execution=True,
            enable_order_logging=True
        )
        
        broker.connect()
        
        assert broker.account_manager is not None
        assert broker.position_manager is not None
        assert broker.order_handler is not None
        assert broker.order_logger is not None
    
    @patch('copilot_quant.brokers.connection_manager.IB')
    def test_disconnect(self, mock_ib_class):
        """Test disconnection"""
        mock_ib = MockIB()
        mock_ib_class.return_value = mock_ib
        
        IBKRBroker = get_broker_class()
        broker = IBKRBroker()
        broker.connect()
        
        assert broker.is_connected() is True
        
        broker.disconnect()
        
        assert broker.is_connected() is False
    
    @patch('copilot_quant.brokers.connection_manager.IB')
    def test_is_connected(self, mock_ib_class):
        """Test is_connected method"""
        mock_ib = MockIB()
        mock_ib_class.return_value = mock_ib
        
        IBKRBroker = get_broker_class()
        broker = IBKRBroker()
        
        assert broker.is_connected() is False
        
        broker.connect()
        
        assert broker.is_connected() is True


class TestIBKRBrokerOrderExecution:
    """Test cases for order execution"""
    
    @patch('copilot_quant.brokers.connection_manager.IB')
    def test_place_market_order(self, mock_ib_class):
        """Test placing a market order"""
        mock_ib = MockIB()
        mock_ib.set_auto_fill(True, delay=0.05)
        mock_ib_class.return_value = mock_ib
        
        IBKRBroker = get_broker_class()
        broker = IBKRBroker()
        broker.connect()
        
        contract = Stock('AAPL')
        order = MarketOrder('BUY', 100)
        
        trade = broker.ib.placeOrder(contract, order)
        
        assert trade is not None
        assert trade.order.totalQuantity == 100
        assert trade.order.action == 'BUY'
        
        # Wait for fill
        time.sleep(0.2)
        
        assert trade.orderStatus.status == 'Filled'
        assert len(trade.fills) > 0
    
    @patch('copilot_quant.brokers.connection_manager.IB')
    def test_place_order_when_disconnected(self, mock_ib_class):
        """Test placing order when disconnected raises error"""
        mock_ib = MockIB()
        mock_ib_class.return_value = mock_ib
        
        IBKRBroker = get_broker_class()
        broker = IBKRBroker()
        
        contract = Stock('AAPL')
        order = MarketOrder('BUY', 100)
        
        with pytest.raises(RuntimeError):
            broker.ib.placeOrder(contract, order)
    
    @patch('copilot_quant.brokers.connection_manager.IB')
    def test_cancel_order(self, mock_ib_class):
        """Test cancelling an order"""
        mock_ib = MockIB()
        mock_ib.set_auto_fill(False)  # Don't auto-fill
        mock_ib_class.return_value = mock_ib
        
        IBKRBroker = get_broker_class()
        broker = IBKRBroker()
        broker.connect()
        
        contract = Stock('AAPL')
        order = MarketOrder('BUY', 100)
        
        trade = broker.ib.placeOrder(contract, order)
        
        assert trade.orderStatus.status != 'Cancelled'
        
        broker.ib.cancelOrder(order)
        
        assert trade.orderStatus.status == 'Cancelled'


class TestIBKRBrokerAccountInfo:
    """Test cases for account information retrieval"""
    
    @patch('copilot_quant.brokers.connection_manager.IB')
    def test_get_account_balance(self, mock_ib_class):
        """Test getting account balance"""
        mock_ib = MockIB()
        mock_ib_class.return_value = mock_ib
        
        IBKRBroker = get_broker_class()
        broker = IBKRBroker()
        broker.connect()
        
        balance = broker.get_account_balance()
        
        assert isinstance(balance, dict)
        assert 'NetLiquidation' in balance
        assert 'TotalCashValue' in balance
        assert 'BuyingPower' in balance
    
    @patch('copilot_quant.brokers.connection_manager.IB')
    def test_get_account_balance_when_disconnected(self, mock_ib_class):
        """Test getting account balance when disconnected returns empty dict"""
        mock_ib = MockIB()
        mock_ib_class.return_value = mock_ib
        
        IBKRBroker = get_broker_class()
        broker = IBKRBroker()
        
        balance = broker.get_account_balance()
        
        assert balance == {}


class TestIBKRBrokerPositions:
    """Test cases for position management"""
    
    @patch('copilot_quant.brokers.connection_manager.IB')
    def test_get_positions(self, mock_ib_class):
        """Test getting positions"""
        mock_ib = MockIB()
        mock_ib.add_position('AAPL', 100, 150.0)
        mock_ib.add_position('TSLA', 50, 200.0)
        mock_ib_class.return_value = mock_ib
        
        IBKRBroker = get_broker_class()
        broker = IBKRBroker()
        broker.connect()
        
        positions = broker.ib.positions()
        
        assert len(positions) == 2
        assert positions[0].contract.symbol == 'AAPL'
        assert positions[0].position == 100
        assert positions[1].contract.symbol == 'TSLA'
        assert positions[1].position == 50


class TestIBKRBrokerErrorHandling:
    """Test cases for error handling"""
    
    @patch('copilot_quant.brokers.connection_manager.IB')
    def test_order_error_simulation(self, mock_ib_class):
        """Test order error simulation"""
        mock_ib = MockIB()
        mock_ib.set_error_simulation(True, error_code=201)
        mock_ib_class.return_value = mock_ib
        
        IBKRBroker = get_broker_class()
        broker = IBKRBroker(enable_order_execution=True)
        broker.connect()
        
        # Track error events
        error_received = []
        
        def on_error(reqId, errorCode, errorString, contract):
            error_received.append((reqId, errorCode, errorString))
        
        broker.ib.errorEvent += on_error
        
        contract = Stock('AAPL')
        order = MarketOrder('BUY', 100)
        
        broker.ib.placeOrder(contract, order)
        
        # Give time for error event
        time.sleep(0.1)
        
        assert len(error_received) > 0
        assert error_received[0][1] == 201
    
    @patch('copilot_quant.brokers.connection_manager.IB')
    def test_disconnect_reconnect(self, mock_ib_class):
        """Test disconnect and reconnect"""
        mock_ib = MockIB()
        mock_ib_class.return_value = mock_ib
        
        IBKRBroker = get_broker_class()
        broker = IBKRBroker()
        
        # Connect
        broker.connect()
        assert broker.is_connected() is True
        
        # Disconnect
        broker.disconnect()
        assert broker.is_connected() is False
        
        # Reconnect
        broker.connect()
        assert broker.is_connected() is True


class TestIBKRBrokerIBProperty:
    """Test cases for IB property access"""
    
    @patch('copilot_quant.brokers.connection_manager.IB')
    def test_ib_property_when_connected(self, mock_ib_class):
        """Test accessing IB property when connected"""
        mock_ib = MockIB()
        mock_ib_class.return_value = mock_ib
        
        IBKRBroker = get_broker_class()
        broker = IBKRBroker()
        broker.connect()
        
        ib_instance = broker.ib
        
        assert ib_instance is not None
        assert ib_instance.isConnected() is True
    
    @patch('copilot_quant.brokers.connection_manager.IB')
    def test_ib_property_when_disconnected(self, mock_ib_class):
        """Test accessing IB property when disconnected raises error"""
        mock_ib = MockIB()
        mock_ib_class.return_value = mock_ib
        
        IBKRBroker = get_broker_class()
        broker = IBKRBroker()
        
        with pytest.raises(RuntimeError) as exc_info:
            _ = broker.ib
        
        assert "Not connected" in str(exc_info.value)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
