"""
Order Execution Handler for IBKR

This module provides comprehensive order execution management including:
- Order status tracking
- Fill notification handling (complete and partial)
- Error handling with retry logic
- Order deduplication
- Event callbacks for UI integration
"""

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from threading import Lock
from typing import Any, Callable, Dict, List, Optional

try:
    from ib_insync import Trade
except ImportError as e:
    raise ImportError(
        "ib_insync is required for IBKR integration. Install it with: pip install ib_insync>=0.9.86"
    ) from e

logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    """Order status enumeration"""

    PENDING = "Pending"  # Order created but not yet submitted
    SUBMITTED = "Submitted"  # Order submitted to broker
    PARTIALLY_FILLED = "PartiallyFilled"  # Order partially filled
    FILLED = "Filled"  # Order completely filled
    CANCELLED = "Cancelled"  # Order cancelled
    ERROR = "Error"  # Order encountered an error


@dataclass
class Fill:
    """Represents a fill (complete or partial)"""

    fill_id: str
    order_id: int
    symbol: str
    quantity: int  # Number of shares filled
    price: float  # Fill price
    timestamp: datetime
    commission: float = 0.0

    def __post_init__(self):
        if self.fill_id is None:
            self.fill_id = str(uuid.uuid4())


@dataclass
class OrderRecord:
    """Complete record of an order and its history"""

    order_id: int
    symbol: str
    action: str  # BUY or SELL
    total_quantity: int
    order_type: str  # MARKET or LIMIT
    limit_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: int = 0
    remaining_quantity: int = 0
    avg_fill_price: float = 0.0
    fills: List[Fill] = field(default_factory=list)
    error_message: Optional[str] = None
    submission_time: datetime = field(default_factory=datetime.now)
    last_update_time: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    trade_object: Optional[Any] = None  # ib_insync Trade object

    def __post_init__(self):
        if self.remaining_quantity == 0:
            self.remaining_quantity = self.total_quantity

    def add_fill(self, fill: Fill):
        """Add a fill and update order state"""
        self.fills.append(fill)
        self.filled_quantity += fill.quantity
        self.remaining_quantity = self.total_quantity - self.filled_quantity

        # Update average fill price
        if self.filled_quantity > 0:
            total_value = sum(f.quantity * f.price for f in self.fills)
            self.avg_fill_price = total_value / self.filled_quantity

        # Update status
        if self.filled_quantity >= self.total_quantity:
            self.status = OrderStatus.FILLED
        elif self.filled_quantity > 0:
            self.status = OrderStatus.PARTIALLY_FILLED

        self.last_update_time = datetime.now()

    def update_status(self, new_status: OrderStatus, error_message: Optional[str] = None):
        """Update order status"""
        self.status = new_status
        if error_message:
            self.error_message = error_message
        self.last_update_time = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "action": self.action,
            "total_quantity": self.total_quantity,
            "order_type": self.order_type,
            "limit_price": self.limit_price,
            "status": self.status.value,
            "filled_quantity": self.filled_quantity,
            "remaining_quantity": self.remaining_quantity,
            "avg_fill_price": self.avg_fill_price,
            "num_fills": len(self.fills),
            "error_message": self.error_message,
            "submission_time": self.submission_time.isoformat(),
            "last_update_time": self.last_update_time.isoformat(),
            "retry_count": self.retry_count,
        }


