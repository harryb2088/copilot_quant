"""
Broker connector modules (IBKR, etc.)

This package provides broker integrations for live and paper trading.
"""

# Lazy imports to avoid circular dependencies
# Import only when explicitly needed

__all__ = [
    'IBKRBroker',
    'IBKRConnectionManager',
    'ConnectionState',
    'test_connection',
    'IBKRAccountManager',
    'AccountSummary',
    'IBKRPositionManager',
    'Position',
    'PositionChange',
    'IBKRLiveDataFeed',
    'LiveDataFeedAdapter',
    'LiveBrokerAdapter',
    'OrderExecutionHandler',
    'OrderRecord',
    'OrderStatus',
    'Fill',
    'OrderLogger',
    'TradeReconciliation',
    'ReconciliationReport',
    'Discrepancy',
    'DiscrepancyType',
    'TradeDatabase',
    'AuditTrail',
]


def __getattr__(name):
    """Lazy load attributes to avoid circular imports"""
    if name == 'IBKRBroker':
        from .interactive_brokers import IBKRBroker
        return IBKRBroker
    elif name == 'test_connection':
        from .interactive_brokers import test_connection
        return test_connection
    elif name == 'IBKRConnectionManager':
        from .connection_manager import IBKRConnectionManager
        return IBKRConnectionManager
    elif name == 'ConnectionState':
        from .connection_manager import ConnectionState
        return ConnectionState
    elif name == 'IBKRAccountManager':
        from .account_manager import IBKRAccountManager
        return IBKRAccountManager
    elif name == 'AccountSummary':
        from .account_manager import AccountSummary
        return AccountSummary
    elif name == 'IBKRPositionManager':
        from .position_manager import IBKRPositionManager
        return IBKRPositionManager
    elif name == 'Position':
        from .position_manager import Position
        return Position
    elif name == 'PositionChange':
        from .position_manager import PositionChange
        return PositionChange
    elif name == 'IBKRLiveDataFeed':
        from .live_market_data import IBKRLiveDataFeed
        return IBKRLiveDataFeed
    elif name == 'LiveDataFeedAdapter':
        from .live_data_adapter import LiveDataFeedAdapter
        return LiveDataFeedAdapter
    elif name == 'LiveBrokerAdapter':
        from .live_broker_adapter import LiveBrokerAdapter
        return LiveBrokerAdapter
    elif name == 'OrderExecutionHandler':
        from .order_execution_handler import OrderExecutionHandler
        return OrderExecutionHandler
    elif name == 'OrderRecord':
        from .order_execution_handler import OrderRecord
        return OrderRecord
    elif name == 'OrderStatus':
        from .order_execution_handler import OrderStatus
        return OrderStatus
    elif name == 'Fill':
        from .order_execution_handler import Fill
        return Fill
    elif name == 'OrderLogger':
        from .order_logger import OrderLogger
        return OrderLogger
    elif name == 'TradeReconciliation':
        from .trade_reconciliation import TradeReconciliation
        return TradeReconciliation
    elif name == 'ReconciliationReport':
        from .trade_reconciliation import ReconciliationReport
        return ReconciliationReport
    elif name == 'Discrepancy':
        from .trade_reconciliation import Discrepancy
        return Discrepancy
    elif name == 'DiscrepancyType':
        from .trade_reconciliation import DiscrepancyType
        return DiscrepancyType
    elif name == 'TradeDatabase':
        from .trade_database import TradeDatabase
        return TradeDatabase
    elif name == 'AuditTrail':
        from .audit_trail import AuditTrail
        return AuditTrail
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
