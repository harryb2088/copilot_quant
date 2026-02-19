"""
End-of-Day (EOD) Data Loader for S&P500 Equities

This module provides functionality to fetch historical end-of-day market data
for S&P500 constituents using yfinance as the data provider.

Features:
- Fetch data for single or multiple symbols
- Configurable date ranges
- Automatic handling of splits and dividends
- Save to CSV or SQLite database
- Robust error handling and rate limiting
- Progress tracking for bulk downloads

Example Usage:
    # Load data for a single symbol
    loader = SP500EODLoader()
    df = loader.fetch_symbol('AAPL', start_date='2023-01-01', end_date='2024-01-01')

    # Load data for all S&P500 constituents
    loader = SP500EODLoader(symbols_file='data/sp500_symbols.csv')
    loader.fetch_all(start_date='2023-01-01', end_date='2024-01-01')

    # Save to SQLite
    loader = SP500EODLoader(storage_type='sqlite', db_path='data/market_data.db')
    loader.fetch_all(start_date='2023-01-01', end_date='2024-01-01')
"""

import logging
import sqlite3
import time
from pathlib import Path
from typing import List, Optional

import pandas as pd

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logging.warning("yfinance not available - SP500EODLoader will not work")

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class SP500EODLoader:
    """
    End-of-Day data loader for S&P500 equities.

    Fetches historical market data from Yahoo Finance and stores it in CSV or SQLite format.
    Handles splits, dividends, and provides robust error handling with rate limiting.

    Attributes:
        storage_type (str): Either 'csv' or 'sqlite'
        data_dir (Path): Directory for CSV storage
        db_path (Path): Path to SQLite database
        symbols (List[str]): List of stock symbols to fetch
        rate_limit_delay (float): Delay between API calls in seconds
    """

    def __init__(
        self,
        symbols: Optional[List[str]] = None,
        symbols_file: Optional[str] = None,
        storage_type: str = "csv",
        data_dir: str = "data/historical",
        db_path: str = "data/market_data.db",
        rate_limit_delay: float = 0.5,
    ):
        """
        Initialize the EOD loader.

        Args:
            symbols: List of stock symbols to fetch (e.g., ['AAPL', 'GOOGL'])
            symbols_file: Path to CSV file containing symbols (column: 'Symbol')
            storage_type: 'csv' or 'sqlite' for data storage
            data_dir: Directory path for CSV files (default: 'data/historical')
            db_path: Path to SQLite database file (default: 'data/market_data.db')
            rate_limit_delay: Delay between API calls in seconds (default: 0.5)
        """
        self.storage_type = storage_type.lower()
        if self.storage_type not in ["csv", "sqlite"]:
            raise ValueError("storage_type must be 'csv' or 'sqlite'")

        self.data_dir = Path(data_dir)
        self.db_path = Path(db_path)
        self.rate_limit_delay = rate_limit_delay

        # Load symbols
        if symbols:
            self.symbols = symbols
        elif symbols_file:
            self.symbols = self._load_symbols_from_file(symbols_file)
        else:
            self.symbols = []

        # Create directories if needed
        if self.storage_type == "csv":
            self.data_dir.mkdir(parents=True, exist_ok=True)
        elif self.storage_type == "sqlite":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._initialize_database()

        logger.info(f"Initialized SP500EODLoader with {len(self.symbols)} symbols")
        logger.info(f"Storage type: {self.storage_type}")

    def _load_symbols_from_file(self, filepath: str) -> List[str]:
        """
        Load stock symbols from a CSV file.

        Args:
            filepath: Path to CSV file with 'Symbol' column

        Returns:
            List of stock symbols
        """
        try:
            df = pd.read_csv(filepath)
            if "Symbol" not in df.columns:
                raise ValueError("CSV file must contain a 'Symbol' column")
            symbols = df["Symbol"].tolist()
            logger.info(f"Loaded {len(symbols)} symbols from {filepath}")
            return symbols
        except Exception as e:
            logger.error(f"Error loading symbols from {filepath}: {e}")
            raise

    def _initialize_database(self):
        """Initialize SQLite database with schema for historical equity data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create table for historical equity data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS equity_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                adj_close REAL,
                volume INTEGER,
                dividends REAL,
                stock_splits REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, date)
            )
        """)

        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_symbol_date
            ON equity_data(symbol, date)
        """)

        conn.commit()
        conn.close()
        logger.info(f"Initialized database at {self.db_path}")

    def fetch_symbol(
        self, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None, auto_adjust: bool = True
    ) -> Optional[pd.DataFrame]:
        """
        Fetch EOD data for a single symbol.

        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')
            start_date: Start date in 'YYYY-MM-DD' format (default: 1 year ago)
            end_date: End date in 'YYYY-MM-DD' format (default: today)
            auto_adjust: Adjust all OHLC data for splits/dividends (default: True)

        Returns:
            DataFrame with EOD data or None if fetch fails
        """
        try:
            logger.info(f"Fetching data for {symbol}")

            # Create ticker object
            ticker = yf.Ticker(symbol)

            # Fetch historical data
            df = ticker.history(
                start=start_date,
                end=end_date,
                auto_adjust=auto_adjust,
                actions=True,  # Include dividends and splits
            )

            if df.empty:
                logger.warning(f"No data returned for {symbol}")
                return None

            # Add symbol column
            df["Symbol"] = symbol

            # Reset index to make Date a column
            df.reset_index(inplace=True)

            # Rename columns to standardized format
            df.rename(
                columns={
                    "Open": "open",
                    "High": "high",
                    "Low": "low",
                    "Close": "close",
                    "Volume": "volume",
                    "Dividends": "dividends",
                    "Stock Splits": "stock_splits",
                },
                inplace=True,
            )

            # Add adj_close column (same as close if auto_adjust=True)
            if "adj_close" not in df.columns:
                df["adj_close"] = df["close"]

            logger.info(f"Fetched {len(df)} rows for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None

    def save_to_csv(self, df: pd.DataFrame, symbol: str):
        """
        Save DataFrame to CSV file.

        Args:
            df: DataFrame with EOD data
            symbol: Stock symbol for filename
        """
        try:
            filepath = self.data_dir / f"equity_{symbol}.csv"
            df.to_csv(filepath, index=False)
            logger.info(f"Saved data to {filepath}")
        except Exception as e:
            logger.error(f"Error saving CSV for {symbol}: {e}")
            raise

    def save_to_sqlite(self, df: pd.DataFrame, symbol: str):
        """
        Save DataFrame to SQLite database.

        Args:
            df: DataFrame with EOD data
            symbol: Stock symbol
        """
        try:
            conn = sqlite3.connect(self.db_path)

            # Prepare data for insertion
            df_copy = df.copy()
            df_copy["symbol"] = symbol

            # Convert date to string format
            if "Date" in df_copy.columns:
                df_copy["date"] = pd.to_datetime(df_copy["Date"]).dt.strftime("%Y-%m-%d")

            # Select and rename columns for database
            columns_map = {
                "date": "date",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "adj_close": "adj_close",
                "volume": "volume",
                "dividends": "dividends",
                "stock_splits": "stock_splits",
                "symbol": "symbol",
            }

            # Keep only columns that exist
            available_cols = [col for col in columns_map.keys() if col in df_copy.columns]
            df_insert = df_copy[available_cols]

            # Insert data (replace existing records)
            df_insert.to_sql("equity_data", conn, if_exists="append", index=False)

            conn.commit()
            conn.close()
            logger.info(f"Saved {len(df)} rows to database for {symbol}")

        except Exception as e:
            logger.error(f"Error saving to database for {symbol}: {e}")
            raise

    def save(self, df: pd.DataFrame, symbol: str):
        """
        Save data using configured storage type.

        Args:
            df: DataFrame with EOD data
            symbol: Stock symbol
        """
        if self.storage_type == "csv":
            self.save_to_csv(df, symbol)
        elif self.storage_type == "sqlite":
            self.save_to_sqlite(df, symbol)

    def fetch_and_save(
        self, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None, auto_adjust: bool = True
    ) -> bool:
        """
        Fetch data for a symbol and save it.

        Args:
            symbol: Stock ticker symbol
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            auto_adjust: Adjust all OHLC data for splits/dividends

        Returns:
            True if successful, False otherwise
        """
        df = self.fetch_symbol(symbol, start_date, end_date, auto_adjust)

        if df is not None and not df.empty:
            self.save(df, symbol)
            return True
        return False

    def fetch_all(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        auto_adjust: bool = True,
        continue_on_error: bool = True,
    ) -> dict:
        """
        Fetch data for all symbols in the list.

        Args:
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            auto_adjust: Adjust all OHLC data for splits/dividends
            continue_on_error: Continue fetching if one symbol fails

        Returns:
            Dictionary with 'success' and 'failed' symbol lists
        """
        if not self.symbols:
            logger.warning("No symbols to fetch. Load symbols first.")
            return {"success": [], "failed": []}

        logger.info(f"Starting bulk fetch for {len(self.symbols)} symbols")

        success = []
        failed = []

        for i, symbol in enumerate(self.symbols):
            logger.info(f"Processing {i + 1}/{len(self.symbols)}: {symbol}")

            try:
                if self.fetch_and_save(symbol, start_date, end_date, auto_adjust):
                    success.append(symbol)
                else:
                    failed.append(symbol)

            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                failed.append(symbol)
                if not continue_on_error:
                    raise

            # Rate limiting
            if i < len(self.symbols) - 1:  # Don't delay after last symbol
                time.sleep(self.rate_limit_delay)

        logger.info(f"Bulk fetch complete: {len(success)} succeeded, {len(failed)} failed")
        if failed:
            logger.warning(f"Failed symbols: {', '.join(failed)}")

        return {"success": success, "failed": failed}

    def load_from_csv(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Load data from CSV file.

        Args:
            symbol: Stock symbol

        Returns:
            DataFrame or None if file doesn't exist
        """
        filepath = self.data_dir / f"equity_{symbol}.csv"
        try:
            if filepath.exists():
                df = pd.read_csv(filepath)
                logger.info(f"Loaded {len(df)} rows from {filepath}")
                return df
            else:
                logger.warning(f"File not found: {filepath}")
                return None
        except Exception as e:
            logger.error(f"Error loading CSV for {symbol}: {e}")
            return None

    def load_from_sqlite(
        self, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """
        Load data from SQLite database.

        Args:
            symbol: Stock symbol
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            DataFrame or None if no data found
        """
        try:
            conn = sqlite3.connect(self.db_path)

            query = "SELECT * FROM equity_data WHERE symbol = ?"
            params = [symbol]

            if start_date:
                query += " AND date >= ?"
                params.append(start_date)

            if end_date:
                query += " AND date <= ?"
                params.append(end_date)

            query += " ORDER BY date"

            df = pd.read_sql_query(query, conn, params=params)
            conn.close()

            if not df.empty:
                logger.info(f"Loaded {len(df)} rows from database for {symbol}")
                return df
            else:
                logger.warning(f"No data found in database for {symbol}")
                return None

        except Exception as e:
            logger.error(f"Error loading from database for {symbol}: {e}")
            return None