class OrderExecutionHandler:
    """
    Handles order execution with comprehensive tracking and error handling.

    Features:
    - Order status tracking
    - Fill notification handling (complete and partial)
    - Error handling with exponential backoff retry
    - Order deduplication
    - Event callbacks for UI integration

    Example:
        >>> handler = OrderExecutionHandler()
        >>> handler.register_fill_callback(lambda record: print(f"Filled: {record.symbol}"))
        >>> order_record = handler.submit_order(
        ...     ib_connection, symbol="AAPL", action="BUY",
        ...     quantity=100, order_type="MARKET"
        ... )
    """

    def __init__(self, max_retries: int = 3, initial_retry_delay: float = 1.0, retry_backoff_factor: float = 2.0):
        """
        Initialize order execution handler.

        Args:
            max_retries: Maximum number of retry attempts for failed orders
            initial_retry_delay: Initial delay in seconds before first retry
            retry_backoff_factor: Multiplier for exponential backoff
        """
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.retry_backoff_factor = retry_backoff_factor

        # Order tracking
        self._orders: Dict[int, OrderRecord] = {}  # order_id -> OrderRecord
        self._order_lock = Lock()

        # Deduplication tracking (to prevent duplicate orders)
        self._submitted_order_keys: set = set()  # Track unique order combinations

        # Callbacks for events
        self._fill_callbacks: List[Callable[[OrderRecord], None]] = []
        self._status_callbacks: List[Callable[[OrderRecord], None]] = []
        self._error_callbacks: List[Callable[[OrderRecord, str], None]] = []

        logger.info("OrderExecutionHandler initialized")

    def _generate_order_key(self, symbol: str, action: str, quantity: int) -> str:
        """Generate unique key for order deduplication"""
        return f"{symbol}_{action}_{quantity}_{int(time.time())}"

    def _is_duplicate_order(self, order_key: str) -> bool:
        """
        Check if order is a duplicate within a time window.

        Note: Current implementation doesn't auto-cleanup old keys.
        In production, implement periodic cleanup using a background task
        or use a time-based cache like TTLCache from cachetools.
        """
        with self._order_lock:
            if order_key in self._submitted_order_keys:
                logger.warning(f"Duplicate order detected: {order_key}")
                return True
            self._submitted_order_keys.add(order_key)
            return False

    def submit_order(
        self,
        ib_connection,
        symbol: str,
        action: str,
        quantity: int,
        order_type: str = "MARKET",
        limit_price: Optional[float] = None,
        contract=None,
    ) -> Optional[OrderRecord]:
        """
        Submit an order through IBKR.

        Args:
            ib_connection: IB connection instance
            symbol: Stock symbol
            action: 'BUY' or 'SELL'
            quantity: Number of shares
            order_type: 'MARKET' or 'LIMIT'
            limit_price: Limit price for limit orders
            contract: Optional pre-qualified contract

        Returns:
            OrderRecord if successful, None if duplicate or error
        """
        # Check for duplicates
        order_key = self._generate_order_key(symbol, action.upper(), quantity)
        if self._is_duplicate_order(order_key):
            logger.error(f"Duplicate order rejected: {symbol} {action} {quantity}")
            return None

        try:
            # Create contract if not provided
            if contract is None:
                from ib_insync import Stock

                contract = Stock(symbol, "SMART", "USD")
                ib_connection.qualifyContracts(contract)

            # Create order
            from ib_insync import LimitOrder, MarketOrder

            if order_type.upper() == "MARKET":
                order = MarketOrder(action.upper(), quantity)
            elif order_type.upper() == "LIMIT":
                if limit_price is None:
                    raise ValueError("Limit price required for LIMIT orders")
                order = LimitOrder(action.upper(), quantity, limit_price)
            else:
                raise ValueError(f"Unsupported order type: {order_type}")

            # Place order
            trade = ib_connection.placeOrder(contract, order)

            # Create order record
            order_record = OrderRecord(
                order_id=order.orderId,
                symbol=symbol,
                action=action.upper(),
                total_quantity=quantity,
                order_type=order_type.upper(),
                limit_price=limit_price,
                status=OrderStatus.SUBMITTED,
                trade_object=trade,
            )

            # Store order record
            with self._order_lock:
                self._orders[order.orderId] = order_record

            logger.info(f"Order submitted: {order_type} {action} {quantity} {symbol} (Order ID: {order.orderId})")

            # Notify status callbacks
            self._notify_status_callbacks(order_record)

            return order_record

        except Exception as e:
            logger.error(f"Error submitting order: {e}", exc_info=True)
            # Remove from submitted keys on error
            with self._order_lock:
                self._submitted_order_keys.discard(order_key)
            return None

    def handle_fill(self, order_id: int, quantity: int, price: float, commission: float = 0.0) -> bool:
        """
        Handle a fill notification from IBKR.

        Args:
            order_id: Order ID that was filled
            quantity: Quantity filled
            price: Fill price
            commission: Commission charged

        Returns:
            True if fill processed successfully, False otherwise
        """
        with self._order_lock:
            if order_id not in self._orders:
                logger.warning(f"Fill received for unknown order ID: {order_id}")
                return False

            order_record = self._orders[order_id]

        # Create fill record
        fill = Fill(
            fill_id=str(uuid.uuid4()),
            order_id=order_id,
            symbol=order_record.symbol,
            quantity=quantity,
            price=price,
            timestamp=datetime.now(),
            commission=commission,
        )

        # Add fill to order record
        order_record.add_fill(fill)

        logger.info(
            f"Fill processed: {quantity} {order_record.symbol} @ ${price:.2f} "
            f"(Order ID: {order_id}, Status: {order_record.status.value})"
        )

        # Notify callbacks
        self._notify_fill_callbacks(order_record)
        self._notify_status_callbacks(order_record)

        return True

    def handle_error(self, order_id: int, error_code: int, error_message: str) -> bool:
        """
        Handle an error notification from IBKR.

        Args:
            order_id: Order ID that encountered error
            error_code: IBKR error code
            error_message: Error description

        Returns:
            True if error handled, False otherwise
        """
        with self._order_lock:
            if order_id not in self._orders:
                logger.debug(f"Error received for unknown order ID: {order_id}")
                return False

            order_record = self._orders[order_id]

        full_error_message = f"Error {error_code}: {error_message}"
        order_record.update_status(OrderStatus.ERROR, full_error_message)

        logger.error(
            f"Order error: {order_record.symbol} {order_record.action} (Order ID: {order_id}) - {full_error_message}"
        )

        # Notify callbacks
        self._notify_error_callbacks(order_record, full_error_message)
        self._notify_status_callbacks(order_record)

        # Attempt retry if applicable
        if order_record.retry_count < self.max_retries:
            self._schedule_retry(order_record)

        return True

    def _schedule_retry(self, order_record: OrderRecord):
        """
        Log retry attempt for a failed order with exponential backoff.

        IMPORTANT: This method does NOT automatically retry the order.
        It only increments the retry count and logs the retry information.

        Actual retry logic must be implemented externally using:
        - A task scheduler (celery, apscheduler, etc.)
        - Manual retry by calling submit_order() again
        - Custom retry logic in your application

        Args:
            order_record: Order to retry

        Returns:
            Calculated delay in seconds for retry (for external use)
        """
        order_record.retry_count += 1
        delay = self.initial_retry_delay * (self.retry_backoff_factor ** (order_record.retry_count - 1))

        logger.info(
            f"Retry {order_record.retry_count}/{self.max_retries} logged for "
            f"order {order_record.order_id} (suggested delay: {delay:.1f}s). "
            f"Note: Automatic retry NOT implemented - manual retry required."
        )

        return delay

    def update_order_status(self, order_id: int, trade: Trade):
        """
        Update order status from ib_insync Trade object.

        Args:
            order_id: Order ID
            trade: ib_insync Trade object with current status
        """
        with self._order_lock:
            if order_id not in self._orders:
                return

            order_record = self._orders[order_id]

        # Map ib_insync status to our status
        ib_status = trade.orderStatus.status

        if ib_status == "Submitted" or ib_status == "PreSubmitted":
            new_status = OrderStatus.SUBMITTED
        elif ib_status == "Filled":
            new_status = OrderStatus.FILLED
        elif ib_status == "PartiallyFilled":
            new_status = OrderStatus.PARTIALLY_FILLED
        elif ib_status == "Cancelled":
            new_status = OrderStatus.CANCELLED
        elif ib_status in ["Inactive", "ApiCancelled", "PendingCancel"]:
            new_status = OrderStatus.CANCELLED
        else:
            new_status = OrderStatus.PENDING

        if order_record.status != new_status:
            order_record.update_status(new_status)
            logger.debug(f"Order {order_id} status updated to {new_status.value}")
            self._notify_status_callbacks(order_record)

    def get_order(self, order_id: int) -> Optional[OrderRecord]:
        """Get order record by ID"""
        with self._order_lock:
            return self._orders.get(order_id)

    def get_all_orders(self) -> List[OrderRecord]:
        """Get all order records"""
        with self._order_lock:
            return list(self._orders.values())

    def get_active_orders(self) -> List[OrderRecord]:
        """Get all active (not filled or cancelled) orders"""
        with self._order_lock:
            return [
                order
                for order in self._orders.values()
                if order.status not in [OrderStatus.FILLED, OrderStatus.CANCELLED]
            ]

    # Callback registration methods
    def register_fill_callback(self, callback: Callable[[OrderRecord], None]):
        """Register callback for fill events"""
        self._fill_callbacks.append(callback)
        logger.debug(f"Fill callback registered: {getattr(callback, '__name__', repr(callback))}")

    def unregister_fill_callback(self, callback: Callable[[OrderRecord], None]):
        """Unregister fill callback"""
        if callback in self._fill_callbacks:
            self._fill_callbacks.remove(callback)

    def register_status_callback(self, callback: Callable[[OrderRecord], None]):
        """Register callback for status change events"""
        self._status_callbacks.append(callback)
        logger.debug(f"Status callback registered: {getattr(callback, '__name__', repr(callback))}")

    def unregister_status_callback(self, callback: Callable[[OrderRecord], None]):
        """Unregister status callback"""
        if callback in self._status_callbacks:
            self._status_callbacks.remove(callback)

    def register_error_callback(self, callback: Callable[[OrderRecord, str], None]):
        """Register callback for error events"""
        self._error_callbacks.append(callback)
        logger.debug(f"Error callback registered: {getattr(callback, '__name__', repr(callback))}")

    def unregister_error_callback(self, callback: Callable[[OrderRecord, str], None]):
        """Unregister error callback"""
        if callback in self._error_callbacks:
            self._error_callbacks.remove(callback)

    # Callback notification methods
    def _notify_fill_callbacks(self, order_record: OrderRecord):
        """Notify all fill callbacks"""
        for callback in self._fill_callbacks:
            try:
                callback(order_record)
            except Exception as e:
                callback_name = getattr(callback, "__name__", repr(callback))
                logger.error(f"Error in fill callback {callback_name}: {e}", exc_info=True)

    def _notify_status_callbacks(self, order_record: OrderRecord):
        """Notify all status callbacks"""
        for callback in self._status_callbacks:
            try:
                callback(order_record)
            except Exception as e:
                callback_name = getattr(callback, "__name__", repr(callback))
                logger.error(f"Error in status callback {callback_name}: {e}", exc_info=True)

    def _notify_error_callbacks(self, order_record: OrderRecord, error_message: str):
        """Notify all error callbacks"""
        for callback in self._error_callbacks:
            try:
                callback(order_record, error_message)
            except Exception as e:
                callback_name = getattr(callback, "__name__", repr(callback))
                logger.error(f"Error in error callback {callback_name}: {e}", exc_info=True)
