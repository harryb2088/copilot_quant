"""Tests for order management system."""

from datetime import datetime

import pytest

from copilot_quant.backtest.orders import Fill, Order, Position


class TestOrder:
    """Tests for Order class."""

    def test_order_creation_market_buy(self):
        """Test creating a market buy order."""
        order = Order(symbol="AAPL", quantity=100, order_type="market", side="buy")

        assert order.symbol == "AAPL"
        assert order.quantity == 100
        assert order.order_type == "market"
        assert order.side == "buy"
        assert order.limit_price is None

    def test_order_creation_limit_sell(self):
        """Test creating a limit sell order."""
        order = Order(symbol="MSFT", quantity=50, order_type="limit", side="sell", limit_price=350.0)

        assert order.symbol == "MSFT"
        assert order.quantity == 50
        assert order.order_type == "limit"
        assert order.side == "sell"
        assert order.limit_price == 350.0

    def test_order_invalid_type(self):
        """Test that invalid order type raises error."""
        with pytest.raises(ValueError, match="Invalid order_type"):
            Order(
                symbol="AAPL",
                quantity=100,
                order_type="stop",  # Invalid
                side="buy",
            )

    def test_order_invalid_side(self):
        """Test that invalid side raises error."""
        with pytest.raises(ValueError, match="Invalid side"):
            Order(
                symbol="AAPL",
                quantity=100,
                order_type="market",
                side="hold",  # Invalid
            )

    def test_order_zero_quantity(self):
        """Test that zero quantity raises error."""
        with pytest.raises(ValueError, match="Invalid quantity"):
            Order(symbol="AAPL", quantity=0, order_type="market", side="buy")

    def test_order_negative_quantity(self):
        """Test that negative quantity raises error."""
        with pytest.raises(ValueError, match="Invalid quantity"):
            Order(symbol="AAPL", quantity=-100, order_type="market", side="buy")

    def test_limit_order_without_price(self):
        """Test that limit order without price raises error."""
        with pytest.raises(ValueError, match="Limit orders must have a limit_price"):
            Order(symbol="AAPL", quantity=100, order_type="limit", side="buy")

    def test_limit_order_negative_price(self):
        """Test that limit order with negative price raises error."""
        with pytest.raises(ValueError, match="Invalid limit_price"):
            Order(symbol="AAPL", quantity=100, order_type="limit", side="buy", limit_price=-150.0)


class TestFill:
    """Tests for Fill class."""

    @pytest.fixture
    def buy_order(self):
        """Create a sample buy order."""
        return Order(symbol="AAPL", quantity=100, order_type="market", side="buy")

    @pytest.fixture
    def sell_order(self):
        """Create a sample sell order."""
        return Order(symbol="AAPL", quantity=100, order_type="market", side="sell")

    def test_fill_creation(self, buy_order):
        """Test creating a fill."""
        fill = Fill(
            order=buy_order, fill_price=150.0, fill_quantity=100, commission=15.0, timestamp=datetime(2024, 1, 1, 10, 0)
        )

        assert fill.order == buy_order
        assert fill.fill_price == 150.0
        assert fill.fill_quantity == 100
        assert fill.commission == 15.0

    def test_fill_total_cost_buy(self, buy_order):
        """Test total cost calculation for buy fill."""
        fill = Fill(
            order=buy_order, fill_price=150.0, fill_quantity=100, commission=15.0, timestamp=datetime(2024, 1, 1)
        )

        # Cost = price * quantity + commission
        expected_cost = 150.0 * 100 + 15.0
        assert fill.total_cost == expected_cost

    def test_fill_total_cost_sell(self, sell_order):
        """Test total cost calculation for sell fill."""
        fill = Fill(
            order=sell_order, fill_price=150.0, fill_quantity=100, commission=15.0, timestamp=datetime(2024, 1, 1)
        )

        # Cost = price * quantity - commission
        expected_cost = 150.0 * 100 - 15.0
        assert fill.total_cost == expected_cost

    def test_fill_net_proceeds_buy(self, buy_order):
        """Test net proceeds for buy fill (negative)."""
        fill = Fill(
            order=buy_order, fill_price=150.0, fill_quantity=100, commission=15.0, timestamp=datetime(2024, 1, 1)
        )

        # Proceeds are negative for buys
        expected_proceeds = -(150.0 * 100 + 15.0)
        assert fill.net_proceeds == expected_proceeds

    def test_fill_net_proceeds_sell(self, sell_order):
        """Test net proceeds for sell fill (positive)."""
        fill = Fill(
            order=sell_order, fill_price=150.0, fill_quantity=100, commission=15.0, timestamp=datetime(2024, 1, 1)
        )

        # Proceeds are positive for sells
        expected_proceeds = 150.0 * 100 - 15.0
        assert fill.net_proceeds == expected_proceeds

    def test_fill_invalid_price(self, buy_order):
        """Test that negative fill price raises error."""
        with pytest.raises(ValueError, match="Invalid fill_price"):
            Fill(order=buy_order, fill_price=-150.0, fill_quantity=100, commission=15.0, timestamp=datetime(2024, 1, 1))

    def test_fill_invalid_quantity(self, buy_order):
        """Test that negative fill quantity raises error."""
        with pytest.raises(ValueError, match="Invalid fill_quantity"):
            Fill(order=buy_order, fill_price=150.0, fill_quantity=-100, commission=15.0, timestamp=datetime(2024, 1, 1))

    def test_fill_invalid_commission(self, buy_order):
        """Test that negative commission raises error."""
        with pytest.raises(ValueError, match="Invalid commission"):
            Fill(order=buy_order, fill_price=150.0, fill_quantity=100, commission=-15.0, timestamp=datetime(2024, 1, 1))


