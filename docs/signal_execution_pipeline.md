# Signal Execution Pipeline - User Guide

## Overview

The Signal Execution Pipeline connects live signal generation to comprehensive risk management and order execution. It provides the "glue layer" that wires `LiveSignalMonitor` through risk checks, position sizing, and IBKR order submission.

## Quick Start

### Option 1: Production-Ready Setup (Recommended)

The easiest way to get started is using the convenience function:

```python
from copilot_quant.live import create_production_signal_monitor
from copilot_quant.strategies.my_strategy import MySignalStrategy

# Create production monitor with balanced risk profile
monitor = create_production_signal_monitor(
    risk_profile="balanced",  # Options: conservative, balanced, aggressive
    paper_trading=True,
    database_url="sqlite:///live_trading.db"
)

# Add your strategies
monitor.add_strategy(MySignalStrategy())

# Connect and start
monitor.connect()
monitor.start(['AAPL', 'MSFT', 'GOOGL'])

# Monitor runs continuously...
# Stop when done
monitor.stop()
monitor.disconnect()
```

### Option 2: Manual Setup (Advanced)

For more control, you can manually configure each component:

```python
from copilot_quant.live import (
    EnhancedLiveSignalMonitor,
    SignalExecutionPipeline,
    PortfolioStateManager
)
from copilot_quant.brokers.order_execution_handler import OrderExecutionHandler
from src.risk import RiskManager, RiskSettings
from copilot_quant.orchestrator.notifiers import SlackNotifier

# Configure risk settings
risk_settings = RiskSettings(
    max_position_size=0.025,  # 2.5% per position
    max_portfolio_drawdown=0.12,  # 12% max drawdown
    circuit_breaker_threshold=0.10,  # 10% triggers circuit breaker
    position_stop_loss=0.05,  # 5% per-position stop loss
)

# Create components
risk_manager = RiskManager(risk_settings)
order_handler = OrderExecutionHandler()
portfolio_state = PortfolioStateManager(database_url="sqlite:///portfolio.db")
notifier = SlackNotifier(webhook_url="YOUR_WEBHOOK_URL")

# Create enhanced monitor
monitor = EnhancedLiveSignalMonitor(
    risk_manager=risk_manager,
    order_handler=order_handler,
    portfolio_state=portfolio_state,
    notifier=notifier,
    paper_trading=True,
    max_position_pct=0.025,
    max_portfolio_deployment=0.80
)

# Use as normal
monitor.add_strategy(MyStrategy())
monitor.connect()
monitor.start(['AAPL', 'MSFT'])
```

## Risk Profiles

The pipeline supports three pre-configured risk profiles:

### Conservative (Default)
- Max position size: 10% of portfolio
- Max drawdown: 12%
- Circuit breaker: 10%
- Stop loss: 5% per position
- Best for: Capital preservation, lower risk tolerance

### Balanced
- Max position size: 15% of portfolio
- Max drawdown: 15%
- Circuit breaker: 12%
- Stop loss: 7% per position
- Best for: Moderate risk/reward balance

### Aggressive
- Max position size: 20% of portfolio
- Max drawdown: 20%
- Circuit breaker: 15%
- Stop loss: 10% per position
- Best for: Higher risk tolerance, growth focused

## Pipeline Flow

Every signal goes through this pipeline:

```
Signal Generated
    ↓
Risk Checks
  • Circuit breaker active?
  • Portfolio drawdown acceptable?
  • Cash buffer sufficient?
  • Quality score > 0.3?
  • Deployment limit not exceeded?
    ↓
Position Sizing
  • Base size = portfolio * max_position_pct
  • Scaled by signal quality_score
  • Converted to shares
    ↓
Order Submission
  • Create market order
  • Submit to IBKR
  • Track order lifecycle
    ↓
Fill Handling
  • Update portfolio state
  • Send notifications
  • Record for audit trail
```

## Signal Quality Scoring

The pipeline prioritizes signals by their `quality_score`:

```python
quality_score = confidence * min(sharpe_estimate / 2.0, 1.0)
```

- Higher quality signals get more capital allocation
- Batch processing executes highest quality first
- Minimum quality threshold: 0.3

## Risk Controls Enforced

### Portfolio-Level
- ✅ Max drawdown cap (default 12%)
- ✅ Circuit breaker on excessive drawdown
- ✅ Cash buffer requirements (20-80%)
- ✅ Max portfolio deployment (80%)
- ✅ Max number of positions (10)

### Position-Level
- ✅ Max position size (2.5% of portfolio)
- ✅ Per-position stop loss (5%)
- ✅ Signal quality threshold (0.3)

### Correlation & Diversification
- ✅ Max correlation between positions (80%)
- ✅ Limit on highly correlated positions (2)

## Notifications

The pipeline sends structured notifications for:

