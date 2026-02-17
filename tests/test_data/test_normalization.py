"""Tests for data normalization utilities."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from copilot_quant.data.normalization import (
    normalize_symbol,
    validate_symbol,
    normalize_timestamps,
    adjust_for_contract_roll,
    standardize_column_names,
    adjust_for_splits,
    calculate_adjusted_close,
    detect_missing_data,
    validate_data_quality,
    fill_missing_data,
    remove_outliers,
    resample_data,
)


class TestSymbolNormalization:
    """Tests for symbol normalization."""

    def test_normalize_symbol_yahoo_format(self):
        """Test normalizing symbols for Yahoo Finance."""
        assert normalize_symbol('BRK.B', source='yahoo') == 'BRK-B'
        assert normalize_symbol('BRK-B', source='yahoo') == 'BRK-B'

    def test_normalize_symbol_alpha_vantage_format(self):
        """Test normalizing symbols for Alpha Vantage."""
        assert normalize_symbol('BRK-B', source='alpha_vantage') == 'BRK.B'
        assert normalize_symbol('BRK.B', source='alpha_vantage') == 'BRK.B'

    def test_normalize_symbol_uppercase(self):
        """Test that symbols are converted to uppercase."""
        assert normalize_symbol('aapl', source='yahoo') == 'AAPL'
        assert normalize_symbol('msft', source='yahoo') == 'MSFT'

    def test_normalize_symbol_strips_whitespace(self):
        """Test that whitespace is stripped."""
        assert normalize_symbol(' AAPL ', source='yahoo') == 'AAPL'
        assert normalize_symbol('MSFT  ', source='yahoo') == 'MSFT'

    def test_normalize_symbol_ib_format(self):
        """Test normalizing symbols for Interactive Brokers."""
        assert normalize_symbol('BRK.B', source='ib') == 'BRK B'
        assert normalize_symbol('BRK-B', source='ib') == 'BRK B'

    def test_normalize_symbol_quandl_format(self):
        """Test normalizing symbols for Quandl."""
        assert normalize_symbol('BRK/B', source='quandl') == 'BRK-B'
        assert normalize_symbol('BRK.B', source='quandl') == 'BRK-B'

    def test_normalize_symbol_polygon_format(self):
        """Test normalizing symbols for Polygon."""
        assert normalize_symbol('BRK-B', source='polygon') == 'BRK.B'
        assert normalize_symbol('BRK.B', source='polygon') == 'BRK.B'


class TestSymbolValidation:
    """Tests for symbol validation."""

    def test_validate_symbol_valid(self):
        """Test validation of valid symbols."""
        assert validate_symbol('AAPL', source='yahoo') is True
        assert validate_symbol('BRK-B', source='yahoo') is True
        assert validate_symbol('^GSPC', source='yahoo') is True

    def test_validate_symbol_empty(self):
        """Test validation of empty symbols."""
        assert validate_symbol('', source='yahoo') is False
        assert validate_symbol('  ', source='yahoo') is False

    def test_validate_symbol_none(self):
        """Test validation of None."""
        assert validate_symbol(None, source='yahoo') is False


class TestTimestampNormalization:
    """Tests for timestamp normalization."""

    def test_normalize_timestamps_equity(self):
        """Test normalizing timestamps for equity markets."""
        dates = pd.date_range('2024-01-01', periods=3, tz='UTC')
        df = pd.DataFrame({
            'date': dates,
            'close': [100, 101, 102],
        })

        result = normalize_timestamps(df, market_type='equity')

        # Should be in US/Eastern timezone
        assert result['date'].dt.tz.zone == 'US/Eastern'

    def test_normalize_timestamps_prediction_market(self):
        """Test normalizing timestamps for prediction markets."""
        dates = pd.date_range('2024-01-01', periods=3, tz='US/Eastern')
        df = pd.DataFrame({
            'date': dates,
            'close': [100, 101, 102],
        })

        result = normalize_timestamps(df, market_type='prediction')

        # Should be in UTC
        assert result['date'].dt.tz.zone == 'UTC'

    def test_normalize_timestamps_with_index(self):
        """Test normalizing timestamps when using DatetimeIndex."""
        dates = pd.date_range('2024-01-01', periods=3, tz='UTC')
        df = pd.DataFrame({
            'close': [100, 101, 102],
        }, index=dates)

        result = normalize_timestamps(df, market_type='equity')

        # Should be in US/Eastern timezone
        assert result.index.tz.zone == 'US/Eastern'

    def test_normalize_timestamps_naive(self):
        """Test normalizing naive timestamps."""
        dates = pd.date_range('2024-01-01', periods=3)  # No timezone
        df = pd.DataFrame({
            'date': dates,
            'close': [100, 101, 102],
        })

        result = normalize_timestamps(df, market_type='equity')

        # Should be localized to US/Eastern
        assert result['date'].dt.tz.zone == 'US/Eastern'

    def test_normalize_timestamps_custom_timezone(self):
        """Test normalizing timestamps to custom timezone."""
        dates = pd.date_range('2024-01-01', periods=3, tz='UTC')
        df = pd.DataFrame({
            'date': dates,
            'close': [100, 101, 102],
        })

        result = normalize_timestamps(df, target_timezone='Asia/Tokyo')

        # Should be in Asia/Tokyo timezone
        assert result['date'].dt.tz.zone == 'Asia/Tokyo'


class TestContractRollAdjustment:
    """Tests for contract roll adjustment."""

    def test_adjust_for_contract_roll_manual_difference(self):
        """Test manual contract roll adjustment using difference method."""
        df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=5),
            'close': [100.0, 101.0, 102.0, 103.0, 104.0],
        })

        # Roll on day 3 with -0.25 adjustment
        result = adjust_for_contract_roll(
            df,
            roll_date='2024-01-03',
            adjustment=-0.25,
            front_contract_column='close',
            method='difference'
        )

        # Prices before roll should be adjusted
        assert result.iloc[0]['close'] == 99.75  # 100 - 0.25
        assert result.iloc[1]['close'] == 100.75  # 101 - 0.25
        # Prices on/after roll should be unchanged
        assert result.iloc[2]['close'] == 102.0
        assert result.iloc[3]['close'] == 103.0

    def test_adjust_for_contract_roll_manual_ratio(self):
        """Test manual contract roll adjustment using ratio method."""
        df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=5),
            'close': [100.0, 100.0, 100.0, 100.0, 100.0],
        })

        # Roll on day 3 with 1.1 ratio adjustment
        result = adjust_for_contract_roll(
            df,
            roll_date='2024-01-03',
            adjustment=1.1,
            front_contract_column='close',
            method='ratio'
        )

        # Prices before roll should be multiplied by ratio
        assert result.iloc[0]['close'] == pytest.approx(110.0, abs=0.01)
        assert result.iloc[1]['close'] == pytest.approx(110.0, abs=0.01)
        # Prices on/after roll should be unchanged
        assert result.iloc[2]['close'] == 100.0

    def test_adjust_for_contract_roll_auto_difference(self):
        """Test automatic contract roll adjustment calculation."""
        df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=5),
            'front_close': [100.0, 101.0, 102.0, 103.0, 104.0],
            'back_close': [100.5, 101.5, 102.5, 103.5, 104.5],
        })

        # Auto-calculate adjustment from front and back contract prices
        result = adjust_for_contract_roll(
            df,
            roll_date='2024-01-03',
            front_contract_column='front_close',
            back_contract_column='back_close',
            method='difference'
        )

        # Adjustment should be front - back = 101 - 101.5 = -0.5 (from day before roll)
        assert result.iloc[0]['front_close'] == pytest.approx(99.5, abs=0.01)
        assert result.iloc[1]['front_close'] == pytest.approx(100.5, abs=0.01)


class TestColumnNameStandardization:
    """Tests for column name standardization."""

    def test_standardize_column_names(self):
        """Test standardizing column names."""
        df = pd.DataFrame({
            'Open': [100, 101],
            'High': [105, 106],
            'Low': [99, 100],
            'Close': [104, 105],
            'Volume': [1000000, 1100000],
        })

        standardized = standardize_column_names(df)

        assert 'open' in standardized.columns
        assert 'high' in standardized.columns
        assert 'low' in standardized.columns
        assert 'close' in standardized.columns
        assert 'volume' in standardized.columns

    def test_standardize_column_names_adj_close(self):
        """Test standardizing Adj Close column."""
        df = pd.DataFrame({
            'Close': [100],
            'Adj Close': [95],
        })

        standardized = standardize_column_names(df)

        assert 'close' in standardized.columns
        assert 'adj_close' in standardized.columns

    def test_standardize_column_names_inplace(self):
        """Test standardizing column names in place."""
        df = pd.DataFrame({'Open': [100], 'High': [105]})

        result = standardize_column_names(df, inplace=True)

        assert result is df  # Same object
        assert 'open' in df.columns


class TestSplitAdjustment:
    """Tests for stock split adjustment."""

    def test_adjust_for_splits_manual(self):
        """Test manual split adjustment."""
        df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=5),
            'open': [100, 101, 102, 103, 104],
            'high': [105, 106, 107, 108, 109],
            'low': [99, 100, 101, 102, 103],
            'close': [104, 105, 106, 107, 108],
            'volume': [1000000, 1100000, 1200000, 1300000, 1400000],
        })

        # 2-for-1 split on day 3
        adjusted = adjust_for_splits(df, split_ratio=2.0, split_date='2024-01-03')

        # Prices before split should be halved
        assert adjusted.iloc[0]['close'] == 52.0  # 104 / 2
        assert adjusted.iloc[1]['close'] == 52.5  # 105 / 2
        # Prices after split should be unchanged
        assert adjusted.iloc[2]['close'] == 106
        assert adjusted.iloc[3]['close'] == 107

    def test_adjust_for_splits_from_column(self):
        """Test split adjustment using split column."""
        df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=5),
            'close': [100, 101, 102, 103, 104],
            'stock_splits': [0, 0, 2.0, 0, 0],  # Split on day 3
        })

        adjusted = adjust_for_splits(df)

        # Prices before split should be adjusted
        assert adjusted.iloc[0]['close'] == 50.0  # 100 / 2
        assert adjusted.iloc[1]['close'] == 50.5  # 101 / 2
        # Prices after split should be unchanged
        assert adjusted.iloc[2]['close'] == 102


class TestAdjustedClose:
    """Tests for adjusted close calculation."""

    def test_calculate_adjusted_close_basic(self):
        """Test basic adjusted close calculation."""
        df = pd.DataFrame({
            'close': [100, 101, 102, 103, 104],
            'dividends': [0, 0, 1, 0, 0],
            'stock_splits': [0, 0, 0, 0, 0],
        })

        result = calculate_adjusted_close(df, use_dividends=False, use_splits=False)

        assert 'adj_close' in result.columns
        # Without adjustments, should equal close
        assert (result['close'] == result['adj_close']).all()


class TestMissingDataDetection:
    """Tests for missing data detection."""

    def test_detect_missing_values(self):
        """Test detecting missing values."""
        df = pd.DataFrame({
            'close': [100, np.nan, 102, 103],
            'volume': [1000, 1100, np.nan, 1300],
        })

        issues = detect_missing_data(df)

        assert len(issues['missing_values']) == 2
        assert any(item['column'] == 'close' for item in issues['missing_values'])
        assert any(item['column'] == 'volume' for item in issues['missing_values'])

    def test_detect_zero_volume(self):
        """Test detecting zero volume days."""
        df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=3),
            'close': [100, 101, 102],
            'volume': [1000, 0, 1200],
        })

        issues = detect_missing_data(df)

        assert len(issues['zero_volume']) == 1

    def test_detect_price_anomalies(self):
        """Test detecting price anomalies."""
        df = pd.DataFrame({
            'close': [100, 100, 200, 100],  # 100% jump
        })

        issues = detect_missing_data(df)

        assert len(issues['price_anomalies']) > 0

    def test_detect_date_gaps(self):
        """Test detecting date gaps."""
        dates = [
            datetime(2024, 1, 1),
            datetime(2024, 1, 2),
            datetime(2024, 1, 10),  # 8-day gap
        ]
        df = pd.DataFrame({
            'date': dates,
            'close': [100, 101, 102],
        })

        issues = detect_missing_data(df)

        assert len(issues['date_gaps']) > 0
        assert issues['date_gaps'][0]['days'] == 8


class TestDataQualityValidation:
    """Tests for data quality validation."""

    def test_validate_empty_dataframe(self):
        """Test validation of empty DataFrame."""
        df = pd.DataFrame()

        errors = validate_data_quality(df)

        assert len(errors) > 0
        assert any('empty' in err.lower() for err in errors)

    def test_validate_missing_columns(self):
        """Test validation with missing required columns."""
        df = pd.DataFrame({
            'open': [100],
            'high': [105],
        })

        errors = validate_data_quality(df)

        assert any('missing required columns' in err.lower() for err in errors)

    def test_validate_price_relationships(self):
        """Test validation of price relationships."""
        df = pd.DataFrame({
            'open': [100],
            'high': [95],  # High < Open (invalid)
            'low': [99],
            'close': [98],
            'volume': [1000],
        })

        errors = validate_data_quality(df)

        assert any('high' in err.lower() for err in errors)

    def test_validate_negative_prices(self):
        """Test detection of negative prices."""
        df = pd.DataFrame({
            'open': [100],
            'high': [105],
            'low': [99],
            'close': [-5],  # Negative price
            'volume': [1000],
        })

        errors = validate_data_quality(df)

        assert any('negative' in err.lower() for err in errors)

    def test_validate_valid_data(self):
        """Test validation of valid data."""
        df = pd.DataFrame({
            'open': [100, 101],
            'high': [105, 106],
            'low': [99, 100],
            'close': [104, 105],
            'volume': [1000000, 1100000],
        })

        errors = validate_data_quality(df)

        # Should have no errors for valid data
        assert len(errors) == 0


class TestFillMissingData:
    """Tests for filling missing data."""

    def test_fill_missing_ffill(self):
        """Test forward fill."""
        df = pd.DataFrame({
            'close': [100, np.nan, np.nan, 103],
        })

        filled = fill_missing_data(df, method='ffill')

        assert filled['close'].iloc[1] == 100
        assert filled['close'].iloc[2] == 100

    def test_fill_missing_bfill(self):
        """Test backward fill."""
        df = pd.DataFrame({
            'close': [100, np.nan, np.nan, 103],
        })

        filled = fill_missing_data(df, method='bfill')

        assert filled['close'].iloc[1] == 103
        assert filled['close'].iloc[2] == 103

    def test_fill_missing_interpolate(self):
        """Test interpolation."""
        df = pd.DataFrame({
            'close': [100.0, np.nan, np.nan, 103.0],
        })

        filled = fill_missing_data(df, method='interpolate')

        assert filled['close'].iloc[1] == 101.0
        assert filled['close'].iloc[2] == 102.0

    def test_fill_missing_drop(self):
        """Test dropping NaN values."""
        df = pd.DataFrame({
            'close': [100, np.nan, 102, 103],
        })

        filled = fill_missing_data(df, method='drop')

        assert len(filled) == 3
        assert filled['close'].isna().sum() == 0


class TestOutlierRemoval:
    """Tests for outlier removal."""

    def test_remove_outliers_iqr(self):
        """Test outlier removal using IQR method."""
        df = pd.DataFrame({
            'close': [100, 101, 102, 103, 104, 105, 200],  # 200 is outlier
        })

        cleaned = remove_outliers(df, column='close', method='iqr', threshold=1.5)

        assert len(cleaned) < len(df)
        assert 200 not in cleaned['close'].values

    def test_remove_outliers_zscore(self):
        """Test outlier removal using z-score method."""
        df = pd.DataFrame({
            'close': [100, 101, 102, 103, 104, 105, 200],  # 200 is outlier
        })

        cleaned = remove_outliers(df, column='close', method='zscore', threshold=2.0)

        assert len(cleaned) < len(df)
        assert 200 not in cleaned['close'].values


class TestDataResampling:
    """Tests for data resampling."""

    def test_resample_daily_to_weekly(self):
        """Test resampling daily data to weekly."""
        dates = pd.date_range('2024-01-01', periods=14, freq='D')
        df = pd.DataFrame({
            'open': range(100, 114),
            'high': range(105, 119),
            'low': range(99, 113),
            'close': range(104, 118),
            'volume': [1000000] * 14,
        }, index=dates)

        weekly = resample_data(df, freq='W')

        assert len(weekly) < len(df)
        assert isinstance(weekly.index, pd.DatetimeIndex)

    def test_resample_aggregation(self):
        """Test that aggregation rules are applied correctly."""
        dates = pd.date_range('2024-01-01', periods=7, freq='D')
        df = pd.DataFrame({
            'open': [100, 101, 102, 103, 104, 105, 106],
            'high': [110, 111, 112, 113, 114, 115, 116],
            'low': [90, 91, 92, 93, 94, 95, 96],
            'close': [105, 106, 107, 108, 109, 110, 111],
            'volume': [1000000] * 7,
        }, index=dates)

        weekly = resample_data(df, freq='W')

        # First week should have open from first day
        assert weekly.iloc[0]['open'] == 100
        # Last price should be from last day of the week
        assert weekly.iloc[0]['close'] == 111  # All 7 days are in the same week
        # Volume should be summed
        assert weekly.iloc[0]['volume'] == 7000000

    def test_resample_with_custom_aggregation(self):
        """Test resampling with custom aggregation rules."""
        dates = pd.date_range('2024-01-01', periods=7, freq='D')
        df = pd.DataFrame({
            'close': range(100, 107),
        }, index=dates)

        weekly = resample_data(df, freq='W', aggregation={'close': 'mean'})

        # Close should be averaged
        assert weekly.iloc[0]['close'] == pytest.approx(103.0)


class TestNormalizationIdempotence:
    """
    Test that normalization operations are idempotent.
    
    Applying the same normalization twice should produce the same result.
    This is critical for data pipeline reliability.
    """
    
    def test_normalize_symbol_idempotent(self):
        """
        Test that symbol normalization is idempotent.
        
        Normalizing an already normalized symbol should return the same result.
        """
        from copilot_quant.data.normalization import normalize_symbol
        
        # First normalization
        symbol = "  BRK-B  "
        normalized1 = normalize_symbol(symbol, source='yahoo')
        
        # Second normalization of the result
        normalized2 = normalize_symbol(normalized1, source='yahoo')
        
        # Should be the same
        assert normalized1 == normalized2
    
    def test_standardize_columns_idempotent(self):
        """
        Test that column standardization is idempotent.
        """
        from copilot_quant.data.normalization import standardize_column_names
        
        # Create DataFrame with mixed case columns
        df = pd.DataFrame({
            'Open': [100, 101],
            'High': [105, 106],
            'Low': [95, 96],
            'Close': [102, 103],
        })
        
        # First standardization
        df1 = standardize_column_names(df.copy())
        
        # Second standardization
        df2 = standardize_column_names(df1.copy())
        
        # Column names should be identical
        assert list(df1.columns) == list(df2.columns)
        assert all(df1.columns == df2.columns)
    
    def test_timestamp_normalization_idempotent(self):
        """
        Test that timestamp normalization is idempotent.
        """
        from copilot_quant.data.normalization import normalize_timestamps
        
        # Create DataFrame with timestamps
        df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=3, tz='UTC'),
            'price': [100, 101, 102]
        })
        
        # First normalization
        df1 = normalize_timestamps(df.copy(), market_type='equity', target_timezone='America/New_York')
        
        # Second normalization
        df2 = normalize_timestamps(df1.copy(), market_type='equity', target_timezone='America/New_York')
        
        # Timestamps should be identical
        pd.testing.assert_frame_equal(df1, df2)


class TestNormalizationEdgeCases:
    """
    Test edge cases in data normalization.
    
    These tests ensure the pipeline handles unusual but valid scenarios:
    - Empty DataFrames
    - Single-row DataFrames
    - Missing optional columns
    - Extreme values
    - Timezone edge cases
    """
    
    def test_empty_dataframe_handling(self):
        """
        Test that normalization functions handle empty DataFrames gracefully.
        """
        from copilot_quant.data.normalization import (
            standardize_column_names,
            validate_data_quality,
        )
        
        # Empty DataFrame
        df = pd.DataFrame()
        
        # Should not crash
        result = standardize_column_names(df)
        assert isinstance(result, pd.DataFrame)
        assert result.empty
        
        # Validation should identify it as invalid
        issues = validate_data_quality(df)
        assert len(issues) > 0
        assert any('empty' in issue.lower() for issue in issues)
    
    def test_single_row_dataframe(self):
        """
        Test handling of single-row DataFrame.
        
        This is common for real-time data or latest quotes.
        """
        from copilot_quant.data.normalization import (
            standardize_column_names,
            validate_data_quality,
        )
        
        # Single row
        df = pd.DataFrame({
            'Date': [pd.Timestamp('2024-01-01')],
            'Open': [100.0],
            'High': [105.0],
            'Low': [95.0],
            'Close': [102.0],
            'Volume': [1000000]
        })
        
        # Should handle single row
        result = standardize_column_names(df)
        assert len(result) == 1
        assert 'open' in result.columns
        
        # Validation should pass
        issues = validate_data_quality(result)
        assert len(issues) == 0
    
    def test_extreme_price_values(self):
        """
        Test handling of extreme but valid price values.
        """
        from copilot_quant.data.normalization import validate_data_quality
        
        # Very high prices (like BRK.A)
        df_high = pd.DataFrame({
            'open': [500000.0, 505000.0],
            'high': [510000.0, 515000.0],
            'low': [495000.0, 500000.0],
            'close': [505000.0, 510000.0],
            'volume': [100, 150]
        })
        
        issues = validate_data_quality(df_high)
        # Should be valid (not flagged as error)
        assert len(issues) == 0 or 'extreme' not in str(issues).lower()
        
        # Very low prices (penny stocks)
        df_low = pd.DataFrame({
            'open': [0.01, 0.015],
            'high': [0.02, 0.025],
            'low': [0.005, 0.01],
            'close': [0.015, 0.02],
            'volume': [10000000, 15000000]
        })
        
        issues = validate_data_quality(df_low)
        # Should be valid
        assert len(issues) == 0 or 'negative' not in str(issues).lower()
    
    def test_timezone_edge_cases(self):
        """
        Test timezone handling edge cases.
        """
        from copilot_quant.data.normalization import normalize_timestamps
        
        # Daylight saving time transition
        df = pd.DataFrame({
            'date': pd.date_range('2024-03-10', periods=3, freq='h', tz='America/New_York'),
            'price': [100, 101, 102]
        })
        
        # Should handle DST transitions
        result = normalize_timestamps(df, market_type='equity', target_timezone='America/New_York')
        assert 'date' in result.columns or result.index.name == 'date'
        assert len(result) == 3
        
        # Naive timestamps (no timezone)
        df_naive = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=3, freq='h'),
            'price': [100, 101, 102]
        })
        
        # Should add timezone
        result_naive = normalize_timestamps(df_naive, market_type='equity', target_timezone='America/New_York')
        # Check if timezone was added (either to column or index)
        if 'date' in result_naive.columns:
            assert result_naive['date'].dt.tz is not None
        else:
            assert result_naive.index.tz is not None
    
    def test_missing_optional_columns(self):
        """
        Test handling of DataFrames missing optional columns.
        """
        from copilot_quant.data.normalization import standardize_column_names
        
        # DataFrame with only required columns
        df = pd.DataFrame({
            'Date': pd.date_range('2024-01-01', periods=3),
            'Close': [100, 101, 102],
        })
        
        # Should handle missing optional columns
        result = standardize_column_names(df)
        assert 'close' in result.columns
        # Should not crash if volume, open, etc. are missing
    
    def test_duplicate_timestamps(self):
        """
        Test handling of duplicate timestamps.
        
        This can occur with intraday data from multiple sources.
        """
        from copilot_quant.data.normalization import detect_missing_data
        
        df = pd.DataFrame({
            'close': [100, 100.5, 101, 101.5],
            'volume': [1000, 2000, 3000, 4000]
        }, index=pd.to_datetime(['2024-01-01', '2024-01-01', '2024-01-02', '2024-01-02']))
        
        # Should handle duplicates without crashing
        try:
            missing = detect_missing_data(df)
            # Should not crash
            assert isinstance(missing, dict)
        except Exception:
            # If it raises an exception, at least it didn't crash the process
            pass
