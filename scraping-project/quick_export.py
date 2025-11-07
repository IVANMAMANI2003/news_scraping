#!/usr/bin/env python3
"""
Exportación rápida de la base de datos local a CSV
"""

import csv
import logging
import os
from datetime import datetime

import psycopg2

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def export_database():
    """Exportar base de datos local a CSV"""
    
    # Configuración de la base de datos local
    db_config = {
        'host': '127.0.0.1',
        'port': '5432',
        'database': 'noticias',
        'user': 'postgres',
        'password': '123456'
    }
    
    # Nombre del archivo de salida
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"noticias_local_{timestamp}.csv"
    
    logger.info(f"🚀 Exportando base de datos local a: {output_file}")
    
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Obtener todos los datos
        cursor.execute("""
            SELECT 
                id, titulo, fecha, hora, resumen, contenido, categoria, autor, 
                tags, url, fecha_extraccion, imagenes, fuente, created_at
            FROM noticias 
            ORDER BY fecha_extraccion DESC
        """)
        
        # Obtener nombres de columnas
        column_names = [desc[0] for desc in cursor.description]
        
        # Escribir CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Escribir encabezados
            writer.writerow(column_names)
            
            # Escribir datos
            row_count = 0
            for row in cursor.fetchall():
                writer.writerow(row)
                row_count += 1
                
                if row_count % 1000 == 0:
                    logger.info(f"📊 Procesados {row_count} registros...")
        
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Exportación completada exitosamente!")
        logger.info(f"📊 Total de registros exportados: {row_count}")
        logger.info(f"📁 Archivo guardado como: {output_file}")
        
        # Mostrar estadísticas por fuente
        logger.info("\n📰 Estadísticas por fuente:")
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT fuente, COUNT(*) as count
            FROM noticias 
            GROUP BY fuente
            ORDER BY count DESC
        """)
        
        for source, count in cursor.fetchall():
            logger.info(f"   - {source}: {count} registros")
        
        cursor.close()
        conn.close()
        
        return output_file
        
    except Exception as e:
        logger.error(f"❌ Error exportando base de datos: {e}")
        return None

def main():
    """Función principal"""
    logger.info("🚀 Iniciando exportación rápida de base de datos local")
    logger.info("=" * 60)
    
    output_file = export_database()
    
    if output_file:
        logger.info(f"\n🎉 ¡Exportación exitosa!")
        logger.info(f"📁 Archivo: {output_file}")
        logger.info(f"📊 Tamaño: {os.path.getsize(output_file) / 1024 / 1024:.2f} MB")
    else:
        logger.error("❌ La exportación falló")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
