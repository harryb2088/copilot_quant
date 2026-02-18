# Issue: Paper/Live Trading Toggle and Environment Configuration

**Epic**: Live Trading & Interactive Brokers (IBKR) Integration  
**Priority**: Critical  
**Status**: In Progress  
**Created**: 2026-02-18

## Overview
Implement robust paper/live trading mode toggle with environment-based configuration, safety checks, and clear mode indication throughout the platform.

## Requirements

### 1. Configuration System
- [x] Basic environment variable support (IB_HOST, IB_PORT, etc.)
- [ ] Comprehensive configuration file support
- [ ] Environment-specific configs (dev, staging, production)
- [ ] Configuration validation on startup
- [ ] Configuration override hierarchy (env vars > config file > defaults)
- [ ] Secure credential management

### 2. Trading Mode Management
- [x] Basic paper_trading boolean flag
- [ ] Trading mode enum (PAPER, LIVE, SIMULATION)
- [ ] Mode switching with confirmation
- [ ] Mode persistence (remember last mode)
- [ ] Mode indicator in all UIs
- [ ] Mode-specific logging

### 3. Safety Mechanisms
- [ ] Explicit confirmation required for live mode
- [ ] Warning banners in live mode
- [ ] Different color schemes (green=paper, red=live)
- [ ] Auto-disable live mode on errors
- [ ] Mode mismatch detection
- [ ] Read-only mode for observation

### 4. Environment Detection
- [x] Auto-detect port based on mode
- [ ] Validate connection matches expected mode
- [ ] Detect account type from IB (paper vs live)
- [ ] Prevent live trading in dev environment
- [ ] Environment-specific feature flags

### 5. Configuration Validation
- [ ] Validate all required settings present
- [ ] Validate port matches mode
- [ ] Validate credentials are for correct mode
- [ ] Check IB application is running
- [ ] Verify network connectivity
- [ ] Test connection before enabling trading

## Implementation Tasks

### Configuration Manager
```python
class TradingConfigManager:
    """
    Manages trading configuration and environment settings
    """
    - load_config(config_path: Optional[str] = None) -> Config
    - validate_config(config: Config) -> ValidationResult
    - get_trading_mode() -> TradingMode
    - set_trading_mode(mode: TradingMode, confirm: bool = True) -> bool
    - is_live_trading() -> bool
    - get_config_value(key: str, default: Any = None) -> Any
```

### Environment Manager
```python
class EnvironmentManager:
    """
    Manages environment detection and validation
    """
    - detect_environment() -> Environment
    - validate_environment(mode: TradingMode) -> bool
    - get_ib_config(mode: TradingMode) -> IBConfig
    - is_production() -> bool
    - check_prerequisites() -> List[str]
```

### Safety Guard
```python
class TradingSafetyGuard:
    """
    Enforces safety checks for trading mode
    """
    - require_confirmation(action: str) -> bool
    - validate_mode_switch(from_mode: TradingMode, to_mode: TradingMode) -> bool
    - check_live_trading_allowed() -> bool
    - get_safety_warnings(mode: TradingMode) -> List[str]
    - enable_kill_switch() -> None
```

### Data Models
```python
class TradingMode(Enum):
    PAPER = "paper"
    LIVE = "live"
    SIMULATION = "simulation"  # No broker connection
    READ_ONLY = "read_only"  # View only, no trading

class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    
@dataclass
class Config:
    trading_mode: TradingMode
    environment: Environment
    ib_host: str
    ib_port: int
    ib_client_id: int
    use_gateway: bool
    max_position_size: int
    daily_loss_limit: float
    require_confirmations: bool
    # ... additional settings

@dataclass
class IBConfig:
    host: str
    port: int
    client_id: int
    timeout: int
    expected_account_prefix: str  # e.g., "DU" for paper
```

