"""
Trade Reconciliation Module for IBKR

Reconciles local order logs with IBKR account trade history to identify discrepancies.
This module helps ensure audit trail accuracy and compliance.

Features:
- Fetch fills from IBKR using ib.fills()
- Compare with locally logged trades
- Identify missing or mismatched trades
- Generate reconciliation reports

Example:
    >>> from copilot_quant.brokers.trade_reconciliation import TradeReconciliation
    >>> reconciler = TradeReconciliation(broker)
    >>> report = reconciler.reconcile_today()
    >>> if report.has_discrepancies():
    ...     print(f"Found {len(report.discrepancies)} discrepancies")
"""

import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class DiscrepancyType(Enum):
    """Types of reconciliation discrepancies"""
    MISSING_LOCAL = "MissingLocal"  # Trade in IBKR but not in local logs
    MISSING_IBKR = "MissingIBKR"  # Trade in local logs but not in IBKR
    QUANTITY_MISMATCH = "QuantityMismatch"  # Different quantities
    PRICE_MISMATCH = "PriceMismatch"  # Different prices
    COMMISSION_MISMATCH = "CommissionMismatch"  # Different commissions


@dataclass
class IBKRFill:
    """Normalized representation of an IBKR fill"""
    execution_id: str
    order_id: int
    symbol: str
    side: str  # BUY or SELL
    quantity: int
    price: float
    commission: float
    timestamp: datetime
    raw_data: Optional[Any] = None  # Original Fill object from ib_insync
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'execution_id': self.execution_id,
            'order_id': self.order_id,
            'symbol': self.symbol,
            'side': self.side,
            'quantity': self.quantity,
            'price': self.price,
            'commission': self.commission,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class LocalFill:
    """Normalized representation of a local fill from logs"""
    fill_id: str
    order_id: int
    symbol: str
    side: str  # BUY or SELL
    quantity: int
    price: float
    commission: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'fill_id': self.fill_id,
            'order_id': self.order_id,
            'symbol': self.symbol,
            'side': self.side,
            'quantity': self.quantity,
            'price': self.price,
            'commission': self.commission,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class Discrepancy:
    """Represents a reconciliation discrepancy"""
    type: DiscrepancyType
    order_id: int
    symbol: str
    ibkr_fill: Optional[IBKRFill] = None
    local_fill: Optional[LocalFill] = None
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'type': self.type.value,
            'order_id': self.order_id,
            'symbol': self.symbol,
            'ibkr_fill': self.ibkr_fill.to_dict() if self.ibkr_fill else None,
            'local_fill': self.local_fill.to_dict() if self.local_fill else None,
            'description': self.description
        }


