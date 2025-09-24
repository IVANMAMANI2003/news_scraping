#!/usr/bin/env python3
"""
Sistema principal para AWS
Ejecuta scraping recursivo continuo
"""

import logging
import os
import time
from datetime import datetime, timedelta

import psycopg2
from celery import Celery
from celery.schedules import crontab

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/aws_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuración Celery para AWS
celery_app = Celery('aws_news_system')
celery_app.conf.broker_url = 'redis://redis:6379/0'
celery_app.conf.result_backend = 'redis://redis:6379/0'
celery_app.conf.timezone = 'America/Lima'

# Configuración de tareas
celery_app.conf.beat_schedule = {
    'scrape-pachamama': {
        'task': 'scrape_source',
        'schedule': crontab(minute=0, hour='*/2'),  # Cada 2 horas
        'args': ('pachamamaradio',)
    },
    'scrape-puno': {
        'task': 'scrape_source',
        'schedule': crontab(minute=30, hour='*/2'),  # Cada 2 horas, 30 min después
        'args': ('punonoticias',)
    },
    'scrape-sinfronteras': {
        'task': 'scrape_source',
        'schedule': crontab(minute=0, hour='*/3'),  # Cada 3 horas
        'args': ('sinfronteras',)
    },
    'scrape-losandes': {
        'task': 'scrape_source',
        'schedule': crontab(minute=30, hour='*/3'),  # Cada 3 horas, 30 min después
        'args': ('losandes',)
    },
    'cleanup-old-data': {
        'task': 'cleanup_old_data',
        'schedule': crontab(hour=2, minute=0),  # Diario a las 2 AM
    }
}

def connect_to_db():
    """Conectar a la base de datos"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'postgres'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', '123456'),
            database=os.getenv('POSTGRES_DB', 'noticias')
        )
        return conn
    except Exception as e:
        logger.error(f"Error conectando a DB: {e}")
        return None

@celery_app.task
def scrape_source(source_name):
    """Tarea para hacer scraping de una fuente específica"""
    logger.info(f"🕷️  Iniciando scraping de {source_name}")
    
    try:
        # Importar el scraper correspondiente
        if source_name == 'pachamamaradio':
            from spiders.pachamamaradio_local import PachamamaRadioLocalScraper
            scraper = PachamamaRadioLocalScraper()
        elif source_name == 'punonoticias':
            from spiders.punonoticias_local import PunoNoticiasLocalScraper
            scraper = PunoNoticiasLocalScraper()
        elif source_name == 'sinfronteras':
            from spiders.sinfronteras_local import SinFronterasLocalScraper
            scraper = SinFronterasLocalScraper()
        elif source_name == 'losandes':
            from spiders.losandes_local import LosAndesLocalScraper
            scraper = LosAndesLocalScraper()
        else:
            logger.error(f"Fuente desconocida: {source_name}")
            return False
        
        # Obtener última página procesada
        conn = connect_to_db()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute("SELECT ultima_pagina FROM scraping_control WHERE fuente = %s", (source_name,))
        result = cursor.fetchone()
        last_page = result[0] if result else 0
        
        # Configurar scraper para continuar desde la última página
        scraper.start_page = last_page + 1
        scraper.max_pages = 10  # Procesar 10 páginas por ejecución
        
        # Ejecutar scraping
        articles = scraper.scrape_news()
        
        # Guardar en base de datos
        saved_count = 0
        for article in articles:
            try:
                cursor.execute("""
INSERT INTO noticias (titulo, fecha, hora, resumen, contenido, categoria, autor, tags, url, fecha_extraccion, imagenes, fuente, created_at)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (url) DO NOTHING
                """, (
                    article.get('titulo'),
                    article.get('fecha'),
                    article.get('hora'),
                    article.get('resumen'),
                    article.get('contenido'),
                    article.get('categoria'),
                    article.get('autor'),
                    article.get('tags'),
                    article.get('url'),
                    article.get('fecha_extraccion'),
                    article.get('imagenes'),
                    article.get('fuente'),
                    article.get('created_at')
                ))
                saved_count += 1
            except Exception as e:
                logger.error(f"Error guardando artículo: {e}")
                continue
        
        # Actualizar control de scraping
        cursor.execute("""
UPDATE scraping_control 
SET ultima_pagina = %s, ultima_ejecucion = %s, total_noticias = total_noticias + %s
WHERE fuente = %s
        """, (scraper.start_page + scraper.max_pages - 1, datetime.now(), saved_count, source_name))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ {source_name}: {saved_count} noticias guardadas")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en scraping de {source_name}: {e}")
        return False

@celery_app.task
def cleanup_old_data():
    """Limpiar datos antiguos (opcional)"""
    logger.info("🧹 Limpiando datos antiguos...")
    
    try:
        conn = connect_to_db()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Eliminar noticias más antiguas de 30 días
        cursor.execute("""
DELETE FROM noticias 
WHERE fecha_extraccion < %s
        """, (datetime.now() - timedelta(days=30),))
        
        deleted_count = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Eliminadas {deleted_count} noticias antiguas")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en limpieza: {e}")
        return False

def main():
    """Función principal"""
    logger.info("🚀 Iniciando sistema AWS de noticias")
    
    # Crear directorios necesarios
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Esperar a que los servicios estén listos
    logger.info("⏳ Esperando servicios...")
    time.sleep(30)
    
    # Verificar conexión a base de datos
    conn = connect_to_db()
    if not conn:
        logger.error("❌ No se pudo conectar a la base de datos")
        return
    
    conn.close()
    logger.info("✅ Base de datos conectada")
    
    # Iniciar Celery Beat
    logger.info("🔄 Iniciando Celery Beat...")
    celery_app.start()

if __name__ == "__main__":
    main()
