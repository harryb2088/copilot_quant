"""
Dividend Data Utilities - Mock dividend information for portfolio stocks

Provides functions to generate mock dividend yield and payout history data
for display in the professional dashboard.
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd


def get_dividend_info(symbol):
    """
    Get dividend information for a given stock symbol.

    Args:
        symbol: Stock ticker symbol

    Returns:
        dict with dividend_yield, annual_dividend, next_ex_date, frequency
    """
    # Mock dividend data for common stocks
    dividend_data = {
        "AAPL": {"yield": 0.0052, "annual": 0.96, "frequency": "Quarterly"},
        "GOOGL": {"yield": 0.0000, "annual": 0.00, "frequency": "None"},
        "MSFT": {"yield": 0.0075, "annual": 3.00, "frequency": "Quarterly"},
        "AMZN": {"yield": 0.0000, "annual": 0.00, "frequency": "None"},
        "NVDA": {"yield": 0.0003, "annual": 0.16, "frequency": "Quarterly"},
        "META": {"yield": 0.0000, "annual": 0.00, "frequency": "None"},
        "TSLA": {"yield": 0.0000, "annual": 0.00, "frequency": "None"},
        "JPM": {"yield": 0.0243, "annual": 4.20, "frequency": "Quarterly"},
        "SPY": {"yield": 0.0125, "annual": 6.25, "frequency": "Quarterly"},
    }

    # Get data or use default
    data = dividend_data.get(symbol, {"yield": 0.0050, "annual": 2.50, "frequency": "Quarterly"})

    # Calculate next ex-dividend date (approximate)
    today = datetime.now()
    # Assume next ex-date is within next 30-90 days
    next_ex_date = today + timedelta(days=np.random.randint(30, 90))

    return {
        "dividend_yield": data["yield"],
        "annual_dividend": data["annual"],
        "next_ex_date": next_ex_date,
        "frequency": data["frequency"],
    }


def get_dividend_history(symbol, years=3):
    """
    Get historical dividend payout information.

    Args:
        symbol: Stock ticker symbol
        years: Number of years of history to generate

    Returns:
        DataFrame with columns: date, amount, yield_at_payment
    """
    div_info = get_dividend_info(symbol)

    # Only generate history for dividend-paying stocks
    if div_info["annual_dividend"] == 0:
        return pd.DataFrame(columns=["date", "amount", "yield_at_payment"])

    # Determine payment frequency
    if div_info["frequency"] == "Quarterly":
        payments_per_year = 4
    elif div_info["frequency"] == "Semi-Annual":
        payments_per_year = 2
    elif div_info["frequency"] == "Annual":
        payments_per_year = 1
    else:
        return pd.DataFrame(columns=["date", "amount", "yield_at_payment"])

    # Generate payment history
    total_payments = years * payments_per_year
    payment_amount = div_info["annual_dividend"] / payments_per_year

    # Create dates going back in time
    end_date = datetime.now()
    dates = []
    for i in range(total_payments):
        # Approximate quarterly payment schedule
        months_back = int((12 / payments_per_year) * i)
        payment_date = end_date - timedelta(days=months_back * 30)
        dates.append(payment_date)

    dates.reverse()  # Oldest to newest

    # Create DataFrame with slight variations in amount (to simulate real dividends)
    np.random.seed(hash(symbol) % 2**32)
    amounts = payment_amount + np.random.normal(0, payment_amount * 0.02, total_payments)
    amounts = np.maximum(amounts, 0)  # Ensure non-negative

    # Mock yield at time of payment (slight variation around current yield)
    yields = div_info["dividend_yield"] + np.random.normal(0, div_info["dividend_yield"] * 0.1, total_payments)
    yields = np.maximum(yields, 0)

    df = pd.DataFrame({"date": dates, "amount": amounts, "yield_at_payment": yields})

    return df


def get_portfolio_dividend_summary(positions_df):
    """
    Calculate portfolio-level dividend summary.

    Args:
        positions_df: DataFrame with Symbol, Quantity, Current Price columns

    Returns:
        dict with total_annual_income, portfolio_yield, monthly_income
    """
    total_annual_income = 0
    total_portfolio_value = 0

    for _, row in positions_df.iterrows():
        symbol = row["Symbol"]
        quantity = row["Quantity"]
        current_price = row["Current Price"]
        position_value = quantity * current_price

        div_info = get_dividend_info(symbol)
        annual_div_per_share = div_info["annual_dividend"]

        # Calculate this position's contribution
        position_annual_income = quantity * annual_div_per_share
        total_annual_income += position_annual_income
        total_portfolio_value += position_value

    # Calculate portfolio-level metrics
    portfolio_yield = total_annual_income / total_portfolio_value if total_portfolio_value > 0 else 0
    monthly_income = total_annual_income / 12

    return {
        "total_annual_income": total_annual_income,
        "portfolio_yield": portfolio_yield,
        "monthly_income": monthly_income,
        "quarterly_income": total_annual_income / 4,
    }


def get_next_dividend_calendar(positions_df, days_ahead=90):
    """
    Get upcoming dividend payments for portfolio positions.

    Args:
        positions_df: DataFrame with Symbol, Quantity columns
        days_ahead: Number of days to look ahead

    Returns:
        DataFrame with upcoming dividend payments sorted by date
    """
    calendar_entries = []

    for _, row in positions_df.iterrows():
        symbol = row["Symbol"]
        quantity = row["Quantity"]

        div_info = get_dividend_info(symbol)

        # Only include dividend-paying stocks
        if div_info["annual_dividend"] > 0:
            next_date = div_info["next_ex_date"]

            # Check if within the lookahead window
            if next_date <= datetime.now() + timedelta(days=days_ahead):
                payment_amount = div_info["annual_dividend"] / (4 if div_info["frequency"] == "Quarterly" else 1)
                total_payment = payment_amount * quantity

                calendar_entries.append(
                    {
                        "symbol": symbol,
                        "ex_date": next_date,
                        "payment_per_share": payment_amount,
                        "shares": quantity,
                        "total_payment": total_payment,
                        "yield": div_info["dividend_yield"],
                    }
                )

    if not calendar_entries:
        return pd.DataFrame(columns=["symbol", "ex_date", "payment_per_share", "shares", "total_payment", "yield"])

    df = pd.DataFrame(calendar_entries)
    df = df.sort_values("ex_date")

    return df
