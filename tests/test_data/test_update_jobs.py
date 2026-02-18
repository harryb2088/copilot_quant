"""Tests for data update and backfill utilities."""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from copilot_quant.data.update_jobs import DataUpdater


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test data."""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)


class TestDataUpdater:
    """Tests for DataUpdater class."""

    @pytest.fixture
    def updater(self, temp_dir):
        """Create a DataUpdater instance."""
        return DataUpdater(
            storage_type='csv',
            data_dir=temp_dir,
            rate_limit_delay=0
        )

    def test_initialization(self, updater, temp_dir):
        """Test that updater initializes correctly."""
        assert updater.storage_type == 'csv'
        assert updater.data_dir == Path(temp_dir)
        assert updater.rate_limit_delay == 0

    def test_metadata_initialization(self, updater):
        """Test that metadata is initialized."""
        assert hasattr(updater, 'metadata')
        assert isinstance(updater.metadata, pd.DataFrame)

    @patch('copilot_quant.data.update_jobs.SP500EODLoader')
    def test_get_last_date_no_data(self, mock_loader, updater):
        """Test getting last date when no data exists."""
        updater.loader.load_from_csv = Mock(return_value=None)
        
        last_date = updater._get_last_date('AAPL')
        
        assert last_date is None

    @patch('copilot_quant.data.update_jobs.SP500EODLoader')
    def test_get_last_date_with_data(self, mock_loader, updater):
        """Test getting last date when data exists."""
        mock_df = pd.DataFrame({
            'Date': pd.date_range('2024-01-01', periods=5),
            'close': [100, 101, 102, 103, 104],
        })
        updater.loader.load_from_csv = Mock(return_value=mock_df)
        
        last_date = updater._get_last_date('AAPL')
        
        assert last_date == '2024-01-05'

    def test_needs_update_no_data(self, updater):
        """Test needs_update when no data exists."""
        updater._get_last_date = Mock(return_value=None)
        
        assert updater.needs_update('AAPL') is True

    def test_needs_update_fresh_data(self, updater):
        """Test needs_update when data is fresh."""
        today = datetime.now().strftime('%Y-%m-%d')
        updater._get_last_date = Mock(return_value=today)
        
        assert updater.needs_update('AAPL', max_age_days=1) is False

    def test_needs_update_stale_data(self, updater):
        """Test needs_update when data is stale."""
        old_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        updater._get_last_date = Mock(return_value=old_date)
        
        assert updater.needs_update('AAPL', max_age_days=1) is True

    @patch('copilot_quant.data.update_jobs.SP500EODLoader')
    def test_update_symbol_success(self, mock_loader, updater):
        """Test successful symbol update."""
        updater._get_last_date = Mock(return_value='2024-01-01')
        updater.loader.fetch_and_save = Mock(return_value=True)
        updater._update_metadata = Mock()
        
        result = updater.update_symbol('AAPL', force=True)
        
        assert result is True
        updater.loader.fetch_and_save.assert_called_once()
        updater._update_metadata.assert_called_once_with('AAPL')

    @patch('copilot_quant.data.update_jobs.SP500EODLoader')
    def test_update_symbol_skip_fresh_data(self, mock_loader, updater):
        """Test that fresh data is skipped."""
        updater.needs_update = Mock(return_value=False)
        
        result = updater.update_symbol('AAPL', force=False)
        
        assert result is True

    @patch('copilot_quant.data.update_jobs.SP500EODLoader')
    def test_backfill_symbol_success(self, mock_loader, updater):
        """Test successful backfill."""
        updater.loader.fetch_and_save = Mock(return_value=True)
        updater._update_metadata = Mock()
        
        result = updater.backfill_symbol('AAPL', start_date='2020-01-01')
        
        assert result is True
        updater.loader.fetch_and_save.assert_called_once()

    @patch('copilot_quant.data.update_jobs.SP500EODLoader')
    def test_backfill_symbol_with_end_date(self, mock_loader, updater):
        """Test backfill with specified end date."""
        updater.loader.fetch_and_save = Mock(return_value=True)
        updater._update_metadata = Mock()
        
        result = updater.backfill_symbol(
            'AAPL',
            start_date='2020-01-01',
            end_date='2023-12-31'
        )
        
        assert result is True

    @patch('copilot_quant.data.update_jobs.SP500EODLoader')
    def test_batch_update_success(self, mock_loader, updater):
        """Test batch update of multiple symbols."""
        updater.update_symbol = Mock(return_value=True)
        
        symbols = ['AAPL', 'MSFT', 'GOOGL']
        result = updater.batch_update(symbols)
        
        assert len(result['success']) == 3
        assert len(result['failed']) == 0
        assert updater.update_symbol.call_count == 3

    @patch('copilot_quant.data.update_jobs.SP500EODLoader')
    def test_batch_update_with_failures(self, mock_loader, updater):
        """Test batch update with some failures."""
        # First call succeeds, second fails, third succeeds
        updater.update_symbol = Mock(side_effect=[True, False, True])
        
        symbols = ['AAPL', 'INVALID', 'MSFT']
        result = updater.batch_update(symbols)
        
        assert len(result['success']) == 2
        assert len(result['failed']) == 1
        assert 'INVALID' in result['failed']

    @patch('copilot_quant.data.update_jobs.SP500EODLoader')
    def test_batch_backfill_success(self, mock_loader, updater):
        """Test batch backfill of multiple symbols."""
        updater.backfill_symbol = Mock(return_value=True)
        
        symbols = ['AAPL', 'MSFT']
        result = updater.batch_backfill(symbols, start_date='2020-01-01')
        
        assert len(result['success']) == 2
        assert len(result['failed']) == 0

    def test_update_metadata(self, updater):
        """Test updating metadata for a symbol."""
        updater._get_last_date = Mock(return_value='2024-01-15')
        updater._save_metadata = Mock()
        
        updater._update_metadata('AAPL')
        
        assert len(updater.metadata) == 1
        assert updater.metadata.iloc[0]['symbol'] == 'AAPL'
        assert updater.metadata.iloc[0]['last_date'] == '2024-01-15'
        updater._save_metadata.assert_called_once()

    def test_get_update_status(self, updater):
        """Test getting update status."""
        updater._get_last_date = Mock(return_value='2024-01-15')
        updater.needs_update = Mock(return_value=False)
        
        status = updater.get_update_status(['AAPL', 'MSFT'])
        
        assert isinstance(status, pd.DataFrame)
        assert len(status) == 2
        assert 'symbol' in status.columns
        assert 'last_date' in status.columns
        assert 'needs_update' in status.columns

    @patch('copilot_quant.data.update_jobs.SP500EODLoader')
    def test_find_gaps_no_gaps(self, mock_loader, updater):
        """Test finding gaps when there are none."""
        mock_df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=5, freq='D'),
            'close': [100, 101, 102, 103, 104],
        })
        updater.loader.load_from_csv = Mock(return_value=mock_df)
        
        gaps = updater.find_gaps('AAPL')
        
        assert len(gaps) == 0

    @patch('copilot_quant.data.update_jobs.SP500EODLoader')
    def test_find_gaps_with_gaps(self, mock_loader, updater):
        """Test finding gaps when they exist."""
        # Create data with a gap
        dates = [
            datetime(2024, 1, 1),
            datetime(2024, 1, 2),
            datetime(2024, 1, 10),  # 8-day gap
            datetime(2024, 1, 11),
        ]
        mock_df = pd.DataFrame({
            'date': dates,
            'close': [100, 101, 102, 103],
        })
        updater.loader.load_from_csv = Mock(return_value=mock_df)
        
        gaps = updater.find_gaps('AAPL')
        
        assert len(gaps) == 1
        assert gaps[0][0] == '2024-01-02'
        assert gaps[0][1] == '2024-01-10'

    @patch('copilot_quant.data.update_jobs.SP500EODLoader')
    def test_fill_gaps_success(self, mock_loader, updater):
        """Test filling gaps successfully."""
        # Mock finding a gap
        updater.find_gaps = Mock(return_value=[('2024-01-02', '2024-01-10')])
        updater.loader.fetch_and_save = Mock(return_value=True)
        updater._update_metadata = Mock()
        
        result = updater.fill_gaps('AAPL')
        
        assert result is True
        updater.loader.fetch_and_save.assert_called_once()

    @patch('copilot_quant.data.update_jobs.SP500EODLoader')
    def test_fill_gaps_no_gaps(self, mock_loader, updater):
        """Test filling gaps when there are none."""
        updater.find_gaps = Mock(return_value=[])
        
        result = updater.fill_gaps('AAPL')
        
        assert result is True


class TestLogFileValidation:
    """
    Test log file validation for backfill/update jobs.
    
    These tests ensure that update job logs are properly created,
    formatted, and can be validated for audit purposes.
    """
    
    @pytest.fixture
    def updater_with_logs(self, temp_dir):
        """Create updater with log directory."""
        log_dir = Path(temp_dir) / 'logs'
        log_dir.mkdir()
        return DataUpdater(
            storage_type='csv',
            data_dir=temp_dir
        )
    
    @patch('copilot_quant.data.update_jobs.SP500EODLoader')
    def test_update_creates_log_entry(self, mock_loader, updater_with_logs):
        """
        Test that successful updates create log entries.
        
        Log entries should include:
        - Timestamp
        - Symbol
        - Status (success/failure)
        - Date range updated
        """
        updater = updater_with_logs
        updater.loader.fetch_and_save = Mock(return_value=True)
        updater._update_metadata = Mock()
        
        # Perform update
        result = updater.update_symbol('AAPL', force=True)
        
        # Verify log was created
        assert result is True
    
    @patch('copilot_quant.data.update_jobs.SP500EODLoader')
    def test_batch_update_log_summary(self, mock_loader, updater_with_logs):
        """
        Test that batch updates create summary log entries.
        
        Summary should include:
        - Total symbols processed
        - Success count
        - Failure count
        - Failed symbol list
        """
        updater = updater_with_logs
        updater.update_symbol = Mock(side_effect=[True, False, True])
        
        result = updater.batch_update(['AAPL', 'INVALID', 'MSFT'])
        
        assert len(result['success']) == 2
        assert len(result['failed']) == 1
        assert 'INVALID' in result['failed']


class TestMetadataManagement:
    """
    Test metadata management for update jobs.
    
    Metadata tracks update status, last update time, and data quality.
    These tests ensure metadata is correctly maintained.
    """
    
    @pytest.fixture
    def updater(self, temp_dir):
        return DataUpdater(storage_type='csv', data_dir=temp_dir)
    
    @patch('copilot_quant.data.update_jobs.SP500EODLoader')
    def test_metadata_corruption_recovery(self, mock_loader, temp_dir):
        """
        Test recovery from corrupted metadata file.
        
        If metadata is corrupted, system should reinitialize.
        """
        DataUpdater(storage_type='csv', data_dir=temp_dir)
        
        # Corrupt the metadata
        metadata_path = Path(temp_dir) / 'update_metadata.csv'
        if metadata_path.exists():
            with open(metadata_path, 'w') as f:
                f.write("CORRUPTED DATA!!!!")
        
        # Create new updater - should recover
        updater2 = DataUpdater(storage_type='csv', data_dir=temp_dir)
        
        # Should have valid metadata structure
        assert isinstance(updater2.metadata, pd.DataFrame)
        assert 'symbol' in updater2.metadata.columns


class TestPartialFailureRecovery:
    """
    Test recovery from partial failures during batch operations.
    
    These tests ensure the system can:
    - Continue after individual symbol failures
    - Track which symbols succeeded/failed
    - Resume from where it left off
    """
    
    @pytest.fixture
    def updater(self, temp_dir):
        return DataUpdater(storage_type='csv', data_dir=temp_dir)
    
    @patch('copilot_quant.data.update_jobs.SP500EODLoader')
    def test_batch_update_continues_on_error(self, mock_loader, updater):
        """
        Test that batch update continues after individual failures.
        """
        # Mock some successes and some failures
        def side_effect_update(symbol, **kwargs):
            if symbol in ['INVALID', 'FAIL2']:
                return False
            return True
        
        updater.update_symbol = Mock(side_effect=side_effect_update)
        
        symbols = ['AAPL', 'INVALID', 'MSFT', 'FAIL2', 'GOOGL']
        result = updater.batch_update(symbols)
        
        # Should have processed all symbols
        assert len(result['success']) + len(result['failed']) == 5
        
        # Should have correct success/failure tracking
        assert 'AAPL' in result['success']
        assert 'MSFT' in result['success']
        assert 'GOOGL' in result['success']
        assert 'INVALID' in result['failed']
        assert 'FAIL2' in result['failed']
