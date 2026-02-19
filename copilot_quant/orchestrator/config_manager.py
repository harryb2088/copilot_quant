"""
Configuration Manager Module

Provides unified YAML/TOML configuration management with validation,
runtime reload, and versioning support.

Features:
- Load configuration from YAML or TOML files
- Validate configuration against schema
- Runtime reload without restart
- Configuration versioning and history
- Type-safe access to configuration values
"""

import json
import logging
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class TradingScheduleConfig:
    """Trading schedule configuration"""

    timezone: str = "America/New_York"
    enable_pre_market: bool = False
    enable_post_market: bool = False
    auto_start: bool = True  # Auto-start trading at market open
    auto_stop: bool = True  # Auto-stop trading at market close


@dataclass
class StrategyConfig:
    """Strategy configuration"""

    symbols: List[str] = field(default_factory=list)
    max_positions: int = 10
    position_size_pct: float = 0.10  # 10% of portfolio per position
    rebalance_frequency: str = "daily"  # daily, weekly, intraday


@dataclass
class RiskConfig:
    """Risk management configuration"""

    max_portfolio_drawdown: float = 0.12
    max_position_size: float = 0.10
    position_stop_loss: float = 0.05
    enable_circuit_breaker: bool = True
    circuit_breaker_threshold: float = 0.10
    min_cash_buffer: float = 0.20
    max_cash_buffer: float = 0.80
    max_correlation: float = 0.80
    enable_volatility_targeting: bool = True
    target_portfolio_volatility: float = 0.15


@dataclass
class BrokerConfig:
    """Broker connection configuration"""

    broker_type: str = "ibkr"  # ibkr, alpaca, etc.
    host: str = "127.0.0.1"
    port: int = 7497  # Paper trading port for TWS
    client_id: int = 1
    account_number: Optional[str] = None
    use_gateway: bool = False
    paper_trading: bool = True
    commission: float = 0.001
    slippage: float = 0.0005


@dataclass
class DataConfig:
    """Data feed configuration"""

    primary_source: str = "ibkr"  # ibkr, polygon, yahoo, etc.
    update_interval: float = 1.0  # seconds
    enable_reconnect: bool = True
    cache_enabled: bool = True
    cache_dir: str = "./data/cache"


@dataclass
class NotificationConfig:
    """Notification configuration"""

    enabled: bool = True
    channels: List[str] = field(default_factory=list)  # slack, discord, email, webhook
    alert_levels: List[str] = field(default_factory=lambda: ["warning", "critical"])

    # Slack
    slack_webhook_url: Optional[str] = None
    slack_channel: Optional[str] = None

    # Discord
    discord_webhook_url: Optional[str] = None

    # Email
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None
    email_to: List[str] = field(default_factory=list)

    # Webhook
    webhook_url: Optional[str] = None
    webhook_headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class TradingConfig:
    """Complete trading configuration"""

    version: str = "1.0.0"
    mode: str = "paper"  # paper or live
    schedule: TradingScheduleConfig = field(default_factory=TradingScheduleConfig)
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    broker: BrokerConfig = field(default_factory=BrokerConfig)
    data: DataConfig = field(default_factory=DataConfig)
    notifications: NotificationConfig = field(default_factory=NotificationConfig)

    # Metadata
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __post_init__(self):
        """Initialize timestamps if not set"""
        now = datetime.now().isoformat()
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now


