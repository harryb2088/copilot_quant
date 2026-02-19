"""
Real-Time Performance Analytics Engine

Computes live performance metrics including realized/unrealized PnL, 
rolling Sharpe, Sortino, drawdown, and win rate from trade data.
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import numpy as np
import pandas as pd

from copilot_quant.brokers.trade_database import TradeDatabase

logger = logging.getLogger(__name__)


@dataclass
class PerformanceSnapshot:
    """Snapshot of performance metrics at a point in time"""
    timestamp: datetime
    portfolio_value: float
    cash: float
    positions_value: float
    realized_pnl: float
    unrealized_pnl: float
    total_pnl: float
    total_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    current_drawdown: float
    win_rate: float
    profit_factor: float
    num_trades: int
    num_winning_trades: int
    num_losing_trades: int


class PerformanceEngine:
    """
    Real-time performance analytics engine.
    
    Computes live performance metrics from trade database and position data.
    Supports both snapshot and historical reporting.
    
    Example:
        >>> db = TradeDatabase("sqlite:///trades.db")
        >>> engine = PerformanceEngine(db, initial_capital=100000)
        >>> snapshot = engine.get_current_performance(positions)
        >>> print(f"Total PnL: ${snapshot.total_pnl:,.2f}")
    """
    
    def __init__(
        self,
        trade_db: TradeDatabase,
        initial_capital: float,
        risk_free_rate: float = 0.02
    ):
        """
        Initialize performance engine.
        
        Args:
            trade_db: TradeDatabase instance for accessing trade data
            initial_capital: Starting portfolio capital
            risk_free_rate: Annual risk-free rate for Sharpe/Sortino (default: 2%)
        """
        self.trade_db = trade_db
        self.initial_capital = initial_capital
        self.risk_free_rate = risk_free_rate
        
        logger.info(f"PerformanceEngine initialized with capital: ${initial_capital:,.2f}")
    
    def get_current_performance(
        self,
        current_positions: Dict[str, Dict[str, float]],
        current_cash: float
    ) -> PerformanceSnapshot:
        """
        Get current performance snapshot.
        
        Args:
            current_positions: Dict of {symbol: {'quantity': qty, 'current_price': price, 'avg_cost': cost}}
            current_cash: Current cash balance
            
        Returns:
            PerformanceSnapshot with current metrics
        """
        # Calculate positions value and unrealized PnL
        positions_value = 0.0
        unrealized_pnl = 0.0
        
        for symbol, pos in current_positions.items():
            qty = pos.get('quantity', 0)
            current_price = pos.get('current_price', 0)
            avg_cost = pos.get('avg_cost', 0)
            
            position_value = qty * current_price
            positions_value += position_value
            unrealized_pnl += qty * (current_price - avg_cost)
        
        # Get realized PnL from trades
        realized_pnl = self._calculate_realized_pnl()
        
        # Portfolio metrics
        portfolio_value = current_cash + positions_value
        total_pnl = realized_pnl + unrealized_pnl
        total_return = total_pnl / self.initial_capital
        
        # Get equity curve for time-series metrics
        equity_curve = self._build_equity_curve(current_positions, current_cash)
        
        # Risk metrics
        sharpe = self._calculate_rolling_sharpe(equity_curve)
        sortino = self._calculate_rolling_sortino(equity_curve)
        max_dd, current_dd = self._calculate_drawdown_metrics(equity_curve)
        
        # Trade statistics
        trade_stats = self._calculate_trade_statistics()
        
        return PerformanceSnapshot(
            timestamp=datetime.now(),
            portfolio_value=portfolio_value,
            cash=current_cash,
            positions_value=positions_value,
            realized_pnl=realized_pnl,
            unrealized_pnl=unrealized_pnl,
            total_pnl=total_pnl,
            total_return=total_return,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown=max_dd,
            current_drawdown=current_dd,
            win_rate=trade_stats['win_rate'],
            profit_factor=trade_stats['profit_factor'],
            num_trades=trade_stats['num_trades'],
            num_winning_trades=trade_stats['num_winning'],
            num_losing_trades=trade_stats['num_losing']
        )
    
    def get_historical_snapshots(
        self,
        start_date: date,
        end_date: date,
        frequency: str = 'daily'
    ) -> List[Dict[str, Any]]:
        """
        Get historical performance snapshots.
        
        Args:
            start_date: Start date for snapshots
            end_date: End date for snapshots
            frequency: Snapshot frequency ('daily', 'weekly', 'monthly')
            
        Returns:
            List of performance snapshot dictionaries
        """
        snapshots = []
        
        # Get date range based on frequency
        if frequency == 'daily':
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
        elif frequency == 'weekly':
            dates = pd.date_range(start=start_date, end=end_date, freq='W')
        elif frequency == 'monthly':
            dates = pd.date_range(start=start_date, end=end_date, freq='M')
        else:
            raise ValueError(f"Invalid frequency: {frequency}")
        
        for snapshot_date in dates:
            # Build historical snapshot
            snapshot = self._build_historical_snapshot(snapshot_date.date())
            if snapshot:
                snapshots.append(snapshot)
        
        return snapshots
    
    def export_performance_report(
        self,
        start_date: date,
        end_date: date,
        format: str = 'json'
    ) -> str:
        """
        Export performance report.
        
        Args:
            start_date: Report start date
            end_date: Report end date
            format: Export format ('json' or 'csv')
            
        Returns:
            Report data as string
        """
        snapshots = self.get_historical_snapshots(start_date, end_date, frequency='daily')
        
        if format == 'json':
            import json
            return json.dumps(snapshots, indent=2, default=str)
        elif format == 'csv':
            df = pd.DataFrame(snapshots)
            return df.to_csv(index=False)
        else:
            raise ValueError(f"Invalid format: {format}")
    
    def _calculate_realized_pnl(self) -> float:
        """Calculate total realized PnL from closed positions"""
        # Get all fills from database
        with self.trade_db.get_session() as session:
            from copilot_quant.brokers.trade_database import FillModel
            fills = session.query(FillModel).all()
            
            # Match buys with sells using FIFO
            positions = {}  # {symbol: [(quantity, price), ...]}
            realized_pnl = 0.0
            
            for fill in fills:
                symbol = fill.symbol
                quantity = fill.quantity
                price = fill.price
                
                if symbol not in positions:
                    positions[symbol] = []
                
                # Determine if this is a buy or sell based on existing position
                current_qty = sum(q for q, p in positions[symbol])
                
                if quantity > 0:  # Buy
                    positions[symbol].append((quantity, price))
                else:  # Sell (quantity is negative)
                    sell_qty = abs(quantity)
                    remaining_sell = sell_qty
                    
                    while remaining_sell > 0 and positions[symbol]:
                        buy_qty, buy_price = positions[symbol][0]
                        
                        if buy_qty <= remaining_sell:
                            # Close entire buy position
                            realized_pnl += buy_qty * (price - buy_price)
                            remaining_sell -= buy_qty
                            positions[symbol].pop(0)
                        else:
                            # Partial close
                            realized_pnl += remaining_sell * (price - buy_price)
                            positions[symbol][0] = (buy_qty - remaining_sell, buy_price)
                            remaining_sell = 0
            
            return realized_pnl
    
    def _build_equity_curve(
        self,
        current_positions: Dict[str, Dict[str, float]],
        current_cash: float
    ) -> pd.Series:
        """Build equity curve from historical trade data"""
        # Get all fills ordered by time
        with self.trade_db.get_session() as session:
            from copilot_quant.brokers.trade_database import FillModel
            fills = session.query(FillModel).order_by(FillModel.timestamp).all()
            
            if not fills:
                return pd.Series([self.initial_capital], index=[datetime.now()])
            
            # Build daily equity values
            equity_data = []
            positions = {}
            cash = self.initial_capital
            
            # Group fills by date
            fills_by_date = {}
            for fill in fills:
                fill_date = fill.timestamp.date()
                if fill_date not in fills_by_date:
                    fills_by_date[fill_date] = []
                fills_by_date[fill_date].append(fill)
            
            # Process each day
            for trade_date in sorted(fills_by_date.keys()):
                for fill in fills_by_date[trade_date]:
                    symbol = fill.symbol
                    quantity = fill.quantity
                    price = fill.price
                    
                    # Update position
                    if symbol not in positions:
                        positions[symbol] = {'quantity': 0, 'avg_cost': 0}
                    
                    pos = positions[symbol]
                    total_cost = pos['quantity'] * pos['avg_cost']
                    total_cost += quantity * price
                    pos['quantity'] += quantity
                    
                    if pos['quantity'] != 0:
                        pos['avg_cost'] = total_cost / pos['quantity']
                    else:
                        pos['avg_cost'] = 0
                        if abs(pos['quantity']) < 1e-6:
                            del positions[symbol]
                    
                    # Update cash
                    cash -= quantity * price + fill.commission
                
                # Calculate equity at end of day (using closing prices = last fill price as proxy)
                positions_value = sum(
                    pos['quantity'] * pos['avg_cost']  # Using avg_cost as proxy for market value
                    for pos in positions.values()
                )
                equity = cash + positions_value
                equity_data.append((trade_date, equity))
            
            # Add current day
            current_equity = current_cash + sum(
                p['quantity'] * p['current_price']
                for p in current_positions.values()
            )
            equity_data.append((datetime.now().date(), current_equity))
            
            # Create series
            dates, values = zip(*equity_data)
            return pd.Series(values, index=pd.DatetimeIndex(dates))
    
    def _calculate_rolling_sharpe(
        self,
        equity_curve: pd.Series,
        window_days: int = 30
    ) -> float:
        """Calculate rolling Sharpe ratio"""
        if len(equity_curve) < 2:
            return 0.0
        
        returns = equity_curve.pct_change().dropna()
        
        if len(returns) < window_days:
            window_returns = returns
        else:
            window_returns = returns.tail(window_days)
        
        if len(window_returns) == 0 or window_returns.std() == 0:
            return 0.0
        
        # Annualized Sharpe
        excess_returns = window_returns - (self.risk_free_rate / 252)
        sharpe = np.sqrt(252) * excess_returns.mean() / window_returns.std()
        
        return float(sharpe)
    
    def _calculate_rolling_sortino(
        self,
        equity_curve: pd.Series,
        window_days: int = 30
    ) -> float:
        """Calculate rolling Sortino ratio"""
        if len(equity_curve) < 2:
            return 0.0
        
        returns = equity_curve.pct_change().dropna()
        
        if len(returns) < window_days:
            window_returns = returns
        else:
            window_returns = returns.tail(window_days)
        
        if len(window_returns) == 0:
            return 0.0
        
        # Downside deviation (only negative returns)
        excess_returns = window_returns - (self.risk_free_rate / 252)
        downside_returns = excess_returns[excess_returns < 0]
        
        if len(downside_returns) == 0:
            return 0.0
        
        downside_std = np.sqrt(np.mean(downside_returns ** 2))
        
        if downside_std == 0:
            return 0.0
        
        sortino = np.sqrt(252) * excess_returns.mean() / downside_std
        
        return float(sortino)
    
    def _calculate_drawdown_metrics(
        self,
        equity_curve: pd.Series
    ) -> tuple[float, float]:
        """Calculate max drawdown and current drawdown"""
        if len(equity_curve) == 0:
            return 0.0, 0.0
        
        # Calculate running maximum
        running_max = equity_curve.expanding().max()
        
        # Calculate drawdown
        drawdown = (equity_curve - running_max) / running_max
        
        max_drawdown = float(drawdown.min())
        current_drawdown = float(drawdown.iloc[-1])
        
        return max_drawdown, current_drawdown
    
    def _calculate_trade_statistics(self) -> Dict[str, Any]:
        """Calculate trade win rate and profit factor"""
        # Get all closed trades (matched buy/sell pairs)
        with self.trade_db.get_session() as session:
            from copilot_quant.brokers.trade_database import FillModel
            fills = session.query(FillModel).order_by(FillModel.timestamp).all()
            
            # Match buys with sells
            positions = {}  # {symbol: [(quantity, price), ...]}
            trades_pnl = []
            
            for fill in fills:
                symbol = fill.symbol
                quantity = fill.quantity
                price = fill.price
                
                if symbol not in positions:
                    positions[symbol] = []
                
                if quantity > 0:  # Buy
                    positions[symbol].append((quantity, price))
                else:  # Sell
                    sell_qty = abs(quantity)
                    remaining_sell = sell_qty
                    
                    while remaining_sell > 0 and positions[symbol]:
                        buy_qty, buy_price = positions[symbol][0]
                        
                        if buy_qty <= remaining_sell:
                            pnl = buy_qty * (price - buy_price)
                            trades_pnl.append(pnl)
                            remaining_sell -= buy_qty
                            positions[symbol].pop(0)
                        else:
                            pnl = remaining_sell * (price - buy_price)
                            trades_pnl.append(pnl)
                            positions[symbol][0] = (buy_qty - remaining_sell, buy_price)
                            remaining_sell = 0
            
            # Calculate statistics
            if not trades_pnl:
                return {
                    'num_trades': 0,
                    'num_winning': 0,
                    'num_losing': 0,
                    'win_rate': 0.0,
                    'profit_factor': 0.0
                }
            
            winning_trades = [t for t in trades_pnl if t > 0]
            losing_trades = [t for t in trades_pnl if t < 0]
            
            win_rate = len(winning_trades) / len(trades_pnl) if trades_pnl else 0.0
            
            gross_profit = sum(winning_trades) if winning_trades else 0.0
            gross_loss = abs(sum(losing_trades)) if losing_trades else 0.0
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0
            
            return {
                'num_trades': len(trades_pnl),
                'num_winning': len(winning_trades),
                'num_losing': len(losing_trades),
                'win_rate': win_rate,
                'profit_factor': profit_factor
            }
    
    def _build_historical_snapshot(self, snapshot_date: date) -> Optional[Dict[str, Any]]:
        """Build performance snapshot for a historical date"""
        # Get fills up to this date
        with self.trade_db.get_session() as session:
            from copilot_quant.brokers.trade_database import FillModel
            from datetime import datetime as dt
            
            end_datetime = dt.combine(snapshot_date, dt.max.time())
            fills = session.query(FillModel).filter(
                FillModel.timestamp <= end_datetime
            ).order_by(FillModel.timestamp).all()
            
            if not fills:
                return None
            
            # Reconstruct positions and cash at end of day
            positions = {}
            cash = self.initial_capital
            
            for fill in fills:
                symbol = fill.symbol
                quantity = fill.quantity
                price = fill.price
                
                if symbol not in positions:
                    positions[symbol] = {'quantity': 0, 'avg_cost': 0, 'current_price': price}
                
                pos = positions[symbol]
                total_cost = pos['quantity'] * pos['avg_cost']
                total_cost += quantity * price
                pos['quantity'] += quantity
                
                if pos['quantity'] != 0:
                    pos['avg_cost'] = total_cost / pos['quantity']
                    pos['current_price'] = price  # Last known price
                else:
                    pos['avg_cost'] = 0
                    if abs(pos['quantity']) < 1e-6:
                        del positions[symbol]
                
                cash -= quantity * price + fill.commission
            
            # Calculate metrics (simplified for historical)
            positions_value = sum(
                p['quantity'] * p['current_price']
                for p in positions.values()
            )
            portfolio_value = cash + positions_value
            total_pnl = portfolio_value - self.initial_capital
            
            return {
                'date': snapshot_date.isoformat(),
                'portfolio_value': portfolio_value,
                'cash': cash,
                'positions_value': positions_value,
                'total_pnl': total_pnl,
                'total_return': total_pnl / self.initial_capital
            }
