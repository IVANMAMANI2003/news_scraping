#!/usr/bin/env python3
"""
Script maestro para ejecutar TODOS los spiders completos sin límites:
1. Los Andes - Extrae TODAS las noticias
2. Puno Noticias - Extrae TODAS las noticias  
3. Pachamama Radio - Extrae TODAS las noticias
4. Sin Fronteras - Extrae TODAS las noticias
5. Migra todo a PostgreSQL
"""

import os
import sys
from datetime import datetime

# Agregar el directorio actual al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_losandes_complete():
    """Ejecutar scraping COMPLETO de Los Andes"""
    print("🕷️  SPIDER 1: Los Andes - SCRAPING COMPLETO")
    print("=" * 70)
    
    try:
        from spiders.losandes_local import main as losandes_main
        
        csv_file, json_file = losandes_main()
        
        if csv_file and json_file:
            print(f"\n✅ Los Andes completado exitosamente")
            return csv_file, json_file
        else:
            print(f"\n❌ Error en Los Andes")
            return None, None
            
    except Exception as e:
        print(f"❌ Error al ejecutar Los Andes: {e}")
        return None, None

def run_punonoticias_complete():
    """Ejecutar scraping COMPLETO de Puno Noticias"""
    print("\n🕷️  SPIDER 2: Puno Noticias - SCRAPING COMPLETO")
    print("=" * 70)
    
    try:
        from spiders.punonoticias_local import main as puno_main
        
        csv_file, json_file = puno_main()
        
        if csv_file and json_file:
            print(f"\n✅ Puno Noticias completado exitosamente")
            return csv_file, json_file
        else:
            print(f"\n❌ Error en Puno Noticias")
            return None, None
            
    except Exception as e:
        print(f"❌ Error al ejecutar Puno Noticias: {e}")
        return None, None

def run_pachamama_complete():
    """Ejecutar scraping COMPLETO de Pachamama Radio"""
    print("\n🕷️  SPIDER 3: Pachamama Radio - SCRAPING COMPLETO")
    print("=" * 70)
    
    try:
        from spiders.pachamamaradio_local import main as pachamama_main
        
        csv_file, json_file = pachamama_main()
        
        if csv_file and json_file:
            print(f"\n✅ Pachamama Radio completado exitosamente")
            return csv_file, json_file
        else:
            print(f"\n❌ Error en Pachamama Radio")
            return None, None
            
    except Exception as e:
        print(f"❌ Error al ejecutar Pachamama Radio: {e}")
        return None, None

def run_sinfronteras_complete():
    """Ejecutar scraping COMPLETO de Sin Fronteras"""
    print("\n🕷️  SPIDER 4: Sin Fronteras - SCRAPING COMPLETO")
    print("=" * 70)
    
    try:
        from spiders.sinfronteras_local import main as sinfronteras_main
        
        csv_file, json_file = sinfronteras_main()
        
        if csv_file and json_file:
            print(f"\n✅ Sin Fronteras completado exitosamente")
            return csv_file, json_file
        else:
            print(f"\n❌ Error en Sin Fronteras")
            return None, None
            
    except Exception as e:
        print(f"❌ Error al ejecutar Sin Fronteras: {e}")
        return None, None

def migrate_all_to_database():
    """Migrar todos los datos a PostgreSQL"""
    print("\n🗄️  MIGRACIÓN A POSTGRESQL")
    print("=" * 70)
    
    migration_results = []
    
    # Migrar Los Andes
    try:
        print("📄 Migrando Los Andes...")
        from migrate_losandes_to_db import main as migrate_losandes
        migrate_losandes()
        migration_results.append("✅ Los Andes migrado")
    except Exception as e:
        migration_results.append(f"❌ Error migrando Los Andes: {e}")
    
    # Migrar Puno Noticias
    try:
        print("\n📄 Migrando Puno Noticias...")
        from migrate_punonoticias_to_db import main as migrate_puno
        migrate_puno()
        migration_results.append("✅ Puno Noticias migrado")
    except Exception as e:
        migration_results.append(f"❌ Error migrando Puno Noticias: {e}")
    
    # Migrar Pachamama Radio
    try:
        print("\n📄 Migrando Pachamama Radio...")
        from migrate_pachamamaradio_to_db import main as migrate_pachamama
        migrate_pachamama()
        migration_results.append("✅ Pachamama Radio migrado")
    except Exception as e:
        migration_results.append(f"❌ Error migrando Pachamama Radio: {e}")
    
    # Migrar Sin Fronteras
    try:
        print("\n📄 Migrando Sin Fronteras...")
        from migrate_sinfronteras_to_db import main as migrate_sinfronteras
        migrate_sinfronteras()
        migration_results.append("✅ Sin Fronteras migrado")
    except Exception as e:
        migration_results.append(f"❌ Error migrando Sin Fronteras: {e}")
    
    return migration_results

def main():
    """Función principal"""
    print("🚀 SCRAPING COMPLETO DE TODAS LAS FUENTES")
    print("=" * 80)
    print(f"⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print("🎯 Objetivo: Extraer TODAS las noticias sin límites")
    print("📊 Fuentes: Los Andes, Puno Noticias, Pachamama Radio, Sin Fronteras")
    print("=" * 80)
    
    results = {}
    
    # Ejecutar Los Andes
    losandes_csv, losandes_json = run_losandes_complete()
    results['losandes'] = {'csv': losandes_csv, 'json': losandes_json}
    
    # Ejecutar Puno Noticias
    puno_csv, puno_json = run_punonoticias_complete()
    results['punonoticias'] = {'csv': puno_csv, 'json': puno_json}
    
    # Ejecutar Pachamama Radio
    pachamama_csv, pachamama_json = run_pachamama_complete()
    results['pachamama'] = {'csv': pachamama_csv, 'json': pachamama_json}
    
    # Ejecutar Sin Fronteras
    sinfronteras_csv, sinfronteras_json = run_sinfronteras_complete()
    results['sinfronteras'] = {'csv': sinfronteras_csv, 'json': sinfronteras_json}
    
    # Migrar todo a la base de datos
    migration_results = migrate_all_to_database()
    
    # Resumen final
    print(f"\n" + "=" * 80)
    print(f"🎉 ¡SCRAPING COMPLETO FINALIZADO!")
    print(f"⏰ Finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"=" * 80)
    
    print(f"\n📁 Archivos generados:")
    for source, files in results.items():
        if files['csv'] and files['json']:
            print(f"   {source.upper()}:")
            print(f"     - CSV: {files['csv']}")
            print(f"     - JSON: {files['json']}")
        else:
            print(f"   {source.upper()}: ❌ Error en la generación")
    
    print(f"\n🗄️  Resultados de migración:")
    for result in migration_results:
        print(f"   {result}")
    
    print(f"\n📊 Datos guardados en:")
    print(f"   - Archivos locales: data/losandes/, data/punonoticias/, data/pachamamaradio/, data/sinfronteras/")
    print(f"   - Base de datos: PostgreSQL (tabla 'noticias')")
    
    print(f"\n📝 Próximos pasos:")
    print(f"1. Verifica los datos en la base de datos")
    print(f"2. Revisa los archivos CSV/JSON generados")
    print(f"3. Configura el programador automático si es necesario")

if __name__ == "__main__":
    main()
