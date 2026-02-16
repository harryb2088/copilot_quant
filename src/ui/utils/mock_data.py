"""Mock data generators for UI development"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_mock_strategies():
    """Returns list of mock strategy dictionaries"""
    strategies = [
        {
            "id": "strat_001",
            "name": "Mean Reversion Alpha",
            "type": "Mean Reversion",
            "status": "Active",
            "last_modified": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
            "description": "Statistical arbitrage strategy based on mean reversion signals"
        },
        {
            "id": "strat_002",
            "name": "Momentum Breakout",
            "type": "Momentum",
            "status": "Active",
            "last_modified": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
            "description": "Trend following strategy with breakout confirmation"
        },
        {
            "id": "strat_003",
            "name": "Pairs Trading Strategy",
            "type": "Statistical Arbitrage",
            "status": "Draft",
            "last_modified": (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"),
            "description": "Cointegration-based pairs trading strategy"
        },
        {
            "id": "strat_004",
            "name": "Vol Surface Arbitrage",
            "type": "Volatility",
            "status": "Inactive",
            "last_modified": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            "description": "Options volatility surface trading strategy"
        }
    ]
    return strategies


def generate_mock_backtest_results():
    """Returns sample backtest data with equity curve"""
    # Generate equity curve data
    dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
    np.random.seed(42)
    
    # Simulate equity curve with upward drift
    returns = np.random.normal(0.001, 0.02, len(dates))
    equity = 100000 * np.cumprod(1 + returns)
    
    equity_df = pd.DataFrame({
        'Date': dates,
        'Equity': equity
    })
    
    # Calculate drawdown
    rolling_max = equity_df['Equity'].expanding().max()
    drawdown = (equity_df['Equity'] - rolling_max) / rolling_max * 100
    equity_df['Drawdown'] = drawdown
    
    # Performance metrics
    metrics = {
        "total_return": f"{((equity[-1] - 100000) / 100000 * 100):.2f}%",
        "sharpe_ratio": f"{np.random.uniform(1.2, 2.5):.2f}",
        "max_drawdown": f"{drawdown.min():.2f}%",
        "win_rate": f"{np.random.uniform(52, 65):.1f}%",
        "total_trades": np.random.randint(150, 500),
        "avg_trade": f"${np.random.uniform(50, 300):.2f}",
        "profit_factor": f"{np.random.uniform(1.3, 2.0):.2f}"
    }
    
    return equity_df, metrics


def generate_mock_trades():
    """Returns sample trade log DataFrame"""
    np.random.seed(42)
    n_trades = 50
    
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX']
    actions = ['BUY', 'SELL']
    
    trades = []
    start_date = datetime(2023, 1, 1)
    
    for i in range(n_trades):
        trade_date = start_date + timedelta(days=np.random.randint(0, 365))
        symbol = np.random.choice(symbols)
        action = np.random.choice(actions)
        quantity = np.random.randint(10, 200)
        price = np.random.uniform(50, 300)
        pnl = np.random.uniform(-500, 1500) if action == 'SELL' else 0
        
        trades.append({
            'Date': trade_date.strftime('%Y-%m-%d'),
            'Symbol': symbol,
            'Action': action,
            'Quantity': quantity,
            'Price': f"${price:.2f}",
            'P&L': f"${pnl:.2f}" if action == 'SELL' else "-"
        })
    
    trades_df = pd.DataFrame(trades)
    trades_df = trades_df.sort_values('Date', ascending=False).reset_index(drop=True)
    
    return trades_df


def generate_mock_positions():
    """Returns current positions DataFrame"""
    positions = [
        {
            'Symbol': 'AAPL',
            'Quantity': 150,
            'Entry Price': '$175.50',
            'Current Price': '$182.30',
            'P&L': '$1,020.00',
            'P&L %': '+3.87%'
        },
        {
            'Symbol': 'GOOGL',
            'Quantity': 80,
            'Entry Price': '$138.20',
            'Current Price': '$141.80',
            'P&L': '$288.00',
            'P&L %': '+2.60%'
        },
        {
            'Symbol': 'MSFT',
            'Quantity': 200,
            'Entry Price': '$380.00',
            'Current Price': '$375.50',
            'P&L': '-$900.00',
            'P&L %': '-1.18%'
        }
    ]
    
    return pd.DataFrame(positions)


def generate_mock_backtests():
    """Returns list of past backtests"""
    backtests = [
        {
            "id": "bt_001",
            "strategy": "Mean Reversion Alpha",
            "date_range": "2023-01-01 to 2023-12-31",
            "status": "Completed",
            "return": "+18.5%"
        },
        {
            "id": "bt_002",
            "strategy": "Momentum Breakout",
            "date_range": "2023-01-01 to 2023-12-31",
            "status": "Completed",
            "return": "+24.3%"
        },
        {
            "id": "bt_003",
            "strategy": "Pairs Trading Strategy",
            "date_range": "2023-06-01 to 2023-12-31",
            "status": "Running",
            "return": "-"
        },
        {
            "id": "bt_004",
            "strategy": "Mean Reversion Alpha",
            "date_range": "2022-01-01 to 2022-12-31",
            "status": "Completed",
            "return": "+12.7%"
        }
    ]
    return backtests
