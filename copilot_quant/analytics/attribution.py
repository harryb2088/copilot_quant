"""
Strategy Attribution Analyzer

Tracks which strategies generated what percentage of profit/loss.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict

from copilot_quant.brokers.trade_database import TradeDatabase

logger = logging.getLogger(__name__)


class AttributionAnalyzer:
    """
    Analyze performance attribution by strategy.
    
    Tracks which strategies contributed to overall performance,
    enabling strategy-level analysis and optimization.
    
    Example:
        >>> db = TradeDatabase("sqlite:///trades.db")
        >>> analyzer = AttributionAnalyzer(db)
        >>> attribution = analyzer.get_strategy_attribution()
        >>> for strategy, metrics in attribution.items():
        ...     print(f"{strategy}: {metrics['pnl']:,.2f} ({metrics['contribution_pct']:.1f}%)")
    """
    
    def __init__(self, trade_db: TradeDatabase):
        """
        Initialize attribution analyzer.
        
        Args:
            trade_db: TradeDatabase instance for accessing trade data
        """
        self.trade_db = trade_db
        logger.info("AttributionAnalyzer initialized")
    
    def get_strategy_attribution(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get performance attribution by strategy.
        
        Args:
            start_date: Optional start date for analysis
            end_date: Optional end date for analysis
            
        Returns:
            Dict mapping strategy name to performance metrics
        """
        # Get all fills in the date range
        with self.trade_db.get_session() as session:
            from copilot_quant.brokers.trade_database import FillModel, OrderModel
            
            query = session.query(FillModel).join(
                OrderModel,
                FillModel.order_db_id == OrderModel.id
            )
            
            if start_date:
                query = query.filter(
                    FillModel.timestamp >= datetime.combine(start_date, datetime.min.time())
                )
            if end_date:
                query = query.filter(
                    FillModel.timestamp <= datetime.combine(end_date, datetime.max.time())
                )
            
            fills = query.all()
            
            # Group fills by symbol (used as proxy for strategy)
            # In a real implementation, orders would have a strategy_id field
            strategy_fills = defaultdict(list)
            
            for fill in fills:
                # Use symbol as strategy proxy (TODO: add strategy field to OrderModel)
                strategy_name = f"Strategy_{fill.symbol}"
                strategy_fills[strategy_name].append(fill)
            
            # Calculate attribution for each strategy
            attribution = {}
            total_pnl = 0.0
            
            for strategy_name, fills in strategy_fills.items():
                pnl = self._calculate_strategy_pnl(fills)
                trades = self._calculate_strategy_trades(fills)
                
                attribution[strategy_name] = {
                    'pnl': pnl,
                    'num_trades': trades['num_trades'],
                    'win_rate': trades['win_rate'],
                    'profit_factor': trades['profit_factor'],
                    'avg_trade_pnl': pnl / trades['num_trades'] if trades['num_trades'] > 0 else 0.0
                }
                
                total_pnl += pnl
            
            # Add contribution percentages
            for strategy_name in attribution:
                contrib_pct = (attribution[strategy_name]['pnl'] / total_pnl * 100) if total_pnl != 0 else 0.0
                attribution[strategy_name]['contribution_pct'] = contrib_pct
            
            return attribution
    
    def get_symbol_attribution(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get performance attribution by symbol.
        
        Args:
            start_date: Optional start date for analysis
            end_date: Optional end date for analysis
            
        Returns:
            Dict mapping symbol to performance metrics
        """
        # Get all fills in the date range
        with self.trade_db.get_session() as session:
            from copilot_quant.brokers.trade_database import FillModel
            
            query = session.query(FillModel)
            
            if start_date:
                query = query.filter(
                    FillModel.timestamp >= datetime.combine(start_date, datetime.min.time())
                )
            if end_date:
                query = query.filter(
                    FillModel.timestamp <= datetime.combine(end_date, datetime.max.time())
                )
            
            fills = query.all()
            
            # Group fills by symbol
            symbol_fills = defaultdict(list)
            
            for fill in fills:
                symbol_fills[fill.symbol].append(fill)
            
            # Calculate attribution for each symbol
            attribution = {}
            total_pnl = 0.0
            
            for symbol, fills in symbol_fills.items():
                pnl = self._calculate_strategy_pnl(fills)
                trades = self._calculate_strategy_trades(fills)
                
                attribution[symbol] = {
                    'pnl': pnl,
                    'num_trades': trades['num_trades'],
                    'win_rate': trades['win_rate'],
                    'profit_factor': trades['profit_factor'],
                    'avg_trade_pnl': pnl / trades['num_trades'] if trades['num_trades'] > 0 else 0.0,
                    'total_volume': sum(abs(f.quantity * f.price) for f in fills)
                }
                
                total_pnl += pnl
            
            # Add contribution percentages
            for symbol in attribution:
                contrib_pct = (attribution[symbol]['pnl'] / total_pnl * 100) if total_pnl != 0 else 0.0
                attribution[symbol]['contribution_pct'] = contrib_pct
            
            # Sort by PnL
            attribution = dict(sorted(attribution.items(), key=lambda x: x[1]['pnl'], reverse=True))
            
            return attribution
    
    def get_time_attribution(
        self,
        period: str = 'daily',
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get performance attribution over time.
        
        Args:
            period: Time period ('daily', 'weekly', 'monthly')
            start_date: Optional start date for analysis
            end_date: Optional end date for analysis
            
        Returns:
            List of dicts with time period and performance metrics
        """
        # Get all fills in the date range
        with self.trade_db.get_session() as session:
            from copilot_quant.brokers.trade_database import FillModel
            
            query = session.query(FillModel)
            
            if start_date:
                query = query.filter(
                    FillModel.timestamp >= datetime.combine(start_date, datetime.min.time())
                )
            if end_date:
                query = query.filter(
                    FillModel.timestamp <= datetime.combine(end_date, datetime.max.time())
                )
            
            fills = query.order_by(FillModel.timestamp).all()
            
            # Group fills by time period
            period_fills = defaultdict(list)
            
            for fill in fills:
                if period == 'daily':
                    period_key = fill.timestamp.date()
                elif period == 'weekly':
                    # Week starting Monday
                    period_key = fill.timestamp.date() - timedelta(days=fill.timestamp.weekday())
                elif period == 'monthly':
                    period_key = fill.timestamp.date().replace(day=1)
                else:
                    raise ValueError(f"Invalid period: {period}")
                
                period_fills[period_key].append(fill)
            
            # Calculate attribution for each period
            attribution = []
            
            for period_key in sorted(period_fills.keys()):
                fills = period_fills[period_key]
                pnl = self._calculate_strategy_pnl(fills)
                trades = self._calculate_strategy_trades(fills)
                
                attribution.append({
                    'period': period_key.isoformat(),
                    'pnl': pnl,
                    'num_trades': trades['num_trades'],
                    'win_rate': trades['win_rate'],
                    'profit_factor': trades['profit_factor']
                })
            
            return attribution
    
    def _calculate_strategy_pnl(self, fills: List) -> float:
        """Calculate total PnL from a list of fills using FIFO"""
        positions = []  # [(quantity, price), ...]
        realized_pnl = 0.0
        
        for fill in fills:
            quantity = fill.quantity
            price = fill.price
            
            if quantity > 0:  # Buy
                positions.append((quantity, price))
            else:  # Sell
                sell_qty = abs(quantity)
                remaining_sell = sell_qty
                
                while remaining_sell > 0 and positions:
                    buy_qty, buy_price = positions[0]
                    
                    if buy_qty <= remaining_sell:
                        # Close entire buy position
                        realized_pnl += buy_qty * (price - buy_price)
                        remaining_sell -= buy_qty
                        positions.pop(0)
                    else:
                        # Partial close
                        realized_pnl += remaining_sell * (price - buy_price)
                        positions[0] = (buy_qty - remaining_sell, buy_price)
                        remaining_sell = 0
        
        # Add unrealized PnL from open positions
        unrealized_pnl = 0.0
        if positions and fills:
            last_price = fills[-1].price
            for qty, cost in positions:
                unrealized_pnl += qty * (last_price - cost)
        
        return realized_pnl + unrealized_pnl
    
    def _calculate_strategy_trades(self, fills: List) -> Dict[str, Any]:
        """Calculate trade statistics from fills"""
        positions = []
        trades_pnl = []
        
        for fill in fills:
            quantity = fill.quantity
            price = fill.price
            
            if quantity > 0:  # Buy
                positions.append((quantity, price))
            else:  # Sell
                sell_qty = abs(quantity)
                remaining_sell = sell_qty
                
                while remaining_sell > 0 and positions:
                    buy_qty, buy_price = positions[0]
                    
                    if buy_qty <= remaining_sell:
                        pnl = buy_qty * (price - buy_price)
                        trades_pnl.append(pnl)
                        remaining_sell -= buy_qty
                        positions.pop(0)
                    else:
                        pnl = remaining_sell * (price - buy_price)
                        trades_pnl.append(pnl)
                        positions[0] = (buy_qty - remaining_sell, buy_price)
                        remaining_sell = 0
        
        if not trades_pnl:
            return {
                'num_trades': 0,
                'win_rate': 0.0,
                'profit_factor': 0.0
            }
        
        winning_trades = [t for t in trades_pnl if t > 0]
        losing_trades = [t for t in trades_pnl if t < 0]
        
        win_rate = len(winning_trades) / len(trades_pnl)
        
        gross_profit = sum(winning_trades) if winning_trades else 0.0
        gross_loss = abs(sum(losing_trades)) if losing_trades else 0.0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0
        
        return {
            'num_trades': len(trades_pnl),
            'win_rate': win_rate,
            'profit_factor': profit_factor
        }
