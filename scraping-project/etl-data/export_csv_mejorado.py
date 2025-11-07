#!/usr/bin/env python3
"""
Script mejorado para exportar la base de datos a CSV con formato correcto
Soluciona problemas de saltos de línea y caracteres especiales
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

def clean_text(text):
    """Limpiar texto removiendo saltos de línea y caracteres problemáticos"""
    if text is None:
        return ""
    
    # Convertir a string si no lo es
    text = str(text)
    
    # Remover saltos de línea y caracteres de control
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    
    # Remover espacios múltiples
    text = ' '.join(text.split())
    
    return text.strip()

def export_database_mejorado():
    """Exportar base de datos con formato CSV correcto"""
    
    # Configuración de la base de datos
    db_config = {
        'host': '127.0.0.1',
        'port': '5432',
        'database': 'noticias',
        'user': 'postgres',
        'password': '123456'
    }
    
    # Nombre del archivo de salida
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"etl-data/noticias_{timestamp}.csv"
    
    logger.info(f"🚀 Exportando base de datos con formato mejorado a: {output_file}")
    
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
        
        # Escribir CSV con formato correcto
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)  # Quotar todos los campos
            
            # Escribir encabezados
            writer.writerow(column_names)
            
            # Escribir datos
            row_count = 0
            for row in cursor.fetchall():
                # Limpiar cada campo del registro
                cleaned_row = []
                for field in row:
                    cleaned_field = clean_text(field)
                    cleaned_row.append(cleaned_field)
                
                writer.writerow(cleaned_row)
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

def export_by_source_mejorado(output_dir="exports_mejorado"):
    """Exportar datos separados por fuente con formato mejorado"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    logger.info(f"📊 Exportando datos por fuente con formato mejorado en: {output_dir}")
    
    # Configuración de la base de datos
    db_config = {
        'host': '127.0.0.1',
        'port': '5432',
        'database': 'noticias',
        'user': 'postgres',
        'password': '123456'
    }
    
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Obtener fuentes únicas
        cursor.execute("SELECT DISTINCT fuente FROM noticias ORDER BY fuente")
        sources = [row[0] for row in cursor.fetchall()]
        
        exported_files = []
        
        for source in sources:
            # Limpiar nombre de archivo
            safe_source = source.replace(' ', '_').replace('/', '_')
            filename = f"{safe_source}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(output_dir, filename)
            
            # Exportar datos de esta fuente
            cursor.execute("""
                SELECT 
                    id, titulo, fecha, hora, resumen, contenido, categoria, autor, 
                    tags, url, fecha_extraccion, imagenes, fuente, created_at
                FROM noticias 
                WHERE fuente = %s
                ORDER BY fecha_extraccion DESC
            """, (source,))
            
            rows = cursor.fetchall()
            
            # Escribir CSV con formato correcto
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
                
                # Escribir encabezados
                column_names = [desc[0] for desc in cursor.description]
                writer.writerow(column_names)
                
                # Escribir datos limpiados
                for row in rows:
                    cleaned_row = [clean_text(field) for field in row]
                    writer.writerow(cleaned_row)
            
            logger.info(f"✅ {source}: {len(rows)} registros -> {filepath}")
            exported_files.append(filepath)
        
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Exportación por fuente completada: {len(exported_files)} archivos")
        return exported_files
        
    except Exception as e:
        logger.error(f"❌ Error exportando por fuente: {e}")
        return None

def main():
    """Función principal con menú de opciones"""
    logger.info("🚀 Iniciando exportación mejorada de base de datos")
    logger.info("=" * 60)
    
    # Verificar conexión
    db_config = {
        'host': '127.0.0.1',
        'port': '5432',
        'database': 'noticias',
        'user': 'postgres',
        'password': '123456'
    }
    
    try:
        conn = psycopg2.connect(**db_config)
        conn.close()
        logger.info("✅ Conexión a base de datos exitosa")
    except Exception as e:
        logger.error(f"❌ Error conectando a la base de datos: {e}")
        return False
    
    # Menú de opciones
    logger.info("\n📋 OPCIONES DE EXPORTACIÓN MEJORADA:")
    logger.info("1. Exportar todos los datos a un solo CSV (formato mejorado)")
    logger.info("2. Exportar datos separados por fuente (formato mejorado)")
    logger.info("3. Exportar todo (opciones 1 y 2)")
    
    try:
        choice = input("\nSelecciona una opción (1-3): ").strip()
        
        if choice == "1":
            # Exportar todo a un CSV
            output_file = export_database_mejorado()
            if output_file:
                logger.info(f"🎉 ¡Exportación completada! Archivo: {output_file}")
                logger.info(f"📊 Tamaño: {os.path.getsize(output_file) / 1024 / 1024:.2f} MB")
        
        elif choice == "2":
            # Exportar por fuente
            exported_files = export_by_source_mejorado()
            if exported_files:
                logger.info(f"🎉 ¡Exportación completada! {len(exported_files)} archivos creados")
        
        elif choice == "3":
            # Exportar todo
            logger.info("🔄 Exportando todos los datos...")
            
            # Exportar todo a un CSV
            output_file = export_database_mejorado()
            if output_file:
                logger.info(f"✅ Archivo completo: {output_file}")
            
            # Exportar por fuente
            exported_files = export_by_source_mejorado()
            if exported_files:
                logger.info(f"✅ Archivos por fuente: {len(exported_files)} archivos")
            
            logger.info("🎉 ¡Todas las exportaciones completadas!")
        
        else:
            logger.error("❌ Opción no válida")
            return False
        
        return True
        
    except KeyboardInterrupt:
        logger.info("🛑 Exportación cancelada por el usuario")
        return False
    except Exception as e:
        logger.error(f"❌ Error durante la exportación: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
