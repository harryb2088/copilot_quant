"""
Prometheus/OpenMetrics Exporter

Exports system and application metrics in Prometheus format.
"""

import logging
from collections import defaultdict
from datetime import datetime
from threading import Lock
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class MetricsExporter:
    """
    Export metrics in Prometheus/OpenMetrics format.

    Tracks counters, gauges, histograms, and summaries for monitoring
    system performance and health.

    Example:
        >>> exporter = MetricsExporter()
        >>> exporter.increment_counter('orders_processed', labels={'status': 'filled'})
        >>> exporter.set_gauge('portfolio_value', 1000000.0)
        >>> metrics_text = exporter.export_metrics()
    """

    def __init__(self, namespace: str = "copilot_quant"):
        """
        Initialize metrics exporter.

        Args:
            namespace: Metrics namespace prefix
        """
        self.namespace = namespace

        # Metrics storage
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, list] = defaultdict(list)

        # Thread safety
        self._lock = Lock()

        # Metadata
        self._metric_help: Dict[str, str] = {}
        self._metric_type: Dict[str, str] = {}

        logger.info(f"MetricsExporter initialized with namespace: {namespace}")

    def increment_counter(
        self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None, help_text: str = ""
    ):
        """
        Increment a counter metric.

        Args:
            name: Metric name
            value: Increment value (default: 1.0)
            labels: Optional metric labels
            help_text: Help text for the metric
        """
        with self._lock:
            metric_key = self._make_key(name, labels)
            self._counters[metric_key] += value

            if name not in self._metric_type:
                self._metric_type[name] = "counter"
                self._metric_help[name] = help_text or f"{name} counter"

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None, help_text: str = ""):
        """
        Set a gauge metric.

        Args:
            name: Metric name
            value: Gauge value
            labels: Optional metric labels
            help_text: Help text for the metric
        """
        with self._lock:
            metric_key = self._make_key(name, labels)
            self._gauges[metric_key] = value

            if name not in self._metric_type:
                self._metric_type[name] = "gauge"
                self._metric_help[name] = help_text or f"{name} gauge"

    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None, help_text: str = ""):
        """
        Observe a value for a histogram metric.

        Args:
            name: Metric name
            value: Observed value
            labels: Optional metric labels
            help_text: Help text for the metric
        """
        with self._lock:
            metric_key = self._make_key(name, labels)
            self._histograms[metric_key].append(value)

            if name not in self._metric_type:
                self._metric_type[name] = "histogram"
                self._metric_help[name] = help_text or f"{name} histogram"

    def export_metrics(self) -> str:
        """
        Export all metrics in Prometheus text format.

        Returns:
            Metrics in Prometheus format
        """
        with self._lock:
            lines = []

            # Export counters
            for name in set(k.split("{")[0] for k in self._counters.keys()):
                if self._metric_type.get(name) == "counter":
                    lines.append(f"# HELP {self.namespace}_{name} {self._metric_help.get(name, '')}")
                    lines.append(f"# TYPE {self.namespace}_{name} counter")

                    for key, value in self._counters.items():
                        if key.startswith(name):
                            lines.append(f"{self.namespace}_{key} {value}")

            # Export gauges
            for name in set(k.split("{")[0] for k in self._gauges.keys()):
                if self._metric_type.get(name) == "gauge":
                    lines.append(f"# HELP {self.namespace}_{name} {self._metric_help.get(name, '')}")
                    lines.append(f"# TYPE {self.namespace}_{name} gauge")

                    for key, value in self._gauges.items():
                        if key.startswith(name):
                            lines.append(f"{self.namespace}_{key} {value}")

            # Export histograms (simplified - just count, sum, and buckets)
            for name in set(k.split("{")[0] for k in self._histograms.keys()):
                if self._metric_type.get(name) == "histogram":
                    lines.append(f"# HELP {self.namespace}_{name} {self._metric_help.get(name, '')}")
                    lines.append(f"# TYPE {self.namespace}_{name} histogram")

                    for key, values in self._histograms.items():
                        if key.startswith(name):
                            if values:
                                count = len(values)
                                total = sum(values)

                                # Buckets
                                buckets = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
                                for bucket in buckets:
                                    bucket_count = sum(1 for v in values if v <= bucket)
                                    bucket_key = (
                                        key.replace("}", f',le="{bucket}"}}')
                                        if "{" in key
                                        else f'{key}{{le="{bucket}"}}'
                                    )
                                    lines.append(f"{self.namespace}_{bucket_key} {bucket_count}")

                                # +Inf bucket
                                inf_key = key.replace("}", ',le="+Inf"}') if "{" in key else f'{key}{{le="+Inf"}}'
                                lines.append(f"{self.namespace}_{inf_key} {count}")

                                # Sum and count
                                lines.append(f"{self.namespace}_{key.replace('}', '_sum}')} {total}")
                                lines.append(f"{self.namespace}_{key.replace('}', '_count}')} {count}")

            return "\n".join(lines) + "\n"

    def get_metrics_dict(self) -> Dict[str, Any]:
        """
        Get metrics as a dictionary.

        Returns:
            Dictionary with all metrics
        """
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {
                    k: {
                        "count": len(v),
                        "sum": sum(v),
                        "min": min(v) if v else 0,
                        "max": max(v) if v else 0,
                        "mean": sum(v) / len(v) if v else 0,
                    }
                    for k, v in self._histograms.items()
                },
                "timestamp": datetime.now().isoformat(),
            }

    def reset_metrics(self):
        """Reset all metrics to initial state"""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            logger.info("Metrics reset")

    def _make_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """
        Create metric key with labels.

        Args:
            name: Metric name
            labels: Optional labels

        Returns:
            Formatted metric key
        """
        if not labels:
            return name

        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"


# Global metrics exporter instance
_metrics_exporter: Optional[MetricsExporter] = None


def get_metrics_exporter() -> MetricsExporter:
    """Get the global metrics exporter instance"""
    global _metrics_exporter

    if _metrics_exporter is None:
        _metrics_exporter = MetricsExporter()

    return _metrics_exporter


# Convenience functions
def increment_counter(name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
    """Increment a counter metric"""
    get_metrics_exporter().increment_counter(name, value, labels)


def set_gauge(name: str, value: float, labels: Optional[Dict[str, str]] = None):
    """Set a gauge metric"""
    get_metrics_exporter().set_gauge(name, value, labels)


def observe_histogram(name: str, value: float, labels: Optional[Dict[str, str]] = None):
    """Observe a histogram value"""
    get_metrics_exporter().observe_histogram(name, value, labels)
