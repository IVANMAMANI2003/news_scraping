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

def run_pachamama_with_immediate_migration():
    """Ejecutar Pachamama Radio con migración inmediata"""
    print("\n🕷️  SPIDER 1: Pachamama Radio - CON MIGRACIÓN INMEDIATA")
    print("=" * 70)
    
    try:
        from migrate_pachamamaradio_to_db import main as migrate_pachamama
        from spiders.pachamamaradio_local import main as pachamama_main
        
        print("🕷️  Ejecutando scraping de Pachamama Radio...")
        
        # Ejecutar scraping completo
        csv_file, json_file = pachamama_main()
        
        if csv_file and json_file:
            print(f"✅ Scraping completado:")
            print(f"   📄 CSV: {csv_file}")
            print(f"   📄 JSON: {json_file}")
            
            # Migrar inmediatamente después del scraping
            print(f"\n🗄️  Migrando datos a PostgreSQL...")
            migrate_pachamama()
            print(f"✅ Migración completada")
            
            return csv_file, json_file
        else:
            print(f"❌ Error en el scraping de Pachamama Radio")
            return None, None
            
    except Exception as e:
        print(f"❌ Error al ejecutar Pachamama Radio: {e}")
        return None, None

def run_punonoticias_with_immediate_migration():
    """Ejecutar Puno Noticias con migración inmediata"""
    print("\n🕷️  SPIDER 2: Puno Noticias - CON MIGRACIÓN INMEDIATA")
    print("=" * 70)
    
    try:
        from migrate_punonoticias_to_db import main as migrate_puno
        from spiders.punonoticias_local import main as puno_main
        
        print("🕷️  Ejecutando scraping de Puno Noticias...")
        
        # Ejecutar scraping completo
        csv_file, json_file = puno_main()
        
        if csv_file and json_file:
            print(f"✅ Scraping completado:")
            print(f"   📄 CSV: {csv_file}")
            print(f"   📄 JSON: {json_file}")
            
            # Migrar inmediatamente después del scraping
            print(f"\n🗄️  Migrando datos a PostgreSQL...")
            migrate_puno()
            print(f"✅ Migración completada")
            
            return csv_file, json_file
        else:
            print(f"❌ Error en el scraping de Puno Noticias")
            return None, None
            
    except Exception as e:
        print(f"❌ Error al ejecutar Puno Noticias: {e}")
        return None, None

def run_sinfronteras_with_immediate_migration():
    """Ejecutar Sin Fronteras con migración inmediata"""
    print("\n🕷️  SPIDER 3: Sin Fronteras - CON MIGRACIÓN INMEDIATA")
    print("=" * 70)
    
    try:
        from migrate_sinfronteras_to_db import main as migrate_sinfronteras
        from spiders.sinfronteras_local import main as sinfronteras_main
        
        print("🕷️  Ejecutando scraping de Sin Fronteras...")
        
        # Ejecutar scraping completo
        csv_file, json_file = sinfronteras_main()
        
        if csv_file and json_file:
            print(f"✅ Scraping completado:")
            print(f"   📄 CSV: {csv_file}")
            print(f"   📄 JSON: {json_file}")
            
            # Migrar inmediatamente después del scraping
            print(f"\n🗄️  Migrando datos a PostgreSQL...")
            migrate_sinfronteras()
            print(f"✅ Migración completada")
            
            return csv_file, json_file
        else:
            print(f"❌ Error en el scraping de Sin Fronteras")
            return None, None
            
    except Exception as e:
        print(f"❌ Error al ejecutar Sin Fronteras: {e}")
        return None, None

def run_losandes_with_immediate_migration():
    """Ejecutar Los Andes con migración inmediata"""
    print("\n🕷️  SPIDER 4: Los Andes - CON MIGRACIÓN INMEDIATA")
    print("=" * 70)
    
    try:
        from migrate_losandes_to_db import main as migrate_losandes
        from spiders.losandes_local import main as losandes_main
        
        print("🕷️  Ejecutando scraping de Los Andes...")
        
        # Ejecutar scraping completo
        csv_file, json_file = losandes_main()
        
        if csv_file and json_file:
            print(f"✅ Scraping completado:")
            print(f"   📄 CSV: {csv_file}")
            print(f"   📄 JSON: {json_file}")
            
            # Migrar inmediatamente después del scraping
            print(f"\n🗄️  Migrando datos a PostgreSQL...")
            migrate_losandes()
            print(f"✅ Migración completada")
            
            return csv_file, json_file
        else:
            print(f"❌ Error en el scraping de Los Andes")
            return None, None
            
    except Exception as e:
        print(f"❌ Error al ejecutar Los Andes: {e}")
        return None, None

