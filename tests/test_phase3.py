"""
Basic integration tests for Phase 3 components.

Tests analytics, API, and monitoring modules.
"""

import pytest


class TestAnalyticsModules:
    """Test analytics modules"""

    def test_performance_engine_init(self):
        """Test PerformanceEngine initialization"""
        from copilot_quant.analytics.performance_engine import PerformanceEngine
        from copilot_quant.brokers.trade_database import TradeDatabase

        db = TradeDatabase("sqlite:///:memory:")
        engine = PerformanceEngine(db, initial_capital=100000.0)

        assert engine.initial_capital == 100000.0
        assert engine.risk_free_rate == 0.02

    def test_attribution_analyzer_init(self):
        """Test AttributionAnalyzer initialization"""
        from copilot_quant.analytics.attribution import AttributionAnalyzer
        from copilot_quant.brokers.trade_database import TradeDatabase

        db = TradeDatabase("sqlite:///:memory:")
        analyzer = AttributionAnalyzer(db)

        assert analyzer.trade_db is not None

    def test_benchmark_comparator_init(self):
        """Test BenchmarkComparator initialization"""
        from copilot_quant.analytics.benchmarks import BenchmarkComparator

        comparator = BenchmarkComparator()

        assert "SPY" in comparator.SUPPORTED_BENCHMARKS
        assert "QQQ" in comparator.SUPPORTED_BENCHMARKS


class TestMonitoringModules:
    """Test monitoring modules"""

    def test_structured_logger(self, tmp_path):
        """Test StructuredLogger"""
        from copilot_quant.monitoring.structured_logger import StructuredLogger

        log_file = tmp_path / "test.log"
        logger = StructuredLogger("test_logger", log_file=log_file, json_format=True)

        logger.info("Test message", test_field="test_value")

        assert log_file.exists()

    def test_metrics_exporter(self):
        """Test MetricsExporter"""
        from copilot_quant.monitoring.metrics_exporter import MetricsExporter

        exporter = MetricsExporter(namespace="test")

        # Test counter
        exporter.increment_counter("test_counter", value=1.0)

        # Test gauge
        exporter.set_gauge("test_gauge", value=42.0)

        # Test histogram
        exporter.observe_histogram("test_histogram", value=0.5)

        # Export metrics
        metrics_text = exporter.export_metrics()

        assert "test_test_counter" in metrics_text
        assert "test_test_gauge" in metrics_text

    def test_health_monitor(self):
        """Test HealthMonitor"""
        from copilot_quant.monitoring.health_monitor import HealthMonitor

        monitor = HealthMonitor()

        # Get health status
        status = monitor.get_health_status()

        assert "overall_status" in status
        assert "uptime_seconds" in status
        assert "checks" in status
        assert "system_resources" in status["checks"]


class TestAPIEndpoints:
    """Test API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi.testclient import TestClient

        from copilot_quant.api import create_app

        app = create_app(require_auth=False)
        return TestClient(app)

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Copilot Quant API"
        assert data["version"] == "1.0.0"

    def test_health_endpoint(self, client):
        """Test health endpoint"""
        response = client.get("/health/")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data

    def test_detailed_health_endpoint(self, client):
        """Test detailed health endpoint"""
        response = client.get("/health/detailed")

        assert response.status_code == 200
        data = response.json()
        assert "overall_status" in data
        assert "uptime_seconds" in data
        assert "checks" in data

    def test_portfolio_endpoint(self, client):
        """Test portfolio endpoint"""
        response = client.get("/api/v1/portfolio/")

        assert response.status_code == 200
        data = response.json()
        assert "portfolio_value" in data
        assert "cash" in data
        assert "positions_value" in data

    def test_positions_endpoint(self, client):
        """Test positions endpoint"""
        response = client.get("/api/v1/positions/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_performance_endpoint(self, client):
        """Test performance endpoint"""
        response = client.get("/api/v1/performance/")

        assert response.status_code == 200
        data = response.json()
        assert "total_pnl" in data
        assert "sharpe_ratio" in data
        assert "win_rate" in data

    def test_metrics_json_endpoint(self, client):
        """Test metrics JSON endpoint"""
        response = client.get("/metrics/json")

        assert response.status_code == 200
        data = response.json()
        assert "counters" in data
        assert "gauges" in data
        assert "timestamp" in data


class TestAPIAuth:
    """Test API authentication"""

    def test_api_key_manager(self):
        """Test API key generation and validation"""
        from copilot_quant.api.auth import APIKeyManager

        manager = APIKeyManager()

        # Generate key
        api_key = manager.generate_key("test_app", expiry_days=30)

        assert api_key is not None
        assert len(api_key) > 0

        # Validate key
        assert manager.validate_key(api_key) is True

        # Invalid key
        assert manager.validate_key("invalid_key") is False

        # Revoke key
        assert manager.revoke_key(api_key) is True
        assert manager.validate_key(api_key) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
