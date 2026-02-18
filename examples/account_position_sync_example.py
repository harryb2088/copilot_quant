#!/usr/bin/env python3
"""
Example: Using IBKR Account and Position Managers

This script demonstrates how to use the new AccountManager and PositionManager
for real-time account and position synchronization.

Prerequisites:
- TWS or IB Gateway running
- API connections enabled
- Paper trading account connected

Usage:
    python examples/account_position_sync_example.py
"""

import logging
import time
from copilot_quant.brokers import (
    IBKRBroker,
    IBKRAccountManager,
    IBKRPositionManager
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def print_separator(title=""):
    """Print a separator line with optional title"""
    if title:
        print(f"\n{'='*60}")
        print(f" {title}")
        print(f"{'='*60}\n")
    else:
        print(f"{'='*60}\n")


def account_update_callback(summary):
    """Callback for account updates"""
    logger.info(
        f"Account Updated - Net Liq: ${summary.net_liquidation:,.2f}, "
        f"Buying Power: ${summary.buying_power:,.2f}, "
        f"Unrealized P&L: ${summary.unrealized_pnl:+,.2f}"
    )


def position_update_callback(positions):
    """Callback for position updates"""
    logger.info(f"Positions Updated - {len(positions)} positions")
    for pos in positions:
        logger.info(
            f"  {pos.symbol}: {pos.quantity} shares @ ${pos.avg_cost:.2f}, "
            f"P&L: ${pos.unrealized_pnl:+,.2f}"
        )


def main():
    """Main example function"""
    
    print_separator("IBKR Account & Position Sync Example")
    
    # Initialize broker with managers enabled
    print("Initializing IBKR broker...")
    broker = IBKRBroker(
        paper_trading=True,
        enable_account_manager=True,
        enable_position_manager=True
    )
    
    # Connect to IBKR
    print("Connecting to IBKR...")
    if not broker.connect():
        print("❌ Failed to connect to IBKR")
        print("\nPlease ensure:")
        print("  1. TWS or IB Gateway is running")
        print("  2. API connections are enabled")
        print("  3. Port 7497 is accessible (paper trading)")
        return
    
    print("✅ Connected successfully!\n")
    
    # Get managers
    account_mgr = broker.account_manager
    position_mgr = broker.position_manager
    
    # ========================================================================
    # Part 1: Display Initial Account Summary
    # ========================================================================
    
    print_separator("Account Summary")
    
    summary = account_mgr.get_account_summary()
    if summary:
        print(f"Account ID: {summary.account_id}")
        print(f"Net Liquidation: ${summary.net_liquidation:,.2f}")
        print(f"Total Cash: ${summary.total_cash_value:,.2f}")
        print(f"Buying Power: ${summary.buying_power:,.2f}")
        print(f"Unrealized P&L: ${summary.unrealized_pnl:+,.2f}")
        print(f"Realized P&L: ${summary.realized_pnl:+,.2f}")
        print(f"Margin Available: ${summary.margin_available:,.2f}")
        print(f"Gross Position Value: ${summary.gross_position_value:,.2f}")
    else:
        print("⚠️  Could not retrieve account summary")
    
    # ========================================================================
    # Part 2: Display Current Positions
    # ========================================================================
    
    print_separator("Current Positions")
    
    positions = position_mgr.get_positions()
    if positions:
        print(f"Found {len(positions)} positions:\n")
        
        total_value = 0.0
        total_pnl = 0.0
        
        for pos in positions:
            print(f"Symbol: {pos.symbol}")
            print(f"  Quantity: {pos.quantity} shares")
            print(f"  Avg Cost: ${pos.avg_cost:.2f}")
            print(f"  Cost Basis: ${pos.cost_basis:,.2f}")
            if pos.market_price > 0:
                print(f"  Market Price: ${pos.market_price:.2f}")
                print(f"  Market Value: ${pos.market_value:,.2f}")
                print(f"  Unrealized P&L: ${pos.unrealized_pnl:+,.2f} ({pos.pnl_percentage:+.2f}%)")
            print()
            
            total_value += pos.market_value
            total_pnl += pos.unrealized_pnl
        
        print(f"Portfolio Summary:")
        print(f"  Total Market Value: ${total_value:,.2f}")
        print(f"  Total Unrealized P&L: ${total_pnl:+,.2f}")
        
        # Show long/short breakdown
        long_positions = position_mgr.get_long_positions()
        short_positions = position_mgr.get_short_positions()
        print(f"  Long Positions: {len(long_positions)}")
        print(f"  Short Positions: {len(short_positions)}")
    else:
        print("No open positions")
    
    # ========================================================================
    # Part 3: Get All Account Values
    # ========================================================================
    
    print_separator("All Account Values")
    
    all_values = account_mgr.get_all_account_values()
    print(f"Found {len(all_values)} account value tags:")
    
    # Display some key values
    key_tags = [
        'NetLiquidation',
        'TotalCashValue',
        'BuyingPower',
        'GrossPositionValue',
        'UnrealizedPnL',
        'RealizedPnL',
        'AvailableFunds',
        'ExcessLiquidity'
    ]
    
    for tag in key_tags:
        if tag in all_values:
            value = all_values[tag]
            if isinstance(value, (int, float)):
                print(f"  {tag}: ${value:,.2f}")
            else:
                print(f"  {tag}: {value}")
    
    # ========================================================================
    # Part 4: Register Callbacks and Monitor Changes
    # ========================================================================
    
    print_separator("Real-Time Monitoring")
    
    # Register callbacks
    account_mgr.register_update_callback(account_update_callback)
    position_mgr.register_update_callback(position_update_callback)
    
    # Start real-time monitoring
    print("Starting real-time monitoring...")
    if broker.start_real_time_monitoring():
        print("✅ Real-time monitoring started")
        print("\nMonitoring for 30 seconds...")
        print("(Try making changes in TWS to see real-time updates)\n")
        
        # Monitor for 30 seconds
        try:
            time.sleep(30)
        except KeyboardInterrupt:
            print("\n\nMonitoring interrupted by user")
        
        # Stop monitoring
        print("\nStopping real-time monitoring...")
        broker.stop_real_time_monitoring()
        print("✅ Monitoring stopped")
    else:
        print("⚠️  Could not start real-time monitoring")
    
    # ========================================================================
    # Part 5: View Change Logs
    # ========================================================================
    
    print_separator("Recent Changes")
    
    # Account changes
    account_changes = account_mgr.get_change_log(max_entries=10)
    if account_changes:
        print(f"Recent account changes ({len(account_changes)}):")
        for change in account_changes[-5:]:  # Last 5
            print(f"  {change['timestamp'].strftime('%H:%M:%S')} - "
                  f"{change['field']}: ${change['previous']:,.2f} → "
                  f"${change['current']:,.2f} ({change['change']:+,.2f})")
    else:
        print("No account changes recorded")
    
    print()
    
    # Position changes
    position_changes = position_mgr.get_change_log(max_entries=10)
    if position_changes:
        print(f"Recent position changes ({len(position_changes)}):")
        for change in position_changes[-5:]:  # Last 5
            print(f"  {change.timestamp.strftime('%H:%M:%S')} - "
                  f"{change.symbol}: {change.change_type} "
                  f"({change.previous_quantity} → {change.new_quantity})")
    else:
        print("No position changes recorded")
    
    # ========================================================================
    # Part 6: Manual Sync Example
    # ========================================================================
    
    print_separator("Manual Sync")
    
    print("Forcing manual sync of account and positions...")
    account_success = account_mgr.sync_account_state()
    position_success = position_mgr.sync_positions()
    
    if account_success and position_success:
        print("✅ Manual sync successful")
    else:
        if not account_success:
            print("⚠️  Account sync failed")
        if not position_success:
            print("⚠️  Position sync failed")
    
    # ========================================================================
    # Cleanup
    # ========================================================================
    
    print_separator("Cleanup")
    
    print("Disconnecting from IBKR...")
    broker.disconnect()
    print("✅ Disconnected")
    
    print_separator()
    print("Example completed successfully! ✅")
    print_separator()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(f"Error in example: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
