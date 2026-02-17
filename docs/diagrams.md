# Backtesting Engine Diagrams

This document contains visual diagrams for the backtesting engine architecture using Mermaid.js, which renders natively on GitHub.

## System Architecture

```mermaid
graph TB
    subgraph "Backtesting Engine"
        Strategy[Strategy<br/>Interface]
        DataFeed[DataFeed<br/>Connector]
        Broker[Broker<br/>Execution]
        Engine[Backtest Engine<br/>Core]
        Portfolio[Portfolio<br/>Manager]
        Results[Results<br/>Tracker]
        
        Strategy --> Engine
        DataFeed --> Engine
        Engine --> Broker
        Engine --> Portfolio
        Engine --> Results
        Broker --> Portfolio
    end
    
    subgraph "External"
        DataSource[Data Sources<br/>Yahoo Finance, CSV, etc.]
        User[User Strategy<br/>Implementation]
    end
    
    DataSource --> DataFeed
    User --> Strategy
    
    style Engine fill:#4A90E2,stroke:#333,stroke-width:2px,color:#fff
    style Strategy fill:#7ED321,stroke:#333,stroke-width:2px
    style Portfolio fill:#F5A623,stroke:#333,stroke-width:2px
    style Results fill:#BD10E0,stroke:#333,stroke-width:2px
```

## Component Interaction Sequence

```mermaid
sequenceDiagram
    participant User
    participant Engine
    participant Strategy
    participant DataFeed
    participant Broker
    participant Portfolio
    participant Results
    
    User->>Engine: Initialize with config
    User->>Engine: Add strategy
    User->>Engine: Run backtest
    
    Engine->>Strategy: initialize()
    Engine->>DataFeed: Fetch historical data
    DataFeed-->>Engine: Market data
    
    loop For each timestamp
        Engine->>Portfolio: Update positions (mark-to-market)
        Engine->>Results: Record portfolio state
        Engine->>Strategy: on_data(timestamp, data)
        Strategy-->>Engine: [Order, Order, ...]
        
        loop For each order
            Engine->>Broker: execute_order(order)
            Broker->>Portfolio: Check buying power
            Portfolio-->>Broker: Available capital
            Broker->>Broker: Apply slippage & commission
            Broker->>Portfolio: Update position
            Broker-->>Engine: Fill
            Engine->>Strategy: on_fill(fill)
            Engine->>Results: Record trade
        end
    end
    
    Engine->>Strategy: finalize()
    Engine->>Results: Calculate metrics
    Engine-->>User: BacktestResult
```

## Class Hierarchy

```mermaid
classDiagram
    class Strategy {
        <<abstract>>
        +name: str
        +initialize() void
        +on_data(timestamp, data) List[Order]
        +on_fill(fill) void
        +finalize() void
    }
    
    class Order {
        +symbol: str
        +quantity: float
        +order_type: str
        +side: str
        +limit_price: float
    }
    
    class Fill {
        +order: Order
        +fill_price: float
        +fill_quantity: float
        +commission: float
        +timestamp: datetime
        +total_cost() float
        +net_proceeds() float
    }
    
    class Position {
        +symbol: str
        +quantity: float
        +avg_entry_price: float
        +unrealized_pnl: float
        +realized_pnl: float
        +update_from_fill(fill) void
        +update_unrealized_pnl(price) void
    }
    
    class BacktestEngine {
        +initial_capital: float
        +commission_rate: float
        +slippage_rate: float
        -strategy: Strategy
        -cash: float
        -positions: Dict[Position]
        +add_strategy(strategy) void
        +run(start, end, symbols) BacktestResult
        +get_portfolio_value() float
    }
    
    class BacktestResult {
        +strategy_name: str
        +start_date: datetime
        +end_date: datetime
        +initial_capital: float
        +final_capital: float
        +total_return: float
        +trades: List[Fill]
        +portfolio_history: DataFrame
        +get_trade_log() DataFrame
        +get_equity_curve() Series
        +get_summary_stats() dict
    }
    
    class IDataFeed {
        <<interface>>
        +get_historical_data(symbol, start, end) DataFrame
        +get_multiple_symbols(symbols, start, end) DataFrame
        +get_ticker_info(symbol) dict
    }
    
    class IBroker {
        <<interface>>
        +execute_order(order, price, timestamp) Fill
        +check_buying_power(order, price) bool
        +calculate_commission(price, quantity) float
        +calculate_slippage(order, price) float
    }
    
    class IPortfolioManager {
        <<interface>>
        +update_position(symbol, fill, price) void
        +get_position(symbol) Position
        +get_portfolio_value(prices) float
        +mark_to_market(prices) void
    }
    
    Strategy <|-- BuyAndHold
    Strategy <|-- MovingAverage
    Strategy <|-- MeanReversion
    
    BacktestEngine --> Strategy
    BacktestEngine --> IDataFeed
    BacktestEngine --> IBroker
    BacktestEngine --> IPortfolioManager
    BacktestEngine --> Position
    BacktestEngine --> BacktestResult
    
    Order --> Fill
    Fill --> Position
```

