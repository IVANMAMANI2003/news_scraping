import os

from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos PostgreSQL
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'noticias'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres'),
    'port': os.getenv('DB_PORT', '5432')
}

# Configuración de Scrapy
SCRAPY_SETTINGS = {
    'BOT_NAME': 'scraper',
    'SPIDER_MODULES': ['spiders'],
    'NEWSPIDER_MODULE': 'spiders',
    'ROBOTSTXT_OBEY': True,
    'ITEM_PIPELINES': {
        'pepelines.clean_pipeline.CleanPipeline': 300,
        'pepelines.postgres_pipeline.PostgresPipeline': 400,
    },
    'FEEDS': {
        'data/%(name)s_%(time)s.json': {'format': 'json'},
        'data/%(name)s_%(time)s.csv': {'format': 'csv'},
    },
    'LOG_LEVEL': 'INFO',
    'DOWNLOAD_DELAY': 1,  # Delay entre requests para ser respetuoso
    'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
    'AUTOTHROTTLE_ENABLED': True,
    'AUTOTHROTTLE_START_DELAY': 1,
    'AUTOTHROTTLE_MAX_DELAY': 60,
    'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
}
