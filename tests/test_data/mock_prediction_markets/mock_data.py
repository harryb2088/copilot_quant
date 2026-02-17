"""Mock data generators for prediction market tests."""

import pandas as pd
from datetime import datetime, timedelta


def generate_mock_polymarket_markets():
    """Generate mock Polymarket markets data."""
    return pd.DataFrame([
        {
            'market_id': 'mock_condition_123',
            'title': 'Will BTC reach $100k by end of 2024?',
            'category': 'Crypto',
            'close_time': datetime(2024, 12, 31, 23, 59),
            'status': 'active',
            'volume': 150000.50,
            'liquidity': 25000.0,
        },
        {
            'market_id': 'mock_condition_456',
            'title': 'Will S&P 500 close above 5000?',
            'category': 'Finance',
            'close_time': datetime(2024, 6, 30, 23, 59),
            'status': 'active',
            'volume': 250000.75,
            'liquidity': 50000.0,
        },
    ])


def generate_mock_polymarket_price_data():
    """Generate mock Polymarket price history."""
    dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='D')
    return pd.DataFrame({
        'timestamp': dates,
        'price': [0.45, 0.47, 0.48, 0.46, 0.50, 0.52, 0.51, 0.53, 0.54, 0.55],
        'volume': [1000, 1200, 1100, 1300, 1500, 1400, 1600, 1700, 1800, 1900],
    }).set_index('timestamp')


def generate_mock_kalshi_markets():
    """Generate mock Kalshi markets data."""
    return pd.DataFrame([
        {
            'market_id': 'INX-24JUN30-T5000',
            'title': 'S&P 500 above 5000 on June 30',
            'category': 'Finance',
            'close_time': datetime(2024, 6, 30, 16, 0),
            'status': 'open',
            'volume': 50000.0,
            'liquidity': 0.0,
        },
        {
            'market_id': 'FED-24DEC31-GT450',
            'title': 'Fed Funds Rate above 4.5% on Dec 31',
            'category': 'Economics',
            'close_time': datetime(2024, 12, 31, 16, 0),
            'status': 'open',
            'volume': 75000.0,
            'liquidity': 0.0,
        },
    ])


def generate_mock_kalshi_price_data():
    """Generate mock Kalshi price history."""
    dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='D')
    return pd.DataFrame({
        'timestamp': dates,
        'price': [0.60, 0.61, 0.62, 0.63, 0.64, 0.65, 0.64, 0.66, 0.67, 0.68],
        'volume': [500, 550, 600, 650, 700, 750, 800, 850, 900, 950],
    }).set_index('timestamp')


def generate_mock_predictit_markets():
    """Generate mock PredictIt markets data."""
    return pd.DataFrame([
        {
            'market_id': '7890',
            'title': 'Which party will win the White House?',
            'category': 'politics',
            'close_time': datetime(2024, 11, 5, 23, 59),
            'status': 'Open',
            'volume': 0.0,
            'liquidity': 0.0,
        },
        {
            'market_id': '7891',
            'title': 'Will unemployment be below 4% in December?',
            'category': 'economics',
            'close_time': datetime(2024, 12, 31, 23, 59),
            'status': 'Open',
            'volume': 0.0,
            'liquidity': 0.0,
        },
    ])


def generate_mock_predictit_contract_data():
    """Generate mock PredictIt contract data."""
    return pd.DataFrame([
        {
            'contract_id': '12345',
            'contract_name': 'Democratic',
            'last_trade_price': 0.52,
            'best_buy_yes': 0.53,
            'best_buy_no': 0.48,
            'best_sell_yes': 0.54,
            'best_sell_no': 0.47,
        },
        {
            'contract_id': '12346',
            'contract_name': 'Republican',
            'last_trade_price': 0.46,
            'best_buy_yes': 0.47,
            'best_buy_no': 0.52,
            'best_sell_yes': 0.48,
            'best_sell_no': 0.51,
        },
    ])


def generate_mock_metaculus_markets():
    """Generate mock Metaculus questions data."""
    return pd.DataFrame([
        {
            'market_id': '10001',
            'title': 'Will AGI be developed by 2030?',
            'category': 'AI',
            'close_time': datetime(2030, 1, 1, 0, 0),
            'status': 'open',
            'volume': 0.0,
            'liquidity': 0.0,
            'num_predictions': 450,
            'community_prediction': 0.35,
        },
        {
            'market_id': '10002',
            'title': 'Will global temperatures increase by 1.5C by 2035?',
            'category': 'Climate',
            'close_time': datetime(2035, 12, 31, 23, 59),
            'status': 'open',
            'volume': 0.0,
            'liquidity': 0.0,
            'num_predictions': 680,
            'community_prediction': 0.72,
        },
    ])


def generate_mock_metaculus_prediction_data():
    """Generate mock Metaculus prediction history."""
    dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='D')
    return pd.DataFrame({
        'timestamp': dates,
        'prediction': [0.30, 0.31, 0.32, 0.33, 0.34, 0.35, 0.34, 0.36, 0.37, 0.38],
        'q1': [0.20, 0.21, 0.22, 0.23, 0.24, 0.25, 0.24, 0.26, 0.27, 0.28],
        'q2': [0.30, 0.31, 0.32, 0.33, 0.34, 0.35, 0.34, 0.36, 0.37, 0.38],
        'q3': [0.40, 0.41, 0.42, 0.43, 0.44, 0.45, 0.44, 0.46, 0.47, 0.48],
    }).set_index('timestamp')
