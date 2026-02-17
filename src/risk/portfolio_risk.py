"""
Portfolio Risk Management Module

Central risk management system that enforces portfolio and position-level controls.
Acts as a gatekeeper for all trading strategies.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd

from .settings import RiskSettings


@dataclass
class RiskCheckResult:
    """Result of a risk check operation."""
    
    approved: bool  # Whether the action is approved
    reason: str  # Human-readable reason for approval/rejection
    details: dict[str, Any] | None = None  # Additional details about the check
    timestamp: datetime | None = None  # When the check was performed
    
    def __post_init__(self) -> None:
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()


class RiskManager:
    """
    Central risk management system for the copilot_quant platform.
    
    Enforces portfolio-level and position-level risk controls to preserve capital
    and prevent excessive losses.
    """
    
    def __init__(self, settings: RiskSettings | None = None) -> None:
        """
        Initialize the risk manager.
        
        Args:
            settings: Risk settings to use. If None, uses conservative defaults.
        """
        self.settings = settings or RiskSettings()
        self._circuit_breaker_triggered = False
        self._breach_log: list[dict[str, Any]] = []
    
    def check_portfolio_risk(
        self,
        portfolio_value: float,
        peak_value: float,
        cash: float,
        positions: list[dict[str, Any]] | None = None,
    ) -> RiskCheckResult:
        """
        Check if portfolio meets risk requirements.
        
        Args:
            portfolio_value: Current total portfolio value
            peak_value: Historical peak portfolio value
            cash: Current cash balance
            positions: List of current positions (optional)
            
        Returns:
            RiskCheckResult indicating if portfolio risk is acceptable
        """
        if portfolio_value <= 0:
            return RiskCheckResult(
                approved=False,
                reason="Portfolio value must be positive",
                details={"portfolio_value": portfolio_value}
            )
        
        # Check if circuit breaker is triggered
        if self._circuit_breaker_triggered:
            return RiskCheckResult(
                approved=False,
                reason="Circuit breaker is active - no new trades allowed",
                details={"circuit_breaker_active": True}
            )
        
        # Calculate current drawdown
        current_drawdown = (peak_value - portfolio_value) / peak_value if peak_value > 0 else 0
        
        # Check maximum drawdown limit
        if current_drawdown > self.settings.max_portfolio_drawdown:
            self._log_breach("max_portfolio_drawdown", current_drawdown, self.settings.max_portfolio_drawdown)
            return RiskCheckResult(
                approved=False,
                reason=f"Portfolio drawdown ({current_drawdown:.1%}) exceeds maximum ({self.settings.max_portfolio_drawdown:.1%})",
                details={
                    "current_drawdown": current_drawdown,
                    "max_drawdown": self.settings.max_portfolio_drawdown,
                    "portfolio_value": portfolio_value,
                    "peak_value": peak_value,
                }
            )
        
        # Check circuit breaker threshold
        if self.settings.enable_circuit_breaker and current_drawdown >= self.settings.circuit_breaker_threshold:
            return self.trigger_circuit_breaker(
                portfolio_value=portfolio_value,
                peak_value=peak_value,
                current_drawdown=current_drawdown
            )
        
        # Check cash buffer constraints
        cash_pct = cash / portfolio_value
        
        if cash_pct < self.settings.min_cash_buffer:
            self._log_breach("min_cash_buffer", cash_pct, self.settings.min_cash_buffer)
            return RiskCheckResult(
                approved=False,
                reason=f"Cash buffer ({cash_pct:.1%}) below minimum ({self.settings.min_cash_buffer:.1%})",
                details={
                    "cash_pct": cash_pct,
                    "min_cash_buffer": self.settings.min_cash_buffer,
                    "cash": cash,
                    "portfolio_value": portfolio_value,
                }
            )
        
        if cash_pct > self.settings.max_cash_buffer:
            return RiskCheckResult(
                approved=False,
                reason=f"Cash buffer ({cash_pct:.1%}) exceeds maximum ({self.settings.max_cash_buffer:.1%})",
                details={
                    "cash_pct": cash_pct,
                    "max_cash_buffer": self.settings.max_cash_buffer,
                    "cash": cash,
                    "portfolio_value": portfolio_value,
                }
            )
        
        # Check number of positions
        if positions is not None and len(positions) >= self.settings.max_positions:
            return RiskCheckResult(
                approved=False,
                reason=f"Maximum number of positions ({self.settings.max_positions}) reached",
                details={
                    "current_positions": len(positions),
                    "max_positions": self.settings.max_positions,
                }
            )
        
        # All checks passed
        return RiskCheckResult(
            approved=True,
            reason="Portfolio risk within acceptable limits",
            details={
                "current_drawdown": current_drawdown,
                "cash_pct": cash_pct,
                "num_positions": len(positions) if positions else 0,
            }
        )
    
    def check_position_risk(
        self,
        position_value: float,
        portfolio_value: float,
        entry_price: float,
        current_price: float,
        symbol: str | None = None,
        existing_positions: list[dict[str, Any]] | None = None,
    ) -> RiskCheckResult:
        """
        Check if a position meets risk requirements.
        
        Args:
            position_value: Value of the position
            portfolio_value: Total portfolio value
            entry_price: Entry price of the position
            current_price: Current price
            symbol: Stock symbol (optional, for correlation checks)
            existing_positions: List of existing positions (optional, for correlation checks)
            
        Returns:
            RiskCheckResult indicating if position risk is acceptable
        """
        if portfolio_value <= 0:
            return RiskCheckResult(
                approved=False,
                reason="Portfolio value must be positive",
                details={"portfolio_value": portfolio_value}
            )
        
        # Check position size limit
        position_pct = abs(position_value) / portfolio_value
        
        if position_pct > self.settings.max_position_size:
            return RiskCheckResult(
                approved=False,
                reason=f"Position size ({position_pct:.1%}) exceeds maximum ({self.settings.max_position_size:.1%})",
                details={
                    "position_pct": position_pct,
                    "max_position_size": self.settings.max_position_size,
                    "position_value": position_value,
                    "portfolio_value": portfolio_value,
                }
            )
        
        # Check stop loss if position has moved against us
        if entry_price > 0:
            position_return = (current_price - entry_price) / entry_price
            
            if position_return < -self.settings.position_stop_loss:
                self._log_breach("position_stop_loss", abs(position_return), self.settings.position_stop_loss)
                return RiskCheckResult(
                    approved=False,
                    reason=f"Position loss ({abs(position_return):.1%}) exceeds stop loss ({self.settings.position_stop_loss:.1%})",
                    details={
                        "position_return": position_return,
                        "position_stop_loss": self.settings.position_stop_loss,
                        "entry_price": entry_price,
                        "current_price": current_price,
                        "symbol": symbol,
                    }
                )
        
        # All checks passed
        return RiskCheckResult(
            approved=True,
            reason="Position risk within acceptable limits",
            details={
                "position_pct": position_pct,
                "symbol": symbol,
            }
        )
    
    def calculate_position_size(
        self,
        signal_strength: float,
        portfolio_value: float,
        volatility: float | None = None,
    ) -> float:
        """
        Calculate position size based on signal strength and risk parameters.
        
        Args:
            signal_strength: Trading signal strength (0-1, where 1 is strongest)
            portfolio_value: Total portfolio value
            volatility: Asset volatility (optional, for volatility targeting)
            
        Returns:
            Position size in dollars
        """
        if not 0 <= signal_strength <= 1:
            raise ValueError(f"signal_strength must be between 0 and 1, got {signal_strength}")
        
        if portfolio_value <= 0:
            return 0.0
        
        # Base position size from signal strength and max position size
        base_size = signal_strength * self.settings.max_position_size * portfolio_value
        
        # Apply volatility targeting if enabled
        if self.settings.enable_volatility_targeting and volatility is not None and volatility > 0:
            # Scale position size inversely with volatility
            # Higher volatility = smaller position size
            vol_scalar = self.settings.target_portfolio_volatility / volatility
            # Cap the scalar to avoid extreme positions
            vol_scalar = min(vol_scalar, 2.0)  # Max 2x leverage
            vol_scalar = max(vol_scalar, 0.1)  # Min 10% of base size
            
            adjusted_size = base_size * vol_scalar
            
            # Ensure we don't exceed max position size
            adjusted_size = min(adjusted_size, self.settings.max_position_size * portfolio_value)
            
            return adjusted_size
        
        return base_size
    
    def check_correlation(
        self,
        new_symbol: str,
        existing_positions: list[dict[str, Any]],
        price_data: pd.DataFrame,
    ) -> RiskCheckResult:
        """
        Check if adding a new position would violate correlation limits.
        
        Args:
            new_symbol: Symbol to check
            existing_positions: List of existing positions with 'symbol' key
            price_data: DataFrame with price data, columns = symbols, index = dates
            
        Returns:
            RiskCheckResult indicating if correlation is acceptable
        """
        if not existing_positions:
            return RiskCheckResult(
                approved=True,
                reason="No existing positions to check correlation against",
                details={"new_symbol": new_symbol}
            )
        
        # Extract symbols from existing positions
        existing_symbols = [pos.get("symbol") for pos in existing_positions if pos.get("symbol")]
        
        if not existing_symbols:
            return RiskCheckResult(
                approved=True,
                reason="No symbols in existing positions",
                details={"new_symbol": new_symbol}
            )
        
        # Check if we have price data for new symbol
        if new_symbol not in price_data.columns:
            return RiskCheckResult(
                approved=True,
                reason=f"No price data available for {new_symbol}",
                details={"new_symbol": new_symbol}
            )
        
        # Calculate correlations with existing positions
        high_correlation_count = 0
        high_corr_symbols = []
        
        for symbol in existing_symbols:
            if symbol not in price_data.columns:
                continue
            
            # Calculate correlation
            correlation = price_data[[new_symbol, symbol]].corr().iloc[0, 1]
            
            if abs(correlation) > self.settings.max_correlation:
                high_correlation_count += 1
                high_corr_symbols.append((symbol, correlation))
        
        # Check if we exceed max correlated positions
        if high_correlation_count >= self.settings.max_correlated_positions:
            return RiskCheckResult(
                approved=False,
                reason=f"Adding {new_symbol} would exceed maximum correlated positions ({self.settings.max_correlated_positions})",
                details={
                    "new_symbol": new_symbol,
                    "high_correlation_count": high_correlation_count,
                    "max_correlated_positions": self.settings.max_correlated_positions,
                    "high_corr_symbols": high_corr_symbols,
                }
            )
        
        return RiskCheckResult(
            approved=True,
            reason="Correlation within acceptable limits",
            details={
                "new_symbol": new_symbol,
                "high_correlation_count": high_correlation_count,
                "correlations": high_corr_symbols,
            }
        )
    
    def trigger_circuit_breaker(
        self,
        portfolio_value: float,
        peak_value: float,
        current_drawdown: float,
    ) -> RiskCheckResult:
        """
        Trigger circuit breaker to halt trading.
        
        Args:
            portfolio_value: Current portfolio value
            peak_value: Historical peak value
            current_drawdown: Current drawdown percentage
            
        Returns:
            RiskCheckResult with circuit breaker triggered
        """
        self._circuit_breaker_triggered = True
        
        breach_info = {
            "event": "circuit_breaker_triggered",
            "timestamp": datetime.now(),
            "portfolio_value": portfolio_value,
            "peak_value": peak_value,
            "current_drawdown": current_drawdown,
            "threshold": self.settings.circuit_breaker_threshold,
        }
        
        self._breach_log.append(breach_info)
        
        return RiskCheckResult(
            approved=False,
            reason=f"CIRCUIT BREAKER TRIGGERED: Drawdown ({current_drawdown:.1%}) reached threshold ({self.settings.circuit_breaker_threshold:.1%})",
            details=breach_info
        )
    
    def reset_circuit_breaker(self) -> None:
        """Reset the circuit breaker to allow trading again."""
        self._circuit_breaker_triggered = False
    
    def is_circuit_breaker_active(self) -> bool:
        """Check if circuit breaker is currently active."""
        return self._circuit_breaker_triggered
    
    def get_breach_log(self) -> list[dict[str, Any]]:
        """Get log of all risk breaches."""
        return self._breach_log.copy()
    
    def clear_breach_log(self) -> None:
        """Clear the breach log."""
        self._breach_log.clear()
    
    def _log_breach(self, breach_type: str, current_value: float, limit_value: float) -> None:
        """
        Log a risk breach.
        
        Args:
            breach_type: Type of breach
            current_value: Current value that breached
            limit_value: Limit that was breached
        """
        breach_info = {
            "breach_type": breach_type,
            "timestamp": datetime.now(),
            "current_value": current_value,
            "limit_value": limit_value,
        }
        self._breach_log.append(breach_info)
