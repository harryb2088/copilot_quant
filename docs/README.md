# Copilot Quant Platform Documentation Index

This document serves as the entry point to the comprehensive platform documentation.

## 🚀 Getting Started

**New to the platform? Start here:**

1. **[Bootstrapping Guide](BOOTSTRAPPING.md)** 🎯 **← START HERE FOR SETUP**
   - Complete setup guide for local, Docker, and cloud deployments
   - Step-by-step instructions for all services (database, orchestrator, UI)
   - Configuration and verification procedures
   - Troubleshooting common issues
   - **Best for: Setting up the platform from scratch**

## 📖 Documentation Structure

### For New Users

Start here if you're new to the backtesting engine:

1. **[Quick Reference](quick_reference.md)** ⚡
   - Concise API reference
   - Common code patterns
   - Quick examples
   - Best for: Copy-paste code snippets

2. **[Usage Guide](usage_guide.md)** 📚
   - Detailed walkthrough
   - Strategy development
   - Complete examples
   - Best practices
   - Best for: Learning by example

3. **[Backtesting API Reference](backtesting.md)** 📘
   - Complete API documentation
   - All classes and methods
   - Parameter descriptions
   - Best for: Full reference

### For Architecture Understanding

For those who want to understand the design:

4. **[Architecture](architecture.md)** 🏛️
   - System design overview
   - Component descriptions
   - Event flow
   - Design patterns
   - Extension points
   - Best for: Understanding how it works

5. **[Diagrams](diagrams.md)** 📊
   - Visual diagrams (Mermaid)
   - System architecture
   - Sequence diagrams
   - Class hierarchies
   - Best for: Visual learners

6. **[Design Decisions](design_decisions.md)** 💭
   - Why things are designed this way
   - Trade-offs considered
   - Alternatives evaluated
   - Best for: Understanding the "why"

### For Advanced Users

For customization and extension:

7. **[Interfaces](../copilot_quant/backtest/interfaces.py)** 🔌
   - Abstract interface definitions
   - IDataFeed, IBroker, IPortfolioManager, etc.
   - Configuration classes
   - Best for: Custom implementations

8. **[Advanced Examples](../examples/advanced_interfaces.py)** 🔬
   - Volume-based broker
   - CSV data feed
   - Advanced performance analyzer
   - Best for: Building custom components

### For Live Trading

For connecting to live markets:

9. **[🎯 IBKR Comprehensive Setup & Usage Guide](IBKR_COMPREHENSIVE_GUIDE.md)** 🔴 **← START HERE**
   - Complete end-to-end guide for IBKR integration
   - Quick start (5 minutes to paper trading)
   - TWS vs IB Gateway comparison
   - Detailed setup instructions
   - Paper and live trading modes
   - Service requirements and system setup
   - Usage examples and code snippets
   - Troubleshooting and best practices
   - **Best for: New users setting up IBKR from scratch**

10. **[Interactive Brokers Setup Guide](ibkr_setup_guide.md)** 📘
    - Detailed technical reference
    - TWS/Gateway installation and configuration
    - API setup and security best practices
    - Rate limits and restrictions
    - Advanced connection code examples
    - **Best for: Developers needing technical details**

11. **[IBKR Connection Manager](IBKR_CONNECTION_MANAGER.md)** 🔌
    - Connection manager API documentation
    - Auto-reconnection features
    - Health monitoring
    - Event handlers
    - **Best for: Understanding connection management**

12. **[IBKR Connection Troubleshooting](IBKR_CONNECTION_TROUBLESHOOTING.md)** 🔧
    - Common connection issues and solutions
    - Debug techniques
    - Network diagnostics
    - **Best for: Solving connection problems**

13. **[Live Integration Guide](LIVE_INTEGRATION_GUIDE.md)** 🚀
    - Integrating IBKR with strategy engine
    - Live data and execution
    - Adapter pattern implementation
    - **Best for: Developers integrating live trading**

14. **[Live Market Data Guide](live_market_data_guide.md)** 📡
    - Real-time market data streaming
    - Historical data downloads
    - Subscription management
    - **Best for: Working with market data**

### For UI Features

For understanding the Streamlit UI features:

15. **[LLM Strategy Generation](llm_strategy_generation.md)** 🤖
    - LLM-based strategy creation
    - Natural language to signal logic
    - Security safeguards
    - Setup and configuration
    - Best for: Internal users generating strategies with AI

16. **[LLM Quick Start](llm_quickstart.md)** ⚡
    - Quick overview of LLM features
    - Step-by-step demo
    - Example strategies
    - Troubleshooting
    - Best for: Getting started quickly with LLM

### Implementation Summaries

Historical implementation summaries from previous development work:

