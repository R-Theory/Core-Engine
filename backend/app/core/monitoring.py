"""
Monitoring and observability setup for Core Engine.
Includes Prometheus metrics, structured logging, and health checks.
"""

import time
import logging
from typing import Dict, Any
from functools import wraps
import psutil
import asyncio
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import json


# Prometheus Metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active connections'
)

DATABASE_CONNECTIONS = Gauge(
    'database_connections_active',
    'Number of active database connections'
)

CELERY_TASKS = Counter(
    'celery_tasks_total',
    'Total Celery tasks',
    ['task_name', 'status']
)

SYSTEM_CPU_USAGE = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage'
)

SYSTEM_MEMORY_USAGE = Gauge(
    'system_memory_usage_bytes',
    'System memory usage in bytes'
)

SYSTEM_DISK_USAGE = Gauge(
    'system_disk_usage_bytes',
    'System disk usage in bytes'
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics for HTTP requests."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Increment active connections
        ACTIVE_CONNECTIONS.inc()

        try:
            response = await call_next(request)

            # Record metrics
            duration = time.time() - start_time
            endpoint = request.url.path
            method = request.method
            status_code = response.status_code

            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()

            REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)

            return response

        finally:
            # Decrement active connections
            ACTIVE_CONNECTIONS.dec()


class StructuredLogger:
    """Structured JSON logger for better log aggregation."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def log(self, level: str, message: str, **kwargs):
        """Log structured data as JSON."""
        log_data = {
            "timestamp": time.time(),
            "level": level,
            "message": message,
            "service": "core-engine",
            **kwargs
        }

        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(json.dumps(log_data))

    def info(self, message: str, **kwargs):
        self.log("INFO", message, **kwargs)

    def error(self, message: str, **kwargs):
        self.log("ERROR", message, **kwargs)

    def warning(self, message: str, **kwargs):
        self.log("WARNING", message, **kwargs)

    def debug(self, message: str, **kwargs):
        self.log("DEBUG", message, **kwargs)


def monitor_function(func_name: str = None):
    """Decorator to monitor function execution time and errors."""
    def decorator(func):
        name = func_name or f"{func.__module__}.{func.__name__}"

        execution_time = Histogram(
            f'function_execution_seconds',
            'Function execution time in seconds',
            ['function_name']
        )

        execution_count = Counter(
            f'function_executions_total',
            'Total function executions',
            ['function_name', 'status']
        )

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_count.labels(function_name=name, status='success').inc()
                return result
            except Exception as e:
                execution_count.labels(function_name=name, status='error').inc()
                raise
            finally:
                duration = time.time() - start_time
                execution_time.labels(function_name=name).observe(duration)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_count.labels(function_name=name, status='success').inc()
                return result
            except Exception as e:
                execution_count.labels(function_name=name, status='error').inc()
                raise
            finally:
                duration = time.time() - start_time
                execution_time.labels(function_name=name).observe(duration)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


async def update_system_metrics():
    """Update system metrics periodically."""
    while True:
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            SYSTEM_CPU_USAGE.set(cpu_percent)

            # Memory usage
            memory = psutil.virtual_memory()
            SYSTEM_MEMORY_USAGE.set(memory.used)

            # Disk usage
            disk = psutil.disk_usage('/')
            SYSTEM_DISK_USAGE.set(disk.used)

        except Exception as e:
            logger.error("Failed to update system metrics", error=str(e))

        await asyncio.sleep(30)  # Update every 30 seconds


def get_health_status() -> Dict[str, Any]:
    """Get comprehensive health status."""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Calculate health score based on resource usage
        health_score = 100
        if cpu_percent > 80:
            health_score -= 20
        if memory.percent > 80:
            health_score -= 20
        if disk.percent > 90:
            health_score -= 30

        status = "healthy"
        if health_score < 70:
            status = "degraded"
        if health_score < 50:
            status = "unhealthy"

        return {
            "status": status,
            "health_score": health_score,
            "timestamp": time.time(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "load_average": psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else None,
            },
            "service": "core-engine",
            "version": "1.0.0",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "health_score": 0,
            "timestamp": time.time(),
            "error": str(e),
            "service": "core-engine",
            "version": "1.0.0",
        }


def setup_monitoring():
    """Initialize monitoring setup."""
    # Start system metrics collection
    asyncio.create_task(update_system_metrics())

    logger.info("Monitoring system initialized")


# Global logger instance
logger = StructuredLogger(__name__)


# Metrics endpoint handler
async def metrics_handler(request: Request) -> Response:
    """Prometheus metrics endpoint."""
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# Health endpoint handler
async def health_handler(request: Request) -> Dict[str, Any]:
    """Health check endpoint with detailed status."""
    return get_health_status()