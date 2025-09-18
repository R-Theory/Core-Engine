from celery import Celery
from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "core_engine",
    broker=settings.REDIS_URL.replace("/0", "/1"),  # Use different Redis DB for Celery
    backend=settings.REDIS_URL.replace("/0", "/2"),  # Use different Redis DB for results
    include=["app.tasks"]
)

# Optimized Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    result_compression='gzip',

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Task execution
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Worker optimization
    worker_prefetch_multiplier=4,  # Increased for better throughput
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=True,
    worker_enable_remote_control=True,

    # Result backend optimization
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        'master_name': 'mymaster',
        'socket_keepalive': True,
        'socket_keepalive_options': {
            'TCP_KEEPIDLE': 1,
            'TCP_KEEPINTVL': 3,
            'TCP_KEEPCNT': 5,
        },
        'retry_on_timeout': True,
        'health_check_interval': 30,
    },

    # Broker optimization
    broker_transport_options={
        'visibility_timeout': 3600,
        'fanout_prefix': True,
        'fanout_patterns': True,
        'socket_keepalive': True,
        'retry_on_timeout': True,
        'health_check_interval': 30,
    },

    # Task compression
    task_compression='gzip',

    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,

    # Performance
    task_always_eager=False,  # Ensure tasks run asynchronously
    task_store_eager_result=False,
)

# Optimized task routing with priorities
celery_app.conf.task_routes = {
    # High priority queues
    "app.tasks.ai_processing.*": {"queue": "ai_queue", "priority": 9},
    "app.tasks.user_actions.*": {"queue": "user_queue", "priority": 8},

    # Medium priority queues
    "app.tasks.plugin_sync.*": {"queue": "plugin_queue", "priority": 5},
    "app.tasks.workflow_execution.*": {"queue": "workflow_queue", "priority": 5},
    "app.tasks.document_processing.*": {"queue": "document_queue", "priority": 5},

    # Low priority queues
    "app.tasks.maintenance.*": {"queue": "maintenance_queue", "priority": 2},
    "app.tasks.analytics.*": {"queue": "analytics_queue", "priority": 1},
}

# Queue configuration with different concurrency levels
celery_app.conf.task_default_queue = 'default'
celery_app.conf.task_default_routing_key = 'default'

# Priority queue configuration
celery_app.conf.broker_transport_options = {
    'priority_steps': list(range(10)),
    'sep': ':',
    'queue_order_strategy': 'priority',
}

# Optimized periodic tasks with staggered scheduling
celery_app.conf.beat_schedule = {
    # Data synchronization tasks
    "sync-canvas-data": {
        "task": "app.tasks.plugin_sync.sync_all_canvas_data",
        "schedule": 3600.0,  # Every hour
        "options": {"queue": "plugin_queue", "priority": 3}
    },
    "sync-github-data": {
        "task": "app.tasks.plugin_sync.sync_all_github_data",
        "schedule": 7200.0,  # Every 2 hours
        "options": {"queue": "plugin_queue", "priority": 3}
    },

    # Maintenance tasks
    "cleanup-old-tasks": {
        "task": "app.tasks.maintenance.cleanup_old_task_results",
        "schedule": 86400.0,  # Daily
        "options": {"queue": "maintenance_queue", "priority": 1}
    },
    "cleanup-cache": {
        "task": "app.tasks.maintenance.cleanup_expired_cache",
        "schedule": 21600.0,  # Every 6 hours
        "options": {"queue": "maintenance_queue", "priority": 1}
    },
    "database-health-check": {
        "task": "app.tasks.maintenance.database_health_check",
        "schedule": 300.0,  # Every 5 minutes
        "options": {"queue": "maintenance_queue", "priority": 5}
    },

    # Analytics tasks
    "generate-usage-stats": {
        "task": "app.tasks.analytics.generate_daily_usage_stats",
        "schedule": 86400.0,  # Daily at midnight
        "options": {"queue": "analytics_queue", "priority": 1}
    },

    # Performance monitoring
    "monitor-performance": {
        "task": "app.tasks.monitoring.collect_performance_metrics",
        "schedule": 600.0,  # Every 10 minutes
        "options": {"queue": "maintenance_queue", "priority": 3}
    },
}