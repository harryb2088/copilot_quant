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


def generate_portfolio_metrics():
    """Generate mock portfolio-level metrics"""
    return {
        'portfolio_value': 1250000.00,
        'initial_capital': 1000000.00,
        'cash_balance': 312500.00,
        'positions_value': 937500.00,
        'total_return': 0.25,
        'sharpe_ratio': 1.85,
        'max_drawdown': -0.087,
        'net_exposure': 0.75,
        'gross_exposure': 0.95,
        'long_exposure': 0.85,
        'short_exposure': 0.10,
        'leverage_ratio': 1.15,
        'num_positions': 8,
        'largest_position': 0.105,
        'avg_position_size': 0.075,
        'turnover_annual': 0.45
    }


def generate_cash_history(days=90):
    """Generate mock cash balance history"""
    import numpy as np
    
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    np.random.seed(42)
    cash_history = 300000 + np.cumsum(np.random.normal(0, 5000, len(dates)))
    
    return pd.DataFrame({
        'Date': dates,
        'Cash': cash_history
    })


def generate_exposure_history(days=90):
    """Generate mock exposure history"""
    import numpy as np
    
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    np.random.seed(42)
    
    # Generate exposure with some variation
    gross_exposure = 0.85 + np.cumsum(np.random.normal(0, 0.01, len(dates)))
    gross_exposure = np.clip(gross_exposure, 0.7, 1.0)
    
    net_exposure = 0.70 + np.cumsum(np.random.normal(0, 0.008, len(dates)))
    net_exposure = np.clip(net_exposure, 0.5, 0.9)
    
    return pd.DataFrame({
        'Date': dates,
        'Gross_Exposure': gross_exposure,
        'Net_Exposure': net_exposure
    })


def generate_leverage_history(days=90):
    """Generate mock leverage ratio history"""
    import numpy as np
    
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    np.random.seed(42)
    
    leverage = 1.0 + np.cumsum(np.random.normal(0, 0.01, len(dates)))
    leverage = np.clip(leverage, 1.0, 1.5)
    
    return pd.DataFrame({
        'Date': dates,
        'Leverage': leverage
    })


def generate_sector_breakdown():
    """Generate mock sector allocation breakdown"""
    return pd.DataFrame({
        'Sector': ['Technology', 'Healthcare', 'Financials', 'Consumer', 'Energy'],
        'Exposure': [0.35, 0.20, 0.15, 0.15, 0.10],
        'P&L': [5850, 1200, 1400, 650, -300]
    })


def generate_asset_attribution():
    """Generate mock P&L attribution by asset"""
    return pd.DataFrame({
        'Symbol': ['AAPL', 'NVDA', 'MSFT', 'META', 'JPM', 'AMZN', 'GOOGL', 'TSLA'],
        'P&L': [3400, 4275, -1575, 1134, 1400, 810, 720, -710],
        'Contribution': [0.34, 0.43, -0.16, 0.11, 0.14, 0.08, 0.07, -0.07]
    })


def generate_risk_metrics():
    """Generate mock advanced risk metrics"""
    return {
        'var_95': -23500,
        'cvar_95': -31200,
        'beta_spy': 1.12,
        'correlation_spy': 0.78,
        'information_ratio': 0.85,
        'tracking_error': 0.082,
        'downside_deviation': 0.123
    }


def generate_liquidity_metrics():
    """Generate mock liquidity metrics"""
    return {
        'turnover_30d': 0.45,
        'avg_holding_period': 87,
        'cash_to_equity': 0.25,
        'avg_daily_volume': 125000,
        'position_concentration': 0.105,
        'largest_position_symbol': 'MSFT',
        'top_5_concentration': 0.405
    }


def generate_price_data_with_signals(symbol='AAPL', days=365):
    """
    Generate mock price data with buy/sell signals for visualization.
    
    Args:
        symbol: Stock symbol
        days: Number of days of data to generate
    
    Returns:
        Tuple of (price_df, signals_df):
            - price_df: DataFrame with Date and Close columns
            - signals_df: DataFrame with timestamp, type ('BUY'/'SELL'), and price columns
    """
    np.random.seed(42)
    
    # Generate price data
    dates = pd.date_range(start='2023-01-01', periods=days, freq='D')
    base_price = 150.0
    
    # Simulate price movement with trend and noise
    trend = np.linspace(0, 20, days)
    noise = np.random.normal(0, 2, days)
    prices = base_price + trend + np.cumsum(noise)
    prices = np.maximum(prices, 50)  # Ensure prices don't go too low
    
    price_df = pd.DataFrame({
        'Date': dates,
        'Close': prices
    })
    
    # Generate buy/sell signals (simulate strategy signals)
    signals = []
    num_signals = np.random.randint(20, 40)
    signal_indices = sorted(np.random.choice(range(10, days-10), num_signals, replace=False))
    
    for i, idx in enumerate(signal_indices):
        signal_type = 'BUY' if i % 2 == 0 else 'SELL'
        signals.append({
            'timestamp': dates[idx],
            'type': signal_type,
            'price': prices[idx],
            'quantity': np.random.randint(10, 100)
        })
    
    signals_df = pd.DataFrame(signals)
    
    return price_df, signals_df


def generate_trades_pnl_table():
    """
    Generate mock P&L table from matched buy/sell pairs.
    
    Returns:
        DataFrame with columns: Entry Time, Exit Time, Entry Price, Exit Price, 
                                Quantity, Side, Gross PnL, Cumulative PnL
    """
    np.random.seed(42)
    
    # Generate matched buy/sell pairs
    trades = []
    start_date = datetime(2023, 1, 1)
    
    num_trades = 15  # Number of complete trade pairs
    cumulative_pnl = 0
    
    for i in range(num_trades):
        # Entry
        entry_time = start_date + timedelta(days=np.random.randint(i*20, (i+1)*20))
        entry_price = np.random.uniform(140, 180)
        quantity = np.random.randint(10, 100)
        
        # Exit (a few days later)
        exit_time = entry_time + timedelta(days=np.random.randint(3, 15))
        # Simulate realistic price movement
        price_change = np.random.normal(0.02, 0.05)  # 2% average gain with 5% volatility
        exit_price = entry_price * (1 + price_change)
        
        # Calculate P&L
        gross_pnl = (exit_price - entry_price) * quantity
        cumulative_pnl += gross_pnl
        
        trades.append({
            'Entry Time': entry_time.strftime('%Y-%m-%d %H:%M'),
            'Exit Time': exit_time.strftime('%Y-%m-%d %H:%M'),
            'Entry Price': f'${entry_price:.2f}',
            'Exit Price': f'${exit_price:.2f}',
            'Quantity': quantity,
            'Side': 'Long',
            'Gross PnL': f'${gross_pnl:.2f}',
            'Cumulative PnL': f'${cumulative_pnl:.2f}'
        })
    
    return pd.DataFrame(trades)
