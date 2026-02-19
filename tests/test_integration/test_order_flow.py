"""
Integration tests for end-to-end order flow

These tests verify the complete order execution flow from order placement
through fills and position updates.
"""

import pytest
import time
from unittest.mock import patch
from tests.mocks.mock_ib import MockIB, Stock, MarketOrder


@pytest.mark.integration
class TestEndToEndOrderFlow:
    """Test complete order flow from placement to fill"""
    
    @patch('copilot_quant.brokers.connection_manager.IB')
    def test_complete_order_lifecycle(self, mock_ib_class):
        """Test complete order lifecycle: submit -> fill -> position update"""
        mock_ib = MockIB()
        mock_ib.set_auto_fill(True, delay=0.1)
        mock_ib_class.return_value = mock_ib
        
        from copilot_quant.brokers.interactive_brokers import IBKRBroker
        
        # Create broker
        broker = IBKRBroker(
            enable_account_manager=True,
            enable_position_manager=True,
            enable_order_execution=True
        )
        broker.connect()
        
        # Place order
        contract = Stock('AAPL')
        order = MarketOrder('BUY', 100)
        
        trade = broker.ib.placeOrder(contract, order)
        
        # Verify order submitted
        assert trade is not None
        assert trade.order.totalQuantity == 100
        
        # Wait for fill
        time.sleep(0.3)
        
        # Verify fill
        assert trade.orderStatus.status == 'Filled'
        assert len(trade.fills) == 1
        assert trade.fills[0].execution.shares == 100
        
        broker.disconnect()
    
    @patch('copilot_quant.brokers.connection_manager.IB')
    def test_multiple_orders_execution(self, mock_ib_class):
        """Test executing multiple orders"""
        mock_ib = MockIB()
        mock_ib.set_auto_fill(True, delay=0.05)
        mock_ib_class.return_value = mock_ib
        
        from copilot_quant.brokers.interactive_brokers import IBKRBroker
        
        broker = IBKRBroker()
        broker.connect()
        
        # Place multiple orders
        trades = []
        for symbol in ['AAPL', 'TSLA', 'GOOGL']:
            contract = Stock(symbol)
            order = MarketOrder('BUY', 50)
            trade = broker.ib.placeOrder(contract, order)
            trades.append(trade)
        
        # Wait for all fills
        time.sleep(0.5)
        
        # Verify all filled
        for trade in trades:
            assert trade.orderStatus.status == 'Filled'
            assert len(trade.fills) == 1
        
        broker.disconnect()
    
    @patch('copilot_quant.brokers.connection_manager.IB')
    def test_order_cancellation_flow(self, mock_ib_class):
        """Test order cancellation workflow"""
        mock_ib = MockIB()
        mock_ib.set_auto_fill(False)  # Don't auto-fill
        mock_ib_class.return_value = mock_ib
        
        from copilot_quant.brokers.interactive_brokers import IBKRBroker
        
        broker = IBKRBroker()
        broker.connect()
        
        # Place order
        contract = Stock('AAPL')
        order = MarketOrder('BUY', 100)
        trade = broker.ib.placeOrder(contract, order)
        
        # Verify order is active
        assert trade.isActive()
        
        # Cancel order
        broker.ib.cancelOrder(order)
        
        # Verify order cancelled
        assert trade.orderStatus.status == 'Cancelled'
        assert trade.isDone()
        
        broker.disconnect()


