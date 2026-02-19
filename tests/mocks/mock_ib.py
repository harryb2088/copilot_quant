"""
Mock Interactive Brokers API for testing

This module provides mock implementations of the ib_insync library's classes
for unit and integration testing without requiring an actual IB connection.
"""

import time
from typing import List, Dict, Optional, Any, Callable
from datetime import datetime
from unittest.mock import MagicMock
from enum import Enum


class MockOrderStatus(Enum):
    """Mock order status enum"""
    PendingSubmit = "PendingSubmit"
    PreSubmitted = "PreSubmitted"
    Submitted = "Submitted"
    Filled = "Filled"
    Cancelled = "Cancelled"
    Inactive = "Inactive"
    PendingCancel = "PendingCancel"


class MockContract:
    """Mock IB Contract"""
    def __init__(self, symbol: str = "AAPL", secType: str = "STK", exchange: str = "SMART", currency: str = "USD"):
        self.symbol = symbol
        self.secType = secType
        self.exchange = exchange
        self.currency = currency
        self.conId = hash(symbol) % 100000


class MockOrder:
    """Mock IB Order"""
    def __init__(self, orderId: int = 0, action: str = "BUY", totalQuantity: float = 100, orderType: str = "MKT"):
        self.orderId = orderId
        self.action = action
        self.totalQuantity = totalQuantity
        self.orderType = orderType
        self.lmtPrice = 0.0
        self.auxPrice = 0.0
        self.tif = "DAY"
        self.account = ""


class MockExecution:
    """Mock IB Execution"""
    def __init__(self, execId: str, orderId: int, shares: float, price: float, side: str):
        self.execId = execId
        self.orderId = orderId
        self.shares = shares
        self.price = price
        self.side = side
        self.time = datetime.now()


class MockCommissionReport:
    """Mock IB Commission Report"""
    def __init__(self, commission: float = 1.0):
        self.commission = commission
        self.currency = "USD"


class MockFill:
    """Mock IB Fill"""
    def __init__(self, execution: MockExecution, commission: float = 1.0):
        self.execution = execution
        self.commissionReport = MockCommissionReport(commission)
        self.time = datetime.now()


class MockOrderStatus:
    """Mock IB Order Status"""
    def __init__(self, status: str = "PreSubmitted"):
        self.status = status
        self.filled = 0.0
        self.remaining = 0.0
        self.avgFillPrice = 0.0
        self.lastFillPrice = 0.0


class MockTrade:
    """Mock IB Trade"""
    def __init__(self, contract: MockContract, order: MockOrder):
        self.contract = contract
        self.order = order
        self.orderStatus = MockOrderStatus()
        self.fills = []
        self.log = []
        
    def isDone(self) -> bool:
        """Check if trade is done"""
        return self.orderStatus.status in ["Filled", "Cancelled", "Inactive"]
    
    def isActive(self) -> bool:
        """Check if trade is active"""
        return not self.isDone()


class MockPosition:
    """Mock IB Position"""
    def __init__(self, account: str, contract: MockContract, position: float, avgCost: float):
        self.account = account
        self.contract = contract
        self.position = position
        self.avgCost = avgCost
        self.marketPrice = avgCost
        self.marketValue = position * avgCost
        self.unrealizedPNL = 0.0
        self.realizedPNL = 0.0


class MockAccountValue:
    """Mock IB Account Value"""
    def __init__(self, tag: str, value: str, currency: str = "USD", account: str = "DU123456"):
        self.tag = tag
        self.value = value
        self.currency = currency
        self.account = account


class MockTickerData:
    """Mock ticker data for market data"""
    def __init__(self, symbol: str, bid: float = 100.0, ask: float = 100.5, last: float = 100.25):
        self.contract = MockContract(symbol=symbol)
        self.bid = bid
        self.ask = ask
        self.last = last
        self.bidSize = 100
        self.askSize = 100
        self.lastSize = 100
        self.volume = 1000000
        self.time = datetime.now()


