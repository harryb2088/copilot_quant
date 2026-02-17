"""
Pairs trading strategy implementation.

This module provides a comprehensive pairs trading strategy that identifies
cointegrated pairs, calculates spreads, and executes mean-reversion trades
based on Z-score signals.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from copilot_quant.backtest import Order, Strategy
from copilot_quant.strategies.pairs_utils import (
    calculate_correlation,
    calculate_hedge_ratio,
    calculate_spread,
    calculate_zscore,
    find_cointegrated_pairs,
    test_cointegration,
)


class PairsTradingStrategy(Strategy):
    """
    Statistical arbitrage strategy using pairs trading.
    
    This strategy identifies pairs of assets with stable historical relationships
    (cointegration) and trades on temporary deviations from their equilibrium
    using mean-reversion signals based on Z-scores.
    
    The strategy:
    1. Identifies cointegrated pairs from the asset universe
    2. Calculates hedge ratios using regression
    3. Computes spreads between paired assets
    4. Generates entry signals when spread Z-score exceeds thresholds
    5. Generates exit signals when spread reverts to mean
    
    Attributes:
        lookback: Historical window for calculating statistics
        entry_zscore: Z-score threshold for entering positions (default: 2.0)
        exit_zscore: Z-score threshold for exiting positions (default: 0.5)
        quantity: Base quantity to trade per asset
        max_pairs: Maximum number of pairs to trade simultaneously
        
    Example:
        >>> strategy = PairsTradingStrategy(
        ...     lookback=60,
        ...     entry_zscore=2.0,
        ...     exit_zscore=0.5,
        ...     quantity=100
        ... )
        >>> engine.add_strategy(strategy)
        >>> result = engine.run(
        ...     start_date=datetime(2020, 1, 1),
        ...     end_date=datetime(2023, 12, 31),
        ...     symbols=['AAPL', 'MSFT', 'GOOGL', 'META']
        ... )
    """
    
    def __init__(
        self,
        lookback: int = 60,
        entry_zscore: float = 2.0,
        exit_zscore: float = 0.5,
        quantity: int = 100,
        max_pairs: int = 5,
        min_correlation: float = 0.6,
        cointegration_pvalue: float = 0.05,
        rebalance_frequency: int = 20
    ):
        """
        Initialize pairs trading strategy.
        
        Args:
            lookback: Window for calculating spread statistics (days)
            entry_zscore: Z-score threshold to enter trades (e.g., 2.0 = 2 std devs)
            exit_zscore: Z-score threshold to exit trades (e.g., 0.5)
            quantity: Number of shares to trade per asset
            max_pairs: Maximum number of pairs to trade at once
            min_correlation: Minimum correlation for pair consideration
            cointegration_pvalue: P-value threshold for cointegration test
            rebalance_frequency: Days between pair re-evaluation
        """
        super().__init__()
        self.lookback = lookback
        self.entry_zscore = entry_zscore
        self.exit_zscore = exit_zscore
        self.quantity = quantity
        self.max_pairs = max_pairs
        self.min_correlation = min_correlation
        self.cointegration_pvalue = cointegration_pvalue
        self.rebalance_frequency = rebalance_frequency
        
        # Strategy state
        self.active_pairs: Dict[Tuple[str, str], Dict] = {}
        self.pair_positions: Dict[Tuple[str, str], int] = {}  # 1=long spread, -1=short spread, 0=flat
        self.last_rebalance_day: int = 0
        self.trading_pairs: List[Tuple[str, str]] = []
        
    def initialize(self):
        """Called before backtest starts."""
        print(f"\nInitializing {self.name} strategy")
        print(f"  Lookback period: {self.lookback} days")
        print(f"  Entry Z-score: ±{self.entry_zscore}")
        print(f"  Exit Z-score: ±{self.exit_zscore}")
        print(f"  Position size: {self.quantity} shares")
        print(f"  Max pairs: {self.max_pairs}")
        
    def on_data(self, timestamp: datetime, data: pd.DataFrame) -> List[Order]:
        """
        Generate trading signals based on pair spreads.
        
        Args:
            timestamp: Current timestamp
            data: Historical price data
        
        Returns:
            List of orders to execute
        """
        if len(data) < self.lookback:
            return []
        
        # Rebalance pairs periodically
        current_day = len(data)
        if current_day - self.last_rebalance_day >= self.rebalance_frequency:
            self._identify_trading_pairs(data)
            self.last_rebalance_day = current_day
        
        if not self.trading_pairs:
            return []
        
        orders = []
        
        # Evaluate each pair
        for pair in self.trading_pairs:
            pair_orders = self._evaluate_pair(pair, timestamp, data)
            orders.extend(pair_orders)
        
        return orders
    
    def _identify_trading_pairs(self, data: pd.DataFrame) -> None:
        """
        Identify cointegrated pairs from the data.
        
        Args:
            data: Historical price data
        """
        # Get unique symbols from data
        if 'Symbol' in data.columns:
            # Data in long format
            symbols = data['Symbol'].unique()
            
            # Pivot to get prices by symbol
            prices_df = data.pivot_table(
                index=data.index,
                columns='Symbol',
                values='Close'
            )
        else:
            # Data already in wide format
            prices_df = data
        
        # Take only recent history for pair identification
        recent_prices = prices_df.tail(self.lookback * 2)
        
        # Find cointegrated pairs
        pairs = find_cointegrated_pairs(
            recent_prices,
            significance_level=self.cointegration_pvalue,
            min_correlation=self.min_correlation
        )
        
        # Select top pairs (up to max_pairs)
        self.trading_pairs = [
            (sym1, sym2) for sym1, sym2, pval, corr in pairs[:self.max_pairs]
        ]
        
        if self.trading_pairs:
            print(f"\n[{datetime.now().date()}] Identified {len(self.trading_pairs)} cointegrated pairs:")
            for sym1, sym2 in self.trading_pairs:
                # Find the pair info from pairs list
                pair_info = next(p for p in pairs if p[0] == sym1 and p[1] == sym2)
                pval, corr = pair_info[2], pair_info[3]
                print(f"  {sym1}-{sym2}: p={pval:.4f}, corr={corr:.3f}")
    
    def _evaluate_pair(
        self,
        pair: Tuple[str, str],
        timestamp: datetime,
        data: pd.DataFrame
    ) -> List[Order]:
        """
        Evaluate a single pair and generate orders.
        
        Args:
            pair: Tuple of (symbol1, symbol2)
            timestamp: Current timestamp
            data: Historical price data
        
        Returns:
            List of orders for this pair
        """
        sym1, sym2 = pair
        
        # Extract price series
        if 'Symbol' in data.columns:
            # Long format
            prices1 = data[data['Symbol'] == sym1]['Close']
            prices2 = data[data['Symbol'] == sym2]['Close']
        else:
            # Wide format
            prices1 = data[sym1] if sym1 in data.columns else None
            prices2 = data[sym2] if sym2 in data.columns else None
        
        if prices1 is None or prices2 is None:
            return []
        
        # Get recent data for spread calculation
        recent_prices1 = prices1.tail(self.lookback)
        recent_prices2 = prices2.tail(self.lookback)
        
        if len(recent_prices1) < self.lookback or len(recent_prices2) < self.lookback:
            return []
        
        # Calculate hedge ratio and spread
        hedge_ratio = calculate_hedge_ratio(recent_prices1, recent_prices2)
        spread = calculate_spread(recent_prices1, recent_prices2, hedge_ratio)
        
        # Calculate Z-score
        zscore = calculate_zscore(spread, window=self.lookback)
        current_zscore = zscore.iloc[-1]
        
        # Check if we have valid Z-score
        if np.isnan(current_zscore) or np.isinf(current_zscore):
            return []
        
        # Get current position for this pair
        current_position = self.pair_positions.get(pair, 0)
        
        orders = []
        
        # Entry signals
        if current_position == 0:
            if current_zscore > self.entry_zscore:
                # Spread too high - short the spread
                # Short sym1, Long sym2
                orders.append(Order(
                    symbol=sym1,
                    quantity=self.quantity,
                    order_type='market',
                    side='sell'
                ))
                orders.append(Order(
                    symbol=sym2,
                    quantity=int(self.quantity * hedge_ratio),
                    order_type='market',
                    side='buy'
                ))
                self.pair_positions[pair] = -1
                print(f"[{timestamp.date()}] SHORT spread {sym1}-{sym2}, Z={current_zscore:.2f}")
                
            elif current_zscore < -self.entry_zscore:
                # Spread too low - long the spread
                # Long sym1, Short sym2
                orders.append(Order(
                    symbol=sym1,
                    quantity=self.quantity,
                    order_type='market',
                    side='buy'
                ))
                orders.append(Order(
                    symbol=sym2,
                    quantity=int(self.quantity * hedge_ratio),
                    order_type='market',
                    side='sell'
                ))
                self.pair_positions[pair] = 1
                print(f"[{timestamp.date()}] LONG spread {sym1}-{sym2}, Z={current_zscore:.2f}")
        
        # Exit signals
        elif abs(current_zscore) < self.exit_zscore:
            # Spread has reverted - close position
            if current_position == 1:
                # Close long spread position
                orders.append(Order(
                    symbol=sym1,
                    quantity=self.quantity,
                    order_type='market',
                    side='sell'
                ))
                orders.append(Order(
                    symbol=sym2,
                    quantity=int(self.quantity * hedge_ratio),
                    order_type='market',
                    side='buy'
                ))
                print(f"[{timestamp.date()}] CLOSE LONG spread {sym1}-{sym2}, Z={current_zscore:.2f}")
                
            elif current_position == -1:
                # Close short spread position
                orders.append(Order(
                    symbol=sym1,
                    quantity=self.quantity,
                    order_type='market',
                    side='buy'
                ))
                orders.append(Order(
                    symbol=sym2,
                    quantity=int(self.quantity * hedge_ratio),
                    order_type='market',
                    side='sell'
                ))
                print(f"[{timestamp.date()}] CLOSE SHORT spread {sym1}-{sym2}, Z={current_zscore:.2f}")
            
            self.pair_positions[pair] = 0
        
        return orders
    
    def finalize(self):
        """Called after backtest ends."""
        print(f"\nFinalizing {self.name} strategy")
        if self.trading_pairs:
            print(f"  Traded {len(self.trading_pairs)} pairs")
