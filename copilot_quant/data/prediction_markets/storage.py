"""
Storage utilities for prediction market data.

Provides functions to save and load prediction market data to/from CSV and SQLite.
"""

import logging
import sqlite3
from pathlib import Path
from typing import Optional, Union

import pandas as pd

logger = logging.getLogger(__name__)


class PredictionMarketStorage:
    """Storage manager for prediction market data."""

    def __init__(
        self,
        storage_type: str = "csv",
        base_path: str = "data/prediction_markets",
        db_path: Optional[str] = None,
    ):
        """
        Initialize storage manager.

        Args:
            storage_type: Type of storage ('csv' or 'sqlite')
            base_path: Base directory for CSV files
            db_path: Path to SQLite database (if using sqlite)
        """
        self.storage_type = storage_type.lower()
        self.base_path = Path(base_path)
        self.db_path = db_path or str(self.base_path / "prediction_markets.db")

        if self.storage_type == "csv":
            self.base_path.mkdir(parents=True, exist_ok=True)
        elif self.storage_type == "sqlite":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self._init_sqlite_db()
        else:
            raise ValueError(f"Invalid storage_type: {storage_type}. Use 'csv' or 'sqlite'")

    def _init_sqlite_db(self):
        """Initialize SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create markets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS markets (
                provider TEXT NOT NULL,
                market_id TEXT NOT NULL,
                title TEXT,
                category TEXT,
                close_time TEXT,
                status TEXT,
                volume REAL,
                liquidity REAL,
                last_updated TEXT,
                PRIMARY KEY (provider, market_id)
            )
        """)

        # Create price_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                provider TEXT NOT NULL,
                market_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                price REAL,
                volume REAL,
                PRIMARY KEY (provider, market_id, timestamp)
            )
        """)

        conn.commit()
        conn.close()
        logger.info(f"Initialized SQLite database at {self.db_path}")

    def save_markets(self, provider: str, markets_df: pd.DataFrame):
        """
        Save market list to storage.

        Args:
            provider: Provider name (e.g., 'polymarket', 'kalshi')
            markets_df: DataFrame with market information
        """
        if markets_df.empty:
            logger.warning(f"No markets to save for {provider}")
            return

        if self.storage_type == "csv":
            filepath = self.base_path / provider / "markets.csv"
            filepath.parent.mkdir(parents=True, exist_ok=True)
            markets_df.to_csv(filepath, index=False)
            logger.info(f"Saved {len(markets_df)} markets to {filepath}")

        elif self.storage_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            
            # Add provider column
            markets_df = markets_df.copy()
            markets_df['provider'] = provider
            markets_df['last_updated'] = pd.Timestamp.now().isoformat()
            
            # Delete existing records for this provider
            conn.execute("DELETE FROM markets WHERE provider = ?", (provider,))
            
            # Insert new records
            markets_df.to_sql('markets', conn, if_exists='append', index=False)
            conn.commit()
            conn.close()
            logger.info(f"Saved {len(markets_df)} markets to SQLite database")

    def save_market_data(
        self,
        provider: str,
        market_id: str,
        data_df: pd.DataFrame,
    ):
        """
        Save market price/prediction data to storage.

        Args:
            provider: Provider name
            market_id: Market identifier
            data_df: DataFrame with price/prediction data
        """
        if data_df.empty:
            logger.warning(f"No data to save for {provider}/{market_id}")
            return

        normalized_id = self._normalize_filename(market_id)

        if self.storage_type == "csv":
            filepath = self.base_path / provider / f"{normalized_id}.csv"
            filepath.parent.mkdir(parents=True, exist_ok=True)
            data_df.to_csv(filepath)
            logger.info(f"Saved {len(data_df)} data points to {filepath}")

        elif self.storage_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            
            # Prepare data
            data_df = data_df.copy()
            if isinstance(data_df.index, pd.DatetimeIndex):
                data_df = data_df.reset_index()
                data_df.rename(columns={data_df.columns[0]: 'timestamp'}, inplace=True)
            
            data_df['provider'] = provider
            data_df['market_id'] = market_id
            
            # Ensure we have the required columns
            required_cols = ['provider', 'market_id', 'timestamp', 'price']
            for col in required_cols:
                if col not in data_df.columns:
                    if col == 'price' and 'prediction' in data_df.columns:
                        data_df['price'] = data_df['prediction']
                    elif col not in ['price', 'volume']:
                        logger.error(f"Missing required column: {col}")
                        return
            
            # Add volume if missing
            if 'volume' not in data_df.columns:
                data_df['volume'] = 0.0
            
            # Select only the columns we need
            cols_to_save = ['provider', 'market_id', 'timestamp', 'price', 'volume']
            data_df = data_df[[col for col in cols_to_save if col in data_df.columns]]
            
            # Delete existing records for this market
            conn.execute(
                "DELETE FROM price_history WHERE provider = ? AND market_id = ?",
                (provider, market_id)
            )
            
            # Insert new records
            data_df.to_sql('price_history', conn, if_exists='append', index=False)
            conn.commit()
            conn.close()
            logger.info(f"Saved {len(data_df)} data points to SQLite database")

    def load_markets(self, provider: str) -> pd.DataFrame:
        """
        Load market list from storage.

        Args:
            provider: Provider name

        Returns:
            DataFrame with market information
        """
        if self.storage_type == "csv":
            filepath = self.base_path / provider / "markets.csv"
            if not filepath.exists():
                logger.warning(f"Markets file not found: {filepath}")
                return pd.DataFrame()
            return pd.read_csv(filepath)

        elif self.storage_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            query = "SELECT * FROM markets WHERE provider = ?"
            df = pd.read_sql_query(query, conn, params=(provider,))
            conn.close()
            return df

    def load_market_data(
        self,
        provider: str,
        market_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Load market price/prediction data from storage.

        Args:
            provider: Provider name
            market_id: Market identifier
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            DataFrame with price/prediction data
        """
        normalized_id = self._normalize_filename(market_id)

        if self.storage_type == "csv":
            filepath = self.base_path / provider / f"{normalized_id}.csv"
            if not filepath.exists():
                logger.warning(f"Market data file not found: {filepath}")
                return pd.DataFrame()
            
            df = pd.read_csv(filepath, index_col=0, parse_dates=True)
            
            # Apply date filters
            if start_date:
                df = df[df.index >= start_date]
            if end_date:
                df = df[df.index <= end_date]
            
            return df

        elif self.storage_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            
            query = """
                SELECT timestamp, price, volume 
                FROM price_history 
                WHERE provider = ? AND market_id = ?
            """
            params = [provider, market_id]
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)
            
            query += " ORDER BY timestamp"
            
            df = pd.read_sql_query(query, conn, params=params, parse_dates=['timestamp'])
            conn.close()
            
            if not df.empty:
                df = df.set_index('timestamp')
            
            return df

    def _normalize_filename(self, market_id: str) -> str:
        """
        Normalize market ID for use as filename.

        Args:
            market_id: Original market ID

        Returns:
            Normalized filename-safe string
        """
        import re
        # Replace non-alphanumeric characters with underscores
        normalized = re.sub(r'[^a-zA-Z0-9]+', '_', market_id)
        # Remove leading/trailing underscores
        normalized = normalized.strip('_')
        # Limit length
        if len(normalized) > 100:
            normalized = normalized[:100]
        return normalized