17. **[Implementation Summaries](implementation-summaries/)** 📝
    - [Account Position Sync](implementation-summaries/ACCOUNT_POSITION_SYNC_SUMMARY.md) - Position synchronization implementation
    - [IBKR Settings Update](implementation-summaries/IBKR_SETTINGS_UPDATE.md) - IBKR configuration updates
    - [IBKR Test Implementation](implementation-summaries/IBKR_TEST_IMPLEMENTATION_SUMMARY.md) - IBKR testing summary
    - [IB Implementation](implementation-summaries/IB_IMPLEMENTATION_SUMMARY.md) - Interactive Brokers implementation
    - [Implementation Details](implementation-summaries/IMPLEMENTATION_DETAILS.md) - General implementation details
    - [Implementation Summary](implementation-summaries/IMPLEMENTATION_SUMMARY.md) - Overall implementation summary
    - [Live Integration](implementation-summaries/LIVE_INTEGRATION_SUMMARY.md) - Live trading integration
    - [Order Execution](implementation-summaries/ORDER_EXECUTION_SUMMARY.md) - Order execution implementation
    - [Trade Logging](implementation-summaries/TRADE_LOGGING_IMPLEMENTATION_SUMMARY.md) - Trade logging implementation
    - [Trading Mode Toggle](implementation-summaries/TRADING_MODE_TOGGLE_SUMMARY.md) - Trading mode toggle feature
    - [Trading Mode UI Mockup](implementation-summaries/TRADING_MODE_TOGGLE_UI_MOCKUP.md) - UI mockup for trading mode

18. **[Testing Guides](testing-guides/)** 🧪
    - [Trading Mode Toggle Manual Test](testing-guides/TRADING_MODE_TOGGLE_MANUAL_TEST.md) - Manual testing procedures

## 🎯 Common Tasks

### "I want to set up the platform from scratch"
→ Start with [Bootstrapping Guide](BOOTSTRAPPING.md) for complete setup

