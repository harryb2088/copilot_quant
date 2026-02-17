"""
Data Normalization Utilities

This module provides utilities for cleaning, standardizing, and normalizing
market data for use in backtesting and live trading.

Features:
- Symbol normalization and standardization across data sources
- Corporate action handling (splits, dividends, contract rolls)
- Time normalization (NYSE timezone for equities, UTC for prediction markets)
- Missing data detection and handling
- Data quality validation
- Price adjustment calculations

Example Usage:
    # Normalize symbol names across different data sources
    normalized = normalize_symbol('BRK.B', source='yahoo')  # Returns 'BRK-B'
    ib_symbol = normalize_symbol('BRK-B', source='ib')  # Returns 'BRK B'
    
    # Normalize timestamps to appropriate timezone
    df = normalize_timestamps(df, market_type='equity')  # NYSE timezone
    df = normalize_timestamps(df, market_type='prediction')  # UTC
    
    # Handle stock splits
    df = adjust_for_splits(df, split_ratio=2.0, split_date='2024-01-15')
    
    # Adjust for contract rolls
    df = adjust_for_contract_roll(df, roll_date='2024-03-15', adjustment=-0.25)
    
    # Validate data quality
    issues = validate_data_quality(df)
    if issues:
        print(f"Found {len(issues)} data quality issues")
"""

import logging
from typing import Dict, List, Optional
import pytz

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def normalize_symbol(symbol: str, source: str = 'yahoo') -> str:
    """
    Normalize stock ticker symbols to a standard format.
    
    Different data sources use different conventions for ticker symbols.
    This function standardizes them for consistent use across the platform.
    
    Supported sources:
    - yahoo/yfinance: Yahoo Finance format (uses hyphens)
    - alpha_vantage/alphavantage: Alpha Vantage format (uses dots)
    - quandl: Quandl/WIKI format (uses underscores for some tickers)
    - ib/interactive_brokers: Interactive Brokers format (uses spaces)
    - polygon: Polygon.io format (uses dots for class shares)
    - standard: Standard format (hyphens for class shares)
    
    Args:
        symbol: Raw ticker symbol
        source: Data source name
        
    Returns:
        Normalized ticker symbol
        
    Example:
        >>> normalize_symbol('BRK.B', source='yahoo')
        'BRK-B'
        >>> normalize_symbol('BRK-B', source='alpha_vantage')
        'BRK.B'
        >>> normalize_symbol('BRK-B', source='ib')
        'BRK B'
        >>> normalize_symbol('BRK/B', source='quandl')
        'BRK-B'
    """
    if not symbol:
        return symbol
        
    symbol = symbol.strip().upper()
    source = source.lower()
    
    # Yahoo Finance and most sources use hyphens for class shares
    if source in ['yahoo', 'yfinance', 'standard']:
        symbol = symbol.replace('.', '-').replace('/', '-').replace(' ', '-')
    
    # Alpha Vantage and Polygon use dots
    elif source in ['alpha_vantage', 'alphavantage', 'polygon']:
        symbol = symbol.replace('-', '.').replace('/', '.').replace(' ', '.')
    
    # Interactive Brokers uses spaces
    elif source in ['ib', 'interactive_brokers', 'interactivebrokers']:
        symbol = symbol.replace('.', ' ').replace('/', ' ').replace('-', ' ')
    
    # Quandl uses underscores or slashes for some tickers
    elif source == 'quandl':
        # Quandl WIKI data uses slashes, convert to hyphens
        symbol = symbol.replace('/', '-').replace('.', '-').replace(' ', '-')
    
    # Default to hyphens
    else:
        symbol = symbol.replace('.', '-').replace('/', '-').replace(' ', '-')
    
    return symbol


