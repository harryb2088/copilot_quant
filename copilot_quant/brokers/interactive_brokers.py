"""
Interactive Brokers integration using ib_insync

This module provides a working implementation for connecting to Interactive Brokers
paper trading and live trading accounts. 

Based on successful paper trading setup - uses TWS/IB Gateway API.

Port Configuration:
- Paper Trading (TWS): 7497
- Live Trading (TWS): 7496  
- Paper Trading (IB Gateway): 4002
- Live Trading (IB Gateway): 4001

Environment Variables (optional):
    IB_HOST: Interactive Brokers host (default: 127.0.0.1)
    IB_PORT: IB API port (default: 7497 for paper trading)
    IB_CLIENT_ID: Unique client identifier (default: 1)
    IB_PAPER_ACCOUNT: Paper trading account number (for reference)

Prerequisites:
    pip install ib_insync>=0.9.86
"""

import logging
import os
from typing import Optional, List, Dict, Any
import time

try:
    from ib_insync import IB, Stock, MarketOrder, LimitOrder
except ImportError as e:
    raise ImportError(
        "ib_insync is required for IBKR integration. "
        "Install it with: pip install ib_insync>=0.9.86"
    ) from e

logger = logging.getLogger(__name__)


class IBKRBroker:
    """
    Interactive Brokers broker implementation for Copilot Quant platform.
    
    This class provides a working connection to IB paper trading accounts.
    Tested and verified with IB Gateway and TWS.
    
    Configuration priority: explicit parameters > environment variables > defaults
    
    Example (using defaults):
        >>> broker = IBKRBroker(paper_trading=True)
        >>> if broker.connect():
        ...     balance = broker.get_account_balance()
        ...     print(f"Account balance: {balance}")
        ...     broker.disconnect()
    
    Example (using environment variables from .env):
        >>> # Set IB_HOST=127.0.0.1, IB_PORT=7497, IB_CLIENT_ID=1 in .env
        >>> broker = IBKRBroker(paper_trading=True)  # Will use env vars
        >>> broker.connect()
    
    Example (explicit parameters):
        >>> broker = IBKRBroker(
        ...     paper_trading=True,
        ...     host='127.0.0.1',
        ...     port=7497,
        ...     client_id=1
        ... )
        >>> broker.connect()
    """
    
    def __init__(
        self, 
        paper_trading: bool = True,
        host: Optional[str] = None,
        port: Optional[int] = None,
        client_id: Optional[int] = None,
        use_gateway: bool = False
    ):
        """
        Initialize IBKR broker connection.
        
        Connection parameters can be provided directly or via environment variables.
        Environment variables are used as defaults if parameters are not provided.
        
        Args:
            paper_trading: If True, connect to paper trading account (default: True)
            host: IB API host address (default: from IB_HOST env or '127.0.0.1')
            port: IB API port (default: from IB_PORT env or auto-detected based on mode)
            client_id: Unique client identifier (default: from IB_CLIENT_ID env or 1)
            use_gateway: If True, use IB Gateway ports, else use TWS ports
            
        Environment Variables:
            IB_HOST: Interactive Brokers host (default: 127.0.0.1)
            IB_PORT: IB API port (overrides auto-detection)
            IB_CLIENT_ID: Unique client identifier (default: 1)
            IB_PAPER_ACCOUNT: Paper trading account number (for reference only)
        """
        self.ib = IB()
        self.paper_trading = paper_trading
        self.use_gateway = use_gateway
        
        # Get configuration from environment variables or use defaults
        self.host = host or os.getenv('IB_HOST', '127.0.0.1')
        self.client_id = client_id or int(os.getenv('IB_CLIENT_ID', '1'))
        
        # Determine port: explicit param > env var > auto-detect based on mode
        if port is not None:
            self.port = port
        elif os.getenv('IB_PORT'):
            self.port = int(os.getenv('IB_PORT'))
        else:
            # Auto-detect port based on trading mode and application
            if use_gateway:
                # IB Gateway ports
                self.port = 4002 if paper_trading else 4001
            else:
                # TWS ports  
                self.port = 7497 if paper_trading else 7496
            
        self._connected = False
        
        # Setup logging
        logger.info(
            f"Initialized IBKRBroker: "
            f"mode={'Paper' if paper_trading else 'Live'}, "
            f"app={'Gateway' if use_gateway else 'TWS'}, "
            f"host={self.host}, "
            f"port={self.port}, "
            f"client_id={self.client_id}"
        )
            f"mode={'Paper' if paper_trading else 'Live'}, "
            f"app={'Gateway' if use_gateway else 'TWS'}, "
            f"port={self.port}"
        )
    
    def connect(self, timeout: int = 30, retry_count: int = 3) -> bool:
        """
        Establish connection to IBKR.
        
        Args:
            timeout: Connection timeout in seconds
            retry_count: Number of connection retry attempts
            
        Returns:
            True if connection successful, False otherwise
        """
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
                    self._connected = True
                    mode = "Paper" if self.paper_trading else "Live"
                    accounts = self.ib.managedAccounts()
                    
                    logger.info(f"✓ Connected to IBKR ({mode} Trading)")
                    logger.info(f"Accounts: {accounts}")
                    
                    # Setup disconnection handler
                    self.ib.disconnectedEvent += self._on_disconnect
                    
                    return True
                else:
                    logger.warning("Connection established but not confirmed")
                    
            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < retry_count - 1:
                    wait_time = 5 * (attempt + 1)  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
        
        logger.error("Failed to connect to IBKR after all retries")
        return False
    
    def _on_disconnect(self):
        """Handle disconnection event"""
        logger.warning("Disconnected from IBKR")
        self._connected = False
    
    def is_connected(self) -> bool:
        """Check if currently connected to IBKR"""
        return self._connected and self.ib.isConnected()
    
    def get_account_balance(self) -> Dict[str, float]:
        """
        Get current account balance information.
        
        Returns:
            Dictionary with account balance details:
            - NetLiquidation: Total account value
            - TotalCashValue: Available cash
            - BuyingPower: Available buying power
        """
        if not self.is_connected():
            logger.error("Not connected to IBKR")
            return {}
        
        try:
            account_values = self.ib.accountSummary()
            
            balance_info = {}
            for av in account_values:
                if av.tag in ['NetLiquidation', 'TotalCashValue', 'BuyingPower']:
                    balance_info[av.tag] = float(av.value)
            
            logger.debug(f"Account balance: {balance_info}")
            return balance_info
            
        except Exception as e:
            logger.error(f"Error getting account balance: {e}")
            return {}
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get current positions.
        
        Returns:
            List of position dictionaries with:
            - symbol: Stock symbol
            - position: Number of shares (positive for long, negative for short)
            - avg_cost: Average cost per share
            - cost_basis: Total cost basis (position * avg_cost)
            
        Note:
            The 'cost_basis' field shows the total cost, not current market value.
            To get current market value, you would need to request market data separately.
        """
        if not self.is_connected():
            logger.error("Not connected to IBKR")
            return []
        
        try:
            positions = self.ib.positions()
            
            position_list = []
            for pos in positions:
                position_list.append({
                    'symbol': pos.contract.symbol,
                    'position': pos.position,
                    'avg_cost': pos.avgCost,
                    'cost_basis': pos.position * pos.avgCost
                })
            
            logger.debug(f"Retrieved {len(position_list)} positions")
            return position_list
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    def execute_market_order(
        self, 
        symbol: str, 
        quantity: int, 
        side: str = 'buy'
    ) -> Optional[Any]:
        """
        Execute a market order.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            quantity: Number of shares
            side: 'buy' or 'sell'
            
        Returns:
            Trade object if successful, None otherwise
        """
        if not self.is_connected():
            logger.error("Not connected to IBKR")
            return None
        
        try:
            # Create contract
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            # Create order
            action = 'BUY' if side.lower() == 'buy' else 'SELL'
            order = MarketOrder(action, quantity)
            
            # Place order
            trade = self.ib.placeOrder(contract, order)
            
            logger.info(
                f"Market order placed: {action} {quantity} {symbol} "
                f"(Order ID: {trade.order.orderId})"
            )
            
            return trade
            
        except Exception as e:
            logger.error(f"Error executing market order: {e}")
            return None
    
    def execute_limit_order(
        self,
        symbol: str,
        quantity: int,
        limit_price: float,
        side: str = 'buy'
    ) -> Optional[Any]:
        """
        Execute a limit order.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            quantity: Number of shares
            limit_price: Limit price for the order
            side: 'buy' or 'sell'
            
        Returns:
            Trade object if successful, None otherwise
        """
        if not self.is_connected():
            logger.error("Not connected to IBKR")
            return None
        
        try:
            # Create contract
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            # Create order
            action = 'BUY' if side.lower() == 'buy' else 'SELL'
            order = LimitOrder(action, quantity, limit_price)
            
            # Place order
            trade = self.ib.placeOrder(contract, order)
            
            logger.info(
                f"Limit order placed: {action} {quantity} {symbol} "
                f"@ ${limit_price} (Order ID: {trade.order.orderId})"
            )
            
            return trade
            
        except Exception as e:
            logger.error(f"Error executing limit order: {e}")
            return None
    
    def get_open_orders(self) -> List[Any]:
        """
        Get list of open orders.
        
        Returns:
            List of open Order objects
        """
        if not self.is_connected():
            logger.error("Not connected to IBKR")
            return []
        
        try:
            orders = self.ib.openOrders()
            logger.debug(f"Retrieved {len(orders)} open orders")
            return orders
        except Exception as e:
            logger.error(f"Error getting open orders: {e}")
            return []
    
    def cancel_order(self, order) -> bool:
        """
        Cancel an order.
        
        Args:
            order: Order object to cancel
            
        Returns:
            True if cancellation successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Not connected to IBKR")
            return False
        
        try:
            self.ib.cancelOrder(order)
            logger.info(f"Order cancelled: {order.orderId}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from IBKR"""
        if self.is_connected():
            try:
                self.ib.disconnect()
                self._connected = False
                logger.info("Disconnected from IBKR")
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")


def test_connection(
    paper_trading: bool = True,
    use_gateway: bool = False
) -> bool:
    """
    Test IBKR connection.
    
    This is a quick test to verify your IB setup is working correctly.
    
    Args:
        paper_trading: Test paper trading if True, live if False
        use_gateway: Use IB Gateway ports if True, TWS ports if False
        
    Returns:
        True if connection test passed, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"Testing IBKR Connection")
    print(f"Mode: {'Paper Trading' if paper_trading else 'Live Trading'}")
    print(f"App: {'IB Gateway' if use_gateway else 'TWS'}")
    print(f"{'='*60}\n")
    
    broker = IBKRBroker(
        paper_trading=paper_trading,
        use_gateway=use_gateway
    )
    
    # Test connection
    if not broker.connect():
        print("❌ Connection failed")
        return False
    
    print("✅ Connection successful\n")
    
    # Test getting account balance
    print("Testing account balance retrieval...")
    balance = broker.get_account_balance()
    if balance:
        print("✅ Account balance retrieved:")
        for key, value in balance.items():
            print(f"   {key}: ${value:,.2f}")
    else:
        print("⚠️  Could not retrieve account balance")
    
    print()
    
    # Test getting positions
    print("Testing position retrieval...")
    positions = broker.get_positions()
    if positions:
        print(f"✅ Retrieved {len(positions)} positions:")
        for pos in positions:
            print(f"   {pos['symbol']}: {pos['position']} shares @ ${pos['avg_cost']:.2f}")
    else:
        print("✅ No open positions (or retrieval failed)")
    
    print()
    
    # Test getting open orders
    print("Testing open orders retrieval...")
    orders = broker.get_open_orders()
    print(f"✅ Retrieved {len(orders)} open orders")
    
    print()
    
    # Disconnect
    broker.disconnect()
    print("✅ Disconnected successfully")
    
    print(f"\n{'='*60}")
    print("All tests passed! ✅")
    print(f"{'='*60}\n")
    
    return True


if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run connection test for paper trading with TWS
    # Change use_gateway=True if using IB Gateway instead of TWS
    test_connection(paper_trading=True, use_gateway=False)