### INFO Level
- Signal execution successful
- Order fills (complete and partial)

### WARNING Level
- Signal rejected by risk checks
- Position size too small
- Deployment limit approaching

### CRITICAL Level
- Circuit breaker triggered
- System errors
- Connection failures

## Structured Logging

All signal processing is logged in JSON format for audit trails:

```json
{
  "signal": {
    "symbol": "AAPL",
    "side": "buy",
    "confidence": 0.8,
    "sharpe_estimate": 1.5,
    "quality_score": 0.6,
    "strategy_name": "MomentumStrategy",
    "entry_price": 150.0
  },
  "status": "executed",
  "timestamp": "2026-02-19T07:00:00",
  "risk_check_passed": true,
  "position_size": 100,
  "position_value": 15000.0,
  "order_id": 12345
}
```

## Batch Processing

When multiple signals arrive simultaneously, they're processed in order:

1. **Rank by Quality**: Signals sorted by descending `quality_score`
2. **Process Sequentially**: Highest quality signals first
3. **Deployment Check**: Stops when portfolio deployment limit hit
4. **Reject Remainder**: Lower quality signals rejected if limit reached

Example:

```python
# Multiple signals arrive
signals = [
    Signal(symbol="AAPL", quality_score=0.8),
    Signal(symbol="MSFT", quality_score=0.6),
    Signal(symbol="GOOGL", quality_score=0.9),
]

# Pipeline processes in order: GOOGL (0.9), AAPL (0.8), MSFT (0.6)
results = await pipeline.process_batch(signals)
```

## Circuit Breaker

The circuit breaker is a safety mechanism that stops all trading when portfolio drawdown exceeds a threshold:

```python
# Automatically triggered when drawdown >= threshold
# Example: 10% threshold, portfolio drops 10%
# Result: All new signals rejected with "Circuit breaker is active"

# Must be manually reset after addressing the issue
risk_manager.reset_circuit_breaker()
```

## Integration with Orchestrator

The pipeline integrates seamlessly with the `TradingOrchestrator`:

- Respects market hours (PRE_MARKET, TRADING, POST_MARKET)
- Only executes during TRADING state
- Automatically stops during off-hours
- Health monitoring and auto-restart built-in

## Best Practices

1. **Start with Conservative Profile**: Begin with lower risk settings
2. **Monitor Circuit Breaker**: Set up alerts for circuit breaker triggers
3. **Review Rejections**: Regularly check rejection logs to understand patterns
4. **Tune Quality Threshold**: Adjust minimum quality_score based on strategy performance
5. **Test in Paper Trading**: Thoroughly test with paper trading before going live
6. **Set Position Limits**: Adjust max_position_pct based on portfolio size
7. **Enable Notifications**: Set up Slack/Discord for real-time alerts

## Troubleshooting

### Signals Getting Rejected

**Check:**
- Signal quality_score (must be > 0.3)
- Portfolio deployment level (must be < 80%)
- Circuit breaker status
- Cash buffer (must be 20-80%)
- Drawdown level

### Orders Not Executing

**Check:**
- IB connection status
- Market hours (must be TRADING state)
- Order handler configuration
- Position size (must be > 0 shares)

### Circuit Breaker Triggered

**Actions:**
1. Review what caused the drawdown
2. Assess current positions
3. Make necessary adjustments
4. Reset circuit breaker when ready
5. Resume trading

## Example Strategies

See `examples/` directory for complete strategy examples:

- `momentum_signals.py` - Momentum-based signal generation
- `mean_reversion_signals.py` - Mean reversion with quality scoring
- `multi_strategy_live.py` - Multiple strategies with pipeline integration

## API Reference

### SignalExecutionPipeline

```python
class SignalExecutionPipeline:
    async def process_signal(signal: TradingSignal) -> ExecutionResult
    async def process_batch(signals: List[TradingSignal]) -> List[ExecutionResult]
    def get_stats() -> Dict[str, int]
```

### EnhancedLiveSignalMonitor

```python
class EnhancedLiveSignalMonitor(LiveSignalMonitor):
    def __init__(risk_manager, order_handler, portfolio_state, notifier, ...)
    def connect(timeout: int = 30, retry_count: int = 3) -> bool
    def start(symbols: List[str]) -> bool
    def stop() -> None
    def get_dashboard_summary() -> Dict
```

### ExecutionResult

```python
@dataclass
class ExecutionResult:
    signal: TradingSignal
    status: SignalStatus  # PENDING, APPROVED, REJECTED, EXECUTED, FAILED
    risk_check_passed: bool
    position_size: int
    order_id: Optional[int]
    rejection_reason: Optional[str]
```

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/harryb2088/copilot_quant/issues
- Documentation: See `docs/` directory
- Examples: See `examples/` directory