## Event Flow

```mermaid
flowchart TD
    Start([Start Backtest]) --> Init[Initialize Strategy]
    Init --> LoadData[Load Historical Data]
    LoadData --> NextTimestamp{More<br/>Timestamps?}
    
    NextTimestamp -->|Yes| UpdatePnL[Update Unrealized P&L]
    UpdatePnL --> Record[Record Portfolio State]
    Record --> CallStrategy[Call Strategy.on_data]
    CallStrategy --> GenerateOrders{Orders<br/>Generated?}
    
    GenerateOrders -->|No| NextTimestamp
    GenerateOrders -->|Yes| ProcessOrder[Process Each Order]
    
    ProcessOrder --> CheckBuyingPower{Sufficient<br/>Capital?}
    CheckBuyingPower -->|No| RejectOrder[Log Warning & Skip]
    RejectOrder --> NextTimestamp
    
    CheckBuyingPower -->|Yes| ApplySlippage[Calculate Fill Price<br/>with Slippage]
    ApplySlippage --> ApplyCommission[Calculate Commission]
    ApplyCommission --> CreateFill[Create Fill]
    CreateFill --> UpdatePortfolio[Update Portfolio<br/>Cash & Positions]
    UpdatePortfolio --> NotifyStrategy[Call Strategy.on_fill]
    NotifyStrategy --> RecordTrade[Record Trade]
    RecordTrade --> NextTimestamp
    
    NextTimestamp -->|No| Finalize[Call Strategy.finalize]
    Finalize --> CalcMetrics[Calculate Performance Metrics]
    CalcMetrics --> CreateResult[Create BacktestResult]
    CreateResult --> End([Return Result])
    
    style Start fill:#7ED321
    style End fill:#7ED321
    style CheckBuyingPower fill:#F5A623
    style RejectOrder fill:#D0021B
    style CreateResult fill:#BD10E0
```

## Order Execution Flow

```mermaid
stateDiagram-v2
    [*] --> OrderCreated: Strategy generates order
    
    OrderCreated --> BuyingPowerCheck: Submit to broker
    
    BuyingPowerCheck --> OrderRejected: Insufficient capital
    BuyingPowerCheck --> PriceCheck: Capital available
    
    PriceCheck --> OrderRejected: Limit price not met
    PriceCheck --> Slippage: Market order or limit met
    
    Slippage --> Commission: Apply slippage
    Commission --> Filled: Calculate commission
    
    Filled --> PositionUpdate: Create fill
    PositionUpdate --> StrategyNotification: Update portfolio
    StrategyNotification --> [*]: Trade complete
    
    OrderRejected --> [*]: Order not executed
```

## Data Flow

```mermaid
flowchart LR
    subgraph "Data Sources"
        YF[Yahoo Finance]
        CSV[CSV Files]
        DB[Database]
    end
    
    subgraph "Data Layer"
        DP[DataProvider<br/>Interface]
        Cache[Data Cache<br/>Optional]
    end
    
    subgraph "Engine"
        BE[Backtest<br/>Engine]
        Strat[Strategy]
    end
    
    subgraph "Output"
        PH[Portfolio<br/>History]
        TL[Trade<br/>Log]
        Metrics[Performance<br/>Metrics]
    end
    
    YF --> DP
    CSV --> DP
    DB --> DP
    
    DP --> Cache
    Cache --> BE
    BE --> Strat
    
    BE --> PH
    BE --> TL
    BE --> Metrics
    
    style DP fill:#4A90E2
    style BE fill:#4A90E2
    style Strat fill:#7ED321
```

## Portfolio State Transitions

```mermaid
stateDiagram-v2
    [*] --> Flat: Initialize with cash
    
    Flat --> Long: Buy order filled
    Long --> Flat: Sell to close
    Long --> LongIncrease: Buy more
    LongIncrease --> Long
    Long --> Short: Sell more than position
    
    Flat --> Short: Sell order filled
    Short --> Flat: Buy to cover
    Short --> ShortIncrease: Sell more
    ShortIncrease --> Short
    Short --> Long: Buy more than short position
    
    note right of Long
        Quantity > 0
        Unrealized P&L updating
        with market price
    end note
    
    note left of Short
        Quantity < 0
        Unrealized P&L updating
        inversely
    end note
    
    note right of Flat
        Quantity = 0
        Only cash, no positions
        Realized P&L locked in
    end note
```

