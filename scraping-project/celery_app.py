#!/usr/bin/env python3
"""
Configuración principal de Celery para el proyecto de scraping
"""

from celery import Celery

from config.redis_config import (CELERY_ACCEPT_CONTENT, CELERY_BROKER_URL,
                                 CELERY_ENABLE_UTC, CELERY_RESULT_BACKEND,
                                 CELERY_RESULT_SERIALIZER,
                                 CELERY_TASK_ACKS_LATE,
                                 CELERY_TASK_DEFAULT_RETRY_DELAY,
                                 CELERY_TASK_MAX_RETRIES,
                                 CELERY_TASK_SERIALIZER, CELERY_TIMEZONE,
                                 CELERY_WORKER_CONCURRENCY,
                                 CELERY_WORKER_DISABLE_RATE_LIMITS,
                                 CELERY_WORKER_PREFETCH_MULTIPLIER)

# Crear instancia de Celery
celery_app = Celery('news_scraping')

# Configurar Celery
celery_app.conf.update(
    broker_url=CELERY_BROKER_URL,
    result_backend=CELERY_RESULT_BACKEND,
    task_serializer=CELERY_TASK_SERIALIZER,
    result_serializer=CELERY_RESULT_SERIALIZER,
    accept_content=CELERY_ACCEPT_CONTENT,
    timezone=CELERY_TIMEZONE,
    enable_utc=CELERY_ENABLE_UTC,
    worker_concurrency=CELERY_WORKER_CONCURRENCY,
    worker_prefetch_multiplier=CELERY_WORKER_PREFETCH_MULTIPLIER,
    task_acks_late=CELERY_TASK_ACKS_LATE,
    worker_disable_rate_limits=CELERY_WORKER_DISABLE_RATE_LIMITS,
    task_default_retry_delay=CELERY_TASK_DEFAULT_RETRY_DELAY,
    task_max_retries=CELERY_TASK_MAX_RETRIES,
)

# Configurar rutas de tareas
celery_app.conf.task_routes = {
    'celery_tasks.scraping_tasks.*': {'queue': 'scraping'},
    'celery_tasks.migration_tasks.*': {'queue': 'migration'},
    'celery_tasks.cleanup_tasks.*': {'queue': 'cleanup'},
}

# Configurar colas
celery_app.conf.task_default_queue = 'scraping'
celery_app.conf.task_queues = {
    'scraping': {
        'exchange': 'scraping',
        'routing_key': 'scraping',
    },
    'migration': {
        'exchange': 'migration', 
        'routing_key': 'migration',
    },
    'cleanup': {
        'exchange': 'cleanup',
        'routing_key': 'cleanup',
    },
}

# Configurar tareas periódicas
celery_app.conf.beat_schedule = {
    'scrape-all-sources': {
        'task': 'celery_tasks.scraping_tasks.scrape_all_sources',
        'schedule': 21600.0,  # 6 horas en segundos
        'options': {'queue': 'scraping'}
    },
    # Limpieza automática deshabilitada para mantener máximo historial de datos
    # 'cleanup-old-data': {
    #     'task': 'celery_tasks.cleanup_tasks.cleanup_old_data',
    #     'schedule': 86400.0,  # 24 horas en segundos
    #     'options': {'queue': 'cleanup'}
    # },
}

# Auto-descubrir tareas
celery_app.autodiscover_tasks([
    'celery_tasks.scraping_tasks',
    'celery_tasks.migration_tasks', 
    'celery_tasks.cleanup_tasks'
])

if __name__ == '__main__':
    celery_app.start()
