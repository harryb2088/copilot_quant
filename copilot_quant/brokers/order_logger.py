"""
Order Logger for IBKR

Provides structured logging for all order-related events:
- Order submissions
- Fills (complete and partial)
- Status changes
- Cancellations
- Errors

Log format is designed for easy parsing and analysis.
"""

import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

from .order_execution_handler import OrderRecord, OrderStatus, Fill

logger = logging.getLogger(__name__)


class OrderLogger:
    """
    Structured logger for order events.
    
    Logs all order-related events in a structured format that can be
    easily parsed for analysis, auditing, and debugging.
    
    Example:
        >>> order_logger = OrderLogger(log_to_file=True, log_dir="./logs")
        >>> order_logger.log_submission(order_record)
        >>> order_logger.log_fill(order_record, fill)
    """
    
    def __init__(
        self,
        log_to_file: bool = True,
        log_dir: Optional[str] = None,
        log_to_console: bool = True
    ):
        """
        Initialize order logger.
        
        Args:
            log_to_file: If True, log to file in addition to standard logging
            log_dir: Directory for log files (default: ./logs/orders)
            log_to_console: If True, also log to console via standard logger
        """
        self.log_to_file = log_to_file
        self.log_to_console = log_to_console
        
        # Set up file logging if enabled
        self.file_logger = None
        if log_to_file:
            if log_dir is None:
                log_dir = "./logs/orders"
            
            self.log_dir = Path(log_dir)
            self.log_dir.mkdir(parents=True, exist_ok=True)
            
            # Create file logger
            log_file = self.log_dir / f"orders_{datetime.now().strftime('%Y%m%d')}.log"
            self.file_logger = logging.getLogger(f"{__name__}.file")
            self.file_logger.setLevel(logging.INFO)
            
            # Only add handler if not already present
            if not self.file_logger.handlers:
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(logging.INFO)
                formatter = logging.Formatter(
                    '%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                file_handler.setFormatter(formatter)
                self.file_logger.addHandler(file_handler)
        
        logger.info(f"OrderLogger initialized (file={log_to_file}, console={log_to_console})")
    
    def _log(self, event_type: str, data: Dict[str, Any]):
        """
        Internal logging method.
        
        Args:
            event_type: Type of event (submission, fill, status_change, etc.)
            data: Event data dictionary
        """
        # Add metadata
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            **data
        }
        
        # Convert to JSON string for structured logging
        json_log = json.dumps(log_entry)
        
        # Log to file
        if self.file_logger:
            self.file_logger.info(json_log)
            # Flush to ensure writes complete
            for handler in self.file_logger.handlers:
                handler.flush()
        
        # Log to console
        if self.log_to_console:
            logger.info(f"[{event_type}] {self._format_for_console(data)}")
    
    def _format_for_console(self, data: Dict[str, Any]) -> str:
        """Format log data for human-readable console output"""
        if 'order_id' in data and 'symbol' in data:
            parts = [f"Order {data['order_id']}", f"{data['symbol']}"]
            if 'action' in data:
                parts.append(data['action'])
            if 'quantity' in data:
                parts.append(f"{data['quantity']} shares")
            if 'price' in data:
                parts.append(f"@ ${data['price']:.2f}")
            if 'status' in data:
                parts.append(f"[{data['status']}]")
            return " ".join(parts)
        return str(data)
    
    def log_submission(self, order_record: OrderRecord):
        """
        Log order submission.
        
        Args:
            order_record: Order that was submitted
        """
        data = {
            'order_id': order_record.order_id,
            'symbol': order_record.symbol,
            'action': order_record.action,
            'quantity': order_record.total_quantity,
            'order_type': order_record.order_type,
            'limit_price': order_record.limit_price,
            'status': order_record.status.value,
            'submission_time': order_record.submission_time.isoformat()
        }
        self._log('SUBMISSION', data)
    
    def log_fill(self, order_record: OrderRecord, fill: Fill):
        """
        Log a fill (complete or partial).
        
        Args:
            order_record: Order that was filled
            fill: Fill details
        """
        is_complete = order_record.status == OrderStatus.FILLED
        
        data = {
            'order_id': order_record.order_id,
            'fill_id': fill.fill_id,
            'symbol': order_record.symbol,
            'action': order_record.action,
            'fill_quantity': fill.quantity,
            'fill_price': fill.price,
            'commission': fill.commission,
            'filled_quantity': order_record.filled_quantity,
            'total_quantity': order_record.total_quantity,
            'remaining_quantity': order_record.remaining_quantity,
            'avg_fill_price': order_record.avg_fill_price,
            'fill_type': 'COMPLETE' if is_complete else 'PARTIAL',
            'fill_time': fill.timestamp.isoformat()
        }
        self._log('FILL', data)
    
    def log_status_change(
        self,
        order_record: OrderRecord,
        old_status: OrderStatus,
        new_status: OrderStatus
    ):
        """
        Log order status change.
        
        Args:
            order_record: Order with status change
            old_status: Previous status
            new_status: New status
        """
        data = {
            'order_id': order_record.order_id,
            'symbol': order_record.symbol,
            'old_status': old_status.value,
            'new_status': new_status.value,
            'filled_quantity': order_record.filled_quantity,
            'total_quantity': order_record.total_quantity
        }
        self._log('STATUS_CHANGE', data)
    
    def log_cancellation(self, order_record: OrderRecord, reason: Optional[str] = None):
        """
        Log order cancellation.
        
        Args:
            order_record: Cancelled order
            reason: Optional cancellation reason
        """
        data = {
            'order_id': order_record.order_id,
            'symbol': order_record.symbol,
            'action': order_record.action,
            'total_quantity': order_record.total_quantity,
            'filled_quantity': order_record.filled_quantity,
            'reason': reason or 'User requested'
        }
        self._log('CANCELLATION', data)
    
    def log_error(self, order_record: OrderRecord, error_message: str):
        """
        Log order error.
        
        Args:
            order_record: Order that encountered error
            error_message: Error description
        """
        data = {
            'order_id': order_record.order_id,
            'symbol': order_record.symbol,
            'action': order_record.action,
            'quantity': order_record.total_quantity,
            'order_type': order_record.order_type,
            'error_message': error_message,
            'retry_count': order_record.retry_count
        }
        self._log('ERROR', data)
    
    def log_retry(self, order_record: OrderRecord, retry_delay: float):
        """
        Log order retry attempt.
        
        Args:
            order_record: Order being retried
            retry_delay: Delay before retry in seconds
        """
        data = {
            'order_id': order_record.order_id,
            'symbol': order_record.symbol,
            'retry_count': order_record.retry_count,
            'retry_delay_seconds': retry_delay,
            'error_message': order_record.error_message
        }
        self._log('RETRY', data)
    
    def log_event(self, event_type: str, order_record: OrderRecord, details: Optional[Dict[str, Any]] = None):
        """
        Log generic order event.
        
        Args:
            event_type: Custom event type
            order_record: Related order
            details: Additional event details
        """
        data = {
            'order_id': order_record.order_id,
            'symbol': order_record.symbol,
            'status': order_record.status.value,
            **(details or {})
        }
        self._log(event_type, data)
    
    def get_order_history(self, order_id: int) -> List[str]:
        """
        Get all log entries for a specific order.
        
        Args:
            order_id: Order ID to search for
            
        Returns:
            List of log lines for the order
        """
        if not self.file_logger or not self.file_logger.handlers:
            logger.warning("File logging not enabled, cannot retrieve history")
            return []
        
        # Get log file path from handler
        log_file = Path(self.file_logger.handlers[0].baseFilename)
        
        if not log_file.exists():
            return []
        
        order_logs = []
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    if f'"order_id": {order_id}' in line or f'"order_id":{order_id}' in line:
                        order_logs.append(line.strip())
        except Exception as e:
            logger.error(f"Error reading log file: {e}", exc_info=True)
        
        return order_logs
    
    def get_todays_summary(self) -> Dict[str, Any]:
        """
        Get summary of today's order activity.
        
        Returns:
            Dictionary with order statistics
        """
        if not self.file_logger or not self.file_logger.handlers:
            logger.warning("File logging not enabled, cannot generate summary")
            return {}
        
        log_file = Path(self.file_logger.handlers[0].baseFilename)
        
        if not log_file.exists():
            return {
                'total_orders': 0,
                'filled_orders': 0,
                'cancelled_orders': 0,
                'error_orders': 0,
                'total_fills': 0,
                'partial_fills': 0,
                'complete_fills': 0
            }
        
        stats = {
            'total_orders': 0,
            'filled_orders': 0,
            'cancelled_orders': 0,
            'error_orders': 0,
            'total_fills': 0,
            'partial_fills': 0,
            'complete_fills': 0
        }
        
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        # Extract JSON part (after timestamp and level)
                        json_start = line.find('{')
                        if json_start == -1:
                            continue
                        
                        log_entry = json.loads(line[json_start:])
                        event_type = log_entry.get('event_type')
                        
                        if event_type == 'SUBMISSION':
                            stats['total_orders'] += 1
                        elif event_type == 'FILL':
                            stats['total_fills'] += 1
                            if log_entry.get('fill_type') == 'COMPLETE':
                                stats['complete_fills'] += 1
                                stats['filled_orders'] += 1
                            else:
                                stats['partial_fills'] += 1
                        elif event_type == 'CANCELLATION':
                            stats['cancelled_orders'] += 1
                        elif event_type == 'ERROR':
                            stats['error_orders'] += 1
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Error reading log file for summary: {e}", exc_info=True)
        
        return stats
