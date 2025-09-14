#!/usr/bin/env python3
"""
Tareas de Celery para migración de datos a PostgreSQL
"""

import logging
import os
import sys
from datetime import datetime

import pandas as pd
import psycopg2

from celery_app import celery_app

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.redis_config import (DATABASE_URL, DUPLICATE_CHECK_ENABLED,
                                 DUPLICATE_CHECK_FIELD)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name='migrate_source_to_db')
def migrate_source_to_db(self, source_key, csv_file, json_file):
    """
    Tarea para migrar datos de una fuente específica a PostgreSQL
    """
    logger.info(f"🗄️ Migrando {source_key} a PostgreSQL")
    
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Crear tabla si no existe
        create_table_if_not_exists(cursor, conn)
        
        total_migrated = 0
        
        # Migrar desde CSV
        if csv_file and os.path.exists(csv_file):
            migrated_csv = migrate_from_csv(cursor, conn, csv_file, source_key)
            total_migrated += migrated_csv
        
        # Migrar desde JSON
        if json_file and os.path.exists(json_file):
            migrated_json = migrate_from_json(cursor, conn, json_file, source_key)
            total_migrated += migrated_json
        
        conn.close()
        
        logger.info(f"✅ {source_key}: {total_migrated} registros migrados")
        
        return {
            'status': 'completed',
            'source': source_key,
            'migrated_count': total_migrated,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error migrando {source_key}: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)

