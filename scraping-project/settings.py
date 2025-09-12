BOT_NAME = "scraper"

SPIDER_MODULES = ["spiders"]
NEWSPIDER_MODULE = "spiders"

ROBOTSTXT_OBEY = True

ITEM_PIPELINES = {
   "pipelines.clean_pipeline.CleanPipeline": 300,
   "pipelines.postgres_pipeline.PostgresPipeline": 400,
}

FEEDS = {
    'data/%(name)s_%(time)s.json': {'format': 'json'},
    'data/%(name)s_%(time)s.csv': {'format': 'csv'},
}

# Configuración de logging
LOG_LEVEL = 'INFO'

# Configuración de descarga (para ser respetuoso con los sitios)
DOWNLOAD_DELAY = 1
RANDOMIZE_DOWNLOAD_DELAY = 0.5
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
