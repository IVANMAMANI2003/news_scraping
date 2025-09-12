#!/usr/bin/env python3
"""
Script completo para Sin Fronteras:
1. Ejecuta el scraping y guarda en CSV/JSON
2. Migra los datos a PostgreSQL
"""

import os
import sys
from datetime import datetime

# Agregar el directorio actual al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_scraping():
    """Ejecutar el scraping de Sin Fronteras"""
    print("🕷️  PASO 1: Ejecutando scraping de Sin Fronteras...")
    print("=" * 60)
    
    try:
        from spiders.sinfronteras_local import main as scraping_main
        
        csv_file, json_file = scraping_main()
        
        if csv_file and json_file:
            print(f"\n✅ Scraping completado exitosamente")
            return csv_file, json_file
        else:
            print(f"\n❌ Error en el scraping")
            return None, None
            
    except Exception as e:
        print(f"❌ Error al ejecutar scraping: {e}")
        return None, None

def run_migration():
    """Ejecutar la migración a PostgreSQL"""
    print(f"\n🗄️  PASO 2: Migrando datos a PostgreSQL...")
    print("=" * 60)
    
    try:
        from migrate_sinfronteras_to_db import main as migration_main
        
        migration_main()
        print(f"\n✅ Migración completada")
        return True
        
    except Exception as e:
        print(f"❌ Error en la migración: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Proceso Completo de Sin Fronteras")
    print("=" * 70)
    print(f"⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Paso 1: Scraping
    csv_file, json_file = run_scraping()
    
    if not csv_file or not json_file:
        print(f"\n❌ El proceso se detuvo debido a errores en el scraping")
        return
    
    # Paso 2: Migración
    migration_success = run_migration()
    
    if not migration_success:
        print(f"\n❌ El proceso se detuvo debido a errores en la migración")
        return
    
    # Resumen final
    print(f"\n" + "=" * 70)
    print(f"🎉 ¡PROCESO COMPLETADO EXITOSAMENTE!")
    print(f"⏰ Finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"=" * 70)
    
    print(f"\n📁 Archivos generados:")
    print(f"   - CSV: {csv_file}")
    print(f"   - JSON: {json_file}")
    
    print(f"\n📊 Datos guardados en:")
    print(f"   - Archivos locales: data/sinfronteras/")
    print(f"   - Base de datos: PostgreSQL (tabla 'noticias')")
    
    print(f"\n📝 Próximos pasos:")
    print(f"1. Verifica los datos en la base de datos")
    print(f"2. Ejecuta otros spiders si es necesario")
    print(f"3. Configura el programador automático")

if __name__ == "__main__":
    main()
