#!/usr/bin/env python3
"""
Tareas de Celery para scraping de noticias
"""

import logging
import os
import sys
from datetime import datetime

from celery import current_task

from celery_app import celery_app

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.redis_config import (DUPLICATE_CHECK_ENABLED,
                                 DUPLICATE_CHECK_FIELD, NEWS_SOURCES)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name='scrape_all_sources')
def scrape_all_sources(self):
    """
    Tarea principal para hacer scraping de todas las fuentes
    """
    logger.info("🚀 Iniciando scraping de todas las fuentes")
    
    results = {}
    total_articles = 0
    
    try:
        # Ejecutar scraping de cada fuente habilitada
        for source_key, source_config in NEWS_SOURCES.items():
            if source_config['enabled']:
                logger.info(f"📰 Iniciando scraping de {source_config['name']}")
                
                # Ejecutar tarea de scraping individual
                task_result = scrape_single_source.delay(source_key)
                results[source_key] = {
                    'task_id': task_result.id,
                    'status': 'started',
                    'source_name': source_config['name']
                }
        
        # Esperar a que terminen todas las tareas
        for source_key, result in results.items():
            try:
                task_result = celery_app.AsyncResult(result['task_id'])
                final_result = task_result.get(timeout=300)  # 5 minutos timeout
                
                results[source_key]['status'] = 'completed'
                results[source_key]['articles_count'] = final_result.get('articles_count', 0)
                total_articles += final_result.get('articles_count', 0)
                
                logger.info(f"✅ {result['source_name']}: {final_result.get('articles_count', 0)} artículos")
                
            except Exception as e:
                results[source_key]['status'] = 'failed'
                results[source_key]['error'] = str(e)
                logger.error(f"❌ Error en {result['source_name']}: {e}")
        
        logger.info(f"🎉 Scraping completado. Total: {total_articles} artículos")
        
        return {
            'status': 'completed',
            'total_articles': total_articles,
            'sources': results,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error en scraping general: {e}")
        return {
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@celery_app.task(bind=True, name='scrape_single_source')
def scrape_single_source(self, source_key):
    """
    Tarea para hacer scraping de una fuente específica
    """
    logger.info(f"🕷️ Iniciando scraping de {source_key}")
    
    try:
        # Importar el spider correspondiente
        if source_key == 'losandes':
            from spiders.losandes_local import main as spider_main
        elif source_key == 'punonoticias':
            from spiders.punonoticias_local import main as spider_main
        elif source_key == 'pachamamaradio':
            from spiders.pachamamaradio_local import main as spider_main
        elif source_key == 'sinfronteras':
            from spiders.sinfronteras_local import main as spider_main
        else:
            raise ValueError(f"Fuente no reconocida: {source_key}")
        
        # Ejecutar el spider
        csv_file, json_file = spider_main()
        
        if csv_file and json_file:
            # Contar artículos extraídos
            import pandas as pd
            df = pd.read_csv(csv_file)
            articles_count = len(df)
            
            logger.info(f"✅ {source_key}: {articles_count} artículos extraídos")
            
            # Ejecutar migración a la base de datos
            migrate_task = migrate_source_to_db.delay(source_key, csv_file, json_file)
            
            return {
                'status': 'completed',
                'articles_count': articles_count,
                'csv_file': csv_file,
                'json_file': json_file,
                'migration_task_id': migrate_task.id
            }
        else:
            raise Exception("No se pudieron generar los archivos de datos")
            
    except Exception as e:
        logger.error(f"❌ Error en scraping de {source_key}: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)

@celery_app.task(bind=True, name='scrape_source_now')
def scrape_source_now(self, source_key):
    """
    Tarea para hacer scraping inmediato de una fuente específica
    """
    logger.info(f"⚡ Scraping inmediato de {source_key}")
    
    try:
        # Ejecutar scraping
        result = scrape_single_source.delay(source_key)
        final_result = result.get(timeout=300)
        
        return {
            'status': 'completed',
            'source': source_key,
            'result': final_result,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error en scraping inmediato de {source_key}: {e}")
        return {
            'status': 'failed',
            'source': source_key,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@celery_app.task(bind=True, name='check_duplicates')
def check_duplicates(self, source_key, articles_data):
    """
    Tarea para verificar duplicados en los artículos extraídos
    """
    if not DUPLICATE_CHECK_ENABLED:
        return {'duplicates_found': 0, 'unique_articles': len(articles_data)}
    
    logger.info(f"🔍 Verificando duplicados para {source_key}")
    
    try:
        import psycopg2

        from config.redis_config import DATABASE_URL

        # Conectar a la base de datos
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Obtener URLs existentes
        cursor.execute(f"SELECT {DUPLICATE_CHECK_FIELD} FROM noticias")
        existing_urls = {row[0] for row in cursor.fetchall()}
        
        # Filtrar duplicados
        unique_articles = []
        duplicates_count = 0
        
        for article in articles_data:
            if article.get(DUPLICATE_CHECK_FIELD) not in existing_urls:
                unique_articles.append(article)
            else:
                duplicates_count += 1
        
        conn.close()
        
        logger.info(f"📊 {source_key}: {duplicates_count} duplicados, {len(unique_articles)} únicos")
        
        return {
            'duplicates_found': duplicates_count,
            'unique_articles': len(unique_articles),
            'filtered_articles': unique_articles
        }
        
    except Exception as e:
        logger.error(f"❌ Error verificando duplicados: {e}")
        return {
            'duplicates_found': 0,
            'unique_articles': len(articles_data),
            'error': str(e)
        }
