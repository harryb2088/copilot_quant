"""Basic sanity test to verify test infrastructure."""


def test_import_modules():
    """Test that all main modules can be imported."""
    import copilot_quant
    import copilot_quant.backtest
    import copilot_quant.brokers
    import copilot_quant.data
    import copilot_quant.strategies
    import copilot_quant.ui
    import copilot_quant.utils

    assert copilot_quant.__version__ == "0.1.0"


def test_basic_math():
    """Simple test to verify pytest is working."""
    assert 1 + 1 == 2
    assert 2 * 3 == 6
