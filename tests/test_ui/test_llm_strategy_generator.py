"""
Tests for LLM Strategy Generator

Tests the LLM-based strategy generation functionality including:
- Input sanitization
- Rate limiting
- Strategy generation
- API configuration
"""

import pytest
from datetime import datetime, timedelta
from src.ui.utils.llm_strategy_generator import LLMStrategyGenerator


class TestLLMStrategyGenerator:
    """Test suite for LLM strategy generator."""
    
    def test_initialization(self):
        """Test basic initialization."""
        generator = LLMStrategyGenerator()
        assert generator is not None
        assert generator.model == "gpt-3.5-turbo"
        assert generator.max_requests_per_hour == 20
    
    def test_api_not_configured(self):
        """Test behavior when API is not configured."""
        generator = LLMStrategyGenerator(api_key="")
        assert not generator.is_api_configured()
        
        result = generator.generate_strategy("Test strategy")
        assert not result["success"]
        assert "not configured" in result["error"].lower()
    
    def test_api_configured(self):
        """Test API configuration detection."""
        generator = LLMStrategyGenerator(api_key="sk-test-key-12345")
        assert generator.is_api_configured()
    
    def test_input_sanitization_valid(self):
        """Test that valid input passes sanitization."""
        generator = LLMStrategyGenerator()
        
        valid_inputs = [
            "A momentum strategy using moving averages",
            "Buy when RSI < 30, sell when RSI > 70",
            "Mean reversion with Bollinger Bands"
        ]
        
        for input_text in valid_inputs:
            sanitized = generator._sanitize_input(input_text)
            assert sanitized == input_text.strip()
    
    def test_input_sanitization_dangerous(self):
        """Test that dangerous input is rejected."""
        generator = LLMStrategyGenerator()
        
        dangerous_inputs = [
            "__import__('os').system('ls')",
            "eval('print(1)')",
            "exec('import sys')",
            "open('/etc/passwd')",
        ]
        
        for dangerous_input in dangerous_inputs:
            with pytest.raises(ValueError):
                generator._sanitize_input(dangerous_input)
    
    def test_input_sanitization_length_limit(self):
        """Test that overly long input is truncated."""
        generator = LLMStrategyGenerator()
        
        long_input = "A" * 2000
        sanitized = generator._sanitize_input(long_input)
        assert len(sanitized) == 1000
    
    def test_rate_limiting_allows_initial_requests(self):
        """Test that initial requests are allowed."""
        generator = LLMStrategyGenerator()
        
        is_allowed, message = generator._check_rate_limit("test_user")
        assert is_allowed
        assert message == ""
    
    def test_rate_limiting_blocks_excessive_requests(self):
        """Test that excessive requests are blocked."""
        generator = LLMStrategyGenerator()
        user_id = "test_user_2"
        
        # Make max requests
        for i in range(generator.max_requests_per_hour):
            generator.rate_limit_tracker.setdefault(user_id, []).append(datetime.now())
        
        # Next request should be blocked
        is_allowed, message = generator._check_rate_limit(user_id)
        assert not is_allowed
        assert "rate limit exceeded" in message.lower()
    
    def test_rate_limiting_resets_after_hour(self):
        """Test that rate limit resets after an hour."""
        generator = LLMStrategyGenerator()
        user_id = "test_user_3"
        
        # Add old requests (more than 1 hour ago)
        old_time = datetime.now() - timedelta(hours=2)
        generator.rate_limit_tracker[user_id] = [old_time] * generator.max_requests_per_hour
        
        # Should be allowed since old requests expired
        is_allowed, message = generator._check_rate_limit(user_id)
        assert is_allowed
        assert len(generator.rate_limit_tracker[user_id]) == 0
    
    def test_strategy_type_inference_momentum(self):
        """Test inferring momentum strategy type."""
        generator = LLMStrategyGenerator(api_key="sk-test-key")
        
        momentum_inputs = [
            "A momentum strategy",
            "trend following approach",
            "breakout trading system"
        ]
        
        for input_text in momentum_inputs:
            strategy_type = generator._infer_strategy_type(input_text)
            assert strategy_type == "Momentum"
    
    def test_strategy_type_inference_mean_reversion(self):
        """Test inferring mean reversion strategy type."""
        generator = LLMStrategyGenerator(api_key="sk-test-key")
        
        mean_reversion_inputs = [
            "mean reversion strategy",
            "reversion to the mean",
            "statistical mean reversion"
        ]
        
        for input_text in mean_reversion_inputs:
            strategy_type = generator._infer_strategy_type(input_text)
            assert strategy_type == "Mean Reversion"
    
    def test_strategy_name_generation(self):
        """Test strategy name generation."""
        generator = LLMStrategyGenerator(api_key="sk-test-key")
        
        description = "momentum trading with moving averages"
        name = generator._generate_strategy_name(description)
        
        assert "Momentum" in name
        assert "Strategy" in name
        assert len(name) <= 40
    
    def test_signal_generation_with_rsi(self):
        """Test signal generation when RSI is mentioned."""
        generator = LLMStrategyGenerator(api_key="sk-test-key")
        
        description = "Use RSI indicator for trading"
        signals = generator._generate_signals_from_description(description, "Mean Reversion")
        
        assert len(signals) > 0
        assert any(s["type"] == "RSI" for s in signals)
    
    def test_signal_generation_with_moving_average(self):
        """Test signal generation when moving average is mentioned."""
        generator = LLMStrategyGenerator(api_key="sk-test-key")
        
        description = "Trade using moving average crossovers"
        signals = generator._generate_signals_from_description(description, "Momentum")
        
        assert len(signals) > 0
        assert any(s["type"] == "SMA" for s in signals)
    
    def test_parameter_extraction_capital(self):
        """Test extracting capital amount from description."""
        generator = LLMStrategyGenerator(api_key="sk-test-key")
        
        descriptions = [
            ("Start with $50000", 50000),
            ("Use 100k capital", 100000),
            ("Trade with $1 million", 1000000),
        ]
        
        for description, expected_capital in descriptions:
            params = generator._extract_parameters(description)
            assert params["initial_capital"] == expected_capital
    
    def test_risk_management_generation(self):
        """Test risk management rules generation."""
        generator = LLMStrategyGenerator(api_key="sk-test-key")
        
        risk_mgmt = generator._generate_risk_management()
        
        assert "stop_loss_pct" in risk_mgmt
        assert "take_profit_pct" in risk_mgmt
        assert "max_drawdown_pct" in risk_mgmt
        assert "position_sizing" in risk_mgmt
    
    def test_generate_strategy_without_api_key(self):
        """Test generating strategy without API key."""
        generator = LLMStrategyGenerator(api_key="")
        
        result = generator.generate_strategy("Test strategy")
        
        assert not result["success"]
        assert result["error"] is not None
        assert result["strategy"] is None
    
    def test_generate_strategy_with_valid_input(self):
        """Test generating strategy with valid input and API key."""
        generator = LLMStrategyGenerator(api_key="sk-test-key-12345")
        
        description = "A momentum strategy using 20 and 50 day moving averages"
        result = generator.generate_strategy(description)
        
        assert result["success"]
        assert result["error"] is None
        assert result["strategy"] is not None
        
        strategy = result["strategy"]
        assert "name" in strategy
        assert "type" in strategy
        assert "description" in strategy
        assert "signals" in strategy
        assert "parameters" in strategy
        assert "risk_management" in strategy
        assert strategy["description"] == description
    
    def test_generate_strategy_with_dangerous_input(self):
        """Test that dangerous input is rejected."""
        generator = LLMStrategyGenerator(api_key="sk-test-key-12345")
        
        dangerous_input = "exec('import os; os.system(\"ls\")')"
        result = generator.generate_strategy(dangerous_input)
        
        assert not result["success"]
        assert "dangerous" in result["error"].lower()
    
    def test_generate_strategy_rate_limit(self):
        """Test that rate limiting works in strategy generation."""
        generator = LLMStrategyGenerator(api_key="sk-test-key-12345")
        user_id = "test_user_limit"
        
        # Fill up rate limit
        for i in range(generator.max_requests_per_hour):
            result = generator.generate_strategy("Test strategy", user_id)
            if i < generator.max_requests_per_hour - 1:
                assert result["success"]
        
        # Next one should be rate limited
        result = generator.generate_strategy("Another strategy", user_id)
        assert not result["success"]
        assert "rate limit" in result["error"].lower()
    
    def test_refine_strategy(self):
        """Test refining an existing strategy."""
        generator = LLMStrategyGenerator(api_key="sk-test-key-12345")
        
        # Create initial strategy
        initial_result = generator.generate_strategy("Momentum strategy")
        assert initial_result["success"]
        
        initial_strategy = initial_result["strategy"]
        
        # Refine it
        refinement = "Add stop loss at 2% and take profit at 5%"
        refined_result = generator.refine_strategy(initial_strategy, refinement)
        
        assert refined_result["success"]
        assert refined_result["strategy"] is not None
        assert "Refinement:" in refined_result["strategy"]["description"]
    
    def test_refine_strategy_dangerous_input(self):
        """Test that dangerous refinement input is rejected."""
        generator = LLMStrategyGenerator(api_key="sk-test-key-12345")
        
        initial_strategy = {"name": "Test", "parameters": {}}
        dangerous_input = "eval('print(1)')"
        
        result = generator.refine_strategy(initial_strategy, dangerous_input)
        
        assert not result["success"]
        assert "dangerous" in result["error"].lower()
