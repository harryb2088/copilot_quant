# Copilot Quant Platform

A comprehensive algorithmic trading platform for strategy development, backtesting, and paper trading.

## 🚀 Features

- **Strategy Development**: Create and manage custom trading strategies
- **Backtesting Engine**: Test strategies against historical market data
- **Performance Analytics**: Comprehensive metrics, charts, and visualizations
- **Paper Trading**: Safe testing environment with real market data
- **Multi-Page UI**: Clean, intuitive Streamlit web interface

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/harryb2088/copilot_quant.git
cd copilot_quant
```

2. Install dependencies:
```bash
pip install -r requirements.in
```

Or if using pip-tools:
```bash
pip install pip-tools
pip-compile requirements.in
pip install -r requirements.txt
```

## 🚀 Running the Application

Start the Streamlit web application:

```bash
streamlit run src/ui/app.py
```

The application will launch in your default web browser at `http://localhost:8501`

## 📱 Application Structure

```
src/ui/
├── app.py                      # Main entry point (Home page)
├── pages/                      # Multi-page application
│   ├── 1_📊_Strategies.py     # Strategy management
│   ├── 2_🔬_Backtests.py      # Backtest configuration
│   ├── 3_📈_Results.py        # Results analysis
│   └── 4_🔴_Live_Trading.py   # Paper trading interface
├── components/                 # Shared UI components
│   ├── sidebar.py             # Navigation sidebar
│   ├── charts.py              # Chart components
│   └── tables.py              # Table components
└── utils/                      # Utility functions
    ├── session.py             # Session state management
    └── mock_data.py           # Mock data generators
```

## 🎯 Quick Start Guide

1. **Home Page**: Overview and quick stats dashboard
2. **Strategies**: Browse and create trading strategies
3. **Backtests**: Configure and run historical simulations
4. **Results**: Analyze performance metrics and charts
5. **Live Trading**: Deploy strategies in paper trading mode

## ⚠️ Safety Notice

**This platform currently operates in PAPER TRADING ONLY mode.**

- No real money is at risk
- All trades are simulated
- Uses real market data for realistic testing
- Safe environment for learning and testing strategies

## 🔧 Development

Current Status: **v0.1.0-alpha**

This is a development version with UI skeleton and mock data.
Backend integration and live data feeds are in progress.

## 📝 License

Copyright © 2024 Copilot Quant Platform

## 🤝 Contributing

This is a personal project. Contributions are welcome!

## 📧 Contact

For questions or support, please open an issue on GitHub.
# copilot_quant 📈

A quantitative trading platform built with modern Python tools for backtesting, strategy development, and automated trading.

## 🎯 Project Goals

copilot_quant aims to provide a comprehensive, modular platform for:
- **Backtesting** trading strategies with historical data
- **Live trading** through broker integrations (Interactive Brokers)
- **Strategy development** with a clean, testable architecture
- **Data management** for market data (S&P 500 via Yahoo Finance)
- **Visualization** through an intuitive Streamlit UI

## ⚠️ Safety Notice

**ALWAYS START WITH PAPER TRADING**
- This platform supports live trading through Interactive Brokers
- Test all strategies thoroughly in paper trading mode before using real capital
- Trading involves risk of loss - never trade with money you cannot afford to lose

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/harryb2088/copilot_quant.git
   cd copilot_quant
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## 📁 Project Structure

```
copilot_quant/
├── copilot_quant/           # Source code
│   ├── data/               # Data ingestion & storage
│   ├── backtest/           # Backtesting engine
│   ├── strategies/         # Trading strategies
│   ├── brokers/            # Broker connectors (IBKR, etc.)
│   ├── ui/                 # Streamlit UI components
│   └── utils/              # Shared utilities
├── tests/                  # Test suite (mirrors copilot_quant structure)
├── data/                   # Local data storage (CSV/SQLite)
├── notebooks/              # Jupyter notebooks for analysis
├── docs/                   # Documentation
├── .github/workflows/      # CI/CD pipelines
├── requirements.in         # Dependency specification
├── requirements.txt        # Pinned dependencies (pip-tools)
└── README.md              # This file
```

## 🧪 Running Tests

Run the full test suite:
```bash
pytest tests/
```

Run tests with coverage:
```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

## 🔍 Linting

We use **ruff** for fast Python linting:

```bash
# Check for issues
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/
```

## 📊 Running Backtests

*(Coming soon - backtesting functionality will be added in future releases)*

Example usage (pseudocode):
```python
# PSEUDOCODE EXAMPLE – BacktestEngine and SampleStrategy are not yet implemented
# from copilot_quant.backtest import BacktestEngine
# from copilot_quant.strategies import SampleStrategy

# Initialize backtest
# engine = BacktestEngine(
#     strategy=SampleStrategy(),
#     start_date='2023-01-01',
#     end_date='2024-01-01'
# )

# Run backtest
# results = engine.run()
# print(results.summary())
```

## 🖥️ Running the Streamlit UI

*(Coming soon - UI functionality will be added in future releases)*

The Streamlit-based web interface is not yet available in this version of the project, and no UI entrypoint script is currently provided.

Once the UI is implemented, this section will be updated with the exact command (for example, a `streamlit run` invocation) and entrypoint path to launch the app.

The planned UI will provide:
- Strategy configuration
- Backtest visualization
- Live trading dashboard
- Performance metrics

## 🔧 Development

### Adding Dependencies

We use **pip-tools** for dependency management:

1. Add your dependency to `requirements.in`
2. Compile the requirements:
   ```bash
   pip-compile requirements.in
   ```
3. Install updated dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines, code style, and pull request process.

## 📚 Documentation

- [Contributing Guidelines](CONTRIBUTING.md)
- [License](LICENSE) - MIT License

## 🛠️ Technology Stack

- **Data Processing**: pandas, numpy
- **Market Data**: yfinance
- **Broker Integration**: ib_insync
- **Database**: SQLAlchemy
- **UI**: Streamlit
- **Testing**: pytest
- **Linting**: ruff

## 📈 Features Roadmap

- [x] Project structure and infrastructure
- [ ] Data ingestion module (Yahoo Finance, CSV import)
- [ ] Backtesting engine core
- [ ] Basic trading strategies (Moving Average, Mean Reversion)
- [ ] Performance metrics and reporting
- [ ] Streamlit UI for strategy configuration
- [ ] Interactive Brokers integration (paper trading)
- [ ] Live trading capabilities
- [ ] Advanced risk management

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Acknowledgments

Built with modern Python tools and best practices for quantitative trading.
