"""
Trading Orchestrator Module

Main daemon service for managing the trading lifecycle.

Features:
- Automatic start/stop based on market hours
- State machine (PRE_MARKET, TRADING, POST_MARKET, CLOSED)
- Health monitoring and heartbeat logging
- Auto-restart on error/deadlock
- Integration with live engine
"""

import logging
import signal
import sys
import threading
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Callable

from copilot_quant.orchestrator.market_calendar import MarketCalendar, MarketState
from copilot_quant.orchestrator.config_manager import ConfigManager, TradingConfig
from copilot_quant.orchestrator.notifiers.base import Notifier, NotificationMessage, AlertLevel

logger = logging.getLogger(__name__)


class OrchestratorState(Enum):
    """Orchestrator state"""
    STOPPED = "stopped"
    PRE_MARKET = "pre_market"
    TRADING = "trading"
    POST_MARKET = "post_market"
    ERROR = "error"


class TradingOrchestrator:
    """
    Trading orchestrator daemon.
    
    Manages the entire trading lifecycle based on market hours:
    - Starts trading engine when market opens
    - Stops trading engine when market closes
    - Monitors health and restarts on errors
    - Sends heartbeat notifications
    - Manages state transitions
    
    Example:
        >>> orchestrator = TradingOrchestrator("config.paper.yaml")
        >>> orchestrator.start()
        >>> # Runs until stopped or interrupted
    """
    
    def __init__(
        self,
        config_path: str,
        heartbeat_interval: int = 300,  # 5 minutes
        health_check_interval: int = 60,  # 1 minute
        max_restart_attempts: int = 3,
        restart_cooldown: int = 300  # 5 minutes between restart attempts
    ):
        """
        Initialize trading orchestrator.
        
        Args:
            config_path: Path to configuration file
            heartbeat_interval: Seconds between heartbeat logs/notifications
            health_check_interval: Seconds between health checks
            max_restart_attempts: Maximum auto-restart attempts
            restart_cooldown: Seconds to wait between restart attempts
        """
        # Load configuration
        self.config_manager = ConfigManager(config_path)
        self.config: TradingConfig = self.config_manager.load()
        
        # Initialize market calendar
        self.market_calendar = MarketCalendar(
            timezone=self.config.schedule.timezone
        )
        
        # State management
        self.state = OrchestratorState.STOPPED
        self._state_lock = threading.Lock()
        self._running = False
        self._stop_event = threading.Event()
        
        # Trading engine (will be initialized when needed)
        self._trading_engine = None
        self._engine_lock = threading.Lock()
        
        # Health monitoring
        self.heartbeat_interval = heartbeat_interval
        self.health_check_interval = health_check_interval
        self.max_restart_attempts = max_restart_attempts
        self.restart_cooldown = restart_cooldown
        
        self._last_heartbeat = datetime.now()
        self._last_health_check = datetime.now()
        self._start_time: Optional[datetime] = None
        self._restart_attempts = 0
        self._last_restart_time: Optional[datetime] = None
        
        # Notifiers
        self._notifiers: List[Notifier] = []
        self._setup_notifiers()
        
        # Callbacks
        self._state_change_callbacks: List[Callable[[OrchestratorState], None]] = []
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"TradingOrchestrator initialized with config: {config_path}")
    
    def _setup_notifiers(self) -> None:
        """Setup notification channels from configuration"""
        if not self.config.notifications.enabled:
            logger.info("Notifications disabled in configuration")
            return
        
        from copilot_quant.orchestrator.notifiers import (
            SlackNotifier,
            DiscordNotifier,
            EmailNotifier,
            WebhookNotifier,
            AlertLevel
        )
        
        # Parse minimum alert level
        min_level_map = {
            "info": AlertLevel.INFO,
            "warning": AlertLevel.WARNING,
            "critical": AlertLevel.CRITICAL,
        }
        min_level = AlertLevel.WARNING  # Default
        if self.config.notifications.alert_levels:
            first_level = self.config.notifications.alert_levels[0].lower()
            min_level = min_level_map.get(first_level, AlertLevel.WARNING)
        
        # Setup Slack
        if "slack" in self.config.notifications.channels:
            if self.config.notifications.slack_webhook_url:
                self._notifiers.append(
                    SlackNotifier(
                        webhook_url=self.config.notifications.slack_webhook_url,
                        channel=self.config.notifications.slack_channel,
                        min_level=min_level
                    )
                )
                logger.info("Slack notifier configured")
        
        # Setup Discord
        if "discord" in self.config.notifications.channels:
            if self.config.notifications.discord_webhook_url:
                self._notifiers.append(
                    DiscordNotifier(
                        webhook_url=self.config.notifications.discord_webhook_url,
                        min_level=min_level
                    )
                )
                logger.info("Discord notifier configured")
        
        # Setup Email
        if "email" in self.config.notifications.channels:
            if (self.config.notifications.smtp_host and 
                self.config.notifications.smtp_username and
                self.config.notifications.email_to):
                self._notifiers.append(
                    EmailNotifier(
                        smtp_host=self.config.notifications.smtp_host,
                        smtp_port=self.config.notifications.smtp_port,
                        username=self.config.notifications.smtp_username,
                        password=self.config.notifications.smtp_password or "",
                        from_email=self.config.notifications.email_from or self.config.notifications.smtp_username,
                        to_emails=self.config.notifications.email_to,
                        min_level=min_level
                    )
                )
                logger.info("Email notifier configured")
        
        # Setup Webhook
        if "webhook" in self.config.notifications.channels:
            if self.config.notifications.webhook_url:
                self._notifiers.append(
                    WebhookNotifier(
                        webhook_url=self.config.notifications.webhook_url,
                        headers=self.config.notifications.webhook_headers,
                        min_level=min_level
                    )
                )
                logger.info("Webhook notifier configured")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.stop()
        sys.exit(0)
    
    def add_notifier(self, notifier: Notifier) -> None:
        """Add a custom notifier"""
        self._notifiers.append(notifier)
    
    def register_state_change_callback(self, callback: Callable[[OrchestratorState], None]) -> None:
        """Register a callback for state changes"""
        self._state_change_callbacks.append(callback)
    
    def _notify(self, message: NotificationMessage) -> None:
        """Send notification to all configured channels"""
        for notifier in self._notifiers:
            try:
                notifier.notify(message)
            except Exception as e:
                logger.error(f"Notifier {notifier.__class__.__name__} failed: {e}")
    
    def _set_state(self, new_state: OrchestratorState) -> None:
        """
        Set orchestrator state and notify callbacks.
        
        Args:
            new_state: New state to transition to
        """
        with self._state_lock:
            old_state = self.state
            if old_state == new_state:
                return
            
            self.state = new_state
            logger.info(f"State transition: {old_state.value} -> {new_state.value}")
            
            # Notify callbacks
            for callback in self._state_change_callbacks:
                try:
                    callback(new_state)
                except Exception as e:
                    logger.error(f"State change callback failed: {e}")
            
            # Send notification for important state changes
            if new_state in [OrchestratorState.TRADING, OrchestratorState.ERROR]:
                level = AlertLevel.INFO if new_state == OrchestratorState.TRADING else AlertLevel.CRITICAL
                self._notify(NotificationMessage(
                    title=f"Orchestrator State: {new_state.value.upper()}",
                    message=f"Trading orchestrator transitioned to {new_state.value} state",
                    level=level,
                    metadata={"previous_state": old_state.value}
                ))
    
    def start(self) -> None:
        """
        Start the trading orchestrator daemon.
        
        This will run indefinitely until stop() is called or interrupted.
        """
        if self._running:
            logger.warning("Orchestrator is already running")
            return
        
        self._running = True
        self._stop_event.clear()
        self._start_time = datetime.now()
        
        logger.info("Starting Trading Orchestrator...")
        self._notify(NotificationMessage(
            title="Orchestrator Started",
            message="Trading orchestrator daemon has started",
            level=AlertLevel.INFO,
            metadata={"mode": self.config.mode}
        ))
        
        # Main orchestrator loop
        try:
            while self._running and not self._stop_event.is_set():
                self._orchestrator_loop()
                time.sleep(1)  # Prevent tight loop
        except Exception as e:
            logger.error(f"Orchestrator encountered fatal error: {e}", exc_info=True)
            self._set_state(OrchestratorState.ERROR)
            self._notify(NotificationMessage(
                title="Orchestrator Fatal Error",
                message=f"Fatal error in orchestrator: {str(e)}",
                level=AlertLevel.CRITICAL
            ))
        finally:
            self._cleanup()
    
    def stop(self) -> None:
        """Stop the trading orchestrator"""
        if not self._running:
            return
        
        logger.info("Stopping Trading Orchestrator...")
        self._running = False
        self._stop_event.set()
        
        # Stop trading engine if running
        self._stop_trading_engine()
        
        self._set_state(OrchestratorState.STOPPED)
        
        self._notify(NotificationMessage(
            title="Orchestrator Stopped",
            message="Trading orchestrator daemon has stopped",
            level=AlertLevel.INFO
        ))
    
    def _orchestrator_loop(self) -> None:
        """Main orchestrator loop iteration"""
        # Get current market state
        market_state = self.market_calendar.get_market_state()
        
        # Map market state to orchestrator state
        if market_state == MarketState.PRE_MARKET:
            target_state = OrchestratorState.PRE_MARKET
        elif market_state == MarketState.TRADING:
            target_state = OrchestratorState.TRADING
        elif market_state == MarketState.POST_MARKET:
            target_state = OrchestratorState.POST_MARKET
        else:  # CLOSED
            target_state = OrchestratorState.STOPPED
        
        # Handle state transitions
        if self.state != target_state and self.state != OrchestratorState.ERROR:
            self._handle_state_transition(target_state)
        
        # Perform periodic tasks
        self._check_heartbeat()
        self._check_health()
    
    def _handle_state_transition(self, target_state: OrchestratorState) -> None:
        """Handle transition to target state"""
        if target_state == OrchestratorState.TRADING:
            if self.config.schedule.auto_start:
                self._start_trading_engine()
                self._set_state(OrchestratorState.TRADING)
        elif target_state in [OrchestratorState.STOPPED, OrchestratorState.POST_MARKET]:
            if self.config.schedule.auto_stop:
                self._stop_trading_engine()
            self._set_state(target_state)
        else:
            self._set_state(target_state)
    
    def _start_trading_engine(self) -> bool:
        """
        Start the trading engine.
        
        Returns:
            True if started successfully
        """
        with self._engine_lock:
            if self._trading_engine is not None:
                logger.warning("Trading engine already running")
                return True
            
            try:
                logger.info("Starting trading engine...")
                
                # Import here to avoid circular dependencies
                from copilot_quant.backtest.live_engine import LiveStrategyEngine
                
                # Create engine instance
                self._trading_engine = LiveStrategyEngine(
                    paper_trading=self.config.broker.paper_trading,
                    host=self.config.broker.host,
                    port=self.config.broker.port,
                    client_id=self.config.broker.client_id,
                    use_gateway=self.config.broker.use_gateway,
                    commission=self.config.broker.commission,
                    slippage=self.config.broker.slippage,
                    update_interval=self.config.data.update_interval,
                    enable_reconnect=self.config.data.enable_reconnect
                )
                
                # Connect to broker
                if not self._trading_engine.connect():
                    raise RuntimeError("Failed to connect to broker")
                
                # Start engine with configured symbols
                if self.config.strategy.symbols:
                    self._trading_engine.start(symbols=self.config.strategy.symbols)
                
                logger.info("Trading engine started successfully")
                self._notify(NotificationMessage(
                    title="Trading Started",
                    message="Trading engine started successfully",
                    level=AlertLevel.INFO,
                    metadata={
                        "symbols": len(self.config.strategy.symbols),
                        "mode": "paper" if self.config.broker.paper_trading else "live"
                    }
                ))
                
                # Reset restart attempts on successful start
                self._restart_attempts = 0
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to start trading engine: {e}", exc_info=True)
                self._trading_engine = None
                self._set_state(OrchestratorState.ERROR)
                
                self._notify(NotificationMessage(
                    title="Trading Engine Start Failed",
                    message=f"Failed to start trading engine: {str(e)}",
                    level=AlertLevel.CRITICAL
                ))
                
                # Attempt restart if within limits
                self._attempt_restart()
                
                return False
    
    def _stop_trading_engine(self) -> None:
        """Stop the trading engine"""
        with self._engine_lock:
            if self._trading_engine is None:
                return
            
            try:
                logger.info("Stopping trading engine...")
                self._trading_engine.stop()
                self._trading_engine.disconnect()
                self._trading_engine = None
                
                logger.info("Trading engine stopped successfully")
                self._notify(NotificationMessage(
                    title="Trading Stopped",
                    message="Trading engine stopped successfully",
                    level=AlertLevel.INFO
                ))
                
            except Exception as e:
                logger.error(f"Error stopping trading engine: {e}", exc_info=True)
                self._trading_engine = None
    
    def _attempt_restart(self) -> None:
        """Attempt to restart the trading engine after error"""
        # Check restart limits
        if self._restart_attempts >= self.max_restart_attempts:
            logger.error(f"Max restart attempts ({self.max_restart_attempts}) reached, giving up")
            self._notify(NotificationMessage(
                title="Restart Limit Reached",
                message=f"Maximum restart attempts ({self.max_restart_attempts}) exceeded",
                level=AlertLevel.CRITICAL
            ))
            return
        
        # Check cooldown period
        if self._last_restart_time:
            time_since_last = (datetime.now() - self._last_restart_time).total_seconds()
            if time_since_last < self.restart_cooldown:
                logger.info(f"Restart cooldown active, waiting {self.restart_cooldown - time_since_last:.0f}s")
                return
        
        # Attempt restart
        self._restart_attempts += 1
        self._last_restart_time = datetime.now()
        
        logger.info(f"Attempting restart {self._restart_attempts}/{self.max_restart_attempts}...")
        self._notify(NotificationMessage(
            title="Restarting Trading Engine",
            message=f"Attempting auto-restart (attempt {self._restart_attempts}/{self.max_restart_attempts})",
            level=AlertLevel.WARNING
        ))
        
        # Wait before restart
        time.sleep(5)
        
        # Try to start
        self._start_trading_engine()
    
    def _check_heartbeat(self) -> None:
        """Check if it's time to send a heartbeat"""
        now = datetime.now()
        if (now - self._last_heartbeat).total_seconds() >= self.heartbeat_interval:
            logger.info(f"Heartbeat: Orchestrator running in {self.state.value} state")
            self._last_heartbeat = now
            
            # Send heartbeat notification for trading state only
            if self.state == OrchestratorState.TRADING and self._start_time:
                uptime_seconds = (now - self._start_time).total_seconds()
                self._notify(NotificationMessage(
                    title="Trading Heartbeat",
                    message=f"Trading orchestrator is active and healthy",
                    level=AlertLevel.INFO,
                    metadata={
                        "state": self.state.value,
                        "uptime": str(timedelta(seconds=int(uptime_seconds)))
                    }
                ))
    
    def _check_health(self) -> None:
        """Perform health checks on the trading engine"""
        now = datetime.now()
        if (now - self._last_health_check).total_seconds() >= self.health_check_interval:
            self._last_health_check = now
            
            # Only check health if trading
            if self.state != OrchestratorState.TRADING:
                return
            
            with self._engine_lock:
                if self._trading_engine is None:
                    logger.warning("Health check: Trading engine is None in TRADING state")
                    self._set_state(OrchestratorState.ERROR)
                    self._attempt_restart()
                    return
                
                # Check if engine is still connected (basic health check)
                # More sophisticated checks can be added here
                try:
                    # This is a placeholder - actual health check depends on engine implementation
                    if hasattr(self._trading_engine, 'is_connected'):
                        if not self._trading_engine.is_connected():
                            logger.warning("Health check: Trading engine disconnected")
                            self._set_state(OrchestratorState.ERROR)
                            self._attempt_restart()
                except Exception as e:
                    logger.error(f"Health check failed: {e}")
                    self._set_state(OrchestratorState.ERROR)
                    self._attempt_restart()
    
    def _cleanup(self) -> None:
        """Cleanup resources"""
        logger.info("Cleaning up orchestrator resources...")
        self._stop_trading_engine()
    
    def get_state(self) -> OrchestratorState:
        """Get current orchestrator state"""
        return self.state
    
    def is_running(self) -> bool:
        """Check if orchestrator is running"""
        return self._running
