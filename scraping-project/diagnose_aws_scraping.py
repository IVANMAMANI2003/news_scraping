#!/usr/bin/env python3
"""
Script de diagnóstico para verificar el estado del scraping en AWS
"""

import logging
import os
import sys
from datetime import datetime, timedelta

import psycopg2

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_database_connection():
    """Verificar conexión a la base de datos"""
    try:
        # Configuración para AWS
        conn = psycopg2.connect(
            host="postgres",  # Nombre del servicio Docker
            port="5432",
            database="noticias",
            user="postgres",
            password="123456"
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        logger.info(f"✅ Conexión a PostgreSQL exitosa: {version}")
        
        return conn, cursor
        
    except Exception as e:
        logger.error(f"❌ Error conectando a PostgreSQL: {e}")
        return None, None

def check_table_structure(cursor):
    """Verificar estructura de la tabla"""
    try:
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'noticias'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        logger.info("📋 Estructura de la tabla 'noticias':")
        for col in columns:
            logger.info(f"   - {col[0]}: {col[1]}{f'({col[2]})' if col[2] else ''}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verificando estructura de tabla: {e}")
        return False

def check_data_by_source(cursor):
    """Verificar datos por fuente"""
    try:
        cursor.execute("""
            SELECT 
                fuente,
                COUNT(*) as total_registros,
                MIN(fecha_extraccion) as primera_extraccion,
                MAX(fecha_extraccion) as ultima_extraccion
            FROM noticias 
            GROUP BY fuente
            ORDER BY total_registros DESC;
        """)
        
        results = cursor.fetchall()
        logger.info("📊 Datos por fuente:")
        for row in results:
            logger.info(f"   - {row[0]}: {row[1]} registros (desde {row[2]} hasta {row[3]})")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Error verificando datos por fuente: {e}")
        return []

def check_recent_activity(cursor):
    """Verificar actividad reciente"""
    try:
        # Últimas 24 horas
        yesterday = datetime.now() - timedelta(days=1)
        
        cursor.execute("""
            SELECT 
                fuente,
                COUNT(*) as registros_ultimas_24h
            FROM noticias 
            WHERE fecha_extraccion >= %s
            GROUP BY fuente
            ORDER BY registros_ultimas_24h DESC;
        """, (yesterday,))
        
        results = cursor.fetchall()
        logger.info("🕐 Actividad en las últimas 24 horas:")
        for row in results:
            logger.info(f"   - {row[0]}: {row[1]} registros")
        
        if not results:
            logger.warning("⚠️ No hay actividad en las últimas 24 horas")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Error verificando actividad reciente: {e}")
        return []

def check_duplicate_urls(cursor):
    """Verificar URLs duplicadas"""
    try:
        cursor.execute("""
            SELECT url, COUNT(*) as count
            FROM noticias 
            GROUP BY url
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            LIMIT 10;
        """)
        
        duplicates = cursor.fetchall()
        if duplicates:
            logger.warning(f"⚠️ Encontradas {len(duplicates)} URLs duplicadas:")
            for dup in duplicates:
                logger.warning(f"   - {dup[0]}: {dup[1]} veces")
        else:
            logger.info("✅ No hay URLs duplicadas")
        
        return duplicates
        
    except Exception as e:
        logger.error(f"❌ Error verificando duplicados: {e}")
        return []

def check_file_system():
    """Verificar archivos de datos"""
    try:
        data_dir = "/app/data"
        if not os.path.exists(data_dir):
            logger.warning(f"⚠️ Directorio de datos no existe: {data_dir}")
            return False
        
        logger.info("📁 Archivos de datos encontrados:")
        for source in ['losandes', 'punonoticias', 'pachamamaradio', 'sinfronteras']:
            source_dir = os.path.join(data_dir, source)
            if os.path.exists(source_dir):
                files = os.listdir(source_dir)
                csv_files = [f for f in files if f.endswith('.csv')]
                json_files = [f for f in files if f.endswith('.json')]
                logger.info(f"   - {source}: {len(csv_files)} CSV, {len(json_files)} JSON")
            else:
                logger.warning(f"   - {source}: directorio no existe")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verificando sistema de archivos: {e}")
        return False

def main():
    """Función principal de diagnóstico"""
    logger.info("🔍 Iniciando diagnóstico del sistema de scraping en AWS")
    logger.info("=" * 60)
    
    # 1. Verificar conexión a base de datos
    conn, cursor = check_database_connection()
    if not conn:
        logger.error("❌ No se puede continuar sin conexión a la base de datos")
        return
    
    try:
        # 2. Verificar estructura de tabla
        logger.info("\n📋 Verificando estructura de tabla...")
        check_table_structure(cursor)
        
        # 3. Verificar datos por fuente
        logger.info("\n📊 Verificando datos por fuente...")
        data_by_source = check_data_by_source(cursor)
        
        # 4. Verificar actividad reciente
        logger.info("\n🕐 Verificando actividad reciente...")
        recent_activity = check_recent_activity(cursor)
        
        # 5. Verificar duplicados
        logger.info("\n🔍 Verificando URLs duplicadas...")
        check_duplicate_urls(cursor)
        
        # 6. Verificar sistema de archivos
        logger.info("\n📁 Verificando sistema de archivos...")
        check_file_system()
        
        # 7. Resumen
        logger.info("\n" + "=" * 60)
        logger.info("📋 RESUMEN DEL DIAGNÓSTICO:")
        
        if data_by_source:
            total_sources = len(data_by_source)
            total_records = sum(row[1] for row in data_by_source)
            logger.info(f"   - Fuentes activas: {total_sources}")
            logger.info(f"   - Total de registros: {total_records}")
            
            if total_sources < 4:
                logger.warning(f"⚠️ Solo {total_sources} de 4 fuentes tienen datos")
                missing_sources = set(['Los Andes', 'Puno Noticias', 'Pachamama Radio', 'Sin Fronteras'])
                active_sources = set(row[0] for row in data_by_source)
                missing = missing_sources - active_sources
                if missing:
                    logger.warning(f"   - Fuentes faltantes: {', '.join(missing)}")
        else:
            logger.warning("⚠️ No se encontraron datos en la base de datos")
        
        if not recent_activity:
            logger.warning("⚠️ No hay actividad reciente - el scraping podría no estar funcionando")
        
    finally:
        cursor.close()
        conn.close()
        logger.info("\n✅ Diagnóstico completado")

if __name__ == "__main__":
    main()
