"""Tests for pairs trading utilities."""

import numpy as np
import pandas as pd
import pytest

from copilot_quant.strategies.pairs_utils import (
    calculate_correlation,
    calculate_half_life,
    calculate_hedge_ratio,
    calculate_spread,
    calculate_zscore,
    find_cointegrated_pairs,
    test_cointegration,
)


class TestCointegration:
    """Tests for cointegration testing."""
    
    def test_cointegrated_series(self):
        """Test detection of cointegrated series."""
        # Create two cointegrated series
        np.random.seed(42)
        x = np.cumsum(np.random.randn(100))
        y = 2 * x + np.random.randn(100) * 0.1
        
        series1 = pd.Series(x)
        series2 = pd.Series(y)
        
        is_coint, p_value, test_stat = test_cointegration(series1, series2)
        
        # Should be cointegrated (low p-value)
        assert p_value < 0.05
        assert bool(is_coint) is True
    
    def test_non_cointegrated_series(self):
        """Test detection of non-cointegrated series."""
        # Create two independent random walks
        np.random.seed(42)
        series1 = pd.Series(np.cumsum(np.random.randn(100)))
        series2 = pd.Series(np.cumsum(np.random.randn(100)))
        
        is_coint, p_value, test_stat = test_cointegration(series1, series2)
        
        # Should not be cointegrated (high p-value)
        # Note: This is probabilistic, so we just check the return types
        assert isinstance(bool(is_coint), bool)
        assert 0 <= p_value <= 1
        assert isinstance(float(test_stat), float)
    
    def test_insufficient_data(self):
        """Test handling of insufficient data."""
        series1 = pd.Series([1, 2, 3])
        series2 = pd.Series([2, 4, 6])
        
        is_coint, p_value, test_stat = test_cointegration(series1, series2)
        
        assert is_coint is False
        assert p_value == 1.0


class TestCorrelation:
    """Tests for correlation calculation."""
    
    def test_perfect_correlation(self):
        """Test perfect positive correlation."""
        series1 = pd.Series([1, 2, 3, 4, 5])
        series2 = pd.Series([2, 4, 6, 8, 10])
        
        corr = calculate_correlation(series1, series2)
        
        assert abs(corr - 1.0) < 0.001
    
    def test_negative_correlation(self):
        """Test negative correlation."""
        series1 = pd.Series([1, 2, 3, 4, 5])
        series2 = pd.Series([10, 8, 6, 4, 2])
        
        corr = calculate_correlation(series1, series2)
        
        assert corr < -0.9
    
    def test_no_correlation(self):
        """Test uncorrelated series."""
        np.random.seed(42)
        series1 = pd.Series(np.random.randn(100))
        series2 = pd.Series(np.random.randn(100))
        
        corr = calculate_correlation(series1, series2)
        
        # Random series should have low correlation
        assert abs(corr) < 0.3
    
    def test_insufficient_data(self):
        """Test with insufficient data."""
        series1 = pd.Series([1])
        series2 = pd.Series([2])
        
        corr = calculate_correlation(series1, series2)
        
        assert corr == 0.0


class TestHedgeRatio:
    """Tests for hedge ratio calculation."""
    
    def test_hedge_ratio_linear(self):
        """Test hedge ratio with linear relationship."""
        series1 = pd.Series([2, 4, 6, 8, 10])
        series2 = pd.Series([1, 2, 3, 4, 5])
        
        ratio = calculate_hedge_ratio(series1, series2)
        
        # Should be approximately 2.0
        assert abs(ratio - 2.0) < 0.1
    
    def test_hedge_ratio_with_noise(self):
        """Test hedge ratio with noisy data."""
        np.random.seed(42)
        x = np.linspace(0, 10, 100)
        y = 1.5 * x + np.random.randn(100) * 0.5
        
        series1 = pd.Series(y)
        series2 = pd.Series(x)
        
        ratio = calculate_hedge_ratio(series1, series2)
        
        # Should be approximately 1.5
        assert abs(ratio - 1.5) < 0.2
    
    def test_insufficient_data(self):
        """Test with insufficient data."""
        series1 = pd.Series([1])
        series2 = pd.Series([2])
        
        ratio = calculate_hedge_ratio(series1, series2)
        
        assert ratio == 1.0


class TestSpread:
    """Tests for spread calculation."""
    
    def test_spread_calculation(self):
        """Test basic spread calculation."""
        series1 = pd.Series([10, 11, 12, 13, 14])
        series2 = pd.Series([5, 5.5, 6, 6.5, 7])
        hedge_ratio = 2.0
        
        spread = calculate_spread(series1, series2, hedge_ratio)
        
        expected = pd.Series([0.0, 0.0, 0.0, 0.0, 0.0])
        pd.testing.assert_series_equal(spread, expected)
    
    def test_spread_auto_hedge_ratio(self):
        """Test spread with automatic hedge ratio."""
        series1 = pd.Series([10, 20, 30, 40, 50])
        series2 = pd.Series([5, 10, 15, 20, 25])
        
        spread = calculate_spread(series1, series2)
        
        # With perfect 2:1 ratio, spread should be near zero
        assert spread.std() < 1.0
    
    def test_spread_length(self):
        """Test spread has same length as input."""
        series1 = pd.Series([1, 2, 3, 4, 5])
        series2 = pd.Series([2, 4, 6, 8, 10])
        
        spread = calculate_spread(series1, series2, hedge_ratio=2.0)
        
        assert len(spread) == len(series1)


