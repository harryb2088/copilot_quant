"""
Test fixtures for IBKR broker modules

This module provides pytest fixtures for testing IBKR broker functionality.
"""

from unittest.mock import patch

import pytest

from tests.mocks.mock_ib import LimitOrder, MarketOrder, MockContract, MockIB, MockPosition, Stock


@pytest.fixture
def mock_ib():
    """Provide a mock IB instance"""
    return MockIB()


@pytest.fixture
def mock_ib_connected():
    """Provide a connected mock IB instance"""
    ib = MockIB()
    ib.connect()
    return ib


@pytest.fixture
def mock_broker():
    """Provide a mock IBKR broker with mocked IB connection"""
    with patch("copilot_quant.brokers.connection_manager.IB") as mock_ib_class:
        mock_ib = MockIB()
        mock_ib.connect()
        mock_ib_class.return_value = mock_ib

        from copilot_quant.brokers.interactive_brokers import IBKRBroker

        broker = IBKRBroker(paper_trading=True)
        broker.connect()

        yield broker

        if broker.is_connected():
            broker.disconnect()


@pytest.fixture
def mock_connection_manager():
    """Provide a mock connection manager"""
    with patch("copilot_quant.brokers.connection_manager.IB") as mock_ib_class:
        mock_ib = MockIB()
        mock_ib_class.return_value = mock_ib

        from copilot_quant.brokers.connection_manager import IBKRConnectionManager

        manager = IBKRConnectionManager(paper_trading=True)

        yield manager


@pytest.fixture
def sample_positions():
    """Provide sample position data"""
    return [
        MockPosition("DU123456", MockContract("AAPL"), 100, 150.0),
        MockPosition("DU123456", MockContract("TSLA"), 50, 200.0),
        MockPosition("DU123456", MockContract("GOOGL"), 25, 2800.0),
    ]


@pytest.fixture
def sample_orders():
    """Provide sample order data"""
    return [
        MarketOrder(action="BUY", totalQuantity=100),
        MarketOrder(action="SELL", totalQuantity=50),
        LimitOrder(action="BUY", totalQuantity=25, lmtPrice=150.0),
    ]


@pytest.fixture
def sample_contracts():
    """Provide sample contract data"""
    return [
        Stock("AAPL"),
        Stock("TSLA"),
        Stock("GOOGL"),
        Stock("MSFT"),
        Stock("AMZN"),
    ]


@pytest.fixture
def mock_account_data():
    """Provide sample account data"""
    return {
        "NetLiquidation": 100000.00,
        "TotalCashValue": 95000.00,
        "BuyingPower": 400000.00,
        "GrossPositionValue": 5000.00,
    }


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset any singleton instances between tests"""
    yield
    # Clean up any singleton state if needed
