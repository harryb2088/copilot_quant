"""
IBKR Position Manager

This module manages position tracking and synchronization including:
- Real-time position updates
- Position P&L (realized and unrealized)
- Position change detection and logging
- Discrepancy flagging between IBKR and local state

Example Usage:
    >>> from copilot_quant.brokers.position_manager import IBKRPositionManager
    >>> from copilot_quant.brokers.connection_manager import IBKRConnectionManager
    >>>
    >>> # Create connection and position manager
    >>> conn = IBKRConnectionManager(paper_trading=True)
    >>> conn.connect()
    >>> pos_mgr = IBKRPositionManager(conn)
    >>>
    >>> # Get all positions
    >>> positions = pos_mgr.get_positions()
    >>> for pos in positions:
    ...     print(f"{pos.symbol}: {pos.quantity} @ ${pos.avg_cost:.2f}")
    >>>
    >>> # Start real-time monitoring
    >>> pos_mgr.start_monitoring()
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Dict, List, Optional

try:
    from ib_insync import Position as IBPosition
except ImportError as e:
    raise ImportError(
        "ib_insync is required for IBKR integration. Install it with: pip install ib_insync>=0.9.86"
    ) from e

from .connection_manager import IBKRConnectionManager

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """
    Position information.

    Attributes:
        symbol: Stock symbol
        quantity: Number of shares (positive=long, negative=short)
        avg_cost: Average cost per share
        market_price: Current market price
        market_value: Current market value (quantity * market_price)
        unrealized_pnl: Unrealized profit/loss
        realized_pnl: Realized profit/loss (from closed trades)
        account_id: Account this position belongs to
        timestamp: When this position was last updated
    """

    symbol: str
    quantity: float
    avg_cost: float
    market_price: float = 0.0
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    account_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def cost_basis(self) -> float:
        """Total cost basis of position."""
        return self.quantity * self.avg_cost

    @property
    def pnl_percentage(self) -> float:
        """P&L as percentage of cost basis."""
        if self.cost_basis == 0:
            return 0.0
        return (self.unrealized_pnl / abs(self.cost_basis)) * 100


@dataclass
class PositionChange:
    """
    Record of a position change.

    Attributes:
        timestamp: When the change occurred
        symbol: Stock symbol
        change_type: Type of change (opened, closed, increased, decreased, price_update)
        previous_quantity: Previous position size
        new_quantity: New position size
        previous_value: Previous market value
        new_value: New market value
        pnl_impact: Impact on P&L
    """

    timestamp: datetime
    symbol: str
    change_type: str
    previous_quantity: float = 0.0
    new_quantity: float = 0.0
    previous_value: float = 0.0
    new_value: float = 0.0
    pnl_impact: float = 0.0


class IBKRPositionManager:
    """
    Manages IBKR position tracking and synchronization.

    This class provides:
    - Initial position load on startup
    - Real-time position updates via callbacks
    - Position P&L tracking (realized and unrealized)
    - Position change detection and logging
    - Discrepancy flagging between expected and actual positions

    Key Features:
    - Automatic sync on initialization
    - Event-driven updates for real-time tracking
    - Configurable update callbacks for UI integration
    - Historical tracking of position changes
    - Reconciliation with expected state

    Attributes:
        connection_manager: IBKR connection manager instance
        positions: Current positions by symbol
        update_callbacks: Registered callbacks for position updates
        change_log: History of position changes

    Example:
        >>> conn_mgr = IBKRConnectionManager(paper_trading=True)
        >>> conn_mgr.connect()
        >>> pos_mgr = IBKRPositionManager(conn_mgr)
        >>>
        >>> # Get all positions
        >>> positions = pos_mgr.get_positions()
        >>>
        >>> # Get specific position
        >>> aapl_pos = pos_mgr.get_position('AAPL')
        >>>
        >>> # Register callback for updates
        >>> def on_update(positions):
        ...     print(f"Positions updated: {len(positions)} positions")
        >>> pos_mgr.register_update_callback(on_update)
        >>> pos_mgr.start_monitoring()
    """

    def __init__(self, connection_manager: IBKRConnectionManager, auto_sync: bool = True):
        """
        Initialize position manager.

        Args:
            connection_manager: Active IBKR connection manager
            auto_sync: If True, automatically sync positions on initialization

        Raises:
            RuntimeError: If connection manager is not connected
        """
        if not connection_manager.is_connected():
            raise RuntimeError("Connection manager must be connected before creating PositionManager")

        self.connection_manager = connection_manager
        self.ib = connection_manager.get_ib()

        # Position state
        self.positions: Dict[str, Position] = {}
        self._last_update_time: Optional[datetime] = None

        # Monitoring state
        self._monitoring_active = False
        self._update_callbacks: List[Callable[[List[Position]], None]] = []
        self._change_log: List[PositionChange] = []

        # Auto-sync on startup
        if auto_sync:
            self.sync_positions()

    def sync_positions(self) -> bool:
        """
        Synchronize positions from IBKR.

        Loads current positions and updates internal state.
        This should be called:
        - On initialization
        - After reconnection
        - Periodically for reconciliation

        Returns:
            True if sync successful, False otherwise
        """
        try:
            logger.info("Syncing positions from IBKR...")

            # Get all positions
            ib_positions = self.ib.positions()

            # Track previous state for change detection
            previous_positions = self.positions.copy()

            # Clear and rebuild positions
            self.positions = {}

            for ib_pos in ib_positions:
                symbol = ib_pos.contract.symbol

                # Create Position object
                position = Position(
                    symbol=symbol,
                    quantity=ib_pos.position,
                    avg_cost=ib_pos.avgCost,
                    market_price=0.0,  # Will be updated by market data
                    market_value=0.0,
                    unrealized_pnl=0.0,
                    account_id=ib_pos.account,
                    timestamp=datetime.now(),
                )

                # Try to get current market value if available
                # Note: This requires market data subscription
                try:
                    # Request current market data (non-blocking snapshot)
                    ticker = self.ib.reqMktData(ib_pos.contract, snapshot=True)
                    # Brief wait for data - intentional to avoid IBKR rate limits
                    # and give time for snapshot data to arrive
                    self.ib.sleep(0.1)

                    if ticker.marketPrice() and ticker.marketPrice() > 0:
                        position.market_price = ticker.marketPrice()
                        position.market_value = position.quantity * position.market_price
                        position.unrealized_pnl = position.market_value - position.cost_basis

                    # Cancel market data request
                    self.ib.cancelMktData(ib_pos.contract)

                except Exception as e:
                    logger.debug(f"Could not get market data for {symbol}: {e}")

                self.positions[symbol] = position

            self._last_update_time = datetime.now()

            # Detect and log changes
            self._detect_and_log_changes(previous_positions, self.positions)

            logger.info(f"Position sync complete - {len(self.positions)} positions")

            # Notify callbacks
            self._notify_update_callbacks()

            return True

        except Exception as e:
            logger.error(f"Error syncing positions: {e}", exc_info=True)
            return False

    def get_positions(self, force_refresh: bool = False) -> List[Position]:
        """
        Get all current positions.

        Args:
            force_refresh: If True, sync from IBKR before returning

        Returns:
            List of Position objects
        """
        if force_refresh:
            self.sync_positions()

        return list(self.positions.values())

    def get_position(self, symbol: str, force_refresh: bool = False) -> Optional[Position]:
        """
        Get position for a specific symbol.

        Args:
            symbol: Stock symbol
            force_refresh: If True, sync from IBKR before returning

        Returns:
            Position object or None if not found
        """
        if force_refresh:
            self.sync_positions()

        return self.positions.get(symbol)

    def has_position(self, symbol: str) -> bool:
        """
        Check if we have a position in a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            True if position exists, False otherwise
        """
        return symbol in self.positions

    def get_total_market_value(self) -> float:
        """
        Get total market value of all positions.

        Returns:
            Total market value
        """
        return sum(pos.market_value for pos in self.positions.values())

    def get_total_unrealized_pnl(self) -> float:
        """
        Get total unrealized P&L across all positions.

        Returns:
            Total unrealized P&L
        """
        return sum(pos.unrealized_pnl for pos in self.positions.values())

    def get_long_positions(self) -> List[Position]:
        """
        Get all long positions (quantity > 0).

        Returns:
            List of long positions
        """
        return [pos for pos in self.positions.values() if pos.quantity > 0]

    def get_short_positions(self) -> List[Position]:
        """
        Get all short positions (quantity < 0).

        Returns:
            List of short positions
        """
        return [pos for pos in self.positions.values() if pos.quantity < 0]

    def start_monitoring(self) -> bool:
        """
        Start real-time position monitoring.

        Registers for position update events from IBKR.
        Updates are delivered via the registered callbacks.

        Returns:
            True if monitoring started, False otherwise
        """
        if self._monitoring_active:
            logger.info("Position monitoring already active")
            return True

        try:
            # Register event handler
            self.ib.positionEvent += self._on_position_update

            self._monitoring_active = True
            logger.info("Started real-time position monitoring")
            return True

        except Exception as e:
            logger.error(f"Error starting position monitoring: {e}", exc_info=True)
            return False

    def stop_monitoring(self) -> bool:
        """
        Stop real-time position monitoring.

        Returns:
            True if monitoring stopped, False otherwise
        """
        if not self._monitoring_active:
            logger.info("Position monitoring already inactive")
            return True

        try:
            # Unregister event handler
            self.ib.positionEvent -= self._on_position_update

            self._monitoring_active = False
            logger.info("Stopped real-time position monitoring")
            return True

        except Exception as e:
            logger.error(f"Error stopping position monitoring: {e}", exc_info=True)
            return False

    def is_monitoring(self) -> bool:
        """
        Check if real-time monitoring is active.

        Returns:
            True if monitoring is active, False otherwise
        """
        return self._monitoring_active

    def register_update_callback(self, callback: Callable[[List[Position]], None]):
        """
        Register a callback for position updates.

        The callback will be called whenever positions are updated.

        Args:
            callback: Function that takes list of Position objects as parameter
        """
        if callback not in self._update_callbacks:
            self._update_callbacks.append(callback)
            callback_name = getattr(callback, "__name__", repr(callback))
            logger.debug(f"Registered position update callback: {callback_name}")

    def unregister_update_callback(self, callback: Callable[[List[Position]], None]):
        """
        Unregister a previously registered callback.

        Args:
            callback: Function to unregister
        """
        if callback in self._update_callbacks:
            self._update_callbacks.remove(callback)
            callback_name = getattr(callback, "__name__", repr(callback))
            logger.debug(f"Unregistered position update callback: {callback_name}")

    def get_change_log(self, max_entries: int = 100) -> List[PositionChange]:
        """
        Get recent position change log.

        Args:
            max_entries: Maximum number of entries to return

        Returns:
            List of PositionChange objects
        """
        return self._change_log[-max_entries:]

    def flag_discrepancy(self, symbol: str, expected_quantity: float, actual_quantity: float):
        """
        Flag a discrepancy between expected and actual position.

        This should be called when the platform's expected position
        doesn't match IBKR's actual position.

        Args:
            symbol: Stock symbol
            expected_quantity: Expected position quantity
            actual_quantity: Actual position quantity from IBKR
        """
        discrepancy = actual_quantity - expected_quantity

        logger.warning(
            f"POSITION DISCREPANCY DETECTED - {symbol}: "
            f"Expected {expected_quantity}, Actual {actual_quantity}, "
            f"Discrepancy: {discrepancy:+.2f}"
        )

        # Log as a change
        change = PositionChange(
            timestamp=datetime.now(),
            symbol=symbol,
            change_type="discrepancy",
            previous_quantity=expected_quantity,
            new_quantity=actual_quantity,
            pnl_impact=0.0,
        )

        self._change_log.append(change)

        # Keep log size manageable
        if len(self._change_log) > 1000:
            self._change_log = self._change_log[-1000:]

    def _detect_and_log_changes(self, previous: Dict[str, Position], current: Dict[str, Position]):
        """
        Detect and log changes in positions.

        Args:
            previous: Previous positions dict
            current: Current positions dict
        """
        # Find new positions
        for symbol, pos in current.items():
            if symbol not in previous:
                change = PositionChange(
                    timestamp=datetime.now(),
                    symbol=symbol,
                    change_type="opened",
                    previous_quantity=0.0,
                    new_quantity=pos.quantity,
                    new_value=pos.market_value,
                    pnl_impact=0.0,
                )

                self._change_log.append(change)

                logger.info(f"Position opened - {symbol}: {pos.quantity} shares @ ${pos.avg_cost:.2f}")

        # Find closed positions
        for symbol, pos in previous.items():
            if symbol not in current:
                change = PositionChange(
                    timestamp=datetime.now(),
                    symbol=symbol,
                    change_type="closed",
                    previous_quantity=pos.quantity,
                    new_quantity=0.0,
                    previous_value=pos.market_value,
                    pnl_impact=pos.unrealized_pnl,
                )

                self._change_log.append(change)

                logger.info(f"Position closed - {symbol}: {pos.quantity} shares, P&L: ${pos.unrealized_pnl:+,.2f}")

        # Find changed positions
        for symbol in set(previous.keys()) & set(current.keys()):
            prev_pos = previous[symbol]
            curr_pos = current[symbol]

            # Check for quantity change
            if abs(curr_pos.quantity - prev_pos.quantity) > 0.0001:
                change_type = "increased" if curr_pos.quantity > prev_pos.quantity else "decreased"

                change = PositionChange(
                    timestamp=datetime.now(),
                    symbol=symbol,
                    change_type=change_type,
                    previous_quantity=prev_pos.quantity,
                    new_quantity=curr_pos.quantity,
                    previous_value=prev_pos.market_value,
                    new_value=curr_pos.market_value,
                )

                self._change_log.append(change)

                logger.info(
                    f"Position {change_type} - {symbol}: {prev_pos.quantity:.2f} -> {curr_pos.quantity:.2f} shares"
                )

        # Keep log size manageable
        if len(self._change_log) > 1000:
            self._change_log = self._change_log[-1000:]

    def _on_position_update(self, pos: IBPosition):
        """
        Handle position update event from IBKR.

        Args:
            pos: Updated Position object from ib_insync
        """
        symbol = pos.contract.symbol

        # Get previous position if exists
        previous_pos = self.positions.get(symbol)

        # Create/update position
        position = Position(
            symbol=symbol,
            quantity=pos.position,
            avg_cost=pos.avgCost,
            market_price=0.0,
            market_value=0.0,
            unrealized_pnl=0.0,
            account_id=pos.account,
            timestamp=datetime.now(),
        )

        # Try to get market price
        try:
            ticker = self.ib.reqMktData(pos.contract, snapshot=True)
            self.ib.sleep(0.1)

            if ticker.marketPrice() and ticker.marketPrice() > 0:
                position.market_price = ticker.marketPrice()
                position.market_value = position.quantity * position.market_price
                position.unrealized_pnl = position.market_value - position.cost_basis

            self.ib.cancelMktData(pos.contract)

        except Exception as e:
            logger.debug(f"Could not get market data for {symbol}: {e}")

        # Update positions
        if pos.position == 0:
            # Position closed
            if symbol in self.positions:
                del self.positions[symbol]
                logger.info(f"Position closed via update - {symbol}")
        else:
            # Position opened or updated
            self.positions[symbol] = position

            if previous_pos:
                if abs(position.quantity - previous_pos.quantity) > 0.0001:
                    logger.info(
                        f"Position updated - {symbol}: {previous_pos.quantity:.2f} -> {position.quantity:.2f} shares"
                    )
            else:
                logger.info(
                    f"Position opened via update - {symbol}: {position.quantity} shares @ ${position.avg_cost:.2f}"
                )

        # Update timestamp
        self._last_update_time = datetime.now()

        # Notify callbacks
        self._notify_update_callbacks()

    def _notify_update_callbacks(self):
        """Notify all registered update callbacks."""
        positions = list(self.positions.values())

        for callback in self._update_callbacks:
            try:
                callback(positions)
            except Exception as e:
                callback_name = getattr(callback, "__name__", repr(callback))
                logger.error(f"Error in update callback {callback_name}: {e}", exc_info=True)

    def __repr__(self):
        """String representation."""
        return (
            f"IBKRPositionManager("
            f"positions={len(self.positions)}, "
            f"monitoring={'active' if self._monitoring_active else 'inactive'}, "
            f"last_update={self._last_update_time})"
        )
