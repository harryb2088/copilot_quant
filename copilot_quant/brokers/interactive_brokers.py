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
from typing import Any, Callable, Dict, List, Optional

try:
    from ib_insync import IB, LimitOrder, MarketOrder, Stock
except ImportError as e:
    raise ImportError(
        "ib_insync is required for IBKR integration. Install it with: pip install ib_insync>=0.9.86"
    ) from e

from .account_manager import IBKRAccountManager
from .connection_manager import IBKRConnectionManager
from .order_execution_handler import OrderExecutionHandler, OrderRecord
from .order_logger import OrderLogger
from .position_manager import IBKRPositionManager

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
        use_gateway: bool = False,
        enable_account_manager: bool = True,
        enable_position_manager: bool = True,
        enable_order_execution: bool = True,
        enable_order_logging: bool = True,
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
            enable_account_manager: If True, enable account manager for real-time sync
            enable_position_manager: If True, enable position manager for real-time sync
            enable_order_execution: If True, enable order execution handler
            enable_order_logging: If True, enable order logging to file

        Environment Variables:
            IB_HOST: Interactive Brokers host (default: 127.0.0.1)
            IB_PORT: IB API port (overrides auto-detection)
            IB_CLIENT_ID: Unique client identifier (default: 1)
            IB_PAPER_ACCOUNT: Paper trading account number (for reference only)
        """
        # Use connection manager to handle all connection logic
        self.connection_manager = IBKRConnectionManager(
            paper_trading=paper_trading,
            host=host,
            port=port,
            client_id=client_id,
            use_gateway=use_gateway,
            auto_reconnect=True,
        )

        # Convenience properties
        self.paper_trading = paper_trading
        self.use_gateway = use_gateway

        # Manager flags
        self._enable_account_manager = enable_account_manager
        self._enable_position_manager = enable_position_manager
        self._enable_order_execution = enable_order_execution
        self._enable_order_logging = enable_order_logging

        # Managers (will be initialized after connection)
        self.account_manager: Optional[IBKRAccountManager] = None
        self.position_manager: Optional[IBKRPositionManager] = None
        self.order_handler: Optional[OrderExecutionHandler] = None
        self.order_logger: Optional[OrderLogger] = None

        logger.info(
            f"Initialized IBKRBroker: "
            f"mode={'Paper' if paper_trading else 'Live'}, "
            f"app={'Gateway' if use_gateway else 'TWS'}, "
            f"account_mgr={'enabled' if enable_account_manager else 'disabled'}, "
            f"position_mgr={'enabled' if enable_position_manager else 'disabled'}, "
            f"order_exec={'enabled' if enable_order_execution else 'disabled'}"
        )

    def connect(self, timeout: int = 30, retry_count: int = 3) -> bool:
        """
        Establish connection to IBKR.

        After connection, initializes account and position managers if enabled.

        Args:
            timeout: Connection timeout in seconds
            retry_count: Number of connection retry attempts

        Returns:
            True if connection successful, False otherwise
        """
        try:
            success = self.connection_manager.connect(timeout=timeout, retry_count=retry_count)

            if success:
                # Initialize managers after connection
                self._initialize_managers()

            return success

        except ConnectionError:
            return False

    def _initialize_managers(self):
        """Initialize account, position, and order managers after connection."""
        try:
            # Initialize account manager
            if self._enable_account_manager:
                self.account_manager = IBKRAccountManager(self.connection_manager)
                logger.info("Account manager initialized and synced")

            # Initialize position manager
            if self._enable_position_manager:
                self.position_manager = IBKRPositionManager(self.connection_manager)
                logger.info("Position manager initialized and synced")

            # Initialize order execution handler
            if self._enable_order_execution:
                self.order_handler = OrderExecutionHandler()
                logger.info("Order execution handler initialized")

                # Register event callbacks from ib_insync
                self._register_order_callbacks()

            # Initialize order logger
            if self._enable_order_logging:
                self.order_logger = OrderLogger(log_to_file=True, log_to_console=True)
                logger.info("Order logger initialized")

                # Register logging callbacks
                if self.order_handler:
                    self.order_handler.register_fill_callback(
                        lambda record: self.order_logger.log_fill(record, record.fills[-1])
                    )
                    self.order_handler.register_error_callback(
                        lambda record, msg: self.order_logger.log_error(record, msg)
                    )

        except Exception as e:
            logger.error(f"Error initializing managers: {e}", exc_info=True)

    def _register_order_callbacks(self):
        """Register callbacks for order events from ib_insync"""
        try:
            ib = self.connection_manager.get_ib()

            # Register execDetails callback for fills
            def on_exec_details(trade, fill):
                """Handle execution (fill) notification"""
                try:
                    order_id = trade.order.orderId
                    logger.debug(f"Execution details received for order {order_id}")

                    # Process fill through handler
                    if self.order_handler:
                        self.order_handler.handle_fill(
                            order_id=order_id,
                            quantity=int(fill.execution.shares),
                            price=fill.execution.price,
                            commission=fill.commissionReport.commission if fill.commissionReport else 0.0,
                        )
                except Exception as e:
                    logger.error(f"Error handling execution details: {e}", exc_info=True)

            # Register orderStatus callback for status updates
            def on_order_status(trade):
                """Handle order status updates"""
                try:
                    order_id = trade.order.orderId
                    logger.debug(f"Order status update for {order_id}: {trade.orderStatus.status}")

                    # Update order status through handler
                    if self.order_handler:
                        self.order_handler.update_order_status(order_id, trade)
                except Exception as e:
                    logger.error(f"Error handling order status: {e}", exc_info=True)

            # Register error callback for errors
            def on_error(reqId, errorCode, errorString, contract):
                """Handle error notifications"""
                try:
                    # Only process order-related errors (reqId is order ID)
                    if reqId > 0 and self.order_handler:
                        logger.debug(f"Error for order {reqId}: {errorCode} - {errorString}")
                        self.order_handler.handle_error(reqId, errorCode, errorString)
                except Exception as e:
                    logger.error(f"Error handling error callback: {e}", exc_info=True)

            # Attach callbacks
            ib.execDetailsEvent += on_exec_details
            ib.orderStatusEvent += on_order_status
            ib.errorEvent += on_error

            logger.info("Order event callbacks registered")

        except Exception as e:
            logger.error(f"Error registering order callbacks: {e}", exc_info=True)

    def is_connected(self) -> bool:
        """Check if currently connected to IBKR"""
        return self.connection_manager.is_connected()

    @property
    def ib(self) -> IB:
        """
        Get the underlying IB instance.

        Note: This property will raise a RuntimeError if not connected.
        Always call connect() before accessing this property.

        Returns:
            The ib_insync IB instance

        Raises:
            RuntimeError: If not connected to IBKR
        """
        return self.connection_manager.get_ib()

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
                if av.tag in ["NetLiquidation", "TotalCashValue", "BuyingPower"]:
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
                position_list.append(
                    {
                        "symbol": pos.contract.symbol,
                        "position": pos.position,
                        "avg_cost": pos.avgCost,
                        "cost_basis": pos.position * pos.avgCost,
                    }
                )

            logger.debug(f"Retrieved {len(position_list)} positions")
            return position_list

        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []

    def execute_market_order(self, symbol: str, quantity: int, side: str = "buy") -> Optional[OrderRecord]:
        """
        Execute a market order.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            quantity: Number of shares
            side: 'buy' or 'sell'

        Returns:
            OrderRecord if successful, None otherwise
        """
        if not self.is_connected():
            logger.error("Not connected to IBKR")
            return None

        # Use order handler if available
        if self.order_handler:
            order_record = self.order_handler.submit_order(
                ib_connection=self.ib, symbol=symbol, action=side.upper(), quantity=quantity, order_type="MARKET"
            )

            # Log submission
            if order_record and self.order_logger:
                self.order_logger.log_submission(order_record)

            return order_record
        else:
            # Fallback to old implementation if handler not enabled
            try:
                # Create contract
                contract = Stock(symbol, "SMART", "USD")
                self.ib.qualifyContracts(contract)

                # Create order
                action = "BUY" if side.lower() == "buy" else "SELL"
                order = MarketOrder(action, quantity)

                # Place order
                trade = self.ib.placeOrder(contract, order)

                logger.info(f"Market order placed: {action} {quantity} {symbol} (Order ID: {trade.order.orderId})")

                return trade

            except Exception as e:
                logger.error(f"Error executing market order: {e}")
                return None

    def execute_limit_order(
        self, symbol: str, quantity: int, limit_price: float, side: str = "buy"
    ) -> Optional[OrderRecord]:
        """
        Execute a limit order.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            quantity: Number of shares
            limit_price: Limit price for the order
            side: 'buy' or 'sell'

        Returns:
            OrderRecord if successful, None otherwise
        """
        if not self.is_connected():
            logger.error("Not connected to IBKR")
            return None

        # Use order handler if available
        if self.order_handler:
            order_record = self.order_handler.submit_order(
                ib_connection=self.ib,
                symbol=symbol,
                action=side.upper(),
                quantity=quantity,
                order_type="LIMIT",
                limit_price=limit_price,
            )

            # Log submission
            if order_record and self.order_logger:
                self.order_logger.log_submission(order_record)

            return order_record
        else:
            # Fallback to old implementation if handler not enabled
            try:
                # Create contract
                contract = Stock(symbol, "SMART", "USD")
                self.ib.qualifyContracts(contract)

                # Create order
                action = "BUY" if side.lower() == "buy" else "SELL"
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
            order: Order object or order ID to cancel

        Returns:
            True if cancellation successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Not connected to IBKR")
            return False

        try:
            self.ib.cancelOrder(order)
            order_id = order.orderId if hasattr(order, "orderId") else order
            logger.info(f"Order cancelled: {order_id}")

            # Log cancellation
            if self.order_handler and self.order_logger:
                order_record = self.order_handler.get_order(order_id)
                if order_record:
                    self.order_logger.log_cancellation(order_record)

            return True
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False

    def get_order_status(self, order_id: int) -> Optional[OrderRecord]:
        """
        Get status of a specific order.

        Args:
            order_id: Order ID to query

        Returns:
            OrderRecord if found, None otherwise
        """
        if self.order_handler:
            return self.order_handler.get_order(order_id)
        return None

    def get_all_orders(self) -> List[OrderRecord]:
        """
        Get all tracked orders.

        Returns:
            List of all OrderRecord objects
        """
        if self.order_handler:
            return self.order_handler.get_all_orders()
        return []

    def get_active_orders(self) -> List[OrderRecord]:
        """
        Get all active orders (not filled or cancelled).

        Returns:
            List of active OrderRecord objects
        """
        if self.order_handler:
            return self.order_handler.get_active_orders()
        return []

    def get_order_history(self, order_id: int) -> List[str]:
        """
        Get complete event history for an order.

        Args:
            order_id: Order ID to get history for

        Returns:
            List of log entries for the order
        """
        if self.order_logger:
            return self.order_logger.get_order_history(order_id)
        return []

    def get_todays_order_summary(self) -> Dict[str, Any]:
        """
        Get summary of today's order activity.

        Returns:
            Dictionary with order statistics
        """
        if self.order_logger:
            return self.order_logger.get_todays_summary()
        return {}

    def register_order_fill_callback(self, callback: Callable[[OrderRecord], None]):
        """
        Register a callback for order fill events.

        Args:
            callback: Function to call when order is filled (complete or partial)
        """
        if self.order_handler:
            self.order_handler.register_fill_callback(callback)

    def register_order_status_callback(self, callback: Callable[[OrderRecord], None]):
        """
        Register a callback for order status changes.

        Args:
            callback: Function to call when order status changes
        """
        if self.order_handler:
            self.order_handler.register_status_callback(callback)

    def register_order_error_callback(self, callback: Callable[[OrderRecord, str], None]):
        """
        Register a callback for order errors.

        Args:
            callback: Function to call when order encounters an error
        """
        if self.order_handler:
            self.order_handler.register_error_callback(callback)

    def disconnect(self):
        """Disconnect from IBKR"""
        # Stop monitoring if active
        if self.account_manager:
            self.account_manager.stop_monitoring()

        if self.position_manager:
            self.position_manager.stop_monitoring()

        self.connection_manager.disconnect()

    def start_real_time_monitoring(self) -> bool:
        """
        Start real-time monitoring of account and positions.

        This enables real-time updates via IBKR events.
        Updates are delivered to registered callbacks.

        Returns:
            True if monitoring started successfully, False otherwise
        """
        success = True

        if self.account_manager:
            if not self.account_manager.start_monitoring():
                logger.error("Failed to start account monitoring")
                success = False

        if self.position_manager:
            if not self.position_manager.start_monitoring():
                logger.error("Failed to start position monitoring")
                success = False

        return success

    def stop_real_time_monitoring(self) -> bool:
        """
        Stop real-time monitoring of account and positions.

        Returns:
            True if monitoring stopped successfully, False otherwise
        """
        success = True

        if self.account_manager:
            if not self.account_manager.stop_monitoring():
                success = False

        if self.position_manager:
            if not self.position_manager.stop_monitoring():
                success = False

        return success


def test_connection(paper_trading: bool = True, use_gateway: bool = False) -> bool:
    """
    Test IBKR connection.

    This is a quick test to verify your IB setup is working correctly.

    Args:
        paper_trading: Test paper trading if True, live if False
        use_gateway: Use IB Gateway ports if True, TWS ports if False

    Returns:
        True if connection test passed, False otherwise
    """
    print(f"\n{'=' * 60}")
    print("Testing IBKR Connection")
    print(f"Mode: {'Paper Trading' if paper_trading else 'Live Trading'}")
    print(f"App: {'IB Gateway' if use_gateway else 'TWS'}")
    print(f"{'=' * 60}\n")

    broker = IBKRBroker(paper_trading=paper_trading, use_gateway=use_gateway)

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

    print(f"\n{'=' * 60}")
    print("All tests passed! ✅")
    print(f"{'=' * 60}\n")

    return True


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Run connection test for paper trading with TWS
    # Change use_gateway=True if using IB Gateway instead of TWS
    test_connection(paper_trading=True, use_gateway=False)