## Strategy Development Pattern

```mermaid
flowchart TD
    subgraph "Strategy Implementation"
        Define[Define Strategy Class<br/>Inherit from Strategy]
        Init[Implement initialize<br/>Setup indicators]
        Logic[Implement on_data<br/>Trading logic]
        Fill[Optional: on_fill<br/>Track executions]
        Final[Optional: finalize<br/>Cleanup]
    end
    
    subgraph "Testing"
        Unit[Unit Tests<br/>Mock data]
        Integration[Integration Tests<br/>Full backtest]
        Validation[Validate Results<br/>Check metrics]
    end
    
    subgraph "Deployment"
        Config[Configure Engine<br/>Set parameters]
        Run[Run Backtest<br/>Historical data]
        Analyze[Analyze Results<br/>Optimize]
    end
    
    Define --> Init
    Init --> Logic
    Logic --> Fill
    Fill --> Final
    
    Final --> Unit
    Unit --> Integration
    Integration --> Validation
    
    Validation --> Config
    Config --> Run
    Run --> Analyze
    Analyze -->|Iterate| Logic
    
    style Define fill:#7ED321
    style Analyze fill:#BD10E0
```

## Performance Analytics Flow

```mermaid
flowchart LR
    subgraph "Input"
        EC[Equity Curve]
        Trades[Trade History]
        Config[Backtest Config]
    end
    
    subgraph "Metrics Calculation"
        Returns[Calculate<br/>Returns]
        Risk[Risk<br/>Metrics]
        DrawDown[Drawdown<br/>Analysis]
        TradeStats[Trade<br/>Statistics]
    end
    
    subgraph "Output"
        TotalReturn[Total Return]
        Sharpe[Sharpe Ratio]
        MaxDD[Max Drawdown]
        WinRate[Win Rate]
        Report[Full Report]
    end
    
    EC --> Returns
    EC --> Risk
    EC --> DrawDown
    Trades --> TradeStats
    
    Returns --> TotalReturn
    Risk --> Sharpe
    DrawDown --> MaxDD
    TradeStats --> WinRate
    
    TotalReturn --> Report
    Sharpe --> Report
    MaxDD --> Report
    WinRate --> Report
    
    style Report fill:#BD10E0
```

## Multi-Symbol Handling

```mermaid
flowchart TD
    Start[Start with Symbol List] --> Fetch[Fetch Data for All Symbols]
    Fetch --> Align[Align Timestamps<br/>Fill Missing Data]
    Align --> Loop{For Each<br/>Timestamp}
    
    Loop -->|Process| ExtractData[Extract Current<br/>Data for All Symbols]
    ExtractData --> Strategy[Pass to Strategy]
    Strategy --> Orders{Orders<br/>Generated?}
    
    Orders -->|Yes| MultiSymbol{Multiple<br/>Symbols?}
    MultiSymbol -->|No| SingleExec[Execute Single Order]
    MultiSymbol -->|Yes| BatchExec[Execute Orders<br/>Sequentially]
    
    SingleExec --> UpdateAll[Update All Positions]
    BatchExec --> UpdateAll
    
    UpdateAll --> Loop
    
    Orders -->|No| Loop
    Loop -->|Done| End[Complete Backtest]
    
    style MultiSymbol fill:#F5A623
```

## Extension Points

```mermaid
mindmap
  root((Backtesting<br/>Engine))
    Strategy
      Custom Logic
      Multiple Strategies
      Strategy Allocation
    Data Provider
      Yahoo Finance
      CSV Files
      Database
      Real-time Feeds
      Custom Sources
    Broker
      Simple Slippage
      Volume-based
      Market Impact
      Partial Fills
    Analytics
      Basic Metrics
      Risk Analysis
      Attribution
      Comparison
    Risk Management
      Position Limits
      Stop Loss
      Portfolio Heat
      Correlation
```

## Usage

These diagrams are rendered automatically on GitHub when viewing markdown files. You can also:

1. **Copy to other docs**: Embed these Mermaid diagrams in any markdown file
2. **Render locally**: Use Mermaid Live Editor (https://mermaid.live/)
3. **Export**: Convert to PNG/SVG using Mermaid CLI
4. **Customize**: Modify colors, layout, and content as needed

## Diagram Updates

When updating the architecture, update the corresponding diagrams to maintain consistency between documentation and implementation.

**Last Updated**: 2026-02-17
