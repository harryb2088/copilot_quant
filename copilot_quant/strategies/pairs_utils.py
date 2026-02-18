"""
Utilities for pairs trading and statistical arbitrage.

This module provides statistical tests and calculations needed for
pairs trading strategies, including cointegration tests, correlation
analysis, and spread calculations.
"""

from typing import List, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import coint


def test_cointegration(
    series1: pd.Series,
    series2: pd.Series,
    significance_level: float = 0.05
) -> Tuple[bool, float, float]:
    """
    Test if two price series are cointegrated using Engle-Granger test.
    
    Cointegration indicates a stable long-term relationship between two
    time series, which is ideal for pairs trading.
    
    Args:
        series1: First price series
        series2: Second price series
        significance_level: P-value threshold for cointegration (default: 0.05)
    
    Returns:
        Tuple of (is_cointegrated, p_value, test_statistic)
        - is_cointegrated: True if series are cointegrated at significance level
        - p_value: P-value from the cointegration test
        - test_statistic: Test statistic from the cointegration test
    
    Example:
        >>> is_coint, pvalue, stat = test_cointegration(prices1, prices2)
        >>> if is_coint:
        ...     print(f"Series are cointegrated (p={pvalue:.4f})")
    """
    # Remove NaN values
    df = pd.DataFrame({'s1': series1, 's2': series2}).dropna()
    
    if len(df) < 30:  # Need sufficient data
        return False, 1.0, 0.0
    
    # Perform Engle-Granger cointegration test
    # Returns (test_statistic, p_value, critical_values)
    test_stat, p_value, crit_values = coint(df['s1'], df['s2'])
    
    is_cointegrated = p_value < significance_level
    
    return is_cointegrated, p_value, test_stat


def calculate_correlation(
    series1: pd.Series,
    series2: pd.Series,
    method: str = 'pearson'
) -> float:
    """
    Calculate correlation between two price series.
    
    Args:
        series1: First price series
        series2: Second price series
        method: Correlation method ('pearson', 'spearman', 'kendall')
    
    Returns:
        Correlation coefficient between -1 and 1
    
    Example:
        >>> corr = calculate_correlation(prices1, prices2)
        >>> print(f"Correlation: {corr:.3f}")
    """
    # Remove NaN values
    df = pd.DataFrame({'s1': series1, 's2': series2}).dropna()
    
    if len(df) < 2:
        return 0.0
    
    return df['s1'].corr(df['s2'], method=method)


def calculate_hedge_ratio(
    series1: pd.Series,
    series2: pd.Series,
    method: str = 'ols'
) -> float:
    """
    Calculate hedge ratio for pair trading.
    
    The hedge ratio determines how many units of series2 to trade
    for each unit of series1 to create a market-neutral spread.
    
    Args:
        series1: First price series (dependent variable)
        series2: Second price series (independent variable)
        method: Calculation method ('ols' for ordinary least squares)
    
    Returns:
        Hedge ratio (beta coefficient from regression)
    
    Example:
        >>> ratio = calculate_hedge_ratio(prices1, prices2)
        >>> spread = prices1 - ratio * prices2
    """
    # Remove NaN values
    df = pd.DataFrame({'s1': series1, 's2': series2}).dropna()
    
    if len(df) < 2:
        return 1.0
    
    if method == 'ols':
        # Ordinary least squares regression: s1 = alpha + beta * s2
        # We want beta (the slope)
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            df['s2'], df['s1']
        )
        return slope
    else:
        # Simple ratio method (less robust)
        return (df['s1'] / df['s2']).mean()


def calculate_spread(
    series1: pd.Series,
    series2: pd.Series,
    hedge_ratio: float = None
) -> pd.Series:
    """
    Calculate spread between two price series.
    
    The spread is the difference between series1 and hedge_ratio * series2.
    If no hedge ratio is provided, it will be calculated automatically.
    
    Args:
        series1: First price series
        series2: Second price series
        hedge_ratio: Optional hedge ratio. If None, calculated automatically.
    
    Returns:
        Series containing the spread values
    
    Example:
        >>> spread = calculate_spread(prices1, prices2)
        >>> print(f"Current spread: {spread.iloc[-1]:.2f}")
    """
    if hedge_ratio is None:
        hedge_ratio = calculate_hedge_ratio(series1, series2)
    
    spread = series1 - hedge_ratio * series2
    return spread


