"""
Live Broker Adapter for Strategy Engine Integration

This module provides an adapter that implements the IBroker interface
from the backtest engine, allowing live IBKR order execution to be used with
strategies designed for backtesting.

Features:
- Implements IBroker interface for seamless strategy integration
- Real-time order execution via IBKR
- Position and account management
- Buying power checks
- Commission and slippage calculation
- Error handling and fallback

Example Usage:
    >>> from copilot_quant.brokers.live_broker_adapter import LiveBrokerAdapter
    >>> from copilot_quant.backtest.orders import Order
    >>> 
    >>> # Initialize adapter
    >>> adapter = LiveBrokerAdapter(paper_trading=True)
    >>> if adapter.connect():
    ...     # Check buying power
    ...     order = Order(symbol='AAPL', quantity=10, order_type='market', side='buy')
    ...     price = 150.0
    ...     can_buy = adapter.check_buying_power(order, price)
    ...     
    ...     # Execute order
    ...     if can_buy:
    ...         fill = adapter.execute_order(order, price, datetime.now())
    ...     
    ...     # Get positions
    ...     positions = adapter.get_positions()
    ...     
    ...     adapter.disconnect()
"""

import logging
from datetime import datetime
from typing import Dict, Optional
import uuid

from copilot_quant.backtest.interfaces import IBroker
from copilot_quant.backtest.orders import Fill, Order, Position
from copilot_quant.brokers.interactive_brokers import IBKRBroker

logger = logging.getLogger(__name__)


