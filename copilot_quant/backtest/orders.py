"""
Order management system for backtesting.

This module defines order types, fills, and positions used in the backtesting engine.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Order:
    """
    Represents a trading order.
    
    Attributes:
        symbol: Ticker symbol (e.g., 'AAPL', 'SPY')
        quantity: Number of shares/contracts (positive for buy, negative for sell)
        order_type: Type of order ('market', 'limit')
        side: Order side ('buy', 'sell')
        limit_price: Limit price for limit orders (None for market orders)
        timestamp: Time when order was created
        order_id: Unique identifier for the order
    """
    symbol: str
    quantity: float
    order_type: str  # 'market', 'limit'
    side: str  # 'buy', 'sell'
    limit_price: Optional[float] = None
    timestamp: Optional[datetime] = None
    order_id: Optional[str] = None
    
    def __post_init__(self):
        """Validate order after initialization."""
        if self.order_type not in ['market', 'limit']:
            raise ValueError(f"Invalid order_type: {self.order_type}. Must be 'market' or 'limit'")
        
        if self.side not in ['buy', 'sell']:
            raise ValueError(f"Invalid side: {self.side}. Must be 'buy' or 'sell'")
        
        if self.quantity <= 0:
            raise ValueError(f"Invalid quantity: {self.quantity}. Must be positive")
        
        if self.order_type == 'limit' and self.limit_price is None:
            raise ValueError("Limit orders must have a limit_price")
        
        if self.order_type == 'limit' and self.limit_price <= 0:
            raise ValueError(f"Invalid limit_price: {self.limit_price}. Must be positive")


@dataclass
class Fill:
    """
    Represents a filled order.
    
    Attributes:
        order: The original order that was filled
        fill_price: Price at which the order was filled
        fill_quantity: Quantity that was filled
        commission: Commission paid for this fill
        timestamp: Time when order was filled
        fill_id: Unique identifier for the fill
    """
    order: Order
    fill_price: float
    fill_quantity: float
    commission: float
    timestamp: datetime
    fill_id: Optional[str] = None
    
    def __post_init__(self):
        """Validate fill after initialization."""
        if self.fill_price <= 0:
            raise ValueError(f"Invalid fill_price: {self.fill_price}. Must be positive")
        
        if self.fill_quantity <= 0:
            raise ValueError(f"Invalid fill_quantity: {self.fill_quantity}. Must be positive")
        
        if self.commission < 0:
            raise ValueError(f"Invalid commission: {self.commission}. Must be non-negative")
    
    @property
    def total_cost(self) -> float:
        """Calculate total cost of fill including commission."""
        cost = self.fill_price * self.fill_quantity
        if self.order.side == 'buy':
            return cost + self.commission
        else:  # sell
            return cost - self.commission
    
    @property
    def net_proceeds(self) -> float:
        """Calculate net proceeds (positive for sells, negative for buys)."""
        if self.order.side == 'buy':
            return -(self.fill_price * self.fill_quantity + self.commission)
        else:  # sell
            return self.fill_price * self.fill_quantity - self.commission


@dataclass
class Position:
    """
    Represents a position in a security.
    
    Attributes:
        symbol: Ticker symbol
        quantity: Current position size (positive = long, negative = short)
        avg_entry_price: Average price at which position was entered
        unrealized_pnl: Current unrealized profit/loss
        realized_pnl: Cumulative realized profit/loss from closed trades
    """
    symbol: str
    quantity: float = 0.0
    avg_entry_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    
    def update_from_fill(self, fill: Fill, current_price: Optional[float] = None) -> None:
        """
        Update position based on a fill.
        
        Args:
            fill: The fill to process
            current_price: Current market price for unrealized PnL calculation
        """
        if fill.order.side == 'buy':
            # Adding to position
            if self.quantity >= 0:
                # Increasing long position or opening long from flat
                total_cost = self.avg_entry_price * self.quantity + fill.fill_price * fill.fill_quantity
                self.quantity += fill.fill_quantity
                self.avg_entry_price = total_cost / self.quantity if self.quantity > 0 else 0.0
            else:
                # Reducing short position
                if fill.fill_quantity > abs(self.quantity):
                    # Closing short and opening long
                    pnl_per_share = self.avg_entry_price - fill.fill_price
                    self.realized_pnl += pnl_per_share * abs(self.quantity) - fill.commission
                    
                    remaining = fill.fill_quantity - abs(self.quantity)
                    self.quantity = remaining
                    self.avg_entry_price = fill.fill_price
                else:
                    # Just reducing short position
                    pnl_per_share = self.avg_entry_price - fill.fill_price
                    self.realized_pnl += pnl_per_share * fill.fill_quantity - fill.commission
                    self.quantity += fill.fill_quantity
                    
        else:  # sell
            # Reducing position
            if self.quantity > 0:
                # Reducing long position
                if fill.fill_quantity > self.quantity:
                    # Closing long and opening short
                    pnl_per_share = fill.fill_price - self.avg_entry_price
                    self.realized_pnl += pnl_per_share * self.quantity - fill.commission
                    
                    remaining = fill.fill_quantity - self.quantity
                    self.quantity = -remaining
                    self.avg_entry_price = fill.fill_price
                else:
                    # Just reducing long position
                    pnl_per_share = fill.fill_price - self.avg_entry_price
                    self.realized_pnl += pnl_per_share * fill.fill_quantity - fill.commission
                    self.quantity -= fill.fill_quantity
            else:
                # Adding to short position or opening short from flat
                total_cost = self.avg_entry_price * abs(self.quantity) + fill.fill_price * fill.fill_quantity
                self.quantity -= fill.fill_quantity
                self.avg_entry_price = total_cost / abs(self.quantity) if self.quantity != 0 else 0.0
        
        # Update unrealized PnL if current price provided
        if current_price is not None:
            self.update_unrealized_pnl(current_price)
    
    def update_unrealized_pnl(self, current_price: float) -> None:
        """
        Update unrealized PnL based on current market price.
        
        Args:
            current_price: Current market price
        """
        if self.quantity == 0:
            self.unrealized_pnl = 0.0
        else:
            self.unrealized_pnl = (current_price - self.avg_entry_price) * self.quantity
    
    @property
    def total_pnl(self) -> float:
        """Total profit/loss (realized + unrealized)."""
        return self.realized_pnl + self.unrealized_pnl
    
    @property
    def market_value(self) -> float:
        """Current market value of the position (requires current price via unrealized_pnl update)."""
        # Market value is the unrealized PnL plus the cost basis
        if self.quantity == 0:
            return 0.0
        cost_basis = self.avg_entry_price * abs(self.quantity)
        return cost_basis + self.unrealized_pnl
