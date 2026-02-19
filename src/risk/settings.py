"""
Risk Settings Configuration Module

Stores all risk parameter defaults, provides validation for user inputs,
and supports persisting settings across sessions.
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class RiskSettings:
    """
    Risk management settings with conservative defaults.

    All defaults prioritize capital preservation over maximum returns.
    """

    # Portfolio-level controls
    max_portfolio_drawdown: float = 0.12  # 12% - maximum allowed portfolio drawdown
    min_cash_buffer: float = 0.20  # 20% - minimum cash as % of portfolio
    max_cash_buffer: float = 0.80  # 80% - maximum cash as % of portfolio
    enable_circuit_breaker: bool = True  # Enable automatic liquidation on breach
    circuit_breaker_threshold: float = 0.10  # 10% - drawdown that triggers circuit breaker

    # Position-level controls
    max_position_size: float = 0.10  # 10% - max position size as % of portfolio
    position_stop_loss: float = 0.05  # 5% - per-position stop loss
    max_positions: int = 10  # Maximum number of concurrent positions

    # Correlation and diversification
    max_correlation: float = 0.80  # Maximum correlation between positions (0-1)
    max_correlated_positions: int = 2  # Max positions with correlation > threshold

    # Volatility targeting
    enable_volatility_targeting: bool = True  # Enable volatility-based position sizing
    target_portfolio_volatility: float = 0.15  # 15% - target annual portfolio volatility

    def __post_init__(self) -> None:
        """Validate settings after initialization."""
        self.validate()

    def validate(self) -> None:
        """
        Validate all risk settings.

        Raises:
            ValueError: If any setting is invalid
        """
        # Validate percentages are between 0 and 1
        if not 0 < self.max_portfolio_drawdown <= 1:
            raise ValueError(f"max_portfolio_drawdown must be between 0 and 1, got {self.max_portfolio_drawdown}")

        if not 0 <= self.min_cash_buffer <= 1:
            raise ValueError(f"min_cash_buffer must be between 0 and 1, got {self.min_cash_buffer}")

        if not 0 <= self.max_cash_buffer <= 1:
            raise ValueError(f"max_cash_buffer must be between 0 and 1, got {self.max_cash_buffer}")

        if not 0 < self.circuit_breaker_threshold <= 1:
            raise ValueError(f"circuit_breaker_threshold must be between 0 and 1, got {self.circuit_breaker_threshold}")

        if not 0 < self.max_position_size <= 1:
            raise ValueError(f"max_position_size must be between 0 and 1, got {self.max_position_size}")

        if not 0 < self.position_stop_loss <= 1:
            raise ValueError(f"position_stop_loss must be between 0 and 1, got {self.position_stop_loss}")

        if not 0 <= self.max_correlation <= 1:
            raise ValueError(f"max_correlation must be between 0 and 1, got {self.max_correlation}")

        if not 0 < self.target_portfolio_volatility <= 1:
            raise ValueError(
                f"target_portfolio_volatility must be between 0 and 1, got {self.target_portfolio_volatility}"
            )

        # Validate cash buffer logic
        if self.min_cash_buffer > self.max_cash_buffer:
            raise ValueError(
                f"min_cash_buffer ({self.min_cash_buffer}) cannot be greater than max_cash_buffer ({self.max_cash_buffer})"
            )

        # Validate integer constraints
        if self.max_positions < 1:
            raise ValueError(f"max_positions must be at least 1, got {self.max_positions}")

        if self.max_correlated_positions < 1:
            raise ValueError(f"max_correlated_positions must be at least 1, got {self.max_correlated_positions}")

        # Validate circuit breaker threshold is less than max drawdown
        if self.circuit_breaker_threshold > self.max_portfolio_drawdown:
            raise ValueError(
                f"circuit_breaker_threshold ({self.circuit_breaker_threshold}) "
                f"cannot exceed max_portfolio_drawdown ({self.max_portfolio_drawdown})"
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RiskSettings":
        """
        Create settings from dictionary.

        Args:
            data: Dictionary containing settings

        Returns:
            RiskSettings instance
        """
        return cls(**data)

    def save(self, filepath: Path | str) -> None:
        """
        Save settings to JSON file.

        Args:
            filepath: Path to save settings
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: Path | str) -> "RiskSettings":
        """
        Load settings from JSON file.

        Args:
            filepath: Path to load settings from

        Returns:
            RiskSettings instance

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Settings file not found: {filepath}")

        with open(filepath, "r") as f:
            data = json.load(f)

        return cls.from_dict(data)

    @classmethod
    def get_conservative_profile(cls) -> "RiskSettings":
        """Get conservative risk settings (default values)."""
        return cls()

    @classmethod
    def get_balanced_profile(cls) -> "RiskSettings":
        """Get balanced risk settings."""
        return cls(
            max_portfolio_drawdown=0.15,  # 15%
            max_position_size=0.15,  # 15%
            min_cash_buffer=0.15,  # 15%
            position_stop_loss=0.07,  # 7%
            max_positions=15,
            circuit_breaker_threshold=0.12,  # 12%
            target_portfolio_volatility=0.18,  # 18%
        )

    @classmethod
    def get_aggressive_profile(cls) -> "RiskSettings":
        """Get aggressive risk settings."""
        return cls(
            max_portfolio_drawdown=0.20,  # 20%
            max_position_size=0.20,  # 20%
            min_cash_buffer=0.10,  # 10%
            position_stop_loss=0.10,  # 10%
            max_positions=20,
            circuit_breaker_threshold=0.15,  # 15%
            target_portfolio_volatility=0.25,  # 25%
            max_correlation=0.85,
        )