def validate_symbol(symbol: str, source: str = 'yahoo') -> bool:
    """
    Validate that a symbol is properly formatted for the given data source.
    
    Args:
        symbol: Ticker symbol to validate
        source: Data source name
        
    Returns:
        True if symbol is valid, False otherwise
        
    Example:
        >>> validate_symbol('AAPL', source='yahoo')
        True
        >>> validate_symbol('', source='yahoo')
        False
        >>> validate_symbol('BRK-B', source='yahoo')
        True
    """
    if not symbol or not isinstance(symbol, str):
        return False
    
    symbol = symbol.strip()
    if not symbol:
        return False
    
    # Basic validation - symbols should be alphanumeric with allowed separators
    allowed_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_./^ ')
    if not all(c in allowed_chars for c in symbol.upper()):
        return False
    
    # Source-specific validation
    source = source.lower()
    if source in ['yahoo', 'yfinance']:
        # Yahoo allows letters, numbers, hyphens, dots, and caret (for indices)
        return True
    elif source in ['ib', 'interactive_brokers']:
        # IB uses spaces for class shares
        return True
    
    return True


def normalize_timestamps(
    df: pd.DataFrame,
    market_type: str = 'equity',
    target_timezone: Optional[str] = None,
    timestamp_column: str = 'date'
) -> pd.DataFrame:
    """
    Normalize timestamps to appropriate timezone for the market type.
    
    Different market types operate in different timezones:
    - Equities: NYSE timezone (US/Eastern)
    - Futures: CME timezone (US/Central)  
    - Crypto: UTC
    - Prediction markets: UTC
    
    Args:
        df: DataFrame with timestamp data
        market_type: Type of market ('equity', 'futures', 'crypto', 'prediction')
        target_timezone: Explicit target timezone (overrides market_type default)
        timestamp_column: Name of the timestamp column or index
        
    Returns:
        DataFrame with normalized timestamps
        
    Example:
        >>> # Normalize equity data to NYSE timezone
        >>> df = normalize_timestamps(df, market_type='equity')
        
        >>> # Normalize prediction market data to UTC
        >>> df = normalize_timestamps(df, market_type='prediction')
        
        >>> # Explicit timezone conversion
        >>> df = normalize_timestamps(df, target_timezone='UTC')
    """
    df = df.copy()
    
    # Determine target timezone based on market type
    if target_timezone is None:
        timezone_map = {
            'equity': 'US/Eastern',  # NYSE
            'futures': 'US/Central',  # CME
            'crypto': 'UTC',
            'prediction': 'UTC',
            'forex': 'UTC',
        }
        target_timezone = timezone_map.get(market_type.lower(), 'UTC')
    
    # Get timezone object
    tz = pytz.timezone(target_timezone)
    
    # Handle timestamp column or index
    if timestamp_column in df.columns:
        # Convert column to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(df[timestamp_column]):
            df[timestamp_column] = pd.to_datetime(df[timestamp_column])
        
        # Localize or convert to target timezone
        if df[timestamp_column].dt.tz is None:
            # Naive datetime - localize to target timezone
            # Use 'infer' for ambiguous times during DST transitions
            # Use 'shift_forward' for nonexistent times (e.g., spring forward)
            df[timestamp_column] = df[timestamp_column].dt.tz_localize(
                tz, ambiguous='infer', nonexistent='shift_forward'
            )
        else:
            # Already timezone-aware - convert to target timezone
            df[timestamp_column] = df[timestamp_column].dt.tz_convert(tz)
            
        logger.info(f"Normalized {timestamp_column} to {target_timezone} timezone")
        
    elif isinstance(df.index, pd.DatetimeIndex):
        # Handle DatetimeIndex
        if df.index.tz is None:
            # Use 'infer' for ambiguous times during DST transitions
            # Use 'shift_forward' for nonexistent times (e.g., spring forward)
            df.index = df.index.tz_localize(
                tz, ambiguous='infer', nonexistent='shift_forward'
            )
        else:
            df.index = df.index.tz_convert(tz)
            
        logger.info(f"Normalized index to {target_timezone} timezone")
    
    else:
        logger.warning(f"No timestamp column '{timestamp_column}' found and index is not DatetimeIndex")
    
    return df


