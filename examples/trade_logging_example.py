"""
Example: Trade Logging and Audit Trail

This example demonstrates how to use the trade logging and audit trail features
for IBKR trading. It shows:
1. Setting up automatic trade logging
2. Executing some trades
3. Reconciling with IBKR account history
4. Generating compliance reports

Note: This requires an active IBKR connection (TWS or IB Gateway).
"""

from datetime import date
import logging

# Direct imports to avoid circular dependency issues
from copilot_quant.brokers.interactive_brokers import IBKRBroker
from copilot_quant.brokers.audit_trail import AuditTrail

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print("=" * 80)
    print("Trade Logging and Audit Trail Example")
    print("=" * 80)
    print()
    
    # 1. Initialize broker with order execution and logging enabled
    print("Step 1: Initializing IBKR broker...")
    broker = IBKRBroker(
        paper_trading=True,
        enable_order_execution=True,
        enable_order_logging=True
    )
    
    # 2. Connect to IBKR
    print("Step 2: Connecting to IBKR...")
    if not broker.connect():
        print("❌ Failed to connect to IBKR. Make sure TWS/IB Gateway is running.")
        return
    
    print("✅ Connected to IBKR")
    print()
    
    # 3. Initialize audit trail with database storage
    print("Step 3: Setting up audit trail...")
    audit = AuditTrail(
        broker,
        database_url="sqlite:///trade_audit_example.db"
    )
    audit.enable()  # Start automatic capture of all trades
    print("✅ Audit trail enabled")
    print()
    
    # 4. Execute some sample trades (or skip if you prefer)
    execute_trades = input("Would you like to execute sample trades? (y/n): ").lower() == 'y'
    
    if execute_trades:
        print("\nStep 4: Executing sample trades...")
        print("Note: This will execute REAL orders in your paper trading account!")
        confirm = input("Are you sure? (yes/no): ").lower()
        
        if confirm == 'yes':
            # Execute a small market order
            print("Placing market order: BUY 1 AAPL...")
            order = broker.execute_market_order("AAPL", 1, "buy")
            if order:
                print(f"✅ Order placed: ID {order.order_id}")
            else:
                print("❌ Order failed")
            
            # Give time for fills
            import time
            print("Waiting 5 seconds for fills...")
            time.sleep(5)
        else:
            print("Skipped trade execution")
    else:
        print("\nStep 4: Skipped (no trades executed)")
    
    print()
    
    # 5. Check today's order activity
    print("Step 5: Checking today's order activity...")
    orders = audit.get_orders_by_date(date.today())
    fills = audit.get_fills_by_date(date.today())
    
    print(f"Orders today: {len(orders)}")
    print(f"Fills today: {len(fills)}")
    
    if orders:
        print("\nOrders:")
        for order in orders:
            print(f"  - Order {order['order_id']}: {order['action']} {order['total_quantity']} "
                  f"{order['symbol']} [{order['status']}]")
    
    if fills:
        print("\nFills:")
        for fill in fills:
            print(f"  - Fill {fill['fill_id']}: {fill['quantity']} {fill['symbol']} "
                  f"@ ${fill['price']:.2f}")
    
    print()
    
    # 6. Reconcile with IBKR
    print("Step 6: Reconciling with IBKR account history...")
    try:
        report = audit.reconcile_today()
        
        print(f"\nReconciliation Summary:")
        summary = report.summary()
        print(f"  IBKR Fills: {summary['total_ibkr_fills']}")
        print(f"  Local Fills: {summary['total_local_fills']}")
        print(f"  Matched Orders: {summary['matched_orders']}")
        print(f"  Discrepancies: {summary['total_discrepancies']}")
        
        if report.has_discrepancies():
            print("\n⚠️  Discrepancies found:")
            for disc in report.discrepancies:
                print(f"    - {disc.type.value}: {disc.description}")
        else:
            print("\n✅ Perfect match - no discrepancies!")
    
    except Exception as e:
        print(f"❌ Reconciliation failed: {e}")
    
    print()
    
    # 7. Generate compliance report
    print("Step 7: Generating compliance report...")
    try:
        audit.export_audit_trail(
            date.today(),
            date.today(),
            output_file="audit_report_example.json"
        )
        print("✅ Audit report exported to: audit_report_example.json")
        
        # Also generate text version
        text_report = audit.generate_compliance_report(
            date.today(),
            date.today(),
            format='text'
        )
        print("\nText Report Preview:")
        print(text_report[:500] + "..." if len(text_report) > 500 else text_report)
    
    except Exception as e:
        print(f"❌ Report generation failed: {e}")
    
    print()
    
    # 8. Check compliance
    print("Step 8: Checking compliance status...")
    try:
        status = audit.check_compliance(
            date.today(),
            date.today(),
            max_discrepancies=0  # Zero-tolerance policy
        )
        
        if status['compliant']:
            print("✅ COMPLIANT - No discrepancies found")
        else:
            print(f"❌ NON-COMPLIANT - {status['total_discrepancies']} discrepancies found")
    
    except Exception as e:
        print(f"❌ Compliance check failed: {e}")
    
    print()
    
    # 9. Cleanup
    print("Step 9: Disconnecting...")
    broker.disconnect()
    print("✅ Disconnected from IBKR")
    
    print()
    print("=" * 80)
    print("Example Complete!")
    print("=" * 80)
    print()
    print("Files created:")
    print("  - trade_audit_example.db (SQLite database with all trade data)")
    print("  - audit_report_example.json (Compliance report)")
    print()
    print("You can query the database or regenerate reports at any time.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