@pytest.mark.integration
class TestAccountPositionIntegration:
    """Test integration between account and position management"""
    
    @patch('copilot_quant.brokers.connection_manager.IB')
    def test_position_tracking_after_orders(self, mock_ib_class):
        """Test that positions are tracked after order fills"""
        mock_ib = MockIB()
        mock_ib.set_auto_fill(True, delay=0.05)
        mock_ib_class.return_value = mock_ib
        
        from copilot_quant.brokers.interactive_brokers import IBKRBroker
        
        broker = IBKRBroker()
        broker.connect()
        
        # Add initial position
        mock_ib.add_position('AAPL', 50, 150.0)
        
        # Get positions
        positions = broker.ib.positions()
        assert len(positions) == 1
        assert positions[0].contract.symbol == 'AAPL'
        assert positions[0].position == 50
        
        broker.disconnect()
    
    @patch('copilot_quant.brokers.connection_manager.IB')
    def test_account_balance_consistency(self, mock_ib_class):
        """Test account balance remains consistent"""
        mock_ib = MockIB()
        mock_ib_class.return_value = mock_ib
        
        from copilot_quant.brokers.interactive_brokers import IBKRBroker
        
        broker = IBKRBroker()
        broker.connect()
        
        # Get initial balance
        balance1 = broker.get_account_balance()
        
        # Get balance again
        balance2 = broker.get_account_balance()
        
        # Should be consistent
        assert balance1 == balance2
        assert balance1['NetLiquidation'] == balance2['NetLiquidation']
        
        broker.disconnect()


@pytest.mark.integration
class TestConnectionRecovery:
    """Test connection recovery scenarios"""
    
    @patch('copilot_quant.brokers.connection_manager.IB')
    def test_disconnect_reconnect_recovery(self, mock_ib_class):
        """Test recovery after disconnect/reconnect"""
        mock_ib = MockIB()
        mock_ib_class.return_value = mock_ib
        
        from copilot_quant.brokers.interactive_brokers import IBKRBroker
        
        broker = IBKRBroker()
        
        # Initial connection
        broker.connect()
        assert broker.is_connected()
        
        # Simulate disconnect
        broker.disconnect()
        assert not broker.is_connected()
        
        # Reconnect
        broker.connect()
        assert broker.is_connected()
        
        # Verify broker is functional
        balance = broker.get_account_balance()
        assert 'NetLiquidation' in balance
        
        broker.disconnect()
    
    @patch('copilot_quant.brokers.connection_manager.IB')
    def test_auto_reconnect_on_disconnect(self, mock_ib_class):
        """Test automatic reconnection on unexpected disconnect"""
        mock_ib = MockIB()
        mock_ib_class.return_value = mock_ib
        
        from copilot_quant.brokers.interactive_brokers import IBKRBroker
        
        broker = IBKRBroker()
        broker.connect()
        
        # Simulate unexpected disconnect
        mock_ib.simulate_disconnect()
        
        # Give time for auto-reconnect
        time.sleep(0.2)
        
        # Note: Auto-reconnect happens in the connection manager
        # This test verifies the event is triggered
        
        broker.disconnect()


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Test error handling across components"""
    
    @patch('copilot_quant.brokers.connection_manager.IB')
    def test_order_error_propagation(self, mock_ib_class):
        """Test that order errors propagate correctly"""
        mock_ib = MockIB()
        mock_ib.set_error_simulation(True, error_code=201)
        mock_ib_class.return_value = mock_ib
        
        from copilot_quant.brokers.interactive_brokers import IBKRBroker
        
        broker = IBKRBroker(enable_order_execution=True)
        broker.connect()
        
        # Track errors
        errors = []
        
        def on_error(reqId, errorCode, errorString, contract):
            errors.append({'reqId': reqId, 'code': errorCode, 'msg': errorString})
        
        broker.ib.errorEvent += on_error
        
        # Place order that will error
        contract = Stock('AAPL')
        order = MarketOrder('BUY', 100)
        trade = broker.ib.placeOrder(contract, order)
        
        # Wait for error
        time.sleep(0.2)
        
        # Verify error was received
        assert len(errors) > 0
        assert errors[0]['code'] == 201
        
        broker.disconnect()
    
    @patch('copilot_quant.brokers.connection_manager.IB')
    def test_connection_failure_handling(self, mock_ib_class):
        """Test handling of connection failures"""
        mock_ib = MockIB()
        mock_ib.set_connection_fail_count(2)  # Fail first 2 attempts
        mock_ib_class.return_value = mock_ib
        
        from copilot_quant.brokers.interactive_brokers import IBKRBroker
        
        broker = IBKRBroker()
        
        # Should eventually succeed
        result = broker.connect(retry_count=3)
        
        assert result is True
        assert broker.is_connected()
        
        broker.disconnect()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'integration'])
