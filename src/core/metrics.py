"""
Metrics collection and monitoring for API predictions.

Tracks:
- Request latency
- Cache hits/misses
- Prediction confidence ranges
- Error rates by type
"""

import time
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class PredictionMetrics:
    """Metrics for a single prediction request."""
    request_id: str
    country: str
    horizon_hours: int
    latency_ms: float
    cache_hit: bool
    model_available: bool
    status: str  # "success", "validation_error", "api_error", etc.
    timestamp: datetime
    confidence_min: Optional[float] = None  # Min confidence level requested
    confidence_max: Optional[float] = None  # Max confidence level requested
    error_message: Optional[str] = None


class MetricsCollector:
    """
    In-memory metrics collection for monitoring API health.
    
    Tracks last N requests and provides aggregated statistics.
    """
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize metrics collector.
        
        Args:
            max_history: Maximum number of requests to keep in memory
        """
        self.max_history = max_history
        self.metrics: deque = deque(maxlen=max_history)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.started_at = datetime.utcnow()
    
    def record(self, metrics: PredictionMetrics):
        """Record metrics for a prediction request."""
        self.metrics.append(metrics)
        
        # Track errors by type
        if metrics.status != "success":
            self.error_counts[metrics.status] += 1
    
    def get_stats(self, minutes: int = 60) -> Dict:
        """
        Get aggregated metrics for the last N minutes.
        
        Args:
            minutes: Time window in minutes (default: 60)
            
        Returns:
            Dictionary with aggregated statistics
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        recent = [m for m in self.metrics if m.timestamp >= cutoff_time]
        
        if not recent:
            return {
                "total_requests": 0,
                "success_rate": 0.0,
                "avg_latency_ms": 0,
                "cache_hit_rate": 0.0,
                "errors_by_type": {}
            }
        
        successful = [m for m in recent if m.status == "success"]
        cache_hits = [m for m in recent if m.cache_hit]
        
        stats = {
            "total_requests": len(recent),
            "successful_requests": len(successful),
            "success_rate": len(successful) / len(recent) * 100 if recent else 0,
            "avg_latency_ms": sum(m.latency_ms for m in recent) / len(recent),
            "min_latency_ms": min(m.latency_ms for m in recent),
            "max_latency_ms": max(m.latency_ms for m in recent),
            "cache_hit_rate": len(cache_hits) / len(recent) * 100 if recent else 0,
            "errors_by_type": dict(self.error_counts),
            "time_window_minutes": minutes,
            "requests_by_country": self._count_by_field(recent, "country"),
            "requests_by_horizon": self._aggregate_horizon(recent)
        }
        
        return stats
    
    def get_health_status(self) -> Dict:
        """Get overall API health status."""
        stats_1h = self.get_stats(minutes=60)
        stats_24h = self.get_stats(minutes=1440)
        
        # Determine health status based on error rate
        success_rate = stats_1h.get("success_rate", 0)
        if success_rate >= 99:
            health = "healthy"
        elif success_rate >= 95:
            health = "degraded"
        else:
            health = "unhealthy"
        
        return {
            "status": health,
            "uptime_seconds": (datetime.utcnow() - self.started_at).total_seconds(),
            "success_rate_1h": success_rate,
            "success_rate_24h": stats_24h.get("success_rate", 0),
            "avg_latency_ms_1h": stats_1h.get("avg_latency_ms", 0),
            "total_requests_1h": stats_1h.get("total_requests", 0),
            "total_requests_24h": stats_24h.get("total_requests", 0),
            "cache_hit_rate": stats_1h.get("cache_hit_rate", 0)
        }
    
    def get_top_errors(self, limit: int = 5) -> List[tuple]:
        """Get most common error types."""
        return sorted(
            self.error_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
    
    def reset(self):
        """Clear all metrics."""
        self.metrics.clear()
        self.error_counts.clear()
        self.started_at = datetime.utcnow()
    
    @staticmethod
    def _count_by_field(metrics: List[PredictionMetrics], field: str) -> Dict[str, int]:
        """Count metrics by a specific field."""
        counts = defaultdict(int)
        for m in metrics:
            value = getattr(m, field, None)
            if value:
                counts[value] += 1
        return dict(counts)
    
    @staticmethod
    def _aggregate_horizon(metrics: List[PredictionMetrics]) -> Dict[str, int]:
        """Aggregate horizon requests into buckets."""
        buckets = {
            "1-24h": 0,
            "25-72h": 0,
            "73-168h": 0
        }
        for m in metrics:
            if m.horizon_hours <= 24:
                buckets["1-24h"] += 1
            elif m.horizon_hours <= 72:
                buckets["25-72h"] += 1
            else:
                buckets["73-168h"] += 1
        return buckets


# Global metrics instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create the global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
