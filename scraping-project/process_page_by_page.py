#!/usr/bin/env python3
"""
Sistema de procesamiento página por página:
1. Extrae datos de una página
2. Migra inmediatamente a la base de datos
3. Continúa con la siguiente página
"""

import os
import sys
import time
from datetime import datetime

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def process_losandes_page_by_page():
    """Procesar Los Andes página por página"""
    print("🕷️  LOS ANDES - PROCESAMIENTO PÁGINA POR PÁGINA")
    print("=" * 60)
    
    try:
        from migrate_losandes_to_db import migrate_from_csv, migrate_from_json
        from spiders.losandes_local import LosAndesSpider
        
        spider = LosAndesSpider()
        total_articles = 0
        page_count = 0
        
        # Obtener todas las páginas
        pages = spider.get_archive_pages()
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
                    temp_csv = f"data/losandes/temp_losandes_{timestamp}.csv"
                    temp_json = f"data/losandes/temp_losandes_{timestamp}.json"
                    
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
        
        print(f"\n✅ Los Andes completado: {total_articles} artículos migrados")
        return total_articles
        
    except Exception as e:
        print(f"❌ Error en Los Andes: {e}")
        return 0

def process_punonoticias_page_by_page():
    """Procesar Puno Noticias página por página"""
    print("\n🕷️  PUNO NOTICIAS - PROCESAMIENTO PÁGINA POR PÁGINA")
    print("=" * 60)
    
    try:
        from migrate_punonoticias_to_db import (migrate_from_csv,
                                                migrate_from_json)
        from spiders.punonoticias_local import PunoNoticiasSpider
        
        spider = PunoNoticiasSpider()
        total_articles = 0
        page_count = 0
        
        # Obtener todas las páginas
        pages = spider.get_archive_pages()
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
                    temp_csv = f"data/punonoticias/temp_punonoticias_{timestamp}.csv"
                    temp_json = f"data/punonoticias/temp_punonoticias_{timestamp}.json"
                    
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
        
        print(f"\n✅ Puno Noticias completado: {total_articles} artículos migrados")
        return total_articles
        
    except Exception as e:
        print(f"❌ Error en Puno Noticias: {e}")
        return 0

def process_pachamama_page_by_page():
    """Procesar Pachamama Radio página por página"""
    print("\n🕷️  PACHAMAMA RADIO - PROCESAMIENTO PÁGINA POR PÁGINA")
    print("=" * 60)
    
    try:
        from migrate_pachamamaradio_to_db import (migrate_from_csv,
                                                  migrate_from_json)
        from spiders.pachamamaradio_local import PachamamaRadioSpider
        
        spider = PachamamaRadioSpider()
        total_articles = 0
        page_count = 0
        
        # Obtener todas las páginas
        pages = spider.get_archive_pages()
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
        return total_articles
        
    except Exception as e:
        print(f"❌ Error en Pachamama Radio: {e}")
        return 0

def process_sinfronteras_page_by_page():
    """Procesar Sin Fronteras página por página"""
    print("\n🕷️  SIN FRONTERAS - PROCESAMIENTO PÁGINA POR PÁGINA")
    print("=" * 60)
    
    try:
        from migrate_sinfronteras_to_db import (migrate_from_csv,
                                                migrate_from_json)
        from spiders.sinfronteras_local import SinFronterasSpider
        
        spider = SinFronterasSpider()
        total_articles = 0
        page_count = 0
        
        # Obtener todas las páginas
        pages = spider.get_archive_pages()
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
                    temp_csv = f"data/sinfronteras/temp_sinfronteras_{timestamp}.csv"
                    temp_json = f"data/sinfronteras/temp_sinfronteras_{timestamp}.json"
                    
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
        
        print(f"\n✅ Sin Fronteras completado: {total_articles} artículos migrados")
        return total_articles
        
    except Exception as e:
        print(f"❌ Error en Sin Fronteras: {e}")
        return 0

def main():
    """Función principal"""
    print("🚀 PROCESAMIENTO PÁGINA POR PÁGINA")
    print("=" * 80)
    print(f"⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print("🎯 Objetivo: Extraer → Migrar → Continuar")
    print("📊 Fuentes: Los Andes, Puno Noticias, Pachamama Radio, Sin Fronteras")
    print("=" * 80)
    
    total_articles = 0
    
    # Procesar cada fuente
    total_articles += process_losandes_page_by_page()
    total_articles += process_punonoticias_page_by_page()
    total_articles += process_pachamama_page_by_page()
    total_articles += process_sinfronteras_page_by_page()
    
    # Resumen final
    print(f"\n" + "=" * 80)
    print(f"🎉 ¡PROCESAMIENTO COMPLETADO!")
    print(f"⏰ Finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Total de artículos migrados: {total_articles}")
    print(f"🗄️  Datos guardados en: PostgreSQL (tabla 'noticias')")
    print(f"=" * 80)

if __name__ == "__main__":
    main()
