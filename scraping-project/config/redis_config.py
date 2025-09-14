#!/usr/bin/env python3
"""
Configuración de Redis para el proyecto de scraping
"""

import os
from urllib.parse import urlparse

# Configuración de Redis
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Configuración de Celery
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# Configuración de la base de datos
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:123456@localhost:5432/noticias')

# Configuración de tareas
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = 'America/Lima'
CELERY_ENABLE_UTC = True

# Configuración de workers
CELERY_WORKER_CONCURRENCY = 4
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_DISABLE_RATE_LIMITS = True

# Configuración de retry
CELERY_TASK_DEFAULT_RETRY_DELAY = 60  # 1 minuto
CELERY_TASK_MAX_RETRIES = 3

# Configuración de duplicados
DUPLICATE_CHECK_ENABLED = True
DUPLICATE_CHECK_FIELD = 'url'

# Configuración de scraping - INTERVALO REDUCIDO PARA PRUEBA
SCRAPING_INTERVAL_HOURS = 6  # Mantener 6 horas para producción
SCRAPING_INTERVAL_MINUTES = 2  # 2 minutos para prueba
SCRAPING_TIMEOUT_SECONDS = 300

# Configuración de logging
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Fuentes de noticias - TODAS HABILITADAS
NEWS_SOURCES = {
    'losandes': {
        'name': 'Los Andes',
        'enabled': True,
        'priority': 1
    },
    'punonoticias': {
        'name': 'Puno Noticias', 
        'enabled': True,
        'priority': 2
    },
    'pachamamaradio': {
        'name': 'Pachamama Radio',
        'enabled': True,
        'priority': 3
    },
    'sinfronteras': {
        'name': 'Sin Fronteras',
        'enabled': True,
        'priority': 4
    }
}