def adjust_for_contract_roll(
    df: pd.DataFrame,
    roll_date: str,
    adjustment: Optional[float] = None,
    front_contract_column: str = 'close',
    back_contract_column: Optional[str] = None,
    method: str = 'difference'
) -> pd.DataFrame:
    """
    Adjust historical prices for futures contract rolls.
    
    When futures contracts expire, positions must be rolled to the next contract.
    This creates discontinuities in the price series that need to be adjusted.
    
    Args:
        df: DataFrame with futures price data (must have date index or column)
        roll_date: Date of the contract roll in 'YYYY-MM-DD' format
        adjustment: Manual adjustment value. If None, calculated from data
        front_contract_column: Column containing front contract prices
        back_contract_column: Column containing back contract prices (for auto-calculation)
        method: Adjustment method - 'difference' (default) or 'ratio'
        
    Returns:
        DataFrame with roll-adjusted prices
        
    Example:
        >>> # Manual adjustment with known roll difference
        >>> df = adjust_for_contract_roll(
        ...     df, 
        ...     roll_date='2024-03-15',
        ...     adjustment=-0.25,  # Front contract was $0.25 cheaper
        ...     method='difference'
        ... )
        
        >>> # Automatic adjustment from front and back contract prices
        >>> df = adjust_for_contract_roll(
        ...     df,
        ...     roll_date='2024-03-15',
        ...     front_contract_column='front_close',
        ...     back_contract_column='back_close',
        ...     method='difference'
        ... )
    """
    df = df.copy()
    
    # Ensure we have a date column
    if 'date' not in df.columns:
        if isinstance(df.index, pd.DatetimeIndex):
            df['date'] = df.index
        else:
            raise ValueError("DataFrame must have 'date' column or DatetimeIndex")
    
    # Convert date column to datetime if needed
    if not pd.api.types.is_datetime64_any_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'])
    
    roll_date = pd.to_datetime(roll_date)
    
    # Calculate adjustment if not provided
    if adjustment is None:
        if back_contract_column is None:
            raise ValueError(
                "Either 'adjustment' or 'back_contract_column' must be provided"
            )
        
        # Find the last trading day before the roll
        pre_roll = df[df['date'] < roll_date].iloc[-1] if len(df[df['date'] < roll_date]) > 0 else None
        
        if pre_roll is None:
            logger.warning(f"No data before roll date {roll_date}")
            return df
        
        if method == 'difference':
            # Additive adjustment
            adjustment = pre_roll[front_contract_column] - pre_roll[back_contract_column]
        elif method == 'ratio':
            # Multiplicative adjustment
            adjustment = pre_roll[front_contract_column] / pre_roll[back_contract_column]
        else:
            raise ValueError(f"Unknown method: {method}. Use 'difference' or 'ratio'")
        
        logger.info(f"Calculated roll adjustment: {adjustment}")
    
    # Apply adjustment to all data before the roll date
    mask = df['date'] < roll_date
    
    if method == 'difference':
        # Additive adjustment - add the difference to historical prices
        df.loc[mask, front_contract_column] = df.loc[mask, front_contract_column] + adjustment
    elif method == 'ratio':
        # Multiplicative adjustment - multiply historical prices by the ratio
        df.loc[mask, front_contract_column] = df.loc[mask, front_contract_column] * adjustment
    
    logger.info(f"Adjusted prices for contract roll on {roll_date} using {method} method")
    
    return df