### "I want to run my first backtest"
→ Start with [Quick Reference](quick_reference.md#quick-start)

### "I want to create a trading strategy"
→ Read [Usage Guide - Strategy Development](usage_guide.md#strategy-development)

### "I want to understand the architecture"
→ Read [Architecture](architecture.md) and [Diagrams](diagrams.md)

### "I want to implement a custom data source"
→ See [Interfaces - IDataFeed](../copilot_quant/backtest/interfaces.py) and [Advanced Examples](../examples/advanced_interfaces.py)

### "I want to customize order execution"
→ See [Interfaces - IBroker](../copilot_quant/backtest/interfaces.py) and [Advanced Examples](../examples/advanced_interfaces.py)

### "I need help debugging"
→ Check [Quick Reference - Error Handling](quick_reference.md#error-handling)

### "I want to understand why things are designed this way"
→ Read [Design Decisions](design_decisions.md)

### "I want to set up live/paper trading with Interactive Brokers"
→ Start with [IBKR Comprehensive Guide](IBKR_COMPREHENSIVE_GUIDE.md) for complete setup
→ Or see [Interactive Brokers Setup Guide](ibkr_setup_guide.md) for technical details

## 📋 Core Concepts

### Strategy
Trading logic that generates buy/sell signals based on market data.
- **Documentation**: [Usage Guide - Strategy Development](usage_guide.md#strategy-development)
- **Interface**: `Strategy` class in `copilot_quant.backtest.strategy`
- **Examples**: [Usage Guide](usage_guide.md#example-strategies)

### DataFeed
Provides historical market data to the backtesting engine.
- **Documentation**: [Architecture - DataFeed Connector](architecture.md#2-datafeed-connector)
- **Interface**: `IDataFeed` in `copilot_quant.backtest.interfaces`
- **Examples**: [Advanced Examples](../examples/advanced_interfaces.py)

### Broker
Executes orders with realistic simulation of slippage and commissions.
- **Documentation**: [Architecture - Broker/Execution Engine](architecture.md#3-brokerexecution-engine)
- **Interface**: `IBroker` in `copilot_quant.backtest.interfaces`
- **Examples**: [Advanced Examples](../examples/advanced_interfaces.py)

### Portfolio
Tracks positions, cash, and profit/loss.
- **Documentation**: [Architecture - Portfolio Manager](architecture.md#4-portfolio-manager)
- **Interface**: `IPortfolioManager` in `copilot_quant.backtest.interfaces`
- **Implementation**: Built into `BacktestEngine`

### Results
Stores backtest outcomes and performance metrics.
- **Documentation**: [Architecture - Results Tracking](architecture.md#5-results-tracking--reporting)
- **Interface**: `IResultsTracker` in `copilot_quant.backtest.interfaces`
- **Class**: `BacktestResult` in `copilot_quant.backtest.results`

## 🔍 By Topic

### Getting Started
- [Quick Start](quick_reference.md#quick-start)
- [Minimal Backtest](usage_guide.md#quick-start)
- [First Strategy](usage_guide.md#1-create-a-strategy)

### Strategy Development
- [Strategy Lifecycle](usage_guide.md#strategy-lifecycle)
- [Example Strategies](usage_guide.md#example-strategies)
- [Common Patterns](quick_reference.md#common-patterns)
- [Best Practices](usage_guide.md#best-practices)

### Order Management
- [Order Types](quick_reference.md#order-types)
- [Market Orders](usage_guide.md#market-orders)
- [Limit Orders](usage_guide.md#limit-orders)
- [Position Sizing](usage_guide.md#position-sizing)

### Results Analysis
- [Basic Metrics](usage_guide.md#basic-metrics)
- [Trade Log](usage_guide.md#trade-log)
- [Equity Curve](usage_guide.md#equity-curve)
- [Portfolio History](usage_guide.md#portfolio-history)

### Advanced Topics
- [Custom Indicators](usage_guide.md#custom-indicators)
- [State Management](usage_guide.md#state-management)
- [Multi-Symbol Trading](quick_reference.md#multi-symbol-trading)
- [Custom Interfaces](../examples/advanced_interfaces.py)

### Architecture
- [System Overview](architecture.md#system-architecture)
- [Event Flow](architecture.md#event-flow-diagram)
- [Component Interactions](architecture.md#component-interactions)
- [Design Patterns](architecture.md#design-patterns-used)

### Testing
- [Unit Testing](usage_guide.md#unit-testing)
- [Mock Data](usage_guide.md#mock-data-provider)
- [Test Examples](quick_reference.md#testing-quick-reference)

### Live Trading
- [🎯 IBKR Comprehensive Guide](IBKR_COMPREHENSIVE_GUIDE.md) - **START HERE** - Complete setup from scratch
- [IBKR Setup Guide](ibkr_setup_guide.md) - Detailed technical reference
- [IBKR Connection Manager](IBKR_CONNECTION_MANAGER.md) - Connection management API
- [IBKR Troubleshooting](IBKR_CONNECTION_TROUBLESHOOTING.md) - Solving connection issues
- [Live Integration Guide](LIVE_INTEGRATION_GUIDE.md) - Strategy integration with live trading
- [Live Market Data Guide](live_market_data_guide.md) - Real-time data streaming

## 📈 Example Strategies

All examples are in the [Usage Guide](usage_guide.md#example-strategies):

1. **Buy and Hold** - Simplest strategy
2. **Moving Average Crossover** - Classic technical indicator
3. **Mean Reversion** - Bollinger Bands
4. **Momentum** - Relative strength
5. **Pairs Trading** - Statistical arbitrage

## 🎓 Learning Path

### Beginner
1. Read [Quick Start](quick_reference.md#quick-start)
2. Try [Minimal Backtest](usage_guide.md#quick-start)
3. Study [Example Strategies](usage_guide.md#example-strategies)
4. Review [Common Patterns](quick_reference.md#common-patterns)

### Intermediate
1. Understand [Strategy Lifecycle](usage_guide.md#strategy-lifecycle)
2. Learn [Order Management](usage_guide.md#order-management)
3. Practice [Results Analysis](usage_guide.md#results-analysis)
4. Review [Best Practices](usage_guide.md#best-practices)

### Advanced
1. Study [Architecture](architecture.md)
2. Review [Design Decisions](design_decisions.md)
3. Explore [Interfaces](../copilot_quant/backtest/interfaces.py)
4. Try [Advanced Examples](../examples/advanced_interfaces.py)

### Expert
1. Implement custom [DataFeed](../copilot_quant/backtest/interfaces.py)
2. Build custom [Broker](../copilot_quant/backtest/interfaces.py)
3. Create [Performance Analyzer](../examples/advanced_interfaces.py)
4. Contribute to the project

## 🔗 Quick Links

### Documentation Files
- [architecture.md](architecture.md) - System architecture
- [diagrams.md](diagrams.md) - Visual diagrams
- [design_decisions.md](design_decisions.md) - Design rationale
- [usage_guide.md](usage_guide.md) - Comprehensive guide
- [quick_reference.md](quick_reference.md) - Quick reference
- [backtesting.md](backtesting.md) - API reference
- [ibkr_setup_guide.md](ibkr_setup_guide.md) - Interactive Brokers setup

### Code Files
- [interfaces.py](../copilot_quant/backtest/interfaces.py) - Interface definitions
- [strategy.py](../copilot_quant/backtest/strategy.py) - Strategy base class
- [engine.py](../copilot_quant/backtest/engine.py) - Backtest engine
- [orders.py](../copilot_quant/backtest/orders.py) - Order/Fill/Position
- [results.py](../copilot_quant/backtest/results.py) - Results class

### Examples
- [advanced_interfaces.py](../examples/advanced_interfaces.py) - Advanced examples
- [run_backtest.py](../examples/run_backtest.py) - Basic example
- [run_backtest_mock.py](../examples/run_backtest_mock.py) - Mock data example

## 🤝 Contributing

Found an issue or want to improve the documentation?

1. Check [CONTRIBUTING.md](../CONTRIBUTING.md)
2. Open an issue on GitHub
3. Submit a pull request

## 📝 Notes

- All code examples are tested and working
- Diagrams are in Mermaid format for GitHub rendering
- Documentation follows the actual implementation
- Examples demonstrate real-world patterns

## 🔄 Last Updated

**Date**: 2026-02-17  
**Version**: v1.0  
**Status**: Complete

---

**Quick Tip**: Bookmark this page and use Ctrl+F to search for what you need!
