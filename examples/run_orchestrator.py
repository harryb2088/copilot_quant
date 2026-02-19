"""
Example: Running the Trading Orchestrator

This script demonstrates how to set up and run the trading orchestrator
with notifications and proper configuration.
"""

import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('orchestrator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Run the trading orchestrator"""
    
    # Import orchestrator components
    from copilot_quant.orchestrator import TradingOrchestrator
    
    # Path to configuration file
    config_path = "config.paper.yaml"
    
    # Check if config exists
    if not Path(config_path).exists():
        logger.error(f"Configuration file not found: {config_path}")
        logger.info("Please create a configuration file. See config.paper.yaml for an example.")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("Starting Trading Orchestrator")
    logger.info("=" * 60)
    logger.info(f"Configuration: {config_path}")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)
    
    try:
        # Create orchestrator
        orchestrator = TradingOrchestrator(
            config_path=config_path,
            heartbeat_interval=300,  # 5 minutes
            health_check_interval=60,  # 1 minute
            max_restart_attempts=3,
            restart_cooldown=300  # 5 minutes
        )
        
        # Optional: Register state change callback
        def on_state_change(new_state):
            logger.info(f"Orchestrator state changed to: {new_state.value}")
        
        orchestrator.register_state_change_callback(on_state_change)
        
        # Start orchestrator (blocks until stopped)
        orchestrator.start()
        
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
        orchestrator.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    
    logger.info("Orchestrator stopped successfully")


if __name__ == "__main__":
    main()
