"""
IBKR Broker Service for UI Integration

This module provides a singleton service for managing IBKR broker connections
in the Streamlit UI. It handles:
- Connection lifecycle (connect, disconnect, reconnect)
- Connection state tracking
- Account data retrieval
- Position data retrieval
- Order data retrieval
- Error handling for UI display

Example Usage:
    >>> from src.ui.services.ibkr_broker_service import get_ibkr_service
    >>> 
    >>> service = get_ibkr_service()
    >>> if service.connect(paper_trading=True):
    ...     status = service.get_connection_status()
    ...     account = service.get_account_summary()
    ...     positions = service.get_positions()
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio

# Fix for eventloop issue in Streamlit with ib_insync
# Set event loop policy for Windows/asyncio compatibility
try:
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    else:
        # For Unix-like systems, create a new event loop if needed
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
except Exception as e:
    logging.debug(f"Event loop setup: {e}")

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Lazy import to avoid event loop issues at module load time
IBKRBroker = None
ConnectionState = None

def _lazy_import_ibkr():
    """Lazy import of IBKR modules to avoid event loop issues."""
    global IBKRBroker, ConnectionState
    if IBKRBroker is None:
        try:
            from copilot_quant.brokers.interactive_brokers import IBKRBroker as _IBKRBroker
            from copilot_quant.brokers.connection_manager import ConnectionState as _ConnectionState
            IBKRBroker = _IBKRBroker
            ConnectionState = _ConnectionState
        except ImportError as e:
            logging.warning(f"Could not import IBKR modules: {e}")
    return IBKRBroker, ConnectionState

logger = logging.getLogger(__name__)


class IBKRBrokerService:
    """
    Service class for managing IBKR broker connection in the UI.
    
    This class provides a simplified interface for the UI to interact with
    the IBKR broker, handling connection lifecycle and data retrieval.
    
    Attributes:
        broker: IBKRBroker instance (None when not initialized)
        last_error: Last error message (None if no error)
        connection_start_time: When connection was established (None if not connected)
    """
    
    def __init__(self):
        """Initialize the IBKR broker service."""
        self.broker: Optional['IBKRBroker'] = None
        self.last_error: Optional[str] = None
        self.connection_start_time: Optional[datetime] = None
        self._paper_trading: bool = True
        self._use_gateway: bool = False
        logger.info("IBKRBrokerService initialized")
    
    def connect(
        self,
        paper_trading: bool = True,
        use_gateway: bool = False,
        timeout: int = 30,
        retry_count: int = 3
    ) -> bool:
        """
        Connect to IBKR.
        
        Args:
            paper_trading: If True, connect to paper trading account
            use_gateway: If True, use IB Gateway ports, else use TWS ports
            timeout: Connection timeout in seconds
            retry_count: Number of connection retry attempts
            
        Returns:
            True if connection successful, False otherwise
        """
        # Lazy import IBKR modules
        _IBKRBroker, _ConnectionState = _lazy_import_ibkr()
        
        if _IBKRBroker is None:
            self.last_error = "IBKR modules not available. Install ib_insync."
            logger.error(self.last_error)
            return False
        
        try:
            # Disconnect existing connection if any
            if self.broker is not None:
                self.disconnect()
            
            # Store connection parameters
            self._paper_trading = paper_trading
            self._use_gateway = use_gateway
            
            # Create new broker instance
            logger.info(
                f"Connecting to IBKR: "
                f"mode={'Paper' if paper_trading else 'Live'}, "
                f"app={'Gateway' if use_gateway else 'TWS'}"
            )
            
            self.broker = _IBKRBroker(
                paper_trading=paper_trading,
                use_gateway=use_gateway,
                enable_account_manager=True,
                enable_position_manager=True,
                enable_order_execution=False,  # Read-only for UI
                enable_order_logging=False
            )
            
            # Attempt connection
            success = self.broker.connect(timeout=timeout, retry_count=retry_count)
            
            if success:
                self.connection_start_time = datetime.now()
                self.last_error = None
                logger.info("Successfully connected to IBKR")
                return True
            else:
                self.last_error = "Failed to connect to IBKR"
                logger.error(self.last_error)
                self.broker = None
                return False
                
        except Exception as e:
            self.last_error = f"Connection error: {str(e)}"
            logger.error(f"Error connecting to IBKR: {e}", exc_info=True)
            self.broker = None
            return False
    
    def disconnect(self) -> None:
        """Disconnect from IBKR."""
        if self.broker is not None:
            try:
                self.broker.disconnect()
                logger.info("Disconnected from IBKR")
            except Exception as e:
                logger.error(f"Error disconnecting: {e}", exc_info=True)
            finally:
                self.broker = None
                self.connection_start_time = None
    
    def reconnect(self) -> bool:
        """
        Attempt to reconnect using the same parameters.
        
        Returns:
            True if reconnection successful, False otherwise
        """
        return self.connect(
            paper_trading=self._paper_trading,
            use_gateway=self._use_gateway
        )
    
    def is_connected(self) -> bool:
        """
        Check if currently connected to IBKR.
        
        Returns:
            True if connected, False otherwise
        """
        if self.broker is None:
            return False
        
        try:
            return self.broker.is_connected()
        except Exception as e:
            logger.error(f"Error checking connection: {e}")
            return False
    
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get detailed connection status.
        
        Returns:
            Dictionary with connection status:
            - connected: Whether currently connected (bool)
            - state: Connection state string
            - paper_trading: Paper trading mode (bool)
            - use_gateway: Using IB Gateway (bool)
            - uptime_seconds: Connection uptime in seconds (float or None)
            - last_error: Last error message (str or None)
            - accounts: List of managed accounts (list or None)
        """
        status = {
            'connected': self.is_connected(),
            'state': 'disconnected',
            'paper_trading': self._paper_trading,
            'use_gateway': self._use_gateway,
            'uptime_seconds': None,
            'last_error': self.last_error,
            'accounts': None
        }
        
        if self.broker is not None and self.is_connected():
            try:
                # Get detailed status from connection manager
                conn_status = self.broker.connection_manager.get_status()
                status.update({
                    'state': conn_status.get('state', 'connected'),
                    'accounts': conn_status.get('accounts'),
                    'uptime_seconds': conn_status.get('uptime_seconds')
                })
                
                # Calculate uptime if not available
                if status['uptime_seconds'] is None and self.connection_start_time:
                    uptime = datetime.now() - self.connection_start_time
                    status['uptime_seconds'] = uptime.total_seconds()
                    
            except Exception as e:
                logger.error(f"Error getting connection status: {e}")
                status['last_error'] = str(e)
        
        return status
    
    def get_account_summary(self) -> Optional[Dict[str, Any]]:
        """
        Get account summary information.
        
        Returns:
            Dictionary with account information or None if not available:
            - account_id: Account identifier
            - net_liquidation: Total account value
            - total_cash_value: Available cash
            - buying_power: Available buying power
            - unrealized_pnl: Unrealized P&L
            - realized_pnl: Realized P&L
            - gross_position_value: Total position value
        """
        if not self.is_connected() or self.broker is None:
            return None
        
        try:
            if self.broker.account_manager is None:
                return None
            
            summary = self.broker.account_manager.get_account_summary()
            
            if summary is None:
                return None
            
            return {
                'account_id': summary.account_id,
                'net_liquidation': summary.net_liquidation,
                'total_cash_value': summary.total_cash_value,
                'buying_power': summary.buying_power,
                'unrealized_pnl': summary.unrealized_pnl,
                'realized_pnl': summary.realized_pnl,
                'gross_position_value': summary.gross_position_value,
                'timestamp': summary.timestamp
            }
            
        except Exception as e:
            logger.error(f"Error getting account summary: {e}", exc_info=True)
            self.last_error = f"Error getting account data: {str(e)}"
            return None
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get current positions.
        
        Returns:
            List of position dictionaries:
            - symbol: Stock symbol
            - quantity: Number of shares
            - avg_cost: Average cost per share
            - market_price: Current market price
            - market_value: Current market value
            - unrealized_pnl: Unrealized P&L
            - pnl_percentage: P&L percentage
        """
        if not self.is_connected() or self.broker is None:
            return []
        
        try:
            if self.broker.position_manager is None:
                return []
            
            positions = self.broker.position_manager.get_positions()
            
            return [
                {
                    'symbol': pos.symbol,
                    'quantity': pos.quantity,
                    'avg_cost': pos.avg_cost,
                    'market_price': pos.market_price,
                    'market_value': pos.market_value,
                    'unrealized_pnl': pos.unrealized_pnl,
                    'pnl_percentage': pos.pnl_percentage,
                    'account_id': pos.account_id
                }
                for pos in positions
            ]
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}", exc_info=True)
            self.last_error = f"Error getting positions: {str(e)}"
            return []
    
    def get_recent_orders(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent orders.
        
        Args:
            limit: Maximum number of orders to return
            
        Returns:
            List of order dictionaries (empty for now, can be extended)
        """
        if not self.is_connected() or self.broker is None:
            return []
        
        try:
            # Get open orders from broker
            ib = self.broker.ib
            trades = ib.trades()
            
            orders = []
            for trade in trades[:limit]:
                orders.append({
                    'order_id': trade.order.orderId,
                    'symbol': trade.contract.symbol,
                    'action': trade.order.action,
                    'quantity': trade.order.totalQuantity,
                    'order_type': trade.order.orderType,
                    'status': trade.orderStatus.status,
                    'filled': trade.orderStatus.filled,
                    'remaining': trade.orderStatus.remaining,
                    'avg_fill_price': trade.orderStatus.avgFillPrice
                })
            
            return orders
            
        except Exception as e:
            logger.error(f"Error getting orders: {e}", exc_info=True)
            self.last_error = f"Error getting orders: {str(e)}"
            return []


# Singleton instance
_ibkr_service: Optional[IBKRBrokerService] = None


def get_ibkr_service() -> IBKRBrokerService:
    """
    Get the singleton IBKR broker service instance.
    
    Returns:
        IBKRBrokerService instance
    """
    global _ibkr_service
    if _ibkr_service is None:
        _ibkr_service = IBKRBrokerService()
    return _ibkr_service


def reset_ibkr_service() -> None:
    """
    Reset the singleton IBKR broker service.
    Useful for testing or forced reconnection.
    """
    global _ibkr_service
    if _ibkr_service is not None:
        _ibkr_service.disconnect()
        _ibkr_service = None