class TestPosition:
    """Tests for Position class."""

    def test_position_creation(self):
        """Test creating an empty position."""
        pos = Position(symbol="AAPL")

        assert pos.symbol == "AAPL"
        assert pos.quantity == 0.0
        assert pos.avg_entry_price == 0.0
        assert pos.unrealized_pnl == 0.0
        assert pos.realized_pnl == 0.0

    def test_position_open_long(self):
        """Test opening a long position."""
        pos = Position(symbol="AAPL")

        buy_order = Order(symbol="AAPL", quantity=100, order_type="market", side="buy")
        fill = Fill(
            order=buy_order, fill_price=150.0, fill_quantity=100, commission=15.0, timestamp=datetime(2024, 1, 1)
        )

        pos.update_from_fill(fill, current_price=150.0)

        assert pos.quantity == 100
        assert pos.avg_entry_price == 150.0
        assert pos.unrealized_pnl == 0.0  # Flat at entry price

    def test_position_increase_long(self):
        """Test increasing a long position."""
        pos = Position(symbol="AAPL", quantity=100, avg_entry_price=150.0)

        buy_order = Order(symbol="AAPL", quantity=50, order_type="market", side="buy")
        fill = Fill(order=buy_order, fill_price=160.0, fill_quantity=50, commission=8.0, timestamp=datetime(2024, 1, 2))

        pos.update_from_fill(fill, current_price=160.0)

        assert pos.quantity == 150
        # Average price = (100*150 + 50*160) / 150 = 23000/150 = 153.33
        assert abs(pos.avg_entry_price - 153.33) < 0.01

    def test_position_close_long(self):
        """Test closing a long position with profit."""
        pos = Position(symbol="AAPL", quantity=100, avg_entry_price=150.0)

        sell_order = Order(symbol="AAPL", quantity=100, order_type="market", side="sell")
        fill = Fill(
            order=sell_order, fill_price=160.0, fill_quantity=100, commission=16.0, timestamp=datetime(2024, 1, 2)
        )

        pos.update_from_fill(fill, current_price=160.0)

        assert pos.quantity == 0
        # Profit = (160 - 150) * 100 - 16 = 1000 - 16 = 984
        assert abs(pos.realized_pnl - 984.0) < 0.01

    def test_position_partial_close_long(self):
        """Test partially closing a long position."""
        pos = Position(symbol="AAPL", quantity=100, avg_entry_price=150.0)

        sell_order = Order(symbol="AAPL", quantity=50, order_type="market", side="sell")
        fill = Fill(
            order=sell_order, fill_price=160.0, fill_quantity=50, commission=8.0, timestamp=datetime(2024, 1, 2)
        )

        pos.update_from_fill(fill, current_price=160.0)

        assert pos.quantity == 50
        assert pos.avg_entry_price == 150.0  # Entry price unchanged
        # Profit on 50 shares = (160 - 150) * 50 - 8 = 500 - 8 = 492
        assert abs(pos.realized_pnl - 492.0) < 0.01

    def test_position_open_short(self):
        """Test opening a short position."""
        pos = Position(symbol="AAPL")

        sell_order = Order(symbol="AAPL", quantity=100, order_type="market", side="sell")
        fill = Fill(
            order=sell_order, fill_price=150.0, fill_quantity=100, commission=15.0, timestamp=datetime(2024, 1, 1)
        )

        pos.update_from_fill(fill, current_price=150.0)

        assert pos.quantity == -100
        assert pos.avg_entry_price == 150.0
        assert pos.unrealized_pnl == 0.0

    def test_position_close_short_profit(self):
        """Test closing a short position with profit."""
        pos = Position(symbol="AAPL", quantity=-100, avg_entry_price=150.0)

        buy_order = Order(symbol="AAPL", quantity=100, order_type="market", side="buy")
        fill = Fill(
            order=buy_order,
            fill_price=140.0,  # Bought back cheaper
            fill_quantity=100,
            commission=14.0,
            timestamp=datetime(2024, 1, 2),
        )

        pos.update_from_fill(fill, current_price=140.0)

        assert pos.quantity == 0
        # Profit = (150 - 140) * 100 - 14 = 1000 - 14 = 986
        assert abs(pos.realized_pnl - 986.0) < 0.01

    def test_position_update_unrealized_pnl(self):
        """Test updating unrealized PnL."""
        pos = Position(symbol="AAPL", quantity=100, avg_entry_price=150.0)

        # Price goes up
        pos.update_unrealized_pnl(160.0)
        assert pos.unrealized_pnl == 1000.0  # (160 - 150) * 100

        # Price goes down
        pos.update_unrealized_pnl(145.0)
        assert pos.unrealized_pnl == -500.0  # (145 - 150) * 100

    def test_position_total_pnl(self):
        """Test total PnL calculation."""
        pos = Position(symbol="AAPL", quantity=100, avg_entry_price=150.0)
        pos.realized_pnl = 500.0
        pos.unrealized_pnl = 300.0

        assert pos.total_pnl == 800.0

    def test_position_market_value(self):
        """Test market value calculation."""
        pos = Position(symbol="AAPL", quantity=100, avg_entry_price=150.0)
        pos.update_unrealized_pnl(160.0)

        # Market value = cost basis + unrealized PnL
        # Cost basis = 150 * 100 = 15000
        # Unrealized PnL = 1000
        # Market value = 16000
        assert pos.market_value == 16000.0
