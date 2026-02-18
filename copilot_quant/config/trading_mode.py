"""
Trading Mode Configuration Module

Manages paper trading vs live trading mode with separate credentials
and safety controls.
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class TradingMode(Enum):
    """Trading mode enumeration"""
    PAPER = "paper"
    LIVE = "live"


@dataclass
class TradingModeConfig:
    """
    Configuration for a specific trading mode (paper or live).
    
    Stores connection parameters and credentials for IBKR trading,
    separate for paper and live modes for safety.
    
    Attributes:
        mode: Trading mode (PAPER or LIVE)
        host: IBKR API host address
        port: IBKR API port number
        client_id: Unique client identifier
        account_number: Trading account number (optional)
        use_gateway: Whether using IB Gateway (vs TWS)
    """
    mode: TradingMode
    host: str
    port: int
    client_id: int
    account_number: Optional[str] = None
    use_gateway: bool = False
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not isinstance(self.mode, TradingMode):
            raise ValueError(f"mode must be TradingMode enum, got {type(self.mode)}")
        
        # Validate port is appropriate for mode
        if not self.use_gateway:
            # TWS ports
            if self.mode == TradingMode.PAPER and self.port not in [7497]:
                logger.warning(
                    f"Paper trading mode typically uses port 7497 (TWS), "
                    f"but configured port is {self.port}"
                )
            elif self.mode == TradingMode.LIVE and self.port not in [7496]:
                logger.warning(
                    f"Live trading mode typically uses port 7496 (TWS), "
                    f"but configured port is {self.port}"
                )
        else:
            # Gateway ports
            if self.mode == TradingMode.PAPER and self.port not in [4002]:
                logger.warning(
                    f"Paper trading mode typically uses port 4002 (Gateway), "
                    f"but configured port is {self.port}"
                )
            elif self.mode == TradingMode.LIVE and self.port not in [4001]:
                logger.warning(
                    f"Live trading mode typically uses port 4001 (Gateway), "
                    f"but configured port is {self.port}"
                )
    
    @property
    def is_paper(self) -> bool:
        """Check if in paper trading mode."""
        return self.mode == TradingMode.PAPER
    
    @property
    def is_live(self) -> bool:
        """Check if in live trading mode."""
        return self.mode == TradingMode.LIVE
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            'mode': self.mode.value,
            'host': self.host,
            'port': self.port,
            'client_id': self.client_id,
            'account_number': self.account_number,
            'use_gateway': self.use_gateway,
        }
    
    def __repr__(self):
        """String representation."""
        return (
            f"TradingModeConfig("
            f"mode={self.mode.value}, "
            f"host={self.host}, "
            f"port={self.port}, "
            f"client_id={self.client_id}, "
            f"account={self.account_number or 'N/A'})"
        )


def get_trading_mode_config(mode: TradingMode) -> TradingModeConfig:
    """
    Get trading mode configuration from environment variables.
    
    This loads separate configuration for paper and live trading modes
    to ensure safety and prevent accidental live trading.
    
    Environment Variables for Paper Trading:
        IB_PAPER_HOST: IBKR host (default: 127.0.0.1)
        IB_PAPER_PORT: IBKR port (default: 7497 for TWS, 4002 for Gateway)
        IB_PAPER_CLIENT_ID: Client ID (default: 1)
        IB_PAPER_ACCOUNT: Account number (optional)
        IB_PAPER_USE_GATEWAY: Use Gateway instead of TWS (default: false)
    
    Environment Variables for Live Trading:
        IB_LIVE_HOST: IBKR host (default: 127.0.0.1)
        IB_LIVE_PORT: IBKR port (default: 7496 for TWS, 4001 for Gateway)
        IB_LIVE_CLIENT_ID: Client ID (default: 2)
        IB_LIVE_ACCOUNT: Account number (optional)
        IB_LIVE_USE_GATEWAY: Use Gateway instead of TWS (default: false)
    
    Backward compatibility:
        IB_HOST, IB_PORT, IB_CLIENT_ID: Used as fallback for paper mode
    
    Args:
        mode: Trading mode to configure
        
    Returns:
        TradingModeConfig for the specified mode
    """
    if mode == TradingMode.PAPER:
        # Paper trading configuration
        use_gateway = os.getenv('IB_PAPER_USE_GATEWAY', 'false').lower() == 'true'
        
        # Fallback to legacy env vars for backward compatibility
        host = os.getenv('IB_PAPER_HOST') or os.getenv('IB_HOST', '127.0.0.1')
        client_id = int(os.getenv('IB_PAPER_CLIENT_ID') or os.getenv('IB_CLIENT_ID', '1'))
        account = os.getenv('IB_PAPER_ACCOUNT') or os.getenv('IB_PAPER_ACCOUNT')
        
        # Port: explicit > env var > auto-detect
        port_env = os.getenv('IB_PAPER_PORT') or os.getenv('IB_PORT')
        if port_env:
            port = int(port_env)
        else:
            port = 4002 if use_gateway else 7497
        
        logger.info(f"Loading paper trading config: host={host}, port={port}, client_id={client_id}")
        
        return TradingModeConfig(
            mode=TradingMode.PAPER,
            host=host,
            port=port,
            client_id=client_id,
            account_number=account,
            use_gateway=use_gateway
        )
    
    else:  # LIVE mode
        # Live trading configuration - requires explicit env vars
        use_gateway = os.getenv('IB_LIVE_USE_GATEWAY', 'false').lower() == 'true'
        host = os.getenv('IB_LIVE_HOST', '127.0.0.1')
        client_id = int(os.getenv('IB_LIVE_CLIENT_ID', '2'))
        account = os.getenv('IB_LIVE_ACCOUNT')
        
        # Port: explicit > auto-detect
        port_env = os.getenv('IB_LIVE_PORT')
        if port_env:
            port = int(port_env)
        else:
            port = 4001 if use_gateway else 7496
        
        logger.info(f"Loading live trading config: host={host}, port={port}, client_id={client_id}")
        
        return TradingModeConfig(
            mode=TradingMode.LIVE,
            host=host,
            port=port,
            client_id=client_id,
            account_number=account,
            use_gateway=use_gateway
        )


class TradingModeManager:
    """
    Manages trading mode state and transitions with safety controls.
    
    Handles switching between paper and live trading modes with:
    - Mode transition logging for traceability
    - Validation before mode switches
    - History tracking of mode changes
    """
    
    def __init__(self, default_mode: TradingMode = TradingMode.PAPER):
        """
        Initialize trading mode manager.
        
        Args:
            default_mode: Initial trading mode (default: PAPER for safety)
        """
        self._current_mode = default_mode
        self._mode_history: list[tuple[datetime, TradingMode]] = [
            (datetime.now(), default_mode)
        ]
        logger.info(f"TradingModeManager initialized with mode: {default_mode.value}")
    
    @property
    def current_mode(self) -> TradingMode:
        """Get current trading mode."""
        return self._current_mode
    
    @property
    def current_config(self) -> TradingModeConfig:
        """Get configuration for current mode."""
        return get_trading_mode_config(self._current_mode)
    
    def switch_mode(self, new_mode: TradingMode, confirmed: bool = False) -> bool:
        """
        Switch to a different trading mode.
        
        Args:
            new_mode: Mode to switch to
            confirmed: Whether user has confirmed the switch (required for LIVE)
            
        Returns:
            True if mode was switched, False if cancelled or invalid
            
        Raises:
            ValueError: If switching to LIVE without confirmation
        """
        if new_mode == self._current_mode:
            logger.info(f"Already in {new_mode.value} mode, no switch needed")
            return False
        
        # Require explicit confirmation for live trading
        if new_mode == TradingMode.LIVE and not confirmed:
            raise ValueError(
                "Switching to LIVE trading mode requires explicit confirmation. "
                "Set confirmed=True after user confirms the switch."
            )
        
        # Log the mode switch
        old_mode = self._current_mode
        self._current_mode = new_mode
        timestamp = datetime.now()
        self._mode_history.append((timestamp, new_mode))
        
        logger.warning(
            f"⚠️  TRADING MODE SWITCHED: {old_mode.value.upper()} → {new_mode.value.upper()} "
            f"at {timestamp.isoformat()}"
        )
        
        return True
    
    def get_mode_history(self) -> list[tuple[datetime, TradingMode]]:
        """
        Get history of mode changes.
        
        Returns:
            List of (timestamp, mode) tuples
        """
        return self._mode_history.copy()
    
    def is_paper_mode(self) -> bool:
        """Check if currently in paper trading mode."""
        return self._current_mode == TradingMode.PAPER
    
    def is_live_mode(self) -> bool:
        """Check if currently in live trading mode."""
        return self._current_mode == TradingMode.LIVE
