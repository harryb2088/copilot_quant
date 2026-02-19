"""
Pytest configuration and shared fixtures

This file makes fixtures available to all test modules.
"""

import pytest
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import all fixtures from fixture modules
pytest_plugins = [
    'tests.fixtures.broker_fixtures',
]