class LiveBrokerAdapter(IBroker):
    """
    Adapter that implements IBroker interface using IBKR live broker.
    
    This class bridges the gap between the backtest engine's broker interface
    and IBKR's live order execution API, allowing strategies to work seamlessly
    in both backtest and live trading modes.
    
    The adapter:
    - Implements all IBroker methods
    - Manages order execution and tracking
    - Handles position management
    - Provides buying power checks
    - Calculates commissions and slippage
    - Provides fallback mechanisms
    
    Example:
        >>> adapter = LiveBrokerAdapter(paper_trading=True)
        >>> adapter.connect()
        >>> 
        >>> # Create and execute order (backtest-compatible)
        >>> order = Order(symbol='AAPL', quantity=10, order_type='market', side='buy')
        >>> fill = adapter.execute_order(order, current_price=150.0, timestamp=datetime.now())
        >>> 
        >>> # Check positions
        >>> positions = adapter.get_positions()
        >>> 
        >>> # Get cash balance
        >>> cash = adapter.get_cash_balance()
        >>> 
        >>> adapter.disconnect()
    """
    
    def __init__(
        self,
        paper_trading: bool = True,
        host: Optional[str] = None,
        port: Optional[int] = None,
        client_id: Optional[int] = None,
        use_gateway: bool = False,
        commission_rate: float = 0.001,
        slippage_rate: float = 0.0005,
        enable_position_tracking: bool = True
    ):
        """
        Initialize the live broker adapter.
        
        Args:
            paper_trading: If True, connect to paper trading account
            host: IB API host address (default: from env or '127.0.0.1')
            port: IB API port (default: auto-detected based on mode)
            client_id: Unique client identifier (default: from env or 1)
            use_gateway: If True, use IB Gateway ports, else use TWS ports
            commission_rate: Commission as decimal (e.g., 0.001 = 0.1%)
            slippage_rate: Slippage as decimal (e.g., 0.0005 = 0.05%)
            enable_position_tracking: If True, track positions locally
        """
        # Initialize underlying IBKR broker
        self._broker = IBKRBroker(
            paper_trading=paper_trading,
            host=host,
            port=port,
            client_id=client_id,
            use_gateway=use_gateway,
            enable_account_manager=True,
            enable_position_manager=enable_position_tracking,
            enable_order_execution=True,
            enable_order_logging=True
        )
        
        # Configuration
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.enable_position_tracking = enable_position_tracking
        
        # Local position tracking (mirrors IBKR positions in backtest format)
        self._positions: Dict[str, Position] = {}
        
        logger.info("LiveBrokerAdapter initialized")
    
    def connect(self, timeout: int = 30, retry_count: int = 3) -> bool:
        """
        Establish connection to IBKR.
        
        Args:
            timeout: Connection timeout in seconds
            retry_count: Number of connection retry attempts
            
        Returns:
            True if connection successful, False otherwise
        """
        success = self._broker.connect(timeout=timeout, retry_count=retry_count)
        
        if success:
            # Sync positions from IBKR
            self._sync_positions()
            logger.info("Live broker connected and positions synced")
        else:
            logger.error("Failed to connect to live broker")
        
        return success
    
    def is_connected(self) -> bool:
        """Check if currently connected to IBKR"""
        return self._broker.is_connected()
    
    # IBroker interface implementation
    
    def execute_order(
        self,
        order: Order,
        current_price: float,
        timestamp: datetime
    ) -> Optional[Fill]:
        """
        Execute an order if conditions are met.
        
        This method translates a backtest-style Order object into an IBKR
        order and executes it through the live broker.
        
        Args:
            order: Order to execute (from backtest engine)
            current_price: Current market price (for validation)
            timestamp: Execution timestamp
        
        Returns:
            Fill object if order executed, None if rejected/unfilled
        
        Note:
            For live execution, the actual fill price may differ from
            current_price due to market movements and slippage.
        """
        if not self.is_connected():
            logger.error("Cannot execute order - not connected to IBKR")
            return None
        
        try:
            # Check buying power first
            if not self.check_buying_power(order, current_price):
                logger.warning(
                    f"Insufficient buying power for order: "
                    f"{order.side} {order.quantity} {order.symbol}"
                )
                return None
            
            # Execute order through IBKR
            if order.order_type.lower() == 'market':
                order_record = self._broker.execute_market_order(
                    symbol=order.symbol,
                    quantity=order.quantity,
                    side=order.side
                )
            elif order.order_type.lower() == 'limit':
                if order.limit_price is None:
                    logger.error("Limit price required for limit orders")
                    return None
                
                order_record = self._broker.execute_limit_order(
                    symbol=order.symbol,
                    quantity=order.quantity,
                    limit_price=order.limit_price,
                    side=order.side
                )
            else:
                logger.error(f"Unsupported order type: {order.order_type}")
                return None
            
            if order_record is None:
                logger.error("Order execution failed")
                return None
            
            # For market orders, we can return an estimated fill immediately
            # For limit orders, we would need to wait for actual fill
            # For simplicity, return estimated fill for market orders
            if order.order_type.lower() == 'market':
                fill_price = self.calculate_slippage(order, current_price)
                commission = self.calculate_commission(fill_price, order.quantity)
                
                fill = Fill(
                    order=order,
                    fill_price=fill_price,
                    fill_quantity=order.quantity,
                    commission=commission,
                    timestamp=timestamp,
                    fill_id=str(uuid.uuid4())
                )
                
                # Update local position tracking
                self._update_position_from_fill(fill, current_price)
                
                logger.info(
                    f"Order executed: {order.side} {order.quantity} {order.symbol} "
                    f"@ ${fill_price:.2f} (Order ID: {order_record.order_id})"
                )
                
                return fill
            
            # For limit orders, return None (would need async fill notification)
            logger.info(
                f"Limit order submitted: {order.side} {order.quantity} {order.symbol} "
                f"@ ${order.limit_price:.2f} (Order ID: {order_record.order_id})"
            )
            return None
            
        except Exception as e:
            logger.error(f"Error executing order: {e}", exc_info=True)
            return None
    
    def check_buying_power(self, order: Order, price: float) -> bool:
        """
        Check if sufficient capital is available for order.
        
        Args:
            order: Order to check
            price: Estimated execution price
        
        Returns:
            True if order can be executed, False otherwise
        """
        if not self.is_connected():
            logger.error("Cannot check buying power - not connected to IBKR")
            return False
        
        try:
            # For sell orders, check if we have the position
            if order.side.lower() == 'sell':
                position = self._positions.get(order.symbol)
                if position is None or position.quantity < order.quantity:
                    logger.warning(
                        f"Insufficient position for sell: have "
                        f"{position.quantity if position else 0}, need {order.quantity}"
                    )
                    return False
                return True
            
            # For buy orders, check buying power
            cost = price * order.quantity
            commission = self.calculate_commission(price, order.quantity)
            total_cost = cost + commission
            
            # Get buying power from IBKR
            balance_info = self._broker.get_account_balance()
            buying_power = balance_info.get('BuyingPower', 0.0)
            
            has_power = buying_power >= total_cost
            
            if not has_power:
                logger.warning(
                    f"Insufficient buying power: need ${total_cost:,.2f}, "
                    f"have ${buying_power:,.2f}"
                )
            
            return has_power
            
        except Exception as e:
            logger.error(f"Error checking buying power: {e}")
            return False
    
    def calculate_commission(self, fill_price: float, quantity: float) -> float:
        """
        Calculate commission for a trade.
        
        Args:
            fill_price: Price at which order filled
            quantity: Quantity traded
        
        Returns:
            Commission amount in dollars
        """
        # Simple percentage-based commission
        gross_value = fill_price * quantity
        commission = gross_value * self.commission_rate
        
        # Minimum commission (e.g., $1.00)
        min_commission = 1.0
        
        return max(commission, min_commission)
    
    def calculate_slippage(self, order: Order, market_price: float) -> float:
        """
        Calculate realistic fill price with slippage.
        
        Args:
            order: Order being filled
            market_price: Current market price
        
        Returns:
            Expected fill price including slippage
        
        Note:
            Slippage is applied to market orders.
            Buy orders pay slippage (higher price).
            Sell orders receive slippage (lower price).
        """
        if order.side.lower() == 'buy':
            # Pay slippage on buys
            return market_price * (1 + self.slippage_rate)
        else:
            # Receive less on sells
            return market_price * (1 - self.slippage_rate)
    
    def get_positions(self) -> Dict[str, Position]:
        """
        Get all current positions.
        
        Returns:
            Dictionary mapping symbol to Position object
        """
        if self.enable_position_tracking:
            # Return local position tracking
            return self._positions.copy()
        else:
            # Sync from IBKR and return
            self._sync_positions()
            return self._positions.copy()
    
    def get_cash_balance(self) -> float:
        """
        Get current cash balance.
        
        Returns:
            Available cash in dollars
        """
        if not self.is_connected():
            logger.error("Cannot get cash balance - not connected to IBKR")
            return 0.0
        
        try:
            balance_info = self._broker.get_account_balance()
            cash = balance_info.get('TotalCashValue', 0.0)
            return cash
        except Exception as e:
            logger.error(f"Error getting cash balance: {e}")
            return 0.0
    
    def disconnect(self):
        """Disconnect from IBKR and clean up"""
        self._broker.disconnect()
        logger.info("Live broker disconnected")
    
    # Helper methods
    
    def _sync_positions(self):
        """
        Sync positions from IBKR to local tracking.
        
        Converts IBKR position format to backtest Position format.
        """
        if not self.is_connected():
            return
        
        try:
            ibkr_positions = self._broker.get_positions()
            
            # Clear local positions
            self._positions.clear()
            
            # Convert IBKR positions to backtest format
            for pos in ibkr_positions:
                symbol = pos['symbol']
                quantity = int(pos['position'])
                avg_cost = pos['avg_cost']
                
                # Create Position object
                position = Position(symbol=symbol)
                position.quantity = quantity
                position.avg_entry_price = avg_cost
                position.cost_basis = quantity * avg_cost
                
                # Note: market_value needs current price, which we don't have here
                # It will be updated when we get market data
                position.market_value = position.cost_basis
                position.unrealized_pnl = 0.0
                
                self._positions[symbol] = position
            
            logger.debug(f"Synced {len(self._positions)} positions from IBKR")
            
        except Exception as e:
            logger.error(f"Error syncing positions: {e}")
    
    def _update_position_from_fill(self, fill: Fill, current_price: float):
        """
        Update local position tracking from a fill.
        
        Args:
            fill: Fill to process
            current_price: Current market price
        """
        if not self.enable_position_tracking:
            return
        
        symbol = fill.order.symbol
        
        # Get or create position
        if symbol not in self._positions:
            self._positions[symbol] = Position(symbol=symbol)
        
        position = self._positions[symbol]
        
        # Update position from fill
        position.update_from_fill(fill, current_price)
        
        # Remove position if flat
        if position.quantity == 0:
            del self._positions[symbol]
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get position for a specific symbol.
        
        Args:
            symbol: Ticker symbol
            
        Returns:
            Position object or None
        """
        return self._positions.get(symbol)
    
    def get_account_value(self) -> float:
        """
        Get total account value (cash + positions).
        
        Returns:
            Total account value in dollars
        """
        if not self.is_connected():
            logger.error("Cannot get account value - not connected to IBKR")
            return 0.0
        
        try:
            balance_info = self._broker.get_account_balance()
            net_liquidation = balance_info.get('NetLiquidation', 0.0)
            return net_liquidation
        except Exception as e:
            logger.error(f"Error getting account value: {e}")
            return 0.0
    
    def register_fill_callback(self, callback):
        """
        Register a callback for order fill events.
        
        Args:
            callback: Function to call when order is filled
        """
        if hasattr(self._broker, 'register_order_fill_callback'):
            self._broker.register_order_fill_callback(callback)
    
    def register_error_callback(self, callback):
        """
        Register a callback for order error events.
        
        Args:
            callback: Function to call when order encounters an error
        """
        if hasattr(self._broker, 'register_order_error_callback'):
            self._broker.register_order_error_callback(callback)
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
        return False
