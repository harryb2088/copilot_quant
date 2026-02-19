"""
LLM-based Strategy Generator

This module provides functionality to generate trading signal strategies using a 
Large Language Model (LLM). This is intended for INTERNAL USE ONLY.

Security Features:
- API key validation
- Input sanitization
- Rate limiting
- No external data transmission without explicit approval
"""

import os
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta


class LLMStrategyGenerator:
    """
    Generate trading signal strategies using LLM.
    
    This class interfaces with an LLM API to generate and refine trading strategies
    based on user input. It includes security safeguards to prevent data leaks.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        Initialize the LLM strategy generator.
        
        Args:
            api_key: OpenAI API key. If None, reads from environment variable.
            model: LLM model to use (default: gpt-3.5-turbo)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model
        self.rate_limit_tracker = {}
        self.max_requests_per_hour = 20
        
    def is_api_configured(self) -> bool:
        """Check if API is properly configured."""
        return bool(self.api_key and self.api_key.startswith("sk-"))
    
    def _check_rate_limit(self, user_id: str = "default") -> Tuple[bool, str]:
        """
        Check if user has exceeded rate limit.
        
        Args:
            user_id: User identifier for rate limiting
            
        Returns:
            Tuple of (is_allowed, message)
        """
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        
        # Clean old entries
        if user_id in self.rate_limit_tracker:
            self.rate_limit_tracker[user_id] = [
                ts for ts in self.rate_limit_tracker[user_id] if ts > hour_ago
            ]
        else:
            self.rate_limit_tracker[user_id] = []
        
        # Check limit
        if len(self.rate_limit_tracker[user_id]) >= self.max_requests_per_hour:
            return False, f"Rate limit exceeded. Max {self.max_requests_per_hour} requests per hour."
        
        return True, ""
    
    def _sanitize_input(self, user_input: str) -> str:
        """
        Sanitize user input to prevent injection attacks.
        
        Args:
            user_input: Raw user input
            
        Returns:
            Sanitized input string
        """
        # Remove any potential code execution attempts
        sanitized = user_input.strip()
        
        # Remove potentially dangerous patterns
        dangerous_patterns = [
            r'__import__',
            r'eval\s*\(',
            r'exec\s*\(',
            r'compile\s*\(',
            r'open\s*\(',
            r'os\.',
            r'sys\.',
            r'subprocess',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, sanitized, re.IGNORECASE):
                raise ValueError(f"Input contains potentially dangerous pattern: {pattern}")
        
        # Limit length
        max_length = 1000
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    def generate_strategy(self, user_description: str, user_id: str = "default") -> Dict:
        """
        Generate a trading strategy based on user description.
        
        Args:
            user_description: Natural language description of desired strategy
            user_id: User identifier for rate limiting
            
        Returns:
            Dictionary with strategy details or error information
        """
        # Check API configuration
        if not self.is_api_configured():
            return {
                "success": False,
                "error": "LLM API not configured. Please set OPENAI_API_KEY environment variable.",
                "strategy": None
            }
        
        # Check rate limit
        is_allowed, message = self._check_rate_limit(user_id)
        if not is_allowed:
            return {
                "success": False,
                "error": message,
                "strategy": None
            }
        
        # Sanitize input
        try:
            sanitized_input = self._sanitize_input(user_description)
        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
                "strategy": None
            }
        
        # Record request for rate limiting
        self.rate_limit_tracker[user_id].append(datetime.now())
        
        # Generate strategy using LLM
        try:
            strategy = self._call_llm(sanitized_input)
            return {
                "success": True,
                "error": None,
                "strategy": strategy
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error generating strategy: {str(e)}",
                "strategy": None
            }
    
    def _call_llm(self, user_input: str) -> Dict:
        """
        Call the LLM API to generate strategy.
        
        Args:
            user_input: Sanitized user input
            
        Returns:
            Strategy dictionary
        """
        # NOTE: This is a placeholder for actual LLM integration
        # In production, this would call OpenAI API or similar
        
        # For now, return a structured response based on input analysis
        strategy_type = self._infer_strategy_type(user_input)
        
        return {
            "name": self._generate_strategy_name(user_input),
            "type": strategy_type,
            "description": user_input,
            "signals": self._generate_signals_from_description(user_input, strategy_type),
            "parameters": self._extract_parameters(user_input),
            "risk_management": self._generate_risk_management(),
            "generated_at": datetime.now().isoformat(),
            "llm_model": self.model
        }
    
    def _infer_strategy_type(self, description: str) -> str:
        """Infer strategy type from description."""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ['momentum', 'trend', 'breakout']):
            return "Momentum"
        elif any(word in description_lower for word in ['mean reversion', 'reversion', 'statistical']):
            return "Mean Reversion"
        elif any(word in description_lower for word in ['pairs', 'arbitrage', 'spread']):
            return "Statistical Arbitrage"
        elif any(word in description_lower for word in ['volatility', 'vol', 'options']):
            return "Volatility"
        else:
            return "Custom"
    
    def _generate_strategy_name(self, description: str) -> str:
        """Generate a strategy name from description."""
        # Take first few words or use strategy type
        words = description.split()[:4]
        name = " ".join(words).title()
        # Account for ' Strategy' suffix (9 chars) in length check
        max_name_length = 30 - 9  # 21 characters for name part
        if len(name) > max_name_length:
            name = name[:max_name_length - 3] + "..."
        return f"{name} Strategy"
    
    def _generate_signals_from_description(self, description: str, strategy_type: str) -> List[Dict]:
        """Generate signal definitions based on description."""
        
        # Extract potential indicators mentioned
        indicators = []
        if 'rsi' in description.lower():
            indicators.append({
                "type": "RSI",
                "period": 14,
                "overbought": 70,
                "oversold": 30
            })
        
        if 'sma' in description.lower() or 'moving average' in description.lower():
            indicators.append({
                "type": "SMA",
                "short_period": 20,
                "long_period": 50
            })
        
        if 'macd' in description.lower():
            indicators.append({
                "type": "MACD",
                "fast": 12,
                "slow": 26,
                "signal": 9
            })
        
        # If no specific indicators mentioned, add defaults based on strategy type
        if not indicators:
            if strategy_type == "Momentum":
                indicators.append({
                    "type": "SMA",
                    "short_period": 20,
                    "long_period": 50
                })
            elif strategy_type == "Mean Reversion":
                indicators.append({
                    "type": "RSI",
                    "period": 14,
                    "overbought": 70,
                    "oversold": 30
                })
        
        return indicators
    
    def _extract_parameters(self, description: str) -> Dict:
        """Extract strategy parameters from description."""
        params = {
            "initial_capital": 100000,
            "position_size_pct": 10,
            "max_positions": 10
        }
        
        # Try to extract capital amount
        capital_match = re.search(r'\$?([\d,]+(?:\.\d+)?)\s*(?:k|thousand|million)?', description.lower())
        if capital_match:
            amount_str = capital_match.group(1).replace(',', '')
            amount = float(amount_str)
            if 'k' in description.lower() or 'thousand' in description.lower():
                amount *= 1000
            elif 'million' in description.lower():
                amount *= 1000000
            params["initial_capital"] = int(amount)
        
        return params
    
    def _generate_risk_management(self) -> Dict:
        """Generate risk management rules."""
        return {
            "stop_loss_pct": 2.0,
            "take_profit_pct": 5.0,
            "max_drawdown_pct": 10.0,
            "position_sizing": "equal_weight"
        }
    
    def refine_strategy(self, current_strategy: Dict, refinement_input: str, 
                       user_id: str = "default") -> Dict:
        """
        Refine an existing strategy based on user feedback.
        
        Args:
            current_strategy: Current strategy dictionary
            refinement_input: User's refinement instructions
            user_id: User identifier
            
        Returns:
            Updated strategy dictionary or error information
        """
        # Check rate limit
        is_allowed, message = self._check_rate_limit(user_id)
        if not is_allowed:
            return {
                "success": False,
                "error": message,
                "strategy": None
            }
        
        # Sanitize input
        try:
            sanitized_input = self._sanitize_input(refinement_input)
        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
                "strategy": None
            }
        
        # Record request
        self.rate_limit_tracker[user_id].append(datetime.now())
        
        # Apply refinements
        refined_strategy = current_strategy.copy()
        
        # Update description
        refined_strategy["description"] = f"{current_strategy.get('description', '')} | Refinement: {sanitized_input}"
        
        # Re-extract parameters based on refinement
        new_params = self._extract_parameters(sanitized_input)
        refined_strategy["parameters"].update(new_params)
        
        # Update timestamp
        refined_strategy["last_refined"] = datetime.now().isoformat()
        
        return {
            "success": True,
            "error": None,
            "strategy": refined_strategy
        }
