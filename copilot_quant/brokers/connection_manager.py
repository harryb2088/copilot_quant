"""
Interactive Brokers Connection Manager

This module provides centralized connection management for Interactive Brokers
using ib_insync. It handles:
- Connection initialization on demand (TWS and IB Gateway)
- Secure configuration via environment variables
- Automatic reconnection on disconnect
- Health monitoring and connection state tracking
- Comprehensive error handling and logging

The connection manager is designed to be shared across multiple IBKR components
to avoid duplicate connection logic.

Example Usage:
    >>> from copilot_quant.brokers.connection_manager import IBKRConnectionManager
    >>> 
    >>> # Create connection manager
    >>> manager = IBKRConnectionManager(paper_trading=True)
    >>> 
    >>> # Connect to IBKR
    >>> if manager.connect():
    ...     print(f"Connected! Status: {manager.get_status()}")
    ...     ib_instance = manager.get_ib()
    ...     # Use ib_instance for trading operations
    ...     manager.disconnect()

Environment Variables:
    IB_HOST: Interactive Brokers host (default: 127.0.0.1)
    IB_PORT: IB API port (overrides auto-detection)
    IB_CLIENT_ID: Unique client identifier (default: 1)

Port Configuration:
    - Paper Trading (TWS): 7497
    - Live Trading (TWS): 7496
    - Paper Trading (IB Gateway): 4002
    - Live Trading (IB Gateway): 4001
"""

import logging
import os
import time
from typing import Optional, Callable, List, Dict, Any
from datetime import datetime
from enum import Enum

try:
    from ib_insync import IB
