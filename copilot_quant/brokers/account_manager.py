"""
IBKR Account Manager

This module manages account information synchronization including:
- Real-time account balance tracking
- Buying power and margin monitoring  
- Account summary with comprehensive metrics
- Automatic sync on startup and real-time updates
- Discrepancy detection and logging

Example Usage:
    >>> from copilot_quant.brokers.account_manager import IBKRAccountManager
    >>> from copilot_quant.brokers.connection_manager import IBKRConnectionManager
    >>> 
    >>> # Create connection and account manager
    >>> conn = IBKRConnectionManager(paper_trading=True)
    >>> conn.connect()
    >>> account_mgr = IBKRAccountManager(conn)
    >>> 
    >>> # Get account summary
    >>> summary = account_mgr.get_account_summary()
    >>> print(f"Net Liquidation: ${summary.net_liquidation:,.2f}")
    >>> print(f"Buying Power: ${summary.buying_power:,.2f}")
    >>> 
    >>> # Start real-time updates
    >>> account_mgr.start_monitoring()
"""

import logging
import time
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from dataclasses import dataclass, field

try:
    from ib_insync import IB, AccountValue
except ImportError as e:
    raise ImportError(
        "ib_insync is required for IBKR integration. "
        "Install it with: pip install ib_insync>=0.9.86"
    ) from e

from .connection_manager import IBKRConnectionManager

logger = logging.getLogger(__name__)


@dataclass
class AccountSummary:
    """
    Comprehensive account summary data.
    
    Attributes:
        account_id: Account identifier
        net_liquidation: Total account value (cash + positions)
        total_cash_value: Available cash
        buying_power: Available buying power
        unrealized_pnl: Unrealized profit/loss on open positions
        realized_pnl: Realized profit/loss
        margin_available: Available margin
        gross_position_value: Total value of all positions
        timestamp: When this snapshot was taken
        raw_values: All raw account values from IBKR
    """
    account_id: str
    net_liquidation: float = 0.0
    total_cash_value: float = 0.0
    buying_power: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    margin_available: float = 0.0
    gross_position_value: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    raw_values: Dict[str, Any] = field(default_factory=dict)


