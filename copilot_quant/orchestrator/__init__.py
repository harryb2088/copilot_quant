"""
Trading Orchestrator Module

This module provides:
- TradingOrchestrator: Main daemon for managing trading lifecycle
- ConfigManager: Unified YAML/TOML configuration management
- MarketCalendar: NYSE market hours and holiday detection
- Notifiers: Multi-channel alerting (Slack, Discord, Email, Webhook)
"""

from copilot_quant.orchestrator.market_calendar import MarketCalendar, MarketState
from copilot_quant.orchestrator.config_manager import ConfigManager
from copilot_quant.orchestrator.trading_orchestrator import TradingOrchestrator

__all__ = [
    'MarketCalendar',
    'MarketState',
    'ConfigManager',
    'TradingOrchestrator',
]
