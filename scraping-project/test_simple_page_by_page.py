#!/usr/bin/env python3
"""
Prueba simple del sistema página por página
"""

import os
import sys
import time
from datetime import datetime

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_simple_scraping():
    """Probar scraping simple y migración"""
    print("🧪 PRUEBA SIMPLE: SCRAPING + MIGRACIÓN")
    print("=" * 50)
    print(f"⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    try:
        # Importar el spider
        from migrate_pachamamaradio_to_db import main as migrate_main
        from spiders.pachamamaradio_local import main as pachamama_main
        
        print("🕷️  Ejecutando scraping de Pachamama Radio...")
        
        # Ejecutar scraping
        csv_file, json_file = pachamama_main()
        
        if csv_file and json_file:
            print(f"✅ Scraping completado:")
            print(f"   📄 CSV: {csv_file}")
            print(f"   📄 JSON: {json_file}")
            
            # Verificar que los archivos existen
            if os.path.exists(csv_file):
                file_size = os.path.getsize(csv_file)
                print(f"   📊 Tamaño del CSV: {file_size} bytes")
                
                # Migrar a la base de datos
                print(f"\n🗄️  Migrando datos a PostgreSQL...")
                migrate_main()
                print(f"✅ Migración completada")
                
                # Verificar datos en la base de datos
                print(f"\n🔍 Verificando datos en la base de datos...")
                from config.database import get_db_connection
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Contar total de noticias
                cursor.execute("SELECT COUNT(*) FROM noticias")
                total = cursor.fetchone()[0]
                print(f"📊 Total de noticias en BD: {total}")
                
                # Contar noticias de Pachamama
                cursor.execute("SELECT COUNT(*) FROM noticias WHERE fuente = 'Pachamama Radio'")
                pachamama_count = cursor.fetchone()[0]
                print(f"📰 Noticias de Pachamama Radio: {pachamama_count}")
                
                # Últimas noticias
                cursor.execute("""
                    SELECT titulo, fecha_extraccion 
                    FROM noticias 
                    WHERE fuente = 'Pachamama Radio' 
                    ORDER BY fecha_extraccion DESC 
                    LIMIT 3
                """)
                recent = cursor.fetchall()
                
                print(f"\n🆕 Últimas noticias:")
                for i, (titulo, fecha) in enumerate(recent, 1):
                    print(f"   {i}. {titulo[:50]}... ({fecha})")
                
                cursor.close()
                conn.close()
                
            else:
                print("❌ El archivo CSV no se generó correctamente")
        else:
            print("❌ No se pudieron generar los archivos")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_scraping()
