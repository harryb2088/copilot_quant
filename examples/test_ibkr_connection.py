"""
Example script to test Interactive Brokers paper trading connection.

This script demonstrates how to:
1. Connect to IB paper trading account
2. Retrieve account information
3. Get current positions
4. Place a test order (commented out for safety)

Prerequisites:
1. Install ib_insync: pip install ib_insync>=0.9.86
2. Have TWS or IB Gateway running
3. Enable API access in TWS/Gateway settings
4. Use paper trading mode (port 7497 for TWS, 4002 for Gateway)

Configuration (Optional):
    You can configure connection settings via .env file:
    - IB_HOST=127.0.0.1
    - IB_PORT=7497 (for paper trading with TWS)
    - IB_CLIENT_ID=1
    - IB_PAPER_ACCOUNT=DUB267514 (your paper account number)
    
    See .env.example for a template.

For detailed setup instructions, see: docs/ibkr_setup_guide.md
"""

import sys
from pathlib import Path
import os

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, will use system environment variables
    pass

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from copilot_quant.brokers.interactive_brokers import IBKRBroker
import logging

# Configure logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def main():
    """Main function to test IB paper trading connection"""
    
    print("\n" + "="*70)
    print("Interactive Brokers Paper Trading Connection Test")
    print("="*70 + "\n")
    
    # Configuration
    PAPER_TRADING = True  # Always use paper trading for safety
    USE_GATEWAY = False   # Set to True if using IB Gateway instead of TWS
    
    # Check if environment variables are set
    env_configured = bool(os.getenv('IB_HOST') or os.getenv('IB_PORT'))
    
    print("Configuration:")
    print(f"  Paper Trading: {PAPER_TRADING}")
    print(f"  Application: {'IB Gateway' if USE_GATEWAY else 'TWS'}")
    print(f"  Environment Variables: {'✓ Found (.env configured)' if env_configured else '✗ Not set (using defaults)'}")
    if env_configured:
        print(f"    IB_HOST: {os.getenv('IB_HOST', 'not set')}")
        print(f"    IB_PORT: {os.getenv('IB_PORT', 'not set')}")
        print(f"    IB_CLIENT_ID: {os.getenv('IB_CLIENT_ID', 'not set')}")
        if os.getenv('IB_PAPER_ACCOUNT'):
            print(f"    IB_PAPER_ACCOUNT: {os.getenv('IB_PAPER_ACCOUNT')}")
    else:
        print(f"  Using Default Port: {4002 if USE_GATEWAY and PAPER_TRADING else 7497 if PAPER_TRADING else 'N/A'}")
    print()
    
    # Create broker instance
    print("Step 1: Creating broker instance...")
    # Broker will automatically use environment variables if available
    broker = IBKRBroker(
        paper_trading=PAPER_TRADING,
        use_gateway=USE_GATEWAY
        # host, port, client_id will be read from .env if available
    )
    print("✓ Broker instance created")
    print(f"  Connecting to: {broker.host}:{broker.port} (Client ID: {broker.client_id})")
    print()
    
    # Connect to IBKR
    print("Step 2: Connecting to Interactive Brokers...")
    print("  (Make sure TWS or IB Gateway is running and API is enabled)")
    
    if not broker.connect(timeout=30, retry_count=3):
        print("\n❌ Failed to connect to IBKR")
        print("\nTroubleshooting:")
        print("  1. Is TWS or IB Gateway running?")
        print("  2. Is API access enabled? (File → Global Configuration → API)")
        print("  3. Is 'Enable ActiveX and Socket Clients' checked?")
        print("  4. Are you using the correct port?")
        print("     - TWS Paper Trading: 7497")
        print("     - TWS Live Trading: 7496")
        print("     - Gateway Paper Trading: 4002")
        print("     - Gateway Live Trading: 4001")
        print("\nSee docs/ibkr_setup_guide.md for detailed setup instructions.")
        return False
    
    print("✓ Connected successfully!")
    print()
    
    # Get account balance
    print("Step 3: Retrieving account balance...")
    balance = broker.get_account_balance()
    
    if balance:
        print("✓ Account Balance:")
        for key, value in balance.items():
            try:
                # Safely format numeric values
                value_float = float(value)
                print(f"     {key:20s}: ${value_float:15,.2f}")
            except (ValueError, TypeError):
                print(f"     {key:20s}: {value}")
    else:
        print("⚠️  Could not retrieve account balance")
    print()
    
    # Get positions
    print("Step 4: Retrieving current positions...")
    positions = broker.get_positions()
    
    if positions:
        print(f"✓ Found {len(positions)} position(s):")
        for pos in positions:
            print(f"     {pos['symbol']:10s}: {pos['position']:8.0f} shares "
                  f"@ ${pos['avg_cost']:10.2f} = ${pos['cost_basis']:12,.2f} (cost basis)")
    else:
        print("✓ No open positions")
    print()
    
    # Get open orders
    print("Step 5: Retrieving open orders...")
    orders = broker.get_open_orders()
    print(f"✓ Found {len(orders)} open order(s)")
    
    if orders:
        for order in orders:
            print(f"     Order {order.orderId}: {order.action} {order.totalQuantity} "
                  f"{order.contract.symbol}")
    print()
    
    # Example: Place a test order (COMMENTED OUT FOR SAFETY)
    print("Step 6: Order placement (example - disabled for safety)")
    print("  To enable, uncomment the code below and modify as needed.")
    print()
    
    # UNCOMMENT THE CODE BELOW TO TEST ORDER PLACEMENT
    # WARNING: This will place a REAL order in your paper trading account!
    
    # print("  Placing test market order: BUY 1 share of SPY...")
    # trade = broker.execute_market_order(
    #     symbol='SPY',
    #     quantity=1,
    #     side='buy'
    # )
    # 
    # if trade:
    #     print(f"  ✓ Order placed successfully!")
    #     print(f"     Order ID: {trade.order.orderId}")
    #     print(f"     Status: {trade.orderStatus.status}")
    #     
    #     # Wait a bit to see if order fills
    #     import time
    #     print("  Waiting 5 seconds for order to process...")
    #     time.sleep(5)
    #     
    #     # Check order status
    #     if trade.isDone():
    #         print(f"  ✓ Order completed: {trade.orderStatus.status}")
    #     else:
    #         print(f"  ⏳ Order still processing: {trade.orderStatus.status}")
    # else:
    #     print("  ❌ Failed to place order")
    
    # Disconnect
    print("Step 7: Disconnecting from IBKR...")
    broker.disconnect()
    print("✓ Disconnected")
    print()
    
    print("="*70)
    print("✅ All tests completed successfully!")
    print("="*70)
    print()
    print("Next steps:")
    print("  1. Review the account balance and positions above")
    print("  2. Uncomment the order placement code to test trading (optional)")
    print("  3. Integrate this into your trading strategy")
    print("  4. See docs/ibkr_setup_guide.md for more examples")
    print()
    
    return True


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