def calculate_zscore(
    series: pd.Series,
    window: int = None,
    min_periods: int = None
) -> pd.Series:
    """
    Calculate rolling Z-score of a series.
    
    Z-score measures how many standard deviations the current value
    is from the mean. Used to identify mean-reversion opportunities.
    
    Args:
        series: Input series (e.g., spread)
        window: Rolling window size. If None, uses entire series.
        min_periods: Minimum observations for calculation
    
    Returns:
        Series containing Z-scores
    
    Example:
        >>> zscore = calculate_zscore(spread, window=60)
        >>> if zscore.iloc[-1] > 2.0:
        ...     print("Spread is 2 std devs above mean - short opportunity")
    """
    if window is None:
        # Use entire series
        mean = series.mean()
        std = series.std()
        zscore = (series - mean) / std if std > 0 else pd.Series(0, index=series.index)
    else:
        # Use rolling window
        if min_periods is None:
            min_periods = window // 2
        
        rolling_mean = series.rolling(window=window, min_periods=min_periods).mean()
        rolling_std = series.rolling(window=window, min_periods=min_periods).std()
        
        # Avoid division by zero
        zscore = (series - rolling_mean) / rolling_std.where(rolling_std > 0, 1.0)
    
    return zscore


def find_cointegrated_pairs(
    prices: pd.DataFrame,
    significance_level: float = 0.05,
    min_correlation: float = 0.5
) -> List[Tuple[str, str, float, float]]:
    """
    Find all cointegrated pairs from a dataframe of price series.
    
    Tests all possible pairs and returns those that are both correlated
    and cointegrated.
    
    Args:
        prices: DataFrame where each column is a price series for a symbol
        significance_level: P-value threshold for cointegration test
        min_correlation: Minimum correlation to consider
    
    Returns:
        List of tuples: (symbol1, symbol2, p_value, correlation)
        Sorted by p-value (most significant first)
    
    Example:
        >>> prices_df = pd.DataFrame({'AAPL': prices_aapl, 'MSFT': prices_msft})
        >>> pairs = find_cointegrated_pairs(prices_df)
        >>> for sym1, sym2, pval, corr in pairs:
        ...     print(f"{sym1}-{sym2}: p={pval:.4f}, corr={corr:.3f}")
    """
    symbols = prices.columns.tolist()
    cointegrated_pairs = []
    
    # Test all unique pairs
    for i in range(len(symbols)):
        for j in range(i + 1, len(symbols)):
            sym1, sym2 = symbols[i], symbols[j]
            
            # Get price series
            s1 = prices[sym1].dropna()
            s2 = prices[sym2].dropna()
            
            # Need overlapping data
            if len(s1) < 30 or len(s2) < 30:
                continue
            
            # Calculate correlation
            corr = calculate_correlation(s1, s2)
            
            # Only test pairs with sufficient correlation
            if abs(corr) < min_correlation:
                continue
            
            # Test cointegration
            is_coint, p_value, test_stat = test_cointegration(s1, s2)
            
            if is_coint:
                cointegrated_pairs.append((sym1, sym2, p_value, corr))
    
    # Sort by p-value (most significant first)
    cointegrated_pairs.sort(key=lambda x: x[2])
    
    return cointegrated_pairs


def calculate_half_life(spread: pd.Series) -> float:
    """
    Calculate mean-reversion half-life of a spread.
    
    The half-life is the expected time for the spread to revert
    halfway back to its mean. Shorter half-life indicates faster
    mean reversion.
    
    Args:
        spread: Spread time series
    
    Returns:
        Half-life in number of periods (same as spread frequency)
        Returns np.inf if spread does not mean-revert
    
    Example:
        >>> half_life = calculate_half_life(spread)
        >>> print(f"Expected mean-reversion time: {half_life:.1f} days")
    """
    # Remove NaN values
    spread_clean = spread.dropna()
    
    if len(spread_clean) < 2:
        return np.inf
    
    # Calculate lagged spread and change in spread
    spread_lag = spread_clean.shift(1).dropna()
    spread_diff = spread_clean.diff().dropna()
    
    # Align the series
    spread_lag = spread_lag.iloc[1:]
    spread_diff = spread_diff.iloc[1:]
    
    if len(spread_lag) < 2:
        return np.inf
    
    # Regression: spread_diff = lambda * spread_lag
    # Half-life = -log(2) / lambda
    try:
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            spread_lag, spread_diff
        )
        
        # lambda should be negative for mean reversion
        if slope >= 0:
            return np.inf
        
        half_life = -np.log(2) / slope
        
        # Sanity check
        if half_life <= 0 or half_life > len(spread_clean):
            return np.inf
        
        return half_life
    except Exception:
        # Catch regression errors (e.g., singular matrix, numerical issues)
        return np.inf