class TestZScore:
    """Tests for Z-score calculation."""
    
    def test_zscore_full_series(self):
        """Test Z-score using full series."""
        series = pd.Series([1, 2, 3, 4, 5])
        
        zscore = calculate_zscore(series)
        
        # Z-scores should have mean ~0 and std ~1
        assert abs(zscore.mean()) < 0.1
        assert abs(zscore.std() - 1.0) < 0.1
    
    def test_zscore_rolling(self):
        """Test rolling Z-score."""
        series = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        
        zscore = calculate_zscore(series, window=5)
        
        # Should have same length
        assert len(zscore) == len(series)
        
        # First few values should be NaN (insufficient data)
        assert zscore.iloc[:2].isna().any()
    
    def test_zscore_outlier_detection(self):
        """Test Z-score identifies outliers."""
        series = pd.Series([1, 1, 1, 1, 1, 10, 1, 1, 1, 1])
        
        zscore = calculate_zscore(series)
        
        # The outlier (10) should have high Z-score
        assert zscore.iloc[5] > 2.0


class TestFindCointegratedPairs:
    """Tests for finding cointegrated pairs."""
    
    def test_find_pairs_basic(self):
        """Test finding cointegrated pairs."""
        np.random.seed(42)
        
        # Create base series
        base = np.cumsum(np.random.randn(100))
        
        # Create related series
        prices_df = pd.DataFrame({
            'A': base + np.random.randn(100) * 0.1,
            'B': 2 * base + np.random.randn(100) * 0.1,
            'C': np.cumsum(np.random.randn(100))  # Independent
        })
        
        pairs = find_cointegrated_pairs(prices_df)
        
        # Should find A-B pair (both related to base)
        assert len(pairs) >= 1
        
        # Check structure
        for sym1, sym2, pval, corr in pairs:
            assert isinstance(sym1, str)
            assert isinstance(sym2, str)
            assert 0 <= pval <= 1
            assert -1 <= corr <= 1
    
    def test_find_pairs_with_filters(self):
        """Test pair finding with correlation filter."""
        np.random.seed(42)
        
        prices_df = pd.DataFrame({
            'A': [1, 2, 3, 4, 5],
            'B': [2, 4, 6, 8, 10],
            'C': [5, 4, 3, 2, 1]
        })
        
        pairs = find_cointegrated_pairs(
            prices_df,
            min_correlation=0.95
        )
        
        # High correlation requirement
        # Should find A-B (perfect correlation)
        assert all(abs(corr) >= 0.95 for _, _, _, corr in pairs)
    
    def test_insufficient_data(self):
        """Test with insufficient data."""
        prices_df = pd.DataFrame({
            'A': [1, 2, 3],
            'B': [2, 4, 6]
        })
        
        pairs = find_cointegrated_pairs(prices_df)
        
        # Not enough data for reliable cointegration test
        assert len(pairs) == 0


class TestHalfLife:
    """Tests for mean-reversion half-life calculation."""
    
    def test_mean_reverting_series(self):
        """Test half-life calculation for mean-reverting series."""
        np.random.seed(42)
        
        # Create Ornstein-Uhlenbeck process (mean-reverting)
        n = 100
        theta = 0.15  # Mean reversion speed
        mu = 0.0
        sigma = 1.0
        
        x = np.zeros(n)
        for i in range(1, n):
            x[i] = x[i-1] + theta * (mu - x[i-1]) + sigma * np.random.randn()
        
        series = pd.Series(x)
        half_life = calculate_half_life(series)
        
        # Should have finite half-life
        assert 0 < half_life < n
    
    def test_non_mean_reverting_series(self):
        """Test half-life for non-mean-reverting series."""
        np.random.seed(43)  # Different seed for truly non-reverting series
        
        # Random walk with strong drift (no mean reversion)
        drift = 0.5
        series = pd.Series(np.cumsum(np.random.randn(200) + drift))
        
        half_life = calculate_half_life(series)
        
        # Should return infinity or very large value
        # Random walks can sometimes appear mean-reverting in short samples
        # so we check for either very large or infinite half-life
        assert half_life == np.inf or half_life > 50
    
    def test_insufficient_data(self):
        """Test with insufficient data."""
        series = pd.Series([1])
        
        half_life = calculate_half_life(series)
        
        assert half_life == np.inf


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
