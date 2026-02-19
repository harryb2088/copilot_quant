"""
System Health Monitor

Monitors system health including connections, data freshness,
and resource usage.
"""

import logging
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheck:
    """Individual health check result"""
    name: str
    status: HealthStatus
    message: str
    timestamp: datetime
    metadata: Dict[str, Any]


class HealthMonitor:
    """
    Monitor system health and status.
    
    Tracks various health indicators including:
    - System resources (CPU, memory, disk)
    - Connection status (IBKR, database)
    - Data freshness
    - Application uptime
    
    Example:
        >>> monitor = HealthMonitor()
        >>> monitor.register_check('database', check_database_connection)
        >>> status = monitor.get_health_status()
        >>> print(status['overall_status'])
    """
    
    def __init__(self):
        """Initialize health monitor"""
        self._checks: Dict[str, callable] = {}
        self._last_results: Dict[str, HealthCheck] = {}
        self._start_time = datetime.now()
        
        # Register default checks
        self.register_check('system_resources', self._check_system_resources)
        
        logger.info("HealthMonitor initialized")
    
    def register_check(self, name: str, check_func: callable):
        """
        Register a health check.
        
        Args:
            name: Check name
            check_func: Function that returns HealthCheck
        """
        self._checks[name] = check_func
        logger.info(f"Registered health check: {name}")
    
    def run_checks(self) -> Dict[str, HealthCheck]:
        """
        Run all registered health checks.
        
        Returns:
            Dict of check results
        """
        results = {}
        
        for name, check_func in self._checks.items():
            try:
                result = check_func()
                results[name] = result
                self._last_results[name] = result
            except Exception as e:
                logger.error(f"Health check '{name}' failed: {e}")
                results[name] = HealthCheck(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Check failed: {str(e)}",
                    timestamp=datetime.now(),
                    metadata={}
                )
        
        return results
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get comprehensive health status.
        
        Returns:
            Health status summary
        """
        checks = self.run_checks()
        
        # Determine overall status
        statuses = [check.status for check in checks.values()]
        
        if all(s == HealthStatus.HEALTHY for s in statuses):
            overall_status = HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall_status = HealthStatus.UNHEALTHY
        else:
            overall_status = HealthStatus.DEGRADED
        
        # Calculate uptime
        uptime = datetime.now() - self._start_time
        
        return {
            'overall_status': overall_status.value,
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': int(uptime.total_seconds()),
            'uptime_formatted': str(uptime).split('.')[0],
            'checks': {
                name: {
                    'status': check.status.value,
                    'message': check.message,
                    'timestamp': check.timestamp.isoformat(),
                    'metadata': check.metadata
                }
                for name, check in checks.items()
            }
        }
    
    def _check_system_resources(self) -> HealthCheck:
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine status based on thresholds
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
                status = HealthStatus.UNHEALTHY
                message = "System resources critically high"
            elif cpu_percent > 75 or memory.percent > 75 or disk.percent > 80:
                status = HealthStatus.DEGRADED
                message = "System resources elevated"
            else:
                status = HealthStatus.HEALTHY
                message = "System resources normal"
            
            return HealthCheck(
                name='system_resources',
                status=status,
                message=message,
                timestamp=datetime.now(),
                metadata={
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_mb': memory.available / (1024 * 1024),
                    'disk_percent': disk.percent,
                    'disk_free_gb': disk.free / (1024 * 1024 * 1024)
                }
            )
        except Exception as e:
            logger.error(f"Failed to check system resources: {e}")
            return HealthCheck(
                name='system_resources',
                status=HealthStatus.UNHEALTHY,
                message=f"Resource check failed: {str(e)}",
                timestamp=datetime.now(),
                metadata={}
            )
    
    def check_connection(
        self,
        name: str,
        is_connected: bool,
        last_activity: Optional[datetime] = None,
        timeout_minutes: int = 5
    ) -> HealthCheck:
        """
        Check connection health.
        
        Args:
            name: Connection name
            is_connected: Whether connection is active
            last_activity: Last activity timestamp
            timeout_minutes: Timeout threshold in minutes
            
        Returns:
            HealthCheck result
        """
        if not is_connected:
            return HealthCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"{name} disconnected",
                timestamp=datetime.now(),
                metadata={'connected': False}
            )
        
        # Check staleness
        if last_activity:
            time_since_activity = datetime.now() - last_activity
            
            if time_since_activity > timedelta(minutes=timeout_minutes):
                return HealthCheck(
                    name=name,
                    status=HealthStatus.DEGRADED,
                    message=f"{name} connection stale",
                    timestamp=datetime.now(),
                    metadata={
                        'connected': True,
                        'last_activity': last_activity.isoformat(),
                        'minutes_since_activity': time_since_activity.total_seconds() / 60
                    }
                )
        
        return HealthCheck(
            name=name,
            status=HealthStatus.HEALTHY,
            message=f"{name} connected",
            timestamp=datetime.now(),
            metadata={
                'connected': True,
                'last_activity': last_activity.isoformat() if last_activity else None
            }
        )
    
    def check_data_freshness(
        self,
        name: str,
        last_update: Optional[datetime],
        max_age_minutes: int = 15
    ) -> HealthCheck:
        """
        Check data freshness.
        
        Args:
            name: Data source name
            last_update: Last update timestamp
            max_age_minutes: Maximum acceptable age in minutes
            
        Returns:
            HealthCheck result
        """
        if not last_update:
            return HealthCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"{name} data never updated",
                timestamp=datetime.now(),
                metadata={'last_update': None}
            )
        
        age = datetime.now() - last_update
        age_minutes = age.total_seconds() / 60
        
        if age_minutes > max_age_minutes * 2:
            status = HealthStatus.UNHEALTHY
            message = f"{name} data critically stale"
        elif age_minutes > max_age_minutes:
            status = HealthStatus.DEGRADED
            message = f"{name} data stale"
        else:
            status = HealthStatus.HEALTHY
            message = f"{name} data fresh"
        
        return HealthCheck(
            name=name,
            status=status,
            message=message,
            timestamp=datetime.now(),
            metadata={
                'last_update': last_update.isoformat(),
                'age_minutes': age_minutes,
                'max_age_minutes': max_age_minutes
            }
        )


# Global health monitor instance
_health_monitor: Optional[HealthMonitor] = None


def get_health_monitor() -> HealthMonitor:
    """Get the global health monitor instance"""
    global _health_monitor
    
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    
    return _health_monitor