### Configuration File Format (config.yaml)
```yaml
# Trading configuration
trading:
  mode: paper  # paper, live, simulation, read_only
  environment: development  # development, staging, production
  
# Interactive Brokers settings
interactive_brokers:
  host: 127.0.0.1
  port: 7497  # 7497=TWS paper, 7496=TWS live, 4002=Gateway paper, 4001=Gateway live
  client_id: 1
  use_gateway: false
  timeout: 30
  max_retries: 3
  
# Risk management
risk:
  max_position_size: 10000
  max_portfolio_value: 100000
  daily_loss_limit: 5000
  max_orders_per_day: 100
  
# Safety settings
safety:
  require_live_confirmation: true
  live_mode_password: ${LIVE_MODE_PASSWORD}  # From environment
  auto_disable_on_loss: true
  loss_threshold: 1000
```

### Environment Variables (.env)
```bash
# Trading mode
TRADING_MODE=paper  # paper or live

# IB Connection
IB_HOST=127.0.0.1
IB_PORT=7497
IB_CLIENT_ID=1
IB_PAPER_ACCOUNT=DU123456
IB_LIVE_ACCOUNT=U123456

# Safety
LIVE_MODE_PASSWORD=your_secure_password
REQUIRE_LIVE_CONFIRMATION=true

# Environment
ENVIRONMENT=development
```

## Acceptance Criteria
- [ ] Configuration can be loaded from file and environment
- [ ] Trading mode clearly indicated in all UIs
- [ ] Live mode requires explicit confirmation
- [ ] Configuration validation prevents misconfigurations
- [ ] Mode switching works with safety checks
- [ ] Different visual indicators for paper vs live
- [ ] Environment detection prevents live trading in dev
- [ ] All configuration changes are logged
- [ ] Unit tests for configuration management
- [ ] Integration tests for mode switching

## Testing Requirements
- [ ] Unit tests for config manager
- [ ] Unit tests for environment manager
- [ ] Unit tests for safety guard
- [ ] Integration tests for mode switching
- [ ] Tests for configuration validation
- [ ] Tests for environment detection
- [ ] Tests for safety confirmations

## Safety Checklist for Live Trading
- [ ] Configuration validated
- [ ] Correct IB application (TWS/Gateway) running
- [ ] Connected to correct port (7496/4001 for live)
- [ ] Account type verified (not paper account)
- [ ] Risk limits configured
- [ ] Stop-loss mechanisms in place
- [ ] Logging enabled
- [ ] Monitoring active
- [ ] User confirmed live mode
- [ ] Environment is production

## UI Indicators
- **Paper Mode**: 
  - Green banner: "PAPER TRADING MODE - No Real Money"
  - Green accents in UI
  - "PAPER" badge on all order buttons
  
- **Live Mode**:
  - Red banner: "⚠️ LIVE TRADING MODE - REAL MONEY AT RISK"
  - Red accents in UI
  - "LIVE" badge on all order buttons
  - Confirmation dialog for every order

## Related Files
- `copilot_quant/brokers/interactive_brokers.py` - Current implementation
- `copilot_quant/config/trading_config.py` - New module (to create)
- `copilot_quant/config/environment.py` - New module (to create)
- `copilot_quant/config/safety.py` - New module (to create)
- `config.yaml` - Configuration file (to create)
- `.env.example` - Environment template (update)
- `tests/test_config/` - Tests (to create)

## Dependencies
- pyyaml (for config file)
- python-dotenv (for .env files)
- Issue #02 (Connection Management) - Required

## Notes
- Current implementation uses basic boolean flag and environment variables
- Need structured configuration system
- Safety is paramount - prevent accidental live trading
- Consider hardware token or 2FA for live mode activation
- Configuration should be version controlled (except secrets)
- Secrets should never be in config files

## Configuration Priority
1. Command-line arguments (if applicable)
2. Environment variables
3. Configuration file
4. Default values

## References
- Python dotenv: https://github.com/theskumar/python-dotenv
- PyYAML: https://pyyaml.org/
