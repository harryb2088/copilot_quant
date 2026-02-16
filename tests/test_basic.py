"""Basic sanity test to verify test infrastructure."""


def test_import_modules():
    """Test that all main modules can be imported."""
    import src
    import src.data
    import src.backtest
    import src.strategies
    import src.brokers
    import src.ui
    import src.utils

    assert src.__version__ == "0.1.0"


def test_basic_math():
    """Simple test to verify pytest is working."""
    assert 1 + 1 == 2
    assert 2 * 3 == 6
