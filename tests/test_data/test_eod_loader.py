"""Tests for EOD data loader module"""

import pytest
import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import shutil
from copilot_quant.data.eod_loader import SP500EODLoader


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test data"""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)


@pytest.fixture
def sample_symbols_file(temp_dir):
    """Create a sample symbols CSV file"""
    filepath = Path(temp_dir) / "test_symbols.csv"
    df = pd.DataFrame({
        'Symbol': ['AAPL', 'MSFT', 'GOOGL'],
        'Company': ['Apple Inc.', 'Microsoft Corporation', 'Alphabet Inc.']
    })
    df.to_csv(filepath, index=False)
    return str(filepath)


class TestSP500EODLoader:
    """Test cases for SP500EODLoader class"""
    
    def test_initialization_with_symbols(self, temp_dir):
        """Test initializing loader with symbol list"""
        symbols = ['AAPL', 'MSFT']
        loader = SP500EODLoader(
            symbols=symbols,
            storage_type='csv',
            data_dir=temp_dir
        )
        assert loader.symbols == symbols
        assert loader.storage_type == 'csv'
        assert loader.data_dir.exists()
    
    def test_initialization_with_symbols_file(self, temp_dir, sample_symbols_file):
        """Test initializing loader with symbols file"""
        loader = SP500EODLoader(
            symbols_file=sample_symbols_file,
            storage_type='csv',
            data_dir=temp_dir
        )
        assert len(loader.symbols) == 3
        assert 'AAPL' in loader.symbols
        assert 'MSFT' in loader.symbols
        assert 'GOOGL' in loader.symbols
    
    def test_invalid_storage_type(self, temp_dir):
        """Test that invalid storage type raises error"""
        with pytest.raises(ValueError, match="storage_type must be 'csv' or 'sqlite'"):
            SP500EODLoader(
                symbols=['AAPL'],
                storage_type='invalid',
                data_dir=temp_dir
            )
    
    def test_sqlite_database_initialization(self, temp_dir):
        """Test that SQLite database is properly initialized"""
        db_path = Path(temp_dir) / "test.db"
        SP500EODLoader(
            symbols=['AAPL'],
            storage_type='sqlite',
            db_path=str(db_path)
        )
        
        # Check database exists
        assert db_path.exists()
        
        # Check table exists
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='equity_data'")
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None
        assert result[0] == 'equity_data'
    
    def test_fetch_symbol_success(self, temp_dir):
        """Test fetching data for a single symbol"""
        loader = SP500EODLoader(
            symbols=['AAPL'],
            storage_type='csv',
            data_dir=temp_dir
        )
        
        # Fetch recent data (last 5 days to ensure data exists)
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        
        df = loader.fetch_symbol('AAPL', start_date=start_date, end_date=end_date)
        
        # Check that data was returned
        assert df is not None
        assert not df.empty
        assert 'Symbol' in df.columns
        assert 'Date' in df.columns
        assert df['Symbol'].iloc[0] == 'AAPL'
        
        # Check expected columns
        expected_cols = ['Date', 'open', 'high', 'low', 'close', 'volume', 'Symbol']
        for col in expected_cols:
            assert col in df.columns
    
    def test_fetch_invalid_symbol(self, temp_dir):
        """Test fetching data for an invalid symbol"""
        loader = SP500EODLoader(
            symbols=['INVALID_SYMBOL_XYZ'],
            storage_type='csv',
            data_dir=temp_dir
        )
        
        df = loader.fetch_symbol('INVALID_SYMBOL_XYZ')
        # Should return None or empty DataFrame for invalid symbols
        assert df is None or df.empty
    
    def test_save_to_csv(self, temp_dir):
        """Test saving data to CSV"""
        loader = SP500EODLoader(
            symbols=['AAPL'],
            storage_type='csv',
            data_dir=temp_dir
        )
        
        # Create sample DataFrame
        df = pd.DataFrame({
            'Date': pd.date_range('2023-01-01', periods=5),
            'open': [100, 101, 102, 103, 104],
            'high': [105, 106, 107, 108, 109],
            'low': [95, 96, 97, 98, 99],
            'close': [102, 103, 104, 105, 106],
            'volume': [1000000, 1100000, 1200000, 1300000, 1400000],
            'Symbol': ['AAPL'] * 5
        })
        
        loader.save_to_csv(df, 'AAPL')
        
        # Check file exists
        filepath = Path(temp_dir) / "equity_AAPL.csv"
        assert filepath.exists()
        
        # Load and verify
        loaded_df = pd.read_csv(filepath)
        assert len(loaded_df) == 5
        assert 'Symbol' in loaded_df.columns
    
    def test_save_to_sqlite(self, temp_dir):
        """Test saving data to SQLite"""
        db_path = Path(temp_dir) / "test.db"
        loader = SP500EODLoader(
            symbols=['AAPL'],
            storage_type='sqlite',
            db_path=str(db_path)
        )
        
        # Create sample DataFrame
        df = pd.DataFrame({
            'Date': pd.date_range('2023-01-01', periods=5),
            'date': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05'],
            'open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'high': [105.0, 106.0, 107.0, 108.0, 109.0],
            'low': [95.0, 96.0, 97.0, 98.0, 99.0],
            'close': [102.0, 103.0, 104.0, 105.0, 106.0],
            'adj_close': [102.0, 103.0, 104.0, 105.0, 106.0],
            'volume': [1000000, 1100000, 1200000, 1300000, 1400000],
            'dividends': [0.0, 0.0, 0.0, 0.0, 0.0],
            'stock_splits': [0.0, 0.0, 0.0, 0.0, 0.0]
        })
        
        loader.save_to_sqlite(df, 'AAPL')
        
        # Check data in database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM equity_data WHERE symbol = 'AAPL'")
        count = cursor.fetchone()[0]
        conn.close()
        
        assert count == 5
    
    def test_load_from_csv(self, temp_dir):
        """Test loading data from CSV"""
        loader = SP500EODLoader(
            symbols=['AAPL'],
            storage_type='csv',
            data_dir=temp_dir
        )
        
        # Create and save sample data
        df = pd.DataFrame({
            'Date': pd.date_range('2023-01-01', periods=3),
            'open': [100, 101, 102],
            'close': [102, 103, 104],
            'Symbol': ['AAPL'] * 3
        })
        loader.save_to_csv(df, 'AAPL')
        
        # Load it back
        loaded_df = loader.load_from_csv('AAPL')
        assert loaded_df is not None
        assert len(loaded_df) == 3
    
    def test_load_from_sqlite(self, temp_dir):
        """Test loading data from SQLite"""
        db_path = Path(temp_dir) / "test.db"
        loader = SP500EODLoader(
            symbols=['AAPL'],
            storage_type='sqlite',
            db_path=str(db_path)
        )
        
        # Create and save sample data
        df = pd.DataFrame({
            'date': ['2023-01-01', '2023-01-02', '2023-01-03'],
            'open': [100.0, 101.0, 102.0],
            'high': [105.0, 106.0, 107.0],
            'low': [95.0, 96.0, 97.0],
            'close': [102.0, 103.0, 104.0],
            'adj_close': [102.0, 103.0, 104.0],
            'volume': [1000000, 1100000, 1200000],
            'dividends': [0.0, 0.0, 0.0],
            'stock_splits': [0.0, 0.0, 0.0]
        })
        loader.save_to_sqlite(df, 'AAPL')
        
        # Load it back
        loaded_df = loader.load_from_sqlite('AAPL')
        assert loaded_df is not None
        assert len(loaded_df) == 3
    
    def test_fetch_and_save_integration(self, temp_dir):
        """Test end-to-end fetch and save"""
        loader = SP500EODLoader(
            symbols=['AAPL'],
            storage_type='csv',
            data_dir=temp_dir
        )
        
        # Fetch and save recent data
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        
        success = loader.fetch_and_save('AAPL', start_date=start_date, end_date=end_date)
        
        assert success is True
        
        # Verify file was created
        filepath = Path(temp_dir) / "equity_AAPL.csv"
        assert filepath.exists()
        
        # Load and verify
        df = pd.read_csv(filepath)
        assert not df.empty
        assert 'Symbol' in df.columns
    
    def test_rate_limiting(self, temp_dir, sample_symbols_file):
        """Test that rate limiting is applied"""
        import time
        
        loader = SP500EODLoader(
            symbols_file=sample_symbols_file,
            storage_type='csv',
            data_dir=temp_dir,
            rate_limit_delay=0.1  # Small delay for testing
        )
        
        # Measure time for fetching multiple symbols
        start_time = time.time()
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        
        result = loader.fetch_all(start_date=start_date, end_date=end_date)
        
        elapsed_time = time.time() - start_time
        
        # With 3 symbols and 0.1s delay, should take at least 0.2s (2 delays)
        # We give some margin for API call time
        assert elapsed_time >= 0.15
        
        # Check that at least some succeeded
        assert len(result['success']) > 0
    
    def test_continue_on_error(self, temp_dir):
        """Test that bulk fetch continues after errors"""
        loader = SP500EODLoader(
            symbols=['AAPL', 'INVALID_XYZ', 'MSFT'],
            storage_type='csv',
            data_dir=temp_dir
        )
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        
        result = loader.fetch_all(
            start_date=start_date,
            end_date=end_date,
            continue_on_error=True
        )
        
        # Should have some successes and some failures
        assert len(result['success']) > 0
        assert 'INVALID_XYZ' in result['failed']