class IBKRAccountManager:
    """
    Manages IBKR account information and synchronization.
    
    This class provides:
    - Initial account data load on startup
    - Real-time account value updates via callbacks
    - Comprehensive account summary
    - Discrepancy detection between expected and actual values
    - Logging of all account changes
    
    Key Features:
    - Automatic sync on initialization
    - Event-driven updates for real-time tracking
    - Configurable update callbacks for UI integration
    - Historical tracking of account state changes
    
    Attributes:
        connection_manager: IBKR connection manager instance
        account_id: Current account identifier
        last_summary: Most recent account summary
        update_callbacks: Registered callbacks for account updates
    
    Example:
        >>> conn_mgr = IBKRConnectionManager(paper_trading=True)
        >>> conn_mgr.connect()
        >>> acct_mgr = IBKRAccountManager(conn_mgr)
        >>> 
        >>> # Get current account summary
        >>> summary = acct_mgr.get_account_summary()
        >>> 
        >>> # Register callback for updates
        >>> def on_update(summary):
        ...     print(f"Account updated: {summary.net_liquidation}")
        >>> acct_mgr.register_update_callback(on_update)
        >>> acct_mgr.start_monitoring()
    """
    
    def __init__(self, connection_manager: IBKRConnectionManager, auto_sync: bool = True):
        """
        Initialize account manager.
        
        Args:
            connection_manager: Active IBKR connection manager
            auto_sync: If True, automatically sync account on initialization
            
        Raises:
            RuntimeError: If connection manager is not connected
        """
        if not connection_manager.is_connected():
            raise RuntimeError("Connection manager must be connected before creating AccountManager")
        
        self.connection_manager = connection_manager
        self.ib = connection_manager.get_ib()
        
        # Account state
        self.account_id: Optional[str] = None
        self.last_summary: Optional[AccountSummary] = None
        self._account_values_cache: Dict[str, AccountValue] = {}
        self._last_update_time: Optional[datetime] = None
        
        # Monitoring state
        self._monitoring_active = False
        self._update_callbacks: List[Callable[[AccountSummary], None]] = []
        self._change_log: List[Dict[str, Any]] = []
        
        # Get account ID
        accounts = self.ib.managedAccounts()
        if accounts:
            self.account_id = accounts[0]
            logger.info(f"Initialized AccountManager for account: {self.account_id}")
        else:
            logger.warning("No managed accounts found")
        
        # Auto-sync on startup
        if auto_sync:
            self.sync_account_state()
    
    def sync_account_state(self) -> bool:
        """
        Synchronize account state from IBKR.
        
        Loads current account values and updates internal state.
        This should be called:
        - On initialization
        - After reconnection
        - Periodically for reconciliation
        
        Returns:
            True if sync successful, False otherwise
        """
        try:
            logger.info("Syncing account state from IBKR...")
            
            # Get all account values
            account_values = self.ib.accountValues()
            
            if not account_values:
                logger.warning("No account values returned from IBKR")
                return False
            
            # Cache account values
            self._account_values_cache = {
                f"{av.tag}_{av.currency}": av for av in account_values
            }
            
            # Build account summary
            previous_summary = self.last_summary
            self.last_summary = self._build_account_summary(account_values)
            self._last_update_time = datetime.now()
            
            # Detect and log changes
            if previous_summary:
                self._detect_and_log_changes(previous_summary, self.last_summary)
            
            logger.info(
                f"Account sync complete - Net Liquidation: ${self.last_summary.net_liquidation:,.2f}, "
                f"Buying Power: ${self.last_summary.buying_power:,.2f}"
            )
            
            # Notify callbacks
            self._notify_update_callbacks()
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing account state: {e}", exc_info=True)
            return False
    
    def get_account_summary(self, force_refresh: bool = False) -> Optional[AccountSummary]:
        """
        Get current account summary.
        
        Args:
            force_refresh: If True, sync from IBKR before returning
            
        Returns:
            AccountSummary object or None if not available
        """
        if force_refresh:
            self.sync_account_state()
        
        return self.last_summary
    
    def get_account_value(self, tag: str, currency: str = "USD") -> Optional[float]:
        """
        Get specific account value by tag.
        
        Common tags:
        - NetLiquidation: Total account value
        - TotalCashValue: Cash balance
        - BuyingPower: Available buying power
        - GrossPositionValue: Total position value
        - UnrealizedPnL: Unrealized profit/loss
        - RealizedPnL: Realized profit/loss
        
        Args:
            tag: Account value tag name
            currency: Currency (default: USD)
            
        Returns:
            Float value or None if not found
        """
        key = f"{tag}_{currency}"
        av = self._account_values_cache.get(key)
        
        if av:
            try:
                return float(av.value)
            except (ValueError, TypeError):
                logger.warning(f"Could not convert account value to float: {tag}={av.value}")
                return None
        
        return None
    
    def get_all_account_values(self) -> Dict[str, Any]:
        """
        Get all account values as a dictionary.
        
        Returns:
            Dictionary mapping tag names to values
        """
        result = {}
        for key, av in self._account_values_cache.items():
            try:
                result[av.tag] = float(av.value)
            except (ValueError, TypeError):
                result[av.tag] = av.value
        
        return result
    
    def start_monitoring(self) -> bool:
        """
        Start real-time account monitoring.
        
        Registers for account update events from IBKR.
        Updates are delivered via the registered callbacks.
        
        Returns:
            True if monitoring started, False otherwise
        """
        if self._monitoring_active:
            logger.info("Account monitoring already active")
            return True
        
        try:
            # Subscribe to account updates
            self.ib.reqAccountUpdates()
            
            # Register event handler
            self.ib.accountValueEvent += self._on_account_value_update
            
            self._monitoring_active = True
            logger.info("Started real-time account monitoring")
            return True
            
        except Exception as e:
            logger.error(f"Error starting account monitoring: {e}", exc_info=True)
            return False
    
    def stop_monitoring(self) -> bool:
        """
        Stop real-time account monitoring.
        
        Returns:
            True if monitoring stopped, False otherwise
        """
        if not self._monitoring_active:
            logger.info("Account monitoring already inactive")
            return True
        
        try:
            # Unregister event handler
            self.ib.accountValueEvent -= self._on_account_value_update
            
            self._monitoring_active = False
            logger.info("Stopped real-time account monitoring")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping account monitoring: {e}", exc_info=True)
            return False
    
    def is_monitoring(self) -> bool:
        """
        Check if real-time monitoring is active.
        
        Returns:
            True if monitoring is active, False otherwise
        """
        return self._monitoring_active
    
    def register_update_callback(self, callback: Callable[[AccountSummary], None]):
        """
        Register a callback for account updates.
        
        The callback will be called whenever account values are updated.
        
        Args:
            callback: Function that takes AccountSummary as parameter
        """
        if callback not in self._update_callbacks:
            self._update_callbacks.append(callback)
            callback_name = getattr(callback, '__name__', repr(callback))
            logger.debug(f"Registered account update callback: {callback_name}")
    
    def unregister_update_callback(self, callback: Callable[[AccountSummary], None]):
        """
        Unregister a previously registered callback.
        
        Args:
            callback: Function to unregister
        """
        if callback in self._update_callbacks:
            self._update_callbacks.remove(callback)
            callback_name = getattr(callback, '__name__', repr(callback))
            logger.debug(f"Unregistered account update callback: {callback_name}")
    
    def get_change_log(self, max_entries: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent account change log.
        
        Args:
            max_entries: Maximum number of entries to return
            
        Returns:
            List of change log entries
        """
        return self._change_log[-max_entries:]
    
    def _build_account_summary(self, account_values: List[AccountValue]) -> AccountSummary:
        """
        Build AccountSummary from raw account values.
        
        Args:
            account_values: List of AccountValue objects from IBKR
            
        Returns:
            AccountSummary object
        """
        # Extract key values
        values = {}
        raw_values = {}
        
        for av in account_values:
            key = f"{av.tag}_{av.currency}"
            raw_values[key] = av.value
            
            try:
                values[av.tag] = float(av.value)
            except (ValueError, TypeError):
                # Some values may not be numeric
                pass
        
        # Build summary
        summary = AccountSummary(
            account_id=self.account_id or "",
            net_liquidation=values.get('NetLiquidation', 0.0),
            total_cash_value=values.get('TotalCashValue', 0.0),
            buying_power=values.get('BuyingPower', 0.0),
            unrealized_pnl=values.get('UnrealizedPnL', 0.0),
            realized_pnl=values.get('RealizedPnL', 0.0),
            margin_available=values.get('AvailableFunds', 0.0),
            gross_position_value=values.get('GrossPositionValue', 0.0),
            timestamp=datetime.now(),
            raw_values=raw_values
        )
        
        return summary
    
    def _detect_and_log_changes(self, previous: AccountSummary, current: AccountSummary):
        """
        Detect and log significant changes in account values.
        
        Args:
            previous: Previous account summary
            current: Current account summary
        """
        changes = []
        
        # Check key fields for changes
        fields_to_monitor = [
            ('net_liquidation', 'Net Liquidation'),
            ('total_cash_value', 'Total Cash'),
            ('buying_power', 'Buying Power'),
            ('unrealized_pnl', 'Unrealized P&L'),
            ('realized_pnl', 'Realized P&L'),
        ]
        
        for field_name, display_name in fields_to_monitor:
            prev_value = getattr(previous, field_name)
            curr_value = getattr(current, field_name)
            
            # Check for significant change (>0.01 to avoid floating point noise)
            if abs(curr_value - prev_value) > 0.01:
                change = {
                    'timestamp': current.timestamp,
                    'field': display_name,
                    'previous': prev_value,
                    'current': curr_value,
                    'change': curr_value - prev_value,
                    'pct_change': ((curr_value - prev_value) / prev_value * 100) if prev_value != 0 else 0
                }
                changes.append(change)
                
                logger.info(
                    f"Account change detected - {display_name}: "
                    f"${prev_value:,.2f} -> ${curr_value:,.2f} "
                    f"(${change['change']:+,.2f}, {change['pct_change']:+.2f}%)"
                )
        
        # Add to change log
        if changes:
            self._change_log.extend(changes)
            
            # Keep log size manageable
            if len(self._change_log) > 1000:
                self._change_log = self._change_log[-1000:]
    
    def _on_account_value_update(self, av: AccountValue):
        """
        Handle account value update event from IBKR.
        
        Args:
            av: Updated AccountValue object
        """
        # Update cache
        key = f"{av.tag}_{av.currency}"
        old_value = self._account_values_cache.get(key)
        self._account_values_cache[key] = av
        
        # Log significant changes
        if old_value:
            try:
                old_float = float(old_value.value)
                new_float = float(av.value)
                
                if abs(new_float - old_float) > 0.01:
                    logger.debug(
                        f"Account value updated - {av.tag}: "
                        f"{old_float:.2f} -> {new_float:.2f}"
                    )
            except (ValueError, TypeError):
                pass
        
        # Rebuild summary and notify (debounced to avoid too many updates)
        if self._should_rebuild_summary():
            self._rebuild_and_notify()
    
    def _should_rebuild_summary(self) -> bool:
        """
        Check if we should rebuild summary now.
        
        Debounces updates to avoid rebuilding too frequently.
        
        Returns:
            True if we should rebuild, False otherwise
        """
        if self._last_update_time is None:
            return True
        
        # Rebuild at most once per second
        elapsed = (datetime.now() - self._last_update_time).total_seconds()
        return elapsed >= 1.0
    
    def _rebuild_and_notify(self):
        """Rebuild summary from cache and notify callbacks."""
        try:
            # Convert cache to list
            account_values = list(self._account_values_cache.values())
            
            if not account_values:
                return
            
            # Build new summary
            previous_summary = self.last_summary
            self.last_summary = self._build_account_summary(account_values)
            self._last_update_time = datetime.now()
            
            # Detect changes
            if previous_summary:
                self._detect_and_log_changes(previous_summary, self.last_summary)
            
            # Notify callbacks
            self._notify_update_callbacks()
            
        except Exception as e:
            logger.error(f"Error rebuilding account summary: {e}", exc_info=True)
    
    def _notify_update_callbacks(self):
        """Notify all registered update callbacks."""
        if not self.last_summary:
            return
        
        for callback in self._update_callbacks:
            try:
                callback(self.last_summary)
            except Exception as e:
                callback_name = getattr(callback, '__name__', repr(callback))
                logger.error(f"Error in update callback {callback_name}: {e}", exc_info=True)
    
    def __repr__(self):
        """String representation."""
        return (
            f"IBKRAccountManager("
            f"account_id={self.account_id}, "
            f"monitoring={'active' if self._monitoring_active else 'inactive'}, "
            f"last_update={self._last_update_time})"
        )