@dataclass
class ReconciliationReport:
    """Report from trade reconciliation"""
    reconciliation_date: date
    ibkr_fills: List[IBKRFill] = field(default_factory=list)
    local_fills: List[LocalFill] = field(default_factory=list)
    discrepancies: List[Discrepancy] = field(default_factory=list)
    matched_order_ids: Set[int] = field(default_factory=set)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def has_discrepancies(self) -> bool:
        """Check if there are any discrepancies"""
        return len(self.discrepancies) > 0
    
    def summary(self) -> Dict[str, Any]:
        """Generate summary statistics"""
        return {
            'reconciliation_date': self.reconciliation_date.isoformat(),
            'timestamp': self.timestamp.isoformat(),
            'total_ibkr_fills': len(self.ibkr_fills),
            'total_local_fills': len(self.local_fills),
            'matched_orders': len(self.matched_order_ids),
            'total_discrepancies': len(self.discrepancies),
            'discrepancy_types': {
                dtype.value: sum(1 for d in self.discrepancies if d.type == dtype)
                for dtype in DiscrepancyType
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert full report to dictionary"""
        return {
            'summary': self.summary(),
            'discrepancies': [d.to_dict() for d in self.discrepancies],
            'ibkr_fills': [f.to_dict() for f in self.ibkr_fills],
            'local_fills': [f.to_dict() for f in self.local_fills]
        }


class TradeReconciliation:
    """
    Reconciles local trade logs with IBKR account history.
    
    This class compares locally logged trades (from OrderLogger) with
    trades reported by IBKR to identify discrepancies for audit purposes.
    
    Example:
        >>> broker = IBKRBroker(paper_trading=True)
        >>> broker.connect()
        >>> reconciler = TradeReconciliation(broker)
        >>> report = reconciler.reconcile_today()
        >>> print(report.summary())
    """
    
    def __init__(self, broker, price_tolerance: float = 0.01, 
                 commission_tolerance: float = 0.01):
        """
        Initialize trade reconciliation.
        
        Args:
            broker: IBKRBroker instance (must be connected)
            price_tolerance: Maximum acceptable price difference (default: $0.01)
            commission_tolerance: Maximum acceptable commission difference (default: $0.01)
        """
        self.broker = broker
        self.price_tolerance = price_tolerance
        self.commission_tolerance = commission_tolerance
        
        logger.info(f"TradeReconciliation initialized with price_tolerance=${price_tolerance}, "
                   f"commission_tolerance=${commission_tolerance}")
    
    def fetch_ibkr_fills(self, start_date: Optional[date] = None) -> List[IBKRFill]:
        """
        Fetch fills from IBKR.
        
        Args:
            start_date: Optional start date (defaults to today)
            
        Returns:
            List of IBKRFill objects
        """
        if not self.broker.is_connected():
            raise RuntimeError("Broker must be connected to fetch IBKR fills")
        
        try:
            # Get fills from IBKR
            ib = self.broker.ib
            fills = ib.fills()
            
            # Filter by date if specified
            if start_date:
                fills = [
                    f for f in fills 
                    if f.time.date() >= start_date
                ]
            
            # Convert to normalized format
            ibkr_fills = []
            for fill in fills:
                try:
                    ibkr_fill = IBKRFill(
                        execution_id=fill.execution.execId,
                        order_id=fill.execution.orderId,
                        symbol=fill.contract.symbol,
                        side=fill.execution.side,
                        quantity=int(fill.execution.shares),
                        price=float(fill.execution.price),
                        commission=float(fill.commissionReport.commission) if fill.commissionReport else 0.0,
                        timestamp=fill.time,
                        raw_data=fill
                    )
                    ibkr_fills.append(ibkr_fill)
                except Exception as e:
                    logger.error(f"Error parsing IBKR fill: {e}", exc_info=True)
                    continue
            
            logger.info(f"Fetched {len(ibkr_fills)} fills from IBKR")
            return ibkr_fills
            
        except Exception as e:
            logger.error(f"Error fetching IBKR fills: {e}", exc_info=True)
            return []
    
    def fetch_local_fills(self, start_date: Optional[date] = None) -> List[LocalFill]:
        """
        Fetch fills from local order handler.
        
        Args:
            start_date: Optional start date filter
            
        Returns:
            List of LocalFill objects
        """
        if not self.broker.order_handler:
            logger.warning("Order handler not available, cannot fetch local fills")
            return []
        
        try:
            local_fills = []
            
            # Get all orders from order handler
            all_orders = self.broker.order_handler.get_all_orders()
            
            for order in all_orders:
                # Filter by date if specified
                if start_date and order.submission_time.date() < start_date:
                    continue
                
                # Process each fill in the order
                for fill in order.fills:
                    # Filter fill by date if specified
                    if start_date and fill.timestamp.date() < start_date:
                        continue
                    
                    local_fill = LocalFill(
                        fill_id=fill.fill_id,
                        order_id=order.order_id,
                        symbol=order.symbol,
                        side=order.action,
                        quantity=fill.quantity,
                        price=fill.price,
                        commission=fill.commission,
                        timestamp=fill.timestamp
                    )
                    local_fills.append(local_fill)
            
            logger.info(f"Fetched {len(local_fills)} fills from local logs")
            return local_fills
            
        except Exception as e:
            logger.error(f"Error fetching local fills: {e}", exc_info=True)
            return []
    
    def reconcile(self, target_date: date) -> ReconciliationReport:
        """
        Reconcile trades for a specific date.
        
        Algorithm:
        1. Fetch all IBKR fills for the date
        2. Fetch all local fills for the date
        3. Match fills by order_id
        4. For matched fills, compare quantity, price, and commission
        5. Identify missing fills in either system
        6. Generate reconciliation report
        
        Args:
            target_date: Date to reconcile
            
        Returns:
            ReconciliationReport with results
        """
        logger.info(f"Starting reconciliation for {target_date}")
        
        # Fetch fills from both sources
        ibkr_fills = self.fetch_ibkr_fills(start_date=target_date)
        local_fills = self.fetch_local_fills(start_date=target_date)
        
        # Filter to exact date
        ibkr_fills = [f for f in ibkr_fills if f.timestamp.date() == target_date]
        local_fills = [f for f in local_fills if f.timestamp.date() == target_date]
        
        # Initialize report
        report = ReconciliationReport(
            reconciliation_date=target_date,
            ibkr_fills=ibkr_fills,
            local_fills=local_fills
        )
        
        # Build lookup maps by order_id and execution_id
        ibkr_by_order: Dict[int, List[IBKRFill]] = {}
        for fill in ibkr_fills:
            if fill.order_id not in ibkr_by_order:
                ibkr_by_order[fill.order_id] = []
            ibkr_by_order[fill.order_id].append(fill)
        
        local_by_order: Dict[int, List[LocalFill]] = {}
        for fill in local_fills:
            if fill.order_id not in local_by_order:
                local_by_order[fill.order_id] = []
            local_by_order[fill.order_id].append(fill)
        
        # Get all order IDs from both sources
        all_order_ids = set(ibkr_by_order.keys()) | set(local_by_order.keys())
        
        # Compare fills for each order
        for order_id in all_order_ids:
            ibkr_order_fills = ibkr_by_order.get(order_id, [])
            local_order_fills = local_by_order.get(order_id, [])
            
            # Check for missing fills
            if not ibkr_order_fills and local_order_fills:
                # Order exists locally but not in IBKR
                for local_fill in local_order_fills:
                    report.discrepancies.append(Discrepancy(
                        type=DiscrepancyType.MISSING_IBKR,
                        order_id=order_id,
                        symbol=local_fill.symbol,
                        local_fill=local_fill,
                        description=f"Fill {local_fill.fill_id} exists in local logs but not in IBKR"
                    ))
            elif ibkr_order_fills and not local_order_fills:
                # Order exists in IBKR but not locally
                for ibkr_fill in ibkr_order_fills:
                    report.discrepancies.append(Discrepancy(
                        type=DiscrepancyType.MISSING_LOCAL,
                        order_id=order_id,
                        symbol=ibkr_fill.symbol,
                        ibkr_fill=ibkr_fill,
                        description=f"Fill {ibkr_fill.execution_id} exists in IBKR but not in local logs"
                    ))
            else:
                # Both exist, compare details
                # Simple matching: compare total quantities and prices
                ibkr_total_qty = sum(f.quantity for f in ibkr_order_fills)
                local_total_qty = sum(f.quantity for f in local_order_fills)
                
                ibkr_avg_price = sum(f.quantity * f.price for f in ibkr_order_fills) / ibkr_total_qty if ibkr_total_qty > 0 else 0
                local_avg_price = sum(f.quantity * f.price for f in local_order_fills) / local_total_qty if local_total_qty > 0 else 0
                
                ibkr_total_commission = sum(f.commission for f in ibkr_order_fills)
                local_total_commission = sum(f.commission for f in local_order_fills)
                
                symbol = ibkr_order_fills[0].symbol if ibkr_order_fills else local_order_fills[0].symbol
                
                # Check for quantity mismatch
                if ibkr_total_qty != local_total_qty:
                    report.discrepancies.append(Discrepancy(
                        type=DiscrepancyType.QUANTITY_MISMATCH,
                        order_id=order_id,
                        symbol=symbol,
                        ibkr_fill=ibkr_order_fills[0] if ibkr_order_fills else None,
                        local_fill=local_order_fills[0] if local_order_fills else None,
                        description=f"Quantity mismatch: IBKR={ibkr_total_qty}, Local={local_total_qty}"
                    ))
                
                # Check for price mismatch (within tolerance)
                if abs(ibkr_avg_price - local_avg_price) > self.price_tolerance:
                    report.discrepancies.append(Discrepancy(
                        type=DiscrepancyType.PRICE_MISMATCH,
                        order_id=order_id,
                        symbol=symbol,
                        ibkr_fill=ibkr_order_fills[0] if ibkr_order_fills else None,
                        local_fill=local_order_fills[0] if local_order_fills else None,
                        description=f"Price mismatch: IBKR=${ibkr_avg_price:.2f}, Local=${local_avg_price:.2f}"
                    ))
                
                # Check for commission mismatch (within tolerance)
                if abs(ibkr_total_commission - local_total_commission) > self.commission_tolerance:
                    report.discrepancies.append(Discrepancy(
                        type=DiscrepancyType.COMMISSION_MISMATCH,
                        order_id=order_id,
                        symbol=symbol,
                        ibkr_fill=ibkr_order_fills[0] if ibkr_order_fills else None,
                        local_fill=local_order_fills[0] if local_order_fills else None,
                        description=f"Commission mismatch: IBKR=${ibkr_total_commission:.2f}, Local=${local_total_commission:.2f}"
                    ))
                
                # If no discrepancies, mark as matched
                if not any(d.order_id == order_id for d in report.discrepancies):
                    report.matched_order_ids.add(order_id)
        
        logger.info(f"Reconciliation complete: {len(report.matched_order_ids)} matched, "
                   f"{len(report.discrepancies)} discrepancies")
        
        return report
    
    def reconcile_today(self) -> ReconciliationReport:
        """
        Reconcile trades for today.
        
        Returns:
            ReconciliationReport for today
        """
        return self.reconcile(date.today())
    
    def reconcile_date_range(self, start_date: date, end_date: date) -> List[ReconciliationReport]:
        """
        Reconcile trades for a date range.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            List of ReconciliationReport objects, one per day
        """
        reports = []
        current_date = start_date
        
        while current_date <= end_date:
            report = self.reconcile(current_date)
            reports.append(report)
            current_date += timedelta(days=1)
        
        return reports
