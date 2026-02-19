"""
Benchmark Comparison Module

Compares portfolio performance against market benchmarks like SPY and QQQ.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any

import numpy as np
import pandas as pd

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logging.warning("yfinance not available - benchmark comparison will use mock data")

logger = logging.getLogger(__name__)


class BenchmarkComparator:
    """
    Compare portfolio performance against market benchmarks.
    
    Supports comparison with major indices (SPY, QQQ) and custom benchmarks.
    Calculates relative performance, alpha, beta, and correlation metrics.
    
    Example:
        >>> comparator = BenchmarkComparator()
        >>> comparison = comparator.compare_to_benchmark(
        ...     portfolio_returns=returns_series,
        ...     benchmark='SPY'
        ... )
        >>> print(f"Alpha: {comparison['alpha']:.2%}")
        >>> print(f"Beta: {comparison['beta']:.2f}")
    """
    
    SUPPORTED_BENCHMARKS = ['SPY', 'QQQ', 'DIA', 'IWM', 'VTI']
    
    def __init__(self, cache_days: int = 1):
        """
        Initialize benchmark comparator.
        
        Args:
            cache_days: Number of days to cache benchmark data
        """
        self.cache_days = cache_days
        self._benchmark_cache = {}
        logger.info("BenchmarkComparator initialized")
    
    def compare_to_benchmark(
        self,
        portfolio_returns: pd.Series,
        benchmark: str = 'SPY',
        risk_free_rate: float = 0.02
    ) -> Dict[str, Any]:
        """
        Compare portfolio returns to benchmark.
        
        Args:
            portfolio_returns: Series of portfolio daily returns
            benchmark: Benchmark ticker symbol (default: SPY)
            risk_free_rate: Annual risk-free rate for alpha calculation
            
        Returns:
            Dict with comparison metrics (alpha, beta, correlation, tracking_error, etc.)
        """
        if benchmark not in self.SUPPORTED_BENCHMARKS:
            logger.warning(f"Unsupported benchmark: {benchmark}. Using SPY.")
            benchmark = 'SPY'
        
        # Get benchmark returns for the same period
        start_date = portfolio_returns.index.min()
        end_date = portfolio_returns.index.max()
        
        benchmark_returns = self._get_benchmark_returns(
            benchmark,
            start_date,
            end_date
        )
        
        # Align the series
        aligned = pd.DataFrame({
            'portfolio': portfolio_returns,
            'benchmark': benchmark_returns
        }).dropna()
        
        if len(aligned) < 2:
            logger.warning("Insufficient data for benchmark comparison")
            return self._empty_comparison()
        
        port_ret = aligned['portfolio']
        bench_ret = aligned['benchmark']
        
        # Calculate metrics
        correlation = float(port_ret.corr(bench_ret))
        
        # Beta (using linear regression)
        if bench_ret.std() > 0:
            covariance = port_ret.cov(bench_ret)
            beta = covariance / bench_ret.var()
        else:
            beta = 0.0
        
        # Alpha (annualized)
        daily_rf = risk_free_rate / 252
        port_excess = port_ret - daily_rf
        bench_excess = bench_ret - daily_rf
        
        alpha = (port_excess.mean() - beta * bench_excess.mean()) * 252
        
        # Tracking error (annualized)
        tracking_diff = port_ret - bench_ret
        tracking_error = tracking_diff.std() * np.sqrt(252)
        
        # Information ratio
        if tracking_error > 0:
            information_ratio = (port_ret.mean() - bench_ret.mean()) * 252 / tracking_error
        else:
            information_ratio = 0.0
        
        # Relative performance
        port_cumulative = (1 + port_ret).prod() - 1
        bench_cumulative = (1 + bench_ret).prod() - 1
        relative_return = port_cumulative - bench_cumulative
        
        return {
            'benchmark': benchmark,
            'correlation': correlation,
            'beta': float(beta),
            'alpha': float(alpha),
            'alpha_pct': float(alpha * 100),
            'tracking_error': float(tracking_error),
            'tracking_error_pct': float(tracking_error * 100),
            'information_ratio': float(information_ratio),
            'portfolio_return': float(port_cumulative),
            'portfolio_return_pct': float(port_cumulative * 100),
            'benchmark_return': float(bench_cumulative),
            'benchmark_return_pct': float(bench_cumulative * 100),
            'relative_return': float(relative_return),
            'relative_return_pct': float(relative_return * 100),
            'num_observations': len(aligned)
        }
    
    def compare_to_multiple_benchmarks(
        self,
        portfolio_returns: pd.Series,
        benchmarks: List[str] = None,
        risk_free_rate: float = 0.02
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compare portfolio to multiple benchmarks.
        
        Args:
            portfolio_returns: Series of portfolio daily returns
            benchmarks: List of benchmark tickers (default: ['SPY', 'QQQ'])
            risk_free_rate: Annual risk-free rate
            
        Returns:
            Dict mapping benchmark to comparison metrics
        """
        if benchmarks is None:
            benchmarks = ['SPY', 'QQQ']
        
        comparisons = {}
        
        for benchmark in benchmarks:
            try:
                comparison = self.compare_to_benchmark(
                    portfolio_returns,
                    benchmark,
                    risk_free_rate
                )
                comparisons[benchmark] = comparison
            except Exception as e:
                logger.error(f"Error comparing to {benchmark}: {e}")
                comparisons[benchmark] = self._empty_comparison()
        
        return comparisons
    
    def get_benchmark_equity_curve(
        self,
        benchmark: str,
        start_date: date,
        end_date: date,
        initial_value: float = 100000
    ) -> pd.Series:
        """
        Get benchmark equity curve for comparison charts.
        
        Args:
            benchmark: Benchmark ticker symbol
            start_date: Start date
            end_date: End date
            initial_value: Starting value for normalization
            
        Returns:
            Series with benchmark equity values
        """
        returns = self._get_benchmark_returns(benchmark, start_date, end_date)
        
        # Convert returns to equity curve
        equity = initial_value * (1 + returns).cumprod()
        
        return equity
    
    def _get_benchmark_returns(
        self,
        benchmark: str,
        start_date: date,
        end_date: date
    ) -> pd.Series:
        """Get benchmark daily returns for date range"""
        # Check cache
        cache_key = f"{benchmark}_{start_date}_{end_date}"
        
        if cache_key in self._benchmark_cache:
            cache_time, data = self._benchmark_cache[cache_key]
            if datetime.now() - cache_time < timedelta(days=self.cache_days):
                return data
        
        # Fetch from yfinance
        if YFINANCE_AVAILABLE:
            try:
                ticker = yf.Ticker(benchmark)
                hist = ticker.history(start=start_date, end=end_date)
                
                if hist.empty:
                    logger.warning(f"No data returned for {benchmark}")
                    return self._generate_mock_returns(start_date, end_date)
                
                returns = hist['Close'].pct_change().dropna()
                
                # Cache the result
                self._benchmark_cache[cache_key] = (datetime.now(), returns)
                
                return returns
                
            except Exception as e:
                logger.error(f"Error fetching {benchmark} data: {e}")
                return self._generate_mock_returns(start_date, end_date)
        else:
            # Use mock data if yfinance not available
            return self._generate_mock_returns(start_date, end_date)
    
    def _generate_mock_returns(
        self,
        start_date: date,
        end_date: date
    ) -> pd.Series:
        """Generate mock benchmark returns for testing"""
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Generate realistic market returns (small positive drift, moderate volatility)
        np.random.seed(42)
        returns = np.random.normal(0.0003, 0.01, len(dates))  # ~7.5% annual return, 16% volatility
        
        return pd.Series(returns, index=dates)
    
    def _empty_comparison(self) -> Dict[str, Any]:
        """Return empty comparison metrics"""
        return {
            'benchmark': 'N/A',
            'correlation': 0.0,
            'beta': 0.0,
            'alpha': 0.0,
            'alpha_pct': 0.0,
            'tracking_error': 0.0,
            'tracking_error_pct': 0.0,
            'information_ratio': 0.0,
            'portfolio_return': 0.0,
            'portfolio_return_pct': 0.0,
            'benchmark_return': 0.0,
            'benchmark_return_pct': 0.0,
            'relative_return': 0.0,
            'relative_return_pct': 0.0,
            'num_observations': 0
        }
