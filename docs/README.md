# Backtesting Engine Documentation Index

This document serves as the entry point to the comprehensive backtesting engine documentation.

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

## 🎯 Common Tasks

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
