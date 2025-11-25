#!/usr/bin/env python3
"""
Script para exportar datos de noticias_limpia a CSV
Exporta exactamente como está en la base de datos, sin transformaciones
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

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': 'noticias',
    'user': 'postgres',
    'password': '123456'
}


def export_noticias_limpia():
    """Exportar datos de noticias_limpia tal cual están en la BD"""
    
    # Nombre del archivo de salida
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"noticias_limpia_{timestamp}.csv"
    
    logger.info(f"🚀 Exportando datos de 'noticias_limpia' a: {output_file}")
    
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Obtener todas las columnas de noticias_limpia
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'noticias_limpia' 
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        column_names = [row[0] for row in cursor.fetchall()]
        
        logger.info(f"📋 Columnas encontradas: {', '.join(column_names)}")
        
        # Construir query SELECT con todas las columnas
        columns_str = ', '.join(column_names)
        query = f"""
            SELECT {columns_str}
            FROM noticias_limpia 
            ORDER BY id DESC
        """
        
        cursor.execute(query)
        
        # Escribir CSV con UTF-8 BOM para Excel (Windows)
        # Excel necesita UTF-8 con BOM para leer correctamente caracteres especiales
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
            
            # Escribir encabezados (TODAS las columnas)
            writer.writerow(column_names)
            logger.info(f"📋 Exportando {len(column_names)} columnas: {', '.join(column_names)}")
            
            # Escribir datos tal cual están (sin transformaciones)
            row_count = 0
            for row in cursor.fetchall():
                # Convertir todos los campos manteniendo tipos originales
                cleaned_row = []
                for i, field in enumerate(row):
                    if field is None:
                        cleaned_row.append('')
                    elif isinstance(field, (int, float)):
                        # Mantener números como están
                        cleaned_row.append(field)
                    elif isinstance(field, bool):
                        # Convertir booleanos a texto
                        cleaned_row.append(str(field))
                    else:
                        # Mantener texto tal cual (ya está en UTF-8)
                        cleaned_row.append(str(field))
                
                writer.writerow(cleaned_row)
                row_count += 1
                
                if row_count % 1000 == 0:
                    logger.info(f"📊 Procesados {row_count} registros...")
        
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Exportación completada exitosamente!")
        logger.info(f"📊 Total de registros exportados: {row_count}")
        logger.info(f"📁 Archivo guardado como: {output_file}")
        logger.info(f"📏 Tamaño: {os.path.getsize(output_file) / 1024 / 1024:.2f} MB")
        
        # Mostrar estadísticas por categoría
        logger.info("\n📊 Estadísticas por categoría:")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT categoria, COUNT(*) as count
            FROM noticias_limpia 
            WHERE categoria IS NOT NULL AND categoria != ''
            GROUP BY categoria
            ORDER BY count DESC
        """)
        
        for categoria, count in cursor.fetchall():
            logger.info(f"   - {categoria}: {count} registros")
        
        # Mostrar estadísticas por fuente
        logger.info("\n📰 Estadísticas por fuente:")
        cursor.execute("""
            SELECT fuente, COUNT(*) as count
            FROM noticias_limpia 
            WHERE fuente IS NOT NULL AND fuente != ''
            GROUP BY fuente
            ORDER BY count DESC
        """)
        
        for fuente, count in cursor.fetchall():
            logger.info(f"   - {fuente}: {count} registros")
        
        cursor.close()
        conn.close()
        
        return output_file
        
    except Exception as e:
        logger.error(f"❌ Error exportando: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Función principal"""
    logger.info("=" * 60)
    logger.info("📤 EXPORTACIÓN DE NOTICIAS_LIMPIA")
    logger.info("=" * 60)
    
    # Verificar conexión
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM noticias_limpia")
        total = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        logger.info(f"✅ Conexión exitosa. Total de registros en noticias_limpia: {total}")
    except Exception as e:
        logger.error(f"❌ Error conectando a la base de datos: {e}")
        return False
    
    # Exportar
    output_file = export_noticias_limpia()
    
    if output_file:
        logger.info(f"\n🎉 ¡Exportación completada!")
        logger.info(f"📁 Archivo: {output_file}")
        return True
    else:
        logger.error("❌ La exportación falló")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

