#!/usr/bin/env python3
"""
Tareas de Celery para limpieza y mantenimiento de datos
"""

import logging
import os
import sys
from datetime import datetime, timedelta

import psycopg2

from celery_app import celery_app

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.redis_config import DATABASE_URL

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name='cleanup_old_data')
def cleanup_old_data(self, days_old=30):
    """
    Tarea para limpiar datos antiguos de la base de datos
    """
    logger.info(f"🧹 Iniciando limpieza de datos antiguos (más de {days_old} días)")
    
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Calcular fecha límite
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        # Contar registros a eliminar
        cursor.execute(
            "SELECT COUNT(*) FROM noticias WHERE created_at < %s",
            (cutoff_date,)
        )
        count_to_delete = cursor.fetchone()[0]
        
        if count_to_delete > 0:
            # Eliminar registros antiguos
            cursor.execute(
                "DELETE FROM noticias WHERE created_at < %s",
                (cutoff_date,)
            )
            conn.commit()
            
            logger.info(f"✅ Eliminados {count_to_delete} registros antiguos")
            
            return {
                'status': 'completed',
                'deleted_count': count_to_delete,
                'cutoff_date': cutoff_date.isoformat(),
                'timestamp': datetime.now().isoformat()
            }
        else:
            logger.info("ℹ️ No hay registros antiguos para eliminar")
            
            return {
                'status': 'completed',
                'deleted_count': 0,
                'message': 'No hay registros antiguos para eliminar',
                'timestamp': datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"❌ Error en limpieza de datos: {e}")
        return {
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
    finally:
        if 'conn' in locals():
            conn.close()

@celery_app.task(bind=True, name='cleanup_duplicates')
def cleanup_duplicates(self):
    """
    Tarea para limpiar duplicados de la base de datos
    """
    logger.info("🔍 Iniciando limpieza de duplicados")
    
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Encontrar duplicados por URL
        cursor.execute("""
            SELECT url, COUNT(*) as count
            FROM noticias 
            GROUP BY url 
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """)
        
        duplicates = cursor.fetchall()
        
        if duplicates:
            deleted_count = 0
            
            for url, count in duplicates:
                # Mantener solo el registro más reciente
                cursor.execute("""
                    DELETE FROM noticias 
                    WHERE url = %s 
                    AND id NOT IN (
                        SELECT id FROM noticias 
                        WHERE url = %s 
                        ORDER BY created_at DESC 
                        LIMIT 1
                    )
                """, (url, url))
                
                deleted_count += cursor.rowcount
            
            conn.commit()
            
            logger.info(f"✅ Eliminados {deleted_count} duplicados")
            
            return {
                'status': 'completed',
                'duplicates_found': len(duplicates),
                'deleted_count': deleted_count,
                'timestamp': datetime.now().isoformat()
            }
        else:
            logger.info("ℹ️ No se encontraron duplicados")
            
            return {
                'status': 'completed',
                'duplicates_found': 0,
                'deleted_count': 0,
                'message': 'No se encontraron duplicados',
                'timestamp': datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"❌ Error en limpieza de duplicados: {e}")
        return {
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
    finally:
        if 'conn' in locals():
            conn.close()

@celery_app.task(bind=True, name='optimize_database')
def optimize_database(self):
    """
    Tarea para optimizar la base de datos
    """
    logger.info("⚡ Iniciando optimización de base de datos")
    
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Analizar tablas
        cursor.execute("ANALYZE noticias;")
        
        # Vacuum (solo si es necesario)
        cursor.execute("VACUUM ANALYZE noticias;")
        
        conn.commit()
        
        # Obtener estadísticas
        cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                attname,
                n_distinct,
                correlation
            FROM pg_stats 
            WHERE tablename = 'noticias'
        """)
        
        stats = cursor.fetchall()
        
        logger.info("✅ Optimización de base de datos completada")
        
        return {
            'status': 'completed',
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error en optimización: {e}")
        return {
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
    finally:
        if 'conn' in locals():
            conn.close()

@celery_app.task(bind=True, name='database_health_check')
def database_health_check(self):
    """
    Tarea para verificar la salud de la base de datos
    """
    logger.info("🏥 Iniciando verificación de salud de la base de datos")
    
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        health_info = {}
        
        # Verificar conexión
        cursor.execute("SELECT 1")
        health_info['connection'] = 'ok'
        
        # Contar registros totales
        cursor.execute("SELECT COUNT(*) FROM noticias")
        health_info['total_records'] = cursor.fetchone()[0]
        
        # Contar por fuente
        cursor.execute("SELECT fuente, COUNT(*) FROM noticias GROUP BY fuente")
        health_info['records_by_source'] = dict(cursor.fetchall())
        
        # Verificar duplicados
        cursor.execute("""
            SELECT COUNT(*) FROM (
                SELECT url, COUNT(*) 
                FROM noticias 
                GROUP BY url 
                HAVING COUNT(*) > 1
            ) as duplicates
        """)
        health_info['duplicate_count'] = cursor.fetchone()[0]
        
        # Verificar registros recientes
        cursor.execute("""
            SELECT COUNT(*) FROM noticias 
            WHERE created_at >= NOW() - INTERVAL '24 hours'
        """)
        health_info['recent_records_24h'] = cursor.fetchone()[0]
        
        # Verificar tamaño de la tabla
        cursor.execute("""
            SELECT pg_size_pretty(pg_total_relation_size('noticias'))
        """)
        health_info['table_size'] = cursor.fetchone()[0]
        
        conn.close()
        
        logger.info("✅ Verificación de salud completada")
        
        return {
            'status': 'completed',
            'health_info': health_info,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error en verificación de salud: {e}")
        return {
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
