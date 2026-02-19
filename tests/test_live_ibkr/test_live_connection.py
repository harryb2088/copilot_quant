"""
Live connection tests for IBKR paper trading

These tests require an actual IB Gateway or TWS connection.
They are marked with @pytest.mark.live_api and skipped by default.
"""

import os

import pytest

from copilot_quant.brokers.interactive_brokers import IBKRBroker


@pytest.mark.integration
@pytest.mark.live_api
class TestLiveConnection:
    """Test live connection to IBKR paper trading account"""

    def test_live_connect(self):
        """Test connecting to live IB paper trading account"""
        # Get connection params from environment
        host = os.getenv("IB_HOST", "127.0.0.1")
        port = int(os.getenv("IB_PORT", "7497"))
        client_id = int(os.getenv("IB_CLIENT_ID", "1"))

        # Create broker
        broker = IBKRBroker(paper_trading=True, host=host, port=port, client_id=client_id)

        # Attempt connection
        try:
            result = broker.connect(timeout=10, retry_count=2)

            # Verify connection
            assert result is True, "Failed to connect to IBKR"
            assert broker.is_connected(), "Broker reports not connected"

            # Get account info to verify connection works
            balance = broker.get_account_balance()
            assert isinstance(balance, dict), "Failed to get account balance"
            assert "NetLiquidation" in balance, "Missing NetLiquidation in balance"

            print("\nConnected successfully!")
            print(f"Account Balance: ${balance.get('NetLiquidation', 'N/A')}")

        finally:
            # Always disconnect
            broker.disconnect()

    def test_live_account_info(self):
        """Test retrieving account information"""
        host = os.getenv("IB_HOST", "127.0.0.1")
        port = int(os.getenv("IB_PORT", "7497"))
        client_id = int(os.getenv("IB_CLIENT_ID", "1"))

        broker = IBKRBroker(paper_trading=True, host=host, port=port, client_id=client_id)

        try:
            broker.connect(timeout=10)

            # Get account summary
            balance = broker.get_account_balance()

            assert "NetLiquidation" in balance
            assert "TotalCashValue" in balance
            assert "BuyingPower" in balance

            # Verify values are numeric
            assert float(balance["NetLiquidation"]) > 0

            print("\nAccount Summary:")
            print(f"  Net Liquidation: ${balance['NetLiquidation']}")
            print(f"  Cash: ${balance['TotalCashValue']}")
            print(f"  Buying Power: ${balance['BuyingPower']}")

        finally:
            broker.disconnect()

    def test_live_positions(self):
        """Test retrieving positions from paper account"""
        host = os.getenv("IB_HOST", "127.0.0.1")
        port = int(os.getenv("IB_PORT", "7497"))
        client_id = int(os.getenv("IB_CLIENT_ID", "1"))

        broker = IBKRBroker(paper_trading=True, host=host, port=port, client_id=client_id)

        try:
            broker.connect(timeout=10)

            # Get positions
            positions = broker.ib.positions()

            assert isinstance(positions, list)

            print(f"\nCurrent Positions: {len(positions)}")
            for pos in positions:
                print(f"  {pos.contract.symbol}: {pos.position} shares @ ${pos.avgCost}")

        finally:
            broker.disconnect()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "live_api", "-s"])
