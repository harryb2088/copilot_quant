"""
Broker connector modules (IBKR, etc.)

This package provides broker integrations for live and paper trading.
"""

from .interactive_brokers import IBKRBroker

__all__ = ['IBKRBroker']