def run_pachamama_page_by_page():
    """Ejecutar Pachamama Radio página por página"""
    print("\n🕷️  SPIDER 1: Pachamama Radio - PÁGINA POR PÁGINA")
    print("=" * 70)
    
    try:
        import os
        import time
        from datetime import datetime

        from migrate_pachamamaradio_to_db import migrate_from_csv
        from spiders.pachamamaradio_local import PachamamaRadioLocalScraper
        
        spider = PachamamaRadioLocalScraper()
        total_articles = 0
        page_count = 0
        
        # Obtener todas las páginas
        pages = spider.find_archive_pages()
        print(f"📄 Total de páginas a procesar: {len(pages)}")
        
        for page_url in pages:
            page_count += 1
            print(f"\n📄 Procesando página {page_count}/{len(pages)}: {page_url}")
            
            try:
                # Extraer datos de la página
                articles = spider.scrape_page(page_url)
                print(f"   📰 Artículos encontrados: {len(articles)}")
                
                if articles:
                    # Crear archivos temporales
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    temp_csv = f"data/pachamamaradio/temp_pachamama_{timestamp}.csv"
                    temp_json = f"data/pachamamaradio/temp_pachamama_{timestamp}.json"
                    
                    # Asegurar que el directorio existe
                    os.makedirs(os.path.dirname(temp_csv), exist_ok=True)
                    
                    # Guardar datos temporalmente
                    spider.save_to_files(articles, temp_csv, temp_json)
                    
                    # Migrar inmediatamente
                    print(f"   🗄️  Migrando {len(articles)} artículos...")
                    migrated_count = migrate_from_csv(temp_csv)
                    print(f"   ✅ Migrados: {migrated_count} artículos")
                    
                    total_articles += migrated_count
                    
                    # Limpiar archivos temporales
                    if os.path.exists(temp_csv):
                        os.remove(temp_csv)
                    if os.path.exists(temp_json):
                        os.remove(temp_json)
                else:
                    print("   ⚠️  No se encontraron artículos en esta página")
                
                # Pequeña pausa entre páginas
                time.sleep(1)
                
            except Exception as e:
                print(f"   ❌ Error en página {page_count}: {e}")
                continue
        
        print(f"\n✅ Pachamama Radio completado: {total_articles} artículos migrados")
        return f"data/pachamamaradio/pachamama_completed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", f"data/pachamamaradio/pachamama_completed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
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
    
    # Migrar Pachamama Radio (PRIMERO)
    try:
        print("📄 Migrando Pachamama Radio...")
        from migrate_pachamamaradio_to_db import main as migrate_pachamama
        migrate_pachamama()
        migration_results.append("✅ Pachamama Radio migrado")
    except Exception as e:
        migration_results.append(f"❌ Error migrando Pachamama Radio: {e}")
    
    # Migrar Puno Noticias (SEGUNDO)
    try:
        print("\n📄 Migrando Puno Noticias...")
        from migrate_punonoticias_to_db import main as migrate_puno
        migrate_puno()
        migration_results.append("✅ Puno Noticias migrado")
    except Exception as e:
        migration_results.append(f"❌ Error migrando Puno Noticias: {e}")
    
    # Migrar Sin Fronteras (TERCERO)
    try:
        print("\n📄 Migrando Sin Fronteras...")
        from migrate_sinfronteras_to_db import main as migrate_sinfronteras
        migrate_sinfronteras()
        migration_results.append("✅ Sin Fronteras migrado")
    except Exception as e:
        migration_results.append(f"❌ Error migrando Sin Fronteras: {e}")
    
    # Migrar Los Andes (CUARTO)
    try:
        print("\n📄 Migrando Los Andes...")
        from migrate_losandes_to_db import main as migrate_losandes
        migrate_losandes()
        migration_results.append("✅ Los Andes migrado")
    except Exception as e:
        migration_results.append(f"❌ Error migrando Los Andes: {e}")
    
    return migration_results

def main():
    """Función principal"""
    print("🚀 SCRAPING COMPLETO DE TODAS LAS FUENTES")
    print("=" * 80)
    print(f"⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print("🎯 Objetivo: Extraer TODAS las noticias sin límites")
    print("📊 Fuentes: Pachamama Radio, Puno Noticias, Sin Fronteras, Los Andes")
    print("=" * 80)
    
    results = {}
    
    # Ejecutar Pachamama Radio (PRIMERO) - CON MIGRACIÓN INMEDIATA
    pachamama_csv, pachamama_json = run_pachamama_with_immediate_migration()
    results['pachamama'] = {'csv': pachamama_csv, 'json': pachamama_json}
    
    # Ejecutar Puno Noticias (SEGUNDO) - CON MIGRACIÓN INMEDIATA
    puno_csv, puno_json = run_punonoticias_with_immediate_migration()
    results['punonoticias'] = {'csv': puno_csv, 'json': puno_json}
    
    # Ejecutar Sin Fronteras (TERCERO) - CON MIGRACIÓN INMEDIATA
    sinfronteras_csv, sinfronteras_json = run_sinfronteras_with_immediate_migration()
    results['sinfronteras'] = {'csv': sinfronteras_csv, 'json': sinfronteras_json}
    
    # Ejecutar Los Andes (CUARTO) - CON MIGRACIÓN INMEDIATA
    losandes_csv, losandes_json = run_losandes_with_immediate_migration()
    results['losandes'] = {'csv': losandes_csv, 'json': losandes_json}
    
    # Las migraciones se realizan inmediatamente después de cada scraping
    migration_results = ["✅ Todas las migraciones completadas inmediatamente"]
    
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
