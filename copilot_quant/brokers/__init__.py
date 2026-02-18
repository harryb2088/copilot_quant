"""
Broker connector modules (IBKR, etc.)

This package provides broker integrations for live and paper trading.
"""

from .interactive_brokers import IBKRBroker, test_connection
from .connection_manager import IBKRConnectionManager, ConnectionState
from .account_manager import IBKRAccountManager, AccountSummary
from .position_manager import IBKRPositionManager, Position, PositionChange
from .live_market_data import IBKRLiveDataFeed
from .live_data_adapter import LiveDataFeedAdapter
from .live_broker_adapter import LiveBrokerAdapter
from .order_execution_handler import OrderExecutionHandler, OrderRecord, OrderStatus, Fill
from .order_logger import OrderLogger
from .trade_reconciliation import TradeReconciliation, ReconciliationReport, Discrepancy, DiscrepancyType
from .trade_database import TradeDatabase
from .audit_trail import AuditTrail

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
