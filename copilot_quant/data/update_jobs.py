"""
Data Backfill and Incremental Update Utilities

This module provides utilities for managing historical data updates,
including backfilling missing data and incrementally updating existing data.

Features:
- Incremental data updates (fetch only new data since last update)
- Backfill historical data gaps
- Data freshness checking
- Scheduled update utilities
- Batch update management

Example Usage:
    # Check if data needs updating
    updater = DataUpdater(storage_type='csv', data_dir='data/historical')
    
    # Update single symbol
    updater.update_symbol('AAPL')
    
    # Backfill historical data
    updater.backfill_symbol('AAPL', start_date='2020-01-01')
    
    # Batch update multiple symbols
    updater.batch_update(['AAPL', 'MSFT', 'GOOGL'])
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time

import pandas as pd
import sqlite3

from copilot_quant.data.eod_loader import SP500EODLoader
from copilot_quant.data.providers import YFinanceProvider

logger = logging.getLogger(__name__)


class DataUpdater:
    """
    Manager for incremental data updates and backfilling.
    
    Tracks the last update time for each symbol and only fetches
    new data since the last update, minimizing API calls and
    improving performance.
    """
    
    def __init__(
        self,
        storage_type: str = 'csv',
        data_dir: str = 'data/historical',
        db_path: str = 'data/market_data.db',
        provider: Optional[YFinanceProvider] = None,
        rate_limit_delay: float = 0.5
    ):
        """
        Initialize the data updater.
        
        Args:
            storage_type: 'csv' or 'sqlite' for data storage
            data_dir: Directory for CSV files
            db_path: Path to SQLite database
            provider: Data provider instance (defaults to YFinanceProvider)
            rate_limit_delay: Delay between API calls in seconds
        """
        self.storage_type = storage_type.lower()
        self.data_dir = Path(data_dir)
        self.db_path = Path(db_path)
        self.rate_limit_delay = rate_limit_delay
        
        # Initialize provider
        self.provider = provider or YFinanceProvider()
        
        # Initialize loader
        self.loader = SP500EODLoader(
            storage_type=storage_type,
            data_dir=str(data_dir),
            db_path=str(db_path),
            rate_limit_delay=rate_limit_delay
        )
        
        # Metadata tracking
        self.metadata_file = self.data_dir / 'update_metadata.csv'
        self._load_metadata()
        
        logger.info("Initialized DataUpdater")
    
    def _load_metadata(self):
        """Load metadata about last update times."""
        if self.metadata_file.exists():
            self.metadata = pd.read_csv(self.metadata_file)
            self.metadata['last_update'] = pd.to_datetime(self.metadata['last_update'])
        else:
            self.metadata = pd.DataFrame(columns=['symbol', 'last_update', 'last_date'])
            
    def _save_metadata(self):
        """Save metadata about update times."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.metadata.to_csv(self.metadata_file, index=False)
        logger.debug(f"Saved metadata to {self.metadata_file}")
    
    def _get_last_date(self, symbol: str) -> Optional[str]:
        """
        Get the last date for which we have data for a symbol.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Last date as 'YYYY-MM-DD' string or None if no data exists
        """
        try:
            if self.storage_type == 'csv':
                df = self.loader.load_from_csv(symbol)
                if df is not None and not df.empty:
                    if 'Date' in df.columns:
                        return pd.to_datetime(df['Date']).max().strftime('%Y-%m-%d')
                    elif 'date' in df.columns:
                        return pd.to_datetime(df['date']).max().strftime('%Y-%m-%d')
                        
            elif self.storage_type == 'sqlite':
                df = self.loader.load_from_sqlite(symbol)
                if df is not None and not df.empty:
                    if 'date' in df.columns:
                        return pd.to_datetime(df['date']).max().strftime('%Y-%m-%d')
                        
        except Exception as e:
            logger.debug(f"Could not get last date for {symbol}: {e}")
            
        return None
    
    def needs_update(self, symbol: str, max_age_days: int = 1) -> bool:
        """
        Check if a symbol needs updating.
        
        Args:
            symbol: Stock ticker symbol
            max_age_days: Maximum age in days before update is needed
            
        Returns:
            True if update is needed, False otherwise
        """
        last_date = self._get_last_date(symbol)
        
        if last_date is None:
            # No data exists, needs update
            return True
        
        # Check if data is stale
        last_date_dt = pd.to_datetime(last_date)
        days_old = (datetime.now() - last_date_dt).days
        
        return days_old >= max_age_days
    
    def update_symbol(
        self,
        symbol: str,
        force: bool = False,
        max_age_days: int = 1
    ) -> bool:
        """
        Incrementally update data for a single symbol.
        
        Fetches only new data since the last update.
        
        Args:
            symbol: Stock ticker symbol
            force: Force update even if data is fresh
            max_age_days: Maximum age in days before update is needed
            
        Returns:
            True if update was successful, False otherwise
            
        Example:
            >>> updater = DataUpdater()
            >>> updater.update_symbol('AAPL')
            True
        """
        if not force and not self.needs_update(symbol, max_age_days):
            logger.info(f"{symbol}: Data is up to date, skipping")
            return True
        
        try:
            # Get last date we have data for
            last_date = self._get_last_date(symbol)
            
            # Set start date for update
            if last_date:
                # Fetch from day after last date
                start_date = (pd.to_datetime(last_date) + timedelta(days=1)).strftime('%Y-%m-%d')
                logger.info(f"{symbol}: Updating from {start_date}")
            else:
                # No existing data, fetch last year
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
                logger.info(f"{symbol}: No existing data, fetching from {start_date}")
            
            # Set end date to today
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            # Fetch new data
            success = self.loader.fetch_and_save(
                symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            if success:
                # Update metadata
                self._update_metadata(symbol)
                logger.info(f"{symbol}: Update successful")
                return True
            else:
                logger.warning(f"{symbol}: Update failed")
                return False
                
        except Exception as e:
            logger.error(f"{symbol}: Error during update: {e}")
            return False
    
    def backfill_symbol(
        self,
        symbol: str,
        start_date: str,
        end_date: Optional[str] = None
    ) -> bool:
        """
        Backfill historical data for a symbol.
        
        Args:
            symbol: Stock ticker symbol
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format (defaults to today)
            
        Returns:
            True if backfill was successful, False otherwise
            
        Example:
            >>> updater = DataUpdater()
            >>> updater.backfill_symbol('AAPL', start_date='2020-01-01')
            True
        """
        try:
            if end_date is None:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            logger.info(f"{symbol}: Backfilling from {start_date} to {end_date}")
            
            # Fetch historical data
            success = self.loader.fetch_and_save(
                symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            if success:
                self._update_metadata(symbol)
                logger.info(f"{symbol}: Backfill successful")
                return True
            else:
                logger.warning(f"{symbol}: Backfill failed")
                return False
                
        except Exception as e:
            logger.error(f"{symbol}: Error during backfill: {e}")
            return False
    
    def batch_update(
        self,
        symbols: List[str],
        force: bool = False,
        max_age_days: int = 1,
        continue_on_error: bool = True
    ) -> Dict[str, List[str]]:
        """
        Update multiple symbols in batch.
        
        Args:
            symbols: List of stock ticker symbols
            force: Force update even if data is fresh
            max_age_days: Maximum age in days before update is needed
            continue_on_error: Continue processing if one symbol fails
            
        Returns:
            Dictionary with 'success' and 'failed' symbol lists
            
        Example:
            >>> updater = DataUpdater()
            >>> result = updater.batch_update(['AAPL', 'MSFT', 'GOOGL'])
            >>> print(f"Updated: {len(result['success'])} symbols")
        """
        logger.info(f"Starting batch update for {len(symbols)} symbols")
        
        success = []
        failed = []
        
        for i, symbol in enumerate(symbols):
            logger.info(f"Processing {i+1}/{len(symbols)}: {symbol}")
            
            try:
                if self.update_symbol(symbol, force=force, max_age_days=max_age_days):
                    success.append(symbol)
                else:
                    failed.append(symbol)
                    
            except Exception as e:
                logger.error(f"Error updating {symbol}: {e}")
                failed.append(symbol)
                if not continue_on_error:
                    raise
            
            # Rate limiting
            if i < len(symbols) - 1:
                time.sleep(self.rate_limit_delay)
        
        logger.info(f"Batch update complete: {len(success)} succeeded, {len(failed)} failed")
        
        return {'success': success, 'failed': failed}
    
    def batch_backfill(
        self,
        symbols: List[str],
        start_date: str,
        end_date: Optional[str] = None,
        continue_on_error: bool = True
    ) -> Dict[str, List[str]]:
        """
        Backfill historical data for multiple symbols.
        
        Args:
            symbols: List of stock ticker symbols
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            continue_on_error: Continue processing if one symbol fails
            
        Returns:
            Dictionary with 'success' and 'failed' symbol lists
            
        Example:
            >>> updater = DataUpdater()
            >>> result = updater.batch_backfill(
            ...     ['AAPL', 'MSFT'],
            ...     start_date='2020-01-01'
            ... )
        """
        logger.info(f"Starting batch backfill for {len(symbols)} symbols")
        
        success = []
        failed = []
        
        for i, symbol in enumerate(symbols):
            logger.info(f"Processing {i+1}/{len(symbols)}: {symbol}")
            
            try:
                if self.backfill_symbol(symbol, start_date, end_date):
                    success.append(symbol)
                else:
                    failed.append(symbol)
                    
            except Exception as e:
                logger.error(f"Error backfilling {symbol}: {e}")
                failed.append(symbol)
                if not continue_on_error:
                    raise
            
            # Rate limiting
            if i < len(symbols) - 1:
                time.sleep(self.rate_limit_delay)
        
        logger.info(f"Batch backfill complete: {len(success)} succeeded, {len(failed)} failed")
        
        return {'success': success, 'failed': failed}
    
    def _update_metadata(self, symbol: str):
        """Update metadata for a symbol."""
        now = datetime.now()
        last_date = self._get_last_date(symbol)
        
        # Update or add metadata entry
        mask = self.metadata['symbol'] == symbol
        if mask.any():
            self.metadata.loc[mask, 'last_update'] = now
            self.metadata.loc[mask, 'last_date'] = last_date
        else:
            new_entry = pd.DataFrame({
                'symbol': [symbol],
                'last_update': [now],
                'last_date': [last_date]
            })
            self.metadata = pd.concat([self.metadata, new_entry], ignore_index=True)
        
        self._save_metadata()
    
    def get_update_status(self, symbols: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Get update status for symbols.
        
        Args:
            symbols: List of symbols to check (None for all symbols in metadata)
            
        Returns:
            DataFrame with update status information
            
        Example:
            >>> updater = DataUpdater()
            >>> status = updater.get_update_status(['AAPL', 'MSFT'])
            >>> print(status)
        """
        if symbols:
            status_data = []
            for symbol in symbols:
                last_date = self._get_last_date(symbol)
                needs_update = self.needs_update(symbol)
                
                # Get metadata if available
                meta_row = self.metadata[self.metadata['symbol'] == symbol]
                last_update = meta_row['last_update'].iloc[0] if not meta_row.empty else None
                
                status_data.append({
                    'symbol': symbol,
                    'last_date': last_date,
                    'last_update': last_update,
                    'needs_update': needs_update,
                    'days_old': (datetime.now() - pd.to_datetime(last_date)).days if last_date else None
                })
            
            return pd.DataFrame(status_data)
        else:
            # Return all metadata
            return self.metadata.copy()
    
    def find_gaps(self, symbol: str) -> List[Tuple[str, str]]:
        """
        Find date gaps in historical data for a symbol.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            List of (start_date, end_date) tuples representing gaps
            
        Example:
            >>> updater = DataUpdater()
            >>> gaps = updater.find_gaps('AAPL')
            >>> for start, end in gaps:
            ...     print(f"Gap: {start} to {end}")
        """
        try:
            if self.storage_type == 'csv':
                df = self.loader.load_from_csv(symbol)
            else:
                df = self.loader.load_from_sqlite(symbol)
            
            if df is None or df.empty:
                return []
            
            # Get date column
            if 'Date' in df.columns:
                dates = pd.to_datetime(df['Date']).sort_values()
            elif 'date' in df.columns:
                dates = pd.to_datetime(df['date']).sort_values()
            else:
                return []
            
            # Find gaps (more than 3 days between consecutive dates)
            gaps = []
            for i in range(1, len(dates)):
                days_diff = (dates.iloc[i] - dates.iloc[i-1]).days
                if days_diff > 3:  # Account for weekends
                    gaps.append((
                        dates.iloc[i-1].strftime('%Y-%m-%d'),
                        dates.iloc[i].strftime('%Y-%m-%d')
                    ))
            
            logger.info(f"{symbol}: Found {len(gaps)} date gaps")
            return gaps
            
        except Exception as e:
            logger.error(f"Error finding gaps for {symbol}: {e}")
            return []
    
    def fill_gaps(self, symbol: str) -> bool:
        """
        Fill date gaps in historical data for a symbol.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            True if gaps were filled successfully, False otherwise
            
        Example:
            >>> updater = DataUpdater()
            >>> updater.fill_gaps('AAPL')
            True
        """
        gaps = self.find_gaps(symbol)
        
        if not gaps:
            logger.info(f"{symbol}: No gaps found")
            return True
        
        logger.info(f"{symbol}: Filling {len(gaps)} date gaps")
        
        for start_date, end_date in gaps:
            try:
                # Fetch data for gap period
                self.loader.fetch_and_save(
                    symbol,
                    start_date=start_date,
                    end_date=end_date
                )
                logger.info(f"{symbol}: Filled gap from {start_date} to {end_date}")
            except Exception as e:
                logger.error(f"{symbol}: Error filling gap {start_date} to {end_date}: {e}")
                return False
        
        self._update_metadata(symbol)
        return True