@celery_app.task(bind=True, name='migrate_all_sources')
def migrate_all_sources(self):
    """
    Tarea para migrar todas las fuentes disponibles
    """
    logger.info("🗄️ Migrando todas las fuentes a PostgreSQL")
    
    try:
        from config.redis_config import NEWS_SOURCES
        
        results = {}
        total_migrated = 0
        
        # Buscar archivos de datos más recientes
        data_folder = "data"
        
        for source_key, source_config in NEWS_SOURCES.items():
            if source_config['enabled']:
                source_folder = os.path.join(data_folder, source_key)
                
                if os.path.exists(source_folder):
                    # Buscar archivos más recientes
                    csv_files = [f for f in os.listdir(source_folder) if f.endswith('.csv')]
                    json_files = [f for f in os.listdir(source_folder) if f.endswith('.json')]
                    
                    if csv_files and json_files:
                        # Obtener archivos más recientes
                        latest_csv = max(csv_files, key=lambda x: os.path.getctime(os.path.join(source_folder, x)))
                        latest_json = max(json_files, key=lambda x: os.path.getctime(os.path.join(source_folder, x)))
                        
                        csv_path = os.path.join(source_folder, latest_csv)
                        json_path = os.path.join(source_folder, latest_json)
                        
                        # Migrar
                        result = migrate_source_to_db.delay(source_key, csv_path, json_path)
                        results[source_key] = {
                            'task_id': result.id,
                            'status': 'started'
                        }
        
        # Esperar resultados
        for source_key, result in results.items():
            try:
                task_result = celery_app.AsyncResult(result['task_id'])
                final_result = task_result.get(timeout=300)
                
                results[source_key]['status'] = 'completed'
                results[source_key]['migrated_count'] = final_result.get('migrated_count', 0)
                total_migrated += final_result.get('migrated_count', 0)
                
            except Exception as e:
                results[source_key]['status'] = 'failed'
                results[source_key]['error'] = str(e)
        
        logger.info(f"🎉 Migración completada. Total: {total_migrated} registros")
        
        return {
            'status': 'completed',
            'total_migrated': total_migrated,
            'sources': results,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error en migración general: {e}")
        return {
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def create_table_if_not_exists(cursor, conn):
    """Crear tabla si no existe"""
    try:
        create_table_query = """
        CREATE TABLE IF NOT EXISTS noticias (
            id SERIAL PRIMARY KEY,
            titulo TEXT,
            fecha TIMESTAMP,
            hora TIME,
            resumen TEXT,
            contenido TEXT,
            categoria VARCHAR(200),
            autor VARCHAR(500),
            tags TEXT,
            url TEXT UNIQUE,
            fecha_extraccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            imagenes TEXT,
            fuente VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        cursor.execute(create_table_query)
        conn.commit()
        logger.info("✅ Tabla 'noticias' verificada/creada")
        
    except Exception as e:
        logger.error(f"❌ Error al crear tabla: {e}")
        raise

def migrate_from_csv(cursor, conn, csv_file, source_key):
    """Migrar datos desde archivo CSV"""
    try:
        logger.info(f"📄 Migrando desde CSV: {csv_file}")
        
        df = pd.read_csv(csv_file)
        logger.info(f"📊 Encontrados {len(df)} registros en CSV")
        
        migrated_count = 0
        skipped_count = 0
        
        for index, row in df.iterrows():
            try:
                # Verificar duplicados si está habilitado
                if DUPLICATE_CHECK_ENABLED:
                    cursor.execute("SELECT id FROM noticias WHERE url = %s", (row['url'],))
                    if cursor.fetchone():
                        skipped_count += 1
                        continue
                
                # Insertar registro
                insert_query = """
                INSERT INTO noticias (
                    titulo, fecha, hora, resumen, contenido, categoria, autor, 
                    tags, url, fecha_extraccion, imagenes, fuente, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """
                
                values = (
                    row.get('titulo'),
                    row.get('fecha'),
                    row.get('hora'),
                    row.get('resumen'),
                    row.get('contenido'),
                    row.get('categoria'),
                    row.get('autor'),
                    row.get('tags'),
                    row.get('url'),
                    row.get('fecha_extraccion'),
                    row.get('imagenes'),
                    row.get('fuente', source_key.title()),
                    row.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                )
                
                cursor.execute(insert_query, values)
                conn.commit()
                migrated_count += 1
                
            except Exception as e:
                logger.warning(f"⚠️ Error en registro {index}: {e}")
                conn.rollback()
                continue
        
        logger.info(f"✅ Migración CSV completada: {migrated_count} migrados, {skipped_count} omitidos")
        return migrated_count
        
    except Exception as e:
        logger.error(f"❌ Error al migrar desde CSV: {e}")
        return 0

def migrate_from_json(cursor, conn, json_file, source_key):
    """Migrar datos desde archivo JSON"""
    try:
        logger.info(f"📄 Migrando desde JSON: {json_file}")
        
        import json
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"📊 Encontrados {len(data)} registros en JSON")
        
        migrated_count = 0
        skipped_count = 0
        
        for item in data:
            try:
                # Verificar duplicados si está habilitado
                if DUPLICATE_CHECK_ENABLED:
                    cursor.execute("SELECT id FROM noticias WHERE url = %s", (item['url'],))
                    if cursor.fetchone():
                        skipped_count += 1
                        continue
                
                # Insertar registro
                insert_query = """
                INSERT INTO noticias (
                    titulo, fecha, hora, resumen, contenido, categoria, autor, 
                    tags, url, fecha_extraccion, imagenes, fuente, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """
                
                values = (
                    item.get('titulo'),
                    item.get('fecha'),
                    item.get('hora'),
                    item.get('resumen'),
                    item.get('contenido'),
                    item.get('categoria'),
                    item.get('autor'),
                    item.get('tags'),
                    item.get('url'),
                    item.get('fecha_extraccion'),
                    item.get('imagenes'),
                    item.get('fuente', source_key.title()),
                    item.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                )
                
                cursor.execute(insert_query, values)
                conn.commit()
                migrated_count += 1
                
            except Exception as e:
                logger.warning(f"⚠️ Error en registro: {e}")
                conn.rollback()
                continue
        
        logger.info(f"✅ Migración JSON completada: {migrated_count} migrados, {skipped_count} omitidos")
        return migrated_count
        
    except Exception as e:
        logger.error(f"❌ Error al migrar desde JSON: {e}")
        return 0