class ConfigManager:
    """
    Unified configuration manager with YAML/TOML support.

    Provides:
    - Load and save configuration files
    - Runtime validation
    - Configuration versioning
    - Hot reload capability

    Example:
        >>> manager = ConfigManager("config.paper.yaml")
        >>> config = manager.load()
        >>> print(f"Trading mode: {config.mode}")
        >>>
        >>> # Update configuration
        >>> config.risk.max_portfolio_drawdown = 0.15
        >>> manager.save(config)
        >>>
        >>> # Reload configuration
        >>> config = manager.reload()
    """

    def __init__(self, config_path: str, enable_versioning: bool = True, version_dir: Optional[str] = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to configuration file (YAML or TOML)
            enable_versioning: Enable configuration versioning
            version_dir: Directory to store config versions. Defaults to {config_dir}/.config_history
        """
        self.config_path = Path(config_path)
        self.enable_versioning = enable_versioning

        # Setup version directory
        if version_dir:
            self.version_dir = Path(version_dir)
        else:
            self.version_dir = self.config_path.parent / ".config_history"

        if self.enable_versioning:
            self.version_dir.mkdir(parents=True, exist_ok=True)

        self._current_config: Optional[TradingConfig] = None

        logger.info(f"ConfigManager initialized with config: {self.config_path}")

    def load(self) -> TradingConfig:
        """
        Load configuration from file.

        Returns:
            TradingConfig object

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is invalid
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        # Load based on file extension
        suffix = self.config_path.suffix.lower()

        try:
            with open(self.config_path, "r") as f:
                if suffix in [".yaml", ".yml"]:
                    data = yaml.safe_load(f)
                elif suffix == ".json":
                    data = json.load(f)
                else:
                    raise ValueError(f"Unsupported config format: {suffix}")

            # Parse into TradingConfig
            config = self._dict_to_config(data)

            # Validate
            self._validate_config(config)

            self._current_config = config
            logger.info(f"Configuration loaded successfully from {self.config_path}")

            return config

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise

    def save(self, config: TradingConfig, create_version: bool = True) -> None:
        """
        Save configuration to file.

        Args:
            config: TradingConfig object to save
            create_version: Create a versioned backup
        """
        # Update timestamp
        config.updated_at = datetime.now().isoformat()

        # Validate before saving
        self._validate_config(config)

        # Create version backup if enabled
        if self.enable_versioning and create_version and self.config_path.exists():
            self._create_version_backup()

        # Convert to dict
        data = self._config_to_dict(config)

        # Save based on file extension
        suffix = self.config_path.suffix.lower()

        try:
            with open(self.config_path, "w") as f:
                if suffix in [".yaml", ".yml"]:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False)
                elif suffix == ".json":
                    json.dump(data, f, indent=2)
                else:
                    raise ValueError(f"Unsupported config format: {suffix}")

            self._current_config = config
            logger.info(f"Configuration saved to {self.config_path}")

        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise

    def reload(self) -> TradingConfig:
        """
        Reload configuration from file (hot reload).

        Returns:
            Updated TradingConfig object
        """
        logger.info("Reloading configuration...")
        return self.load()

    def get_current_config(self) -> Optional[TradingConfig]:
        """
        Get currently loaded configuration.

        Returns:
            Current TradingConfig or None if not loaded
        """
        return self._current_config

    def _dict_to_config(self, data: Dict[str, Any]) -> TradingConfig:
        """Convert dictionary to TradingConfig object"""

        # Helper to convert nested dicts
        def parse_section(data_dict: Dict, config_class):
            if data_dict is None:
                return config_class()
            # Filter to only valid fields
            valid_fields = {f.name for f in config_class.__dataclass_fields__.values()}
            filtered = {k: v for k, v in data_dict.items() if k in valid_fields}
            return config_class(**filtered)

        return TradingConfig(
            version=data.get("version", "1.0.0"),
            mode=data.get("mode", "paper"),
            schedule=parse_section(data.get("schedule"), TradingScheduleConfig),
            strategy=parse_section(data.get("strategy"), StrategyConfig),
            risk=parse_section(data.get("risk"), RiskConfig),
            broker=parse_section(data.get("broker"), BrokerConfig),
            data=parse_section(data.get("data"), DataConfig),
            notifications=parse_section(data.get("notifications"), NotificationConfig),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def _config_to_dict(self, config: TradingConfig) -> Dict[str, Any]:
        """Convert TradingConfig to dictionary"""
        return asdict(config)

    def _validate_config(self, config: TradingConfig) -> None:
        """
        Validate configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        # Validate mode
        if config.mode not in ["paper", "live"]:
            raise ValueError(f"Invalid mode: {config.mode}. Must be 'paper' or 'live'")

        # Validate risk parameters
        if not 0 < config.risk.max_portfolio_drawdown <= 1:
            raise ValueError("max_portfolio_drawdown must be between 0 and 1")

        if not 0 < config.risk.max_position_size <= 1:
            raise ValueError("max_position_size must be between 0 and 1")

        if not 0 <= config.risk.position_stop_loss <= 1:
            raise ValueError("position_stop_loss must be between 0 and 1")

        # Validate broker configuration
        if config.broker.port <= 0:
            raise ValueError("Broker port must be positive")

        if config.broker.commission < 0:
            raise ValueError("Commission must be non-negative")

        # Validate strategy
        if config.strategy.max_positions <= 0:
            raise ValueError("max_positions must be positive")

        if not 0 < config.strategy.position_size_pct <= 1:
            raise ValueError("position_size_pct must be between 0 and 1")

        # Validate notifications
        if config.notifications.enabled:
            if not config.notifications.channels:
                logger.warning("Notifications enabled but no channels configured")

        logger.debug("Configuration validation passed")

    def _create_version_backup(self) -> None:
        """Create a versioned backup of current configuration"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version_filename = f"{self.config_path.stem}_{timestamp}{self.config_path.suffix}"
        version_path = self.version_dir / version_filename

        try:
            shutil.copy2(self.config_path, version_path)
            logger.info(f"Created configuration version: {version_path}")
        except Exception as e:
            logger.error(f"Failed to create version backup: {e}")

    def list_versions(self) -> List[Path]:
        """
        List all configuration versions.

        Returns:
            List of version file paths, sorted by timestamp (newest first)
        """
        if not self.version_dir.exists():
            return []

        pattern = f"{self.config_path.stem}_*{self.config_path.suffix}"
        versions = sorted(self.version_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)

        return versions

    def restore_version(self, version_path: Path) -> TradingConfig:
        """
        Restore configuration from a specific version.

        Args:
            version_path: Path to version file

        Returns:
            Restored TradingConfig
        """
        if not version_path.exists():
            raise FileNotFoundError(f"Version file not found: {version_path}")

        # Create backup of current config before restoring
        if self.config_path.exists():
            self._create_version_backup()

        # Restore version
        shutil.copy2(version_path, self.config_path)
        logger.info(f"Restored configuration from version: {version_path}")

        # Reload
        return self.reload()
