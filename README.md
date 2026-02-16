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
├── app.py                      # Main entry point
├── pages/                      # Multi-page application
│   ├── 1_🏠_Home.py           # Home dashboard
│   ├── 2_📊_Strategies.py     # Strategy management
│   ├── 3_🔬_Backtests.py      # Backtest configuration
│   ├── 4_📈_Results.py        # Results analysis
│   └── 5_🔴_Live_Trading.py   # Paper trading interface
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
