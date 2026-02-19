-- Initialize database schema for copilot_quant
-- This script is automatically run on database initialization

-- Enable extensions if needed
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_orders_symbol ON orders(symbol);
CREATE INDEX IF NOT EXISTS idx_orders_submission_time ON orders(submission_time);
CREATE INDEX IF NOT EXISTS idx_fills_symbol ON fills(symbol);
CREATE INDEX IF NOT EXISTS idx_fills_timestamp ON fills(timestamp);
CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_date ON portfolio_snapshots(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_reconciliation_logs_date ON reconciliation_logs(reconciliation_date);

-- Grant necessary permissions (least privilege principle)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO copilot;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO copilot;
