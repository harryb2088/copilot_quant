"""
S&P500 constituent management utilities.

This module provides functionality to fetch and manage the list of S&P500 constituents.
"""

import logging
from typing import List

import pandas as pd

logger = logging.getLogger(__name__)


def get_sp500_tickers(
    include_index: bool = False,
    source: str = "wikipedia"
) -> List[str]:
    """
    Get list of S&P500 constituent ticker symbols.

    Args:
        include_index: If True, includes '^GSPC' (S&P500 index) in the list
        source: Data source - 'wikipedia' (default) or 'manual'

    Returns:
        List of ticker symbols

    Example:
        >>> tickers = get_sp500_tickers()
        >>> print(f"Found {len(tickers)} S&P500 stocks")
        >>> print(tickers[:5])  # First 5 tickers

    Note:
        Wikipedia is the most reliable free source for current S&P500 constituents.
        The list is updated regularly when companies are added/removed from the index.
    """
    if source == "wikipedia":
        return _get_sp500_from_wikipedia(include_index)
    elif source == "manual":
        return _get_sp500_manual_list(include_index)
    else:
        raise ValueError(f"Unknown source: {source}. Use 'wikipedia' or 'manual'")


def _get_sp500_from_wikipedia(include_index: bool = False) -> List[str]:
    """
    Fetch S&P500 constituents from Wikipedia.

    This is the recommended method as Wikipedia maintains an up-to-date list.

    Args:
        include_index: If True, includes '^GSPC' in the list

    Returns:
        List of ticker symbols
    """
    try:
        # Wikipedia maintains the list of S&P500 companies
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

        # Read the first table which contains current constituents
        tables = pd.read_html(url)
        sp500_table = tables[0]

        # Extract ticker symbols
        tickers = sp500_table["Symbol"].tolist()

        # Clean up tickers (some may have special formatting)
        tickers = [ticker.replace(".", "-") for ticker in tickers]  # Handle BRK.B -> BRK-B

        logger.info(f"Retrieved {len(tickers)} S&P500 tickers from Wikipedia")

        if include_index:
            tickers.append("^GSPC")

        return sorted(tickers)

    except Exception as e:
        logger.error(f"Error fetching S&P500 list from Wikipedia: {e}")
        logger.warning("Falling back to manual list")
        return _get_sp500_manual_list(include_index)


def _get_sp500_manual_list(include_index: bool = False) -> List[str]:
    """
    Fallback manual list of major S&P500 constituents.

    This is a subset of major stocks for testing when Wikipedia is unavailable.

    Args:
        include_index: If True, includes '^GSPC' in the list

    Returns:
        List of ticker symbols
    """
    # Major S&P500 stocks (top holdings by weight) - for testing/fallback
    tickers = [
        # Technology
        "AAPL", "MSFT", "NVDA", "GOOGL", "GOOG", "AMZN", "META", "TSLA", "AVGO", "ORCL",
        "ADBE", "CRM", "CSCO", "ACN", "AMD", "INTC", "TXN", "QCOM", "INTU", "IBM",
        # Financials
        "BRK-B", "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "SPGI", "BLK",
        "C", "AXP", "SCHW", "CB", "PGR", "MMC", "ICE", "CME", "AON", "TFC",
        # Healthcare
        "UNH", "JNJ", "LLY", "ABBV", "MRK", "PFE", "TMO", "ABT", "DHR", "CVS",
        "AMGN", "BMY", "MDT", "GILD", "CI", "ISRG", "REGN", "VRTX", "HCA", "SYK",
        # Consumer
        "WMT", "HD", "COST", "PG", "KO", "PEP", "MCD", "NKE", "DIS", "SBUX",
        "PM", "LOW", "TGT", "TJX", "CMG", "BKNG", "ABNB", "MAR", "YUM", "MO",
        # Communication
        "T", "VZ", "NFLX", "CMCSA", "CHTR", "EA", "TTWO", "MTCH", "NWSA", "FOXA",
        # Industrials
        "BA", "CAT", "HON", "UNP", "RTX", "UPS", "DE", "LMT", "GE", "MMM",
        # Energy
        "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "KMI",
    ]

    logger.info(f"Using manual list with {len(tickers)} major S&P500 stocks")

    if include_index:
        tickers.append("^GSPC")

    return sorted(tickers)


def get_sp500_info() -> pd.DataFrame:
    """
    Get detailed information about S&P500 constituents.

    Returns:
        DataFrame with columns: Symbol, Security, GICS Sector, GICS Sub-Industry,
        Location, Date Added, CIK, Founded

    Example:
        >>> info = get_sp500_info()
        >>> print(info[['Symbol', 'Security', 'GICS Sector']].head())
        >>> # Filter by sector
        >>> tech_stocks = info[info['GICS Sector'] == 'Information Technology']
    """
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        sp500_info = tables[0]

        # Clean up ticker symbols
        sp500_info["Symbol"] = sp500_info["Symbol"].str.replace(".", "-")

        logger.info(f"Retrieved detailed info for {len(sp500_info)} S&P500 companies")
        return sp500_info

    except Exception as e:
        logger.error(f"Error fetching S&P500 info: {e}")
        raise


def get_sp500_by_sector() -> dict:
    """
    Get S&P500 constituents grouped by GICS sector.

    Returns:
        Dictionary mapping sector names to lists of ticker symbols

    Example:
        >>> sectors = get_sp500_by_sector()
        >>> print(f"Sectors: {list(sectors.keys())}")
        >>> print(f"Tech stocks: {len(sectors['Information Technology'])}")
        >>> for sector, tickers in sectors.items():
        ...     print(f"{sector}: {len(tickers)} stocks")
    """
    try:
        info = get_sp500_info()
        sectors = {}

        for sector_name in info["GICS Sector"].unique():
            sector_tickers = info[info["GICS Sector"] == sector_name]["Symbol"].tolist()
            sectors[sector_name] = sorted(sector_tickers)

        logger.info(f"Grouped S&P500 stocks into {len(sectors)} sectors")
        return sectors

    except Exception as e:
        logger.error(f"Error grouping S&P500 by sector: {e}")
        raise


# Commonly used ticker lists
FAANG = ["META", "AAPL", "AMZN", "NFLX", "GOOGL"]
MAGNIFICENT_7 = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]
DOW_30_TICKERS = [
    "AAPL", "AMGN", "AXP", "BA", "CAT", "CRM", "CSCO", "CVX", "DIS", "DOW",
    "GS", "HD", "HON", "IBM", "INTC", "JNJ", "JPM", "KO", "MCD", "MMM",
    "MRK", "MSFT", "NKE", "PG", "TRV", "UNH", "V", "VZ", "WBA", "WMT",
]


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    print("Fetching S&P500 tickers...")
    tickers = get_sp500_tickers()
    print(f"\nFound {len(tickers)} S&P500 stocks")
    print(f"First 10: {tickers[:10]}")

    print("\n" + "="*60)
    print("Fetching S&P500 info by sector...")
    sectors = get_sp500_by_sector()
    for sector, stocks in sorted(sectors.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {sector}: {len(stocks)} stocks")

    print("\n" + "="*60)
    print(f"FAANG stocks: {FAANG}")
    print(f"Magnificent 7: {MAGNIFICENT_7}")
