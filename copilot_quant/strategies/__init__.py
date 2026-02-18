"""Trading strategies module."""

from copilot_quant.strategies.pairs_trading import PairsTradingStrategy
from copilot_quant.strategies.pairs_utils import (
    calculate_correlation,
    calculate_hedge_ratio,
    calculate_spread,
    calculate_zscore,
    find_cointegrated_pairs,
    test_cointegration,
    calculate_half_life,
)

__all__ = [
    "PairsTradingStrategy",
    "test_cointegration",
    "calculate_correlation",
    "calculate_hedge_ratio",
    "calculate_spread",
    "calculate_zscore",
    "find_cointegrated_pairs",
    "calculate_half_life",
]