def standardize_column_names(df: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
    """
    Standardize DataFrame column names to lowercase with underscores.
    
    Args:
        df: DataFrame with market data
        inplace: Modify DataFrame in place
        
    Returns:
        DataFrame with standardized column names
        
    Example:
        >>> df = pd.DataFrame({'Open': [100], 'High': [105], 'Low': [99]})
        >>> standardized = standardize_column_names(df)
        >>> print(standardized.columns.tolist())
        ['open', 'high', 'low']
    """
    if not inplace:
        df = df.copy()
    
    # Map common column name variations to standard names
    column_mapping = {
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Adj Close': 'adj_close',
        'Adj_Close': 'adj_close',
        'Volume': 'volume',
        'Dividends': 'dividends',
        'Stock Splits': 'stock_splits',
        'Stock_Splits': 'stock_splits',
        'Date': 'date',
        'Symbol': 'symbol',
    }
    
    # Apply mapping
    df.rename(columns=column_mapping, inplace=True)
    
    # Convert any remaining columns to lowercase with underscores
    df.columns = [col.lower().replace(' ', '_') for col in df.columns]
    
    logger.debug(f"Standardized column names: {df.columns.tolist()}")
    return df


def adjust_for_splits(
    df: pd.DataFrame,
    split_ratio: Optional[float] = None,
    split_date: Optional[str] = None,
    split_column: str = 'stock_splits'
) -> pd.DataFrame:
    """
    Adjust historical prices for stock splits.
    
    Args:
        df: DataFrame with OHLCV data (must have date index or 'date' column)
        split_ratio: Split ratio (e.g., 2.0 for 2-for-1 split). If None, uses split_column
        split_date: Date of split in 'YYYY-MM-DD' format
        split_column: Column name containing split information
        
    Returns:
        DataFrame with split-adjusted prices
        
    Example:
        >>> # 2-for-1 split on 2024-01-15
        >>> df = adjust_for_splits(df, split_ratio=2.0, split_date='2024-01-15')
    """
    df = df.copy()
    
    # Ensure we have a date column
    if 'date' not in df.columns:
        if isinstance(df.index, pd.DatetimeIndex):
            df['date'] = df.index
        else:
            raise ValueError("DataFrame must have 'date' column or DatetimeIndex")
    
    # Convert date column to datetime if needed
    if not pd.api.types.is_datetime64_any_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'])
    
    # Determine split dates and ratios
    if split_ratio and split_date:
        # Manual split specification
        split_date = pd.to_datetime(split_date)
        # Adjust all prices before the split date
        mask = df['date'] < split_date
        
        for col in ['open', 'high', 'low', 'close', 'adj_close']:
            if col in df.columns:
                df.loc[mask, col] = df.loc[mask, col] / split_ratio
        
        if 'volume' in df.columns:
            df.loc[mask, 'volume'] = df.loc[mask, 'volume'] * split_ratio
            
        logger.info(f"Adjusted prices for {split_ratio}:1 split on {split_date}")
        
    elif split_column in df.columns:
        # Use split information from data
        splits = df[df[split_column] > 0]
        
        for idx, row in splits.iterrows():
            ratio = row[split_column]
            date = row['date']
            
            # Adjust all prices before this split
            mask = df['date'] < date
            
            for col in ['open', 'high', 'low', 'close', 'adj_close']:
                if col in df.columns:
                    df.loc[mask, col] = df.loc[mask, col] / ratio
            
            if 'volume' in df.columns:
                df.loc[mask, 'volume'] = df.loc[mask, 'volume'] * ratio
                
            logger.info(f"Adjusted prices for {ratio}:1 split on {date}")
    
    return df


def calculate_adjusted_close(
    df: pd.DataFrame,
    use_dividends: bool = True,
    use_splits: bool = True
) -> pd.DataFrame:
    """
    Calculate adjusted close prices accounting for dividends and splits.
    
    Args:
        df: DataFrame with OHLCV data
        use_dividends: Include dividend adjustments
        use_splits: Include split adjustments
        
    Returns:
        DataFrame with 'adj_close' column calculated
        
    Example:
        >>> df = calculate_adjusted_close(df, use_dividends=True, use_splits=True)
        >>> print(df[['close', 'adj_close']])
    """
    df = df.copy()
    
    if 'close' not in df.columns:
        raise ValueError("DataFrame must contain 'close' column")
    
    # Start with close prices
    df['adj_close'] = df['close']
    
    # Apply split adjustments
    if use_splits and 'stock_splits' in df.columns:
        df = adjust_for_splits(df, split_column='stock_splits')
    
    # Apply dividend adjustments
    if use_dividends and 'dividends' in df.columns:
        # Calculate cumulative dividend adjustment factor
        # This is a simplified version - production code would be more sophisticated
        cum_dividends = df['dividends'].cumsum()
        df['adj_close'] = df['close'] - cum_dividends
    
    return df


def detect_missing_data(df: pd.DataFrame) -> Dict[str, List]:
    """
    Detect missing data, gaps, and anomalies in market data.
    
    Args:
        df: DataFrame with market data
        
    Returns:
        Dictionary with lists of issues:
        - 'missing_values': Rows with NaN values
        - 'date_gaps': Missing trading days
        - 'zero_volume': Days with zero volume
        - 'price_anomalies': Suspicious price movements
        
    Example:
        >>> issues = detect_missing_data(df)
        >>> print(f"Found {len(issues['missing_values'])} rows with missing values")
    """
    issues = {
        'missing_values': [],
        'date_gaps': [],
        'zero_volume': [],
        'price_anomalies': []
    }
    
    # Check for missing values
    for col in df.columns:
        null_indices = df[df[col].isnull()].index.tolist()
        if null_indices:
            issues['missing_values'].extend([
                {'column': col, 'index': idx} for idx in null_indices
            ])
    
    # Check for date gaps (assuming daily data)
    if 'date' in df.columns or isinstance(df.index, pd.DatetimeIndex):
        dates = df['date'] if 'date' in df.columns else df.index
        dates = pd.to_datetime(dates).sort_values()
        
        # Calculate gaps (accounting for weekends)
        for i in range(1, len(dates)):
            days_diff = (dates.iloc[i] - dates.iloc[i-1]).days
            # More than 3 days gap (accounting for weekends)
            if days_diff > 3:
                issues['date_gaps'].append({
                    'start': dates.iloc[i-1],
                    'end': dates.iloc[i],
                    'days': days_diff
                })
    
    # Check for zero volume
    if 'volume' in df.columns:
        zero_vol_indices = df[df['volume'] == 0].index.tolist()
        if zero_vol_indices:
            issues['zero_volume'] = zero_vol_indices
    
    # Check for price anomalies (extreme movements)
    if 'close' in df.columns:
        returns = df['close'].pct_change()
        # Flag returns > 50% or < -50% as potential anomalies
        extreme_moves = df[abs(returns) > 0.5].index.tolist()
        if extreme_moves:
            issues['price_anomalies'] = extreme_moves
    
    return issues


def validate_data_quality(df: pd.DataFrame) -> List[str]:
    """
    Validate data quality and return list of issues.
    
    Args:
        df: DataFrame with market data
        
    Returns:
        List of validation error messages
        
    Example:
        >>> errors = validate_data_quality(df)
        >>> if errors:
        ...     for error in errors:
        ...         print(f"Error: {error}")
    """
    errors = []
    
    # Check if DataFrame is empty
    if df.empty:
        errors.append("DataFrame is empty")
        return errors
    
    # Check for required columns (OHLCV)
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
    
    # Validate price relationships (High >= Low, etc.)
    if all(col in df.columns for col in ['open', 'high', 'low', 'close']):
        if (df['high'] < df['low']).any():
            errors.append("Found rows where High < Low")
        
        if (df['high'] < df['close']).any():
            errors.append("Found rows where High < Close")
        
        if (df['low'] > df['close']).any():
            errors.append("Found rows where Low > Close")
        
        if (df['high'] < df['open']).any():
            errors.append("Found rows where High < Open")
        
        if (df['low'] > df['open']).any():
            errors.append("Found rows where Low > Open")
    
    # Check for negative prices
    price_cols = ['open', 'high', 'low', 'close', 'adj_close']
    for col in price_cols:
        if col in df.columns:
            if (df[col] < 0).any():
                errors.append(f"Found negative values in {col}")
    
    # Check for negative volume
    if 'volume' in df.columns:
        if (df['volume'] < 0).any():
            errors.append("Found negative volume values")
    
    # Check for excessive missing data
    total_cells = df.size
    missing_cells = df.isnull().sum().sum()
    missing_pct = (missing_cells / total_cells) * 100
    
    if missing_pct > 10:
        errors.append(f"High percentage of missing data: {missing_pct:.2f}%")
    
    return errors


def fill_missing_data(
    df: pd.DataFrame,
    method: str = 'ffill',
    limit: Optional[int] = None
) -> pd.DataFrame:
    """
    Fill missing data using specified method.
    
    Args:
        df: DataFrame with market data
        method: Fill method - 'ffill' (forward fill), 'bfill' (backward fill),
                'interpolate', or 'drop'
        limit: Maximum number of consecutive NaN values to fill
        
    Returns:
        DataFrame with missing values handled
        
    Example:
        >>> df = fill_missing_data(df, method='ffill', limit=5)
    """
    df = df.copy()
    
    if method == 'ffill':
        df = df.fillna(method='ffill', limit=limit)
    elif method == 'bfill':
        df = df.fillna(method='bfill', limit=limit)
    elif method == 'interpolate':
        # Use linear interpolation for numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].interpolate(method='linear', limit=limit)
    elif method == 'drop':
        df = df.dropna()
    else:
        raise ValueError(f"Unknown fill method: {method}")
    
    logger.info(f"Filled missing data using method: {method}")
    return df


def remove_outliers(
    df: pd.DataFrame,
    column: str = 'close',
    method: str = 'iqr',
    threshold: float = 3.0
) -> pd.DataFrame:
    """
    Remove outliers from data using specified method.
    
    Args:
        df: DataFrame with market data
        column: Column to check for outliers
        method: Detection method - 'iqr' (interquartile range) or 'zscore'
        threshold: Threshold for outlier detection (IQR multiplier or z-score)
        
    Returns:
        DataFrame with outliers removed
        
    Example:
        >>> df = remove_outliers(df, column='close', method='iqr', threshold=1.5)
    """
    df = df.copy()
    
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame")
    
    if method == 'iqr':
        # Interquartile range method
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - threshold * IQR
        upper_bound = Q3 + threshold * IQR
        
        mask = (df[column] >= lower_bound) & (df[column] <= upper_bound)
        df = df[mask]
        
    elif method == 'zscore':
        # Z-score method
        mean = df[column].mean()
        std = df[column].std()
        
        z_scores = abs((df[column] - mean) / std)
        mask = z_scores < threshold
        df = df[mask]
        
    else:
        raise ValueError(f"Unknown outlier detection method: {method}")
    
    logger.info(f"Removed outliers from {column} using {method} method")
    return df


def resample_data(
    df: pd.DataFrame,
    freq: str = 'D',
    aggregation: Optional[Dict[str, str]] = None
) -> pd.DataFrame:
    """
    Resample time series data to different frequency.
    
    Args:
        df: DataFrame with market data (must have DatetimeIndex or 'date' column)
        freq: Target frequency ('D' for daily, 'W' for weekly, 'M' for monthly, etc.)
        aggregation: Dictionary mapping columns to aggregation functions
                    Defaults: open='first', high='max', low='min', close='last', volume='sum'
        
    Returns:
        Resampled DataFrame
        
    Example:
        >>> # Resample daily data to weekly
        >>> weekly_df = resample_data(df, freq='W')
    """
    df = df.copy()
    
    # Ensure we have DatetimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        if 'date' in df.columns:
            df = df.set_index('date')
        else:
            raise ValueError("DataFrame must have DatetimeIndex or 'date' column")
    
    # Default aggregation rules
    if aggregation is None:
        aggregation = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
            'adj_close': 'last',
        }
    
    # Filter aggregation to only include columns that exist
    agg_dict = {col: agg for col, agg in aggregation.items() if col in df.columns}
    
    # Resample
    resampled = df.resample(freq).agg(agg_dict)
    
    logger.info(f"Resampled data to {freq} frequency")
    return resampled