except ImportError as e:
    raise ImportError(
        "ib_insync is required for IBKR integration. "
        "Install it with: pip install ib_insync>=0.9.86"
    ) from e

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """Connection state enumeration"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


class IBKRConnectionManager:
    """
    Centralized connection manager for Interactive Brokers.
    
    This class manages the lifecycle of IBKR connections, including:
    - Initial connection establishment
    - Connection health monitoring
    - Automatic reconnection on disconnect
    - Connection state tracking for UI
    - Error handling and logging
    
    The manager can be shared across multiple components (trading, data feed, etc.)
    that need IBKR connectivity.
    
    Attributes:
        state: Current connection state (ConnectionState enum)
        host: IBKR API host address
        port: IBKR API port number
        client_id: Unique client identifier
        paper_trading: Whether connected to paper trading account
        use_gateway: Whether using IB Gateway (vs TWS)
    
    Example:
        >>> manager = IBKRConnectionManager(paper_trading=True)
        >>> manager.connect()
        >>> ib = manager.get_ib()
        >>> # Use ib for operations
        >>> manager.disconnect()
    """
    
    def __init__(
        self,
        paper_trading: bool = True,
        host: Optional[str] = None,
        port: Optional[int] = None,
        client_id: Optional[int] = None,
        use_gateway: bool = False,
        auto_reconnect: bool = True
    ):
        """
        Initialize IBKR connection manager.
        
        Args:
            paper_trading: If True, connect to paper trading account (default: True)
            host: IB API host address (default: from IB_HOST env or '127.0.0.1')
            port: IB API port (default: auto-detected based on mode)
            client_id: Unique client identifier (default: from IB_CLIENT_ID env or 1)
            use_gateway: If True, use IB Gateway ports, else use TWS ports
            auto_reconnect: If True, automatically reconnect on disconnect
            
        Environment Variables:
            IB_HOST: Interactive Brokers host (default: 127.0.0.1)
            IB_PORT: IB API port (overrides auto-detection)
            IB_CLIENT_ID: Unique client identifier (default: 1)
        """
        self.ib = IB()
        self.paper_trading = paper_trading
        self.use_gateway = use_gateway
        self.auto_reconnect = auto_reconnect
        self.state = ConnectionState.DISCONNECTED
        
        # Get configuration from environment variables or use defaults
        self.host = host or os.getenv('IB_HOST', '127.0.0.1')
        self.client_id = client_id or int(os.getenv('IB_CLIENT_ID', '1'))
        
        # Determine port: explicit param > env var > auto-detect
        if port is not None:
            self.port = port
        elif os.getenv('IB_PORT'):
            self.port = int(os.getenv('IB_PORT'))
        else:
            # Auto-detect port based on trading mode and application
            if use_gateway:
                self.port = 4002 if paper_trading else 4001
            else:
                self.port = 7497 if paper_trading else 7496
        
        # Connection state tracking
        self._connected_at: Optional[datetime] = None
        self._last_disconnect_at: Optional[datetime] = None
        self._reconnect_count = 0
        self._disconnect_handlers: List[Callable] = []
        self._connect_handlers: List[Callable] = []
        
        # Setup event handlers
        self.ib.errorEvent += self._on_error
        self.ib.disconnectedEvent += self._on_disconnect
        self.ib.connectedEvent += self._on_connect
        
        logger.info(
            f"Initialized IBKRConnectionManager: "
            f"mode={'Paper' if paper_trading else 'Live'}, "
            f"app={'Gateway' if use_gateway else 'TWS'}, "
            f"host={self.host}, "
            f"port={self.port}, "
            f"client_id={self.client_id}, "
            f"auto_reconnect={auto_reconnect}"
        )
    
    def connect(self, timeout: int = 30, retry_count: int = 3) -> bool:
        """
        Establish connection to IBKR.
        
        Args:
            timeout: Connection timeout in seconds
            retry_count: Number of connection retry attempts
            
        Returns:
            True if connection successful, False otherwise
            
        Raises:
            ConnectionError: If connection fails after all retries
        """
        self.state = ConnectionState.CONNECTING
        
        for attempt in range(retry_count):
            try:
                logger.info(
                    f"Connecting to IBKR at {self.host}:{self.port} "
                    f"(attempt {attempt + 1}/{retry_count})"
                )
                
                self.ib.connect(
                    self.host,
                    self.port,
                    clientId=self.client_id,
                    timeout=timeout
                )
                
                if self.ib.isConnected():
                    self.state = ConnectionState.CONNECTED
                    self._connected_at = datetime.now()
                    mode = "Paper" if self.paper_trading else "Live"
                    accounts = self.ib.managedAccounts()
                    
                    logger.info(f"✓ Connected to IBKR ({mode} Trading)")
                    logger.info(f"Accounts: {accounts}")
                    
                    return True
                else:
                    logger.warning("Connection established but not confirmed")
                    
            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < retry_count - 1:
                    wait_time = 5 * (attempt + 1)  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
        
        self.state = ConnectionState.FAILED
        error_msg = f"Failed to connect to IBKR at {self.host}:{self.port} after {retry_count} attempts"
        logger.error(error_msg)
        raise ConnectionError(error_msg)
    
    def disconnect(self):
        """Disconnect from IBKR"""
        if self.is_connected():
            try:
                self.ib.disconnect()
                self.state = ConnectionState.DISCONNECTED
                self._last_disconnect_at = datetime.now()
                logger.info("Disconnected from IBKR")
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")
    
    def reconnect(self, timeout: int = 30) -> bool:
        """
        Attempt to reconnect to IBKR.
        
        Args:
            timeout: Connection timeout in seconds
            
        Returns:
            True if reconnection successful, False otherwise
        """
        logger.info("Attempting to reconnect to IBKR...")
        self.state = ConnectionState.RECONNECTING
        self._reconnect_count += 1
        
        # Disconnect if still connected
        if self.ib.isConnected():
            try:
                self.ib.disconnect()
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
        
        # Wait a bit before reconnecting
        time.sleep(2)
        
        # Try to reconnect
        try:
            success = self.connect(timeout=timeout, retry_count=3)
            if success:
                logger.info(f"✓ Reconnection successful (attempt #{self._reconnect_count})")
            return success
        except ConnectionError:
            logger.error(f"Reconnection failed (attempt #{self._reconnect_count})")
            return False
    
    def is_connected(self) -> bool:
        """
        Check if currently connected to IBKR.
        
        Returns:
            True if connected, False otherwise
        """
        return self.state == ConnectionState.CONNECTED and self.ib.isConnected()
    
    def get_ib(self) -> IB:
        """
        Get the underlying IB instance.
        
        Returns:
            The ib_insync IB instance
            
        Raises:
            RuntimeError: If not connected
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to IBKR. Call connect() first.")
        return self.ib
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get detailed connection status information.
        
        Returns:
            Dictionary with connection status details:
            - state: Current connection state (str)
            - connected: Whether currently connected (bool)
            - host: Connection host (str)
            - port: Connection port (int)
            - client_id: Client ID (int)
            - paper_trading: Paper trading mode (bool)
            - connected_at: When connection was established (datetime or None)
            - uptime_seconds: Connection uptime in seconds (float or None)
            - reconnect_count: Number of reconnections (int)
            - last_disconnect_at: When last disconnected (datetime or None)
            - accounts: List of managed accounts (list or None)
        """
        status = {
            'state': self.state.value,
            'connected': self.is_connected(),
            'host': self.host,
            'port': self.port,
            'client_id': self.client_id,
            'paper_trading': self.paper_trading,
            'connected_at': self._connected_at,
            'uptime_seconds': None,
            'reconnect_count': self._reconnect_count,
            'last_disconnect_at': self._last_disconnect_at,
            'accounts': None
        }
        
        if self.is_connected():
            if self._connected_at:
                status['uptime_seconds'] = (datetime.now() - self._connected_at).total_seconds()
            try:
                status['accounts'] = self.ib.managedAccounts()
            except Exception as e:
                logger.warning(f"Could not retrieve accounts: {e}")
        
        return status
    
    def add_disconnect_handler(self, handler: Callable):
        """
        Register a callback to be called on disconnect.
        
        Args:
            handler: Callback function to call on disconnect
        """
        self._disconnect_handlers.append(handler)
    
    def add_connect_handler(self, handler: Callable):
        """
        Register a callback to be called on connect.
        
        Args:
            handler: Callback function to call on connect
        """
        self._connect_handlers.append(handler)
    
    def _on_connect(self):
        """Handle connection event"""
        logger.info("Connected to IBKR")
        self.state = ConnectionState.CONNECTED
        self._connected_at = datetime.now()
        
        # Call registered handlers
        for handler in self._connect_handlers:
            try:
                handler()
            except Exception as e:
                logger.error(f"Error in connect handler: {e}")
    
    def _on_disconnect(self):
        """Handle disconnection event"""
        logger.warning("Disconnected from IBKR")
        self.state = ConnectionState.DISCONNECTED
        self._last_disconnect_at = datetime.now()
        
        # Call registered handlers
        for handler in self._disconnect_handlers:
            try:
                handler()
            except Exception as e:
                logger.error(f"Error in disconnect handler: {e}")
        
        # Attempt auto-reconnect if enabled
        if self.auto_reconnect:
            logger.info("Auto-reconnect is enabled, attempting to reconnect...")
            try:
                self.reconnect()
            except Exception as e:
                logger.error(f"Auto-reconnect failed: {e}")
    
    def _on_error(self, reqId: int, errorCode: int, errorString: str, contract):
        """
        Handle error events from IBKR.
        
        Common error codes and meanings:
        - 200: No security definition found (invalid symbol)
        - 502: Couldn't connect to TWS
        - 504: Not connected
        - 1100: Connectivity between IB and TWS has been lost
        - 1101: Connectivity restored
        - 1102: Connectivity restored (data lost)
        - 2104: Market data farm connection is OK
        - 2106: HMDS data farm connection is OK
        - 2158: Sec-def data farm connection is OK
        - 10167: Delayed market data
        
        Args:
            reqId: Request ID
            errorCode: Error code
            errorString: Error message
            contract: Related contract
        """
        # Filter out informational messages
        if errorCode in [2104, 2106, 2158]:  # Market data farm connection messages
            logger.debug(f"Info [{errorCode}]: {errorString}")
        elif errorCode in [1100, 1102]:  # Connection lost/restored
            logger.warning(f"Connection status [{errorCode}]: {errorString}")
            if errorCode == 1100:  # Connection lost
                self.state = ConnectionState.DISCONNECTED
        elif errorCode == 1101:  # Connection restored
            logger.info(f"Connection restored [{errorCode}]: {errorString}")
            self.state = ConnectionState.CONNECTED
        elif errorCode == 200:  # No security definition found
            logger.warning(f"Contract not found [{errorCode}]: {errorString}")
        elif errorCode in [10197, 10167]:  # Delayed market data warnings
            logger.info(f"Market data info [{errorCode}]: {errorString}")
        elif errorCode in [502, 504]:  # Connection errors
            logger.error(f"Connection error [{errorCode}]: {errorString}")
            self.state = ConnectionState.FAILED
        elif errorCode >= 1000:  # System messages
            logger.debug(f"System [{errorCode}]: {errorString}")
        else:
            logger.error(f"Error [{errorCode}]: {errorString}")
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
        return False
    
    def __repr__(self):
        """String representation"""
        return (
            f"IBKRConnectionManager("
            f"state={self.state.value}, "
            f"host={self.host}, "
            f"port={self.port}, "
            f"paper_trading={self.paper_trading})"
        )


# Common error patterns and reconnection tips
ERROR_PATTERNS = {
    502: {
        'description': 'Couldn\'t connect to TWS',
        'tips': [
            'Ensure TWS or IB Gateway is running',
            'Check that API connections are enabled in TWS settings',
            'Verify the port number matches your TWS configuration',
            'Check if another client is already connected with the same client_id'
        ]
    },
    504: {
        'description': 'Not connected',
        'tips': [
            'Ensure you have called connect() before making API calls',
            'Check if connection was lost and reconnect() is needed',
            'Verify network connectivity to the host'
        ]
    },
    1100: {
        'description': 'Connectivity between IB and TWS has been lost',
        'tips': [
            'This is usually temporary, wait for automatic reconnection',
            'If it persists, restart TWS/Gateway',
            'Check your internet connection'
        ]
    },
    1101: {
        'description': 'Connectivity between IB and TWS has been restored',
        'tips': [
            'Connection is restored, data feed should resume',
            'You may need to re-request market data subscriptions'
        ]
    },
    1102: {
        'description': 'Connectivity restored but data lost',
        'tips': [
            'Connection is restored but some data may have been lost',
            'Re-request any important data or subscriptions',
            'Consider implementing a re-subscription mechanism'
        ]
    },
    200: {
        'description': 'No security definition found',
        'tips': [
            'Check that the symbol is valid and traded',
            'Verify the contract details (exchange, currency, etc.)',
            'Try qualifying the contract with more specific details'
        ]
    },
    10167: {
        'description': 'Delayed market data',
        'tips': [
            'You are receiving delayed market data (not real-time)',
            'Subscribe to real-time data in TWS if needed',
            'This is normal for non-professional accounts'
        ]
    }
}


def get_error_tips(error_code: int) -> Dict[str, Any]:
    """
    Get troubleshooting tips for a specific error code.
    
    Args:
        error_code: IBKR error code
        
    Returns:
        Dictionary with 'description' and 'tips' keys, or empty dict if not found
    """
    return ERROR_PATTERNS.get(error_code, {})