class MockEvent:
    """Mock event that supports += operator for callback registration"""
    def __init__(self):
        self._callbacks = []
    
    def __iadd__(self, callback: Callable):
        """Add callback to event"""
        if callback not in self._callbacks:
            self._callbacks.append(callback)
        return self
    
    def __isub__(self, callback: Callable):
        """Remove callback from event"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
        return self
    
    def emit(self, *args, **kwargs):
        """Emit event to all callbacks"""
        for callback in self._callbacks:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"Error in callback: {e}")


class MockIB:
    """
    Mock Interactive Brokers API for testing
    
    This mock simulates the ib_insync.IB class behavior for testing purposes.
    It provides configurable responses and can simulate various scenarios.
    """
    
    def __init__(self):
        self._connected = False
        self._orders: Dict[int, MockTrade] = {}
        self._positions: Dict[str, MockPosition] = {}
        self._account_values: Dict[str, MockAccountValue] = {}
        self._managed_accounts = ["DU123456"]
        self._next_order_id = 1
        self._auto_fill = True
        self._fill_delay = 0.1
        self._simulate_errors = False
        self._error_code = None
        self._connection_fail_count = 0
        self._max_connection_fails = 0
        
        # Mock events
        self.connectedEvent = MockEvent()
        self.disconnectedEvent = MockEvent()
        self.errorEvent = MockEvent()
        self.orderStatusEvent = MockEvent()
        self.execDetailsEvent = MockEvent()
        self.positionEvent = MockEvent()
        self.accountSummaryEvent = MockEvent()
        
        # Initialize default account values
        self._init_default_account()
    
    def _init_default_account(self):
        """Initialize default account values"""
        self._account_values = {
            'NetLiquidation': MockAccountValue('NetLiquidation', '100000.00'),
            'TotalCashValue': MockAccountValue('TotalCashValue', '95000.00'),
            'BuyingPower': MockAccountValue('BuyingPower', '400000.00'),
            'GrossPositionValue': MockAccountValue('GrossPositionValue', '5000.00'),
        }
    
    def connect(self, host: str = '127.0.0.1', port: int = 7497, clientId: int = 1, timeout: int = 30) -> None:
        """Mock connection to IB"""
        if self._max_connection_fails > 0 and self._connection_fail_count < self._max_connection_fails:
            self._connection_fail_count += 1
            raise ConnectionRefusedError(f"Connection refused (simulated failure {self._connection_fail_count})")
        
        self._connected = True
        self._connection_fail_count = 0
        self.connectedEvent.emit()
    
    def disconnect(self) -> None:
        """Mock disconnection from IB"""
        if self._connected:
            self._connected = False
            self.disconnectedEvent.emit()
    
    def isConnected(self) -> bool:
        """Check if connected"""
        return self._connected
    
    def managedAccounts(self) -> List[str]:
        """Get list of managed accounts"""
        return self._managed_accounts
    
    def reqIds(self, numIds: int = 1) -> int:
        """Request valid order IDs"""
        order_id = self._next_order_id
        self._next_order_id += numIds
        return order_id
    
    def placeOrder(self, contract: MockContract, order: MockOrder) -> MockTrade:
        """Place an order"""
        if not self._connected:
            raise RuntimeError("Not connected to IB")
        
        # Assign order ID if not set
        if order.orderId == 0:
            order.orderId = self.reqIds()
        
        # Create trade
        trade = MockTrade(contract, order)
        trade.orderStatus.status = "PreSubmitted"
        trade.orderStatus.remaining = order.totalQuantity
        self._orders[order.orderId] = trade
        
        # Emit order status event
        self.orderStatusEvent.emit(trade)
        
        # Simulate error if configured
        if self._simulate_errors and self._error_code:
            self.errorEvent.emit(order.orderId, self._error_code, "Simulated error", contract)
            return trade
        
        # Auto-fill if enabled
        if self._auto_fill:
            self._simulate_fill(trade)
        
        return trade
    
    def _simulate_fill(self, trade: MockTrade):
        """Simulate order fill after a delay"""
        def do_fill():
            time.sleep(self._fill_delay)
            if trade.order.orderId in self._orders:
                # Create execution
                execution = MockExecution(
                    execId=f"exec_{trade.order.orderId}",
                    orderId=trade.order.orderId,
                    shares=trade.order.totalQuantity,
                    price=100.0,  # Default fill price
                    side=trade.order.action
                )
                
                # Create fill
                fill = MockFill(execution)
                trade.fills.append(fill)
                
                # Update order status
                trade.orderStatus.status = "Filled"
                trade.orderStatus.filled = trade.order.totalQuantity
                trade.orderStatus.remaining = 0.0
                trade.orderStatus.avgFillPrice = 100.0
                
                # Emit events
                self.orderStatusEvent.emit(trade)
                self.execDetailsEvent.emit(trade, fill)
        
        # Run fill in background (simulated async)
        import threading
        threading.Thread(target=do_fill, daemon=True).start()
    
    def cancelOrder(self, order: MockOrder) -> None:
        """Cancel an order"""
        if order.orderId in self._orders:
            trade = self._orders[order.orderId]
            trade.orderStatus.status = "Cancelled"
            trade.orderStatus.remaining = 0.0
            self.orderStatusEvent.emit(trade)
    
    def reqPositions(self) -> List[MockPosition]:
        """Request all positions"""
        return list(self._positions.values())
    
    def positions(self) -> List[MockPosition]:
        """Get current positions"""
        return list(self._positions.values())
    
    def portfolio(self) -> List[MockPosition]:
        """Get portfolio positions"""
        return self.positions()
    
    def accountSummary(self, account: str = "") -> List[MockAccountValue]:
        """Get account summary"""
        return list(self._account_values.values())
    
    def accountValues(self, account: str = "") -> List[MockAccountValue]:
        """Get account values"""
        return list(self._account_values.values())
    
    def reqAccountSummary(self) -> None:
        """Request account summary"""
        for value in self._account_values.values():
            self.accountSummaryEvent.emit(value)
    
    def reqTickers(self, *contracts) -> List[MockTickerData]:
        """Request ticker data"""
        return [MockTickerData(c.symbol if hasattr(c, 'symbol') else 'AAPL') for c in contracts]
    
    def reqMarketDataType(self, marketDataType: int) -> None:
        """Request market data type"""
        pass
    
    def qualifyContracts(self, *contracts) -> List[MockContract]:
        """Qualify contracts"""
        return list(contracts)
    
    def openOrders(self) -> List[MockTrade]:
        """Get open orders"""
        return [t for t in self._orders.values() if t.isActive()]
    
    def openTrades(self) -> List[MockTrade]:
        """Get open trades"""
        return self.openOrders()
    
    def trades(self) -> List[MockTrade]:
        """Get all trades"""
        return list(self._orders.values())
    
    # Helper methods for testing
    
    def set_auto_fill(self, enabled: bool, delay: float = 0.1):
        """Configure auto-fill behavior"""
        self._auto_fill = enabled
        self._fill_delay = delay
    
    def set_error_simulation(self, enabled: bool, error_code: Optional[int] = None):
        """Configure error simulation"""
        self._simulate_errors = enabled
        self._error_code = error_code
    
    def set_connection_fail_count(self, count: int):
        """Set how many times connection should fail before succeeding"""
        self._max_connection_fails = count
        self._connection_fail_count = 0
    
    def add_position(self, symbol: str, quantity: float, avg_cost: float, account: str = "DU123456"):
        """Add a position to the mock broker"""
        contract = MockContract(symbol=symbol)
        position = MockPosition(account, contract, quantity, avg_cost)
        self._positions[symbol] = position
        return position
    
    def set_account_value(self, tag: str, value: str, currency: str = "USD"):
        """Set an account value"""
        self._account_values[tag] = MockAccountValue(tag, value, currency)
    
    def simulate_disconnect(self):
        """Simulate a disconnection"""
        if self._connected:
            self._connected = False
            self.disconnectedEvent.emit()
    
    def simulate_error(self, reqId: int, errorCode: int, errorString: str, contract=None):
        """Simulate an error"""
        self.errorEvent.emit(reqId, errorCode, errorString, contract)
    
    # Context manager support
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


# Mock contract and order factory functions
def Stock(symbol: str, exchange: str = "SMART", currency: str = "USD") -> MockContract:
    """Create a mock stock contract"""
    return MockContract(symbol=symbol, secType="STK", exchange=exchange, currency=currency)


def MarketOrder(action: str, totalQuantity: float, **kwargs) -> MockOrder:
    """Create a mock market order"""
    order = MockOrder(action=action, totalQuantity=totalQuantity, orderType="MKT")
    for key, value in kwargs.items():
        setattr(order, key, value)
    return order


def LimitOrder(action: str, totalQuantity: float, lmtPrice: float, **kwargs) -> MockOrder:
    """Create a mock limit order"""
    order = MockOrder(action=action, totalQuantity=totalQuantity, orderType="LMT")
    order.lmtPrice = lmtPrice
    for key, value in kwargs.items():
        setattr(order, key, value)
    return order
