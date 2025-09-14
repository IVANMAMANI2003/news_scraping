#!/usr/bin/env python3
"""
Prueba del sistema página por página con Pachamama Radio
"""

import os
import sys
import time
from datetime import datetime

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_pachamama_page_by_page():
    """Probar Pachamama Radio página por página"""
    print("🧪 PRUEBA: PACHAMAMA RADIO PÁGINA POR PÁGINA")
    print("=" * 60)
    print(f"⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        from migrate_pachamamaradio_to_db import migrate_from_csv
        from spiders.pachamamaradio_local import PachamamaRadioLocalScraper
        
        spider = PachamamaRadioLocalScraper()
        total_articles = 0
        page_count = 0
        
        # Obtener todas las páginas
        pages = spider.get_archive_pages()
        print(f"📄 Total de páginas a procesar: {len(pages)}")
        
        # Procesar solo las primeras 3 páginas para la prueba
        max_pages = min(3, len(pages))
        print(f"🎯 Procesando solo las primeras {max_pages} páginas para la prueba")
        
        for i in range(max_pages):
            page_url = pages[i]
            page_count += 1
            print(f"\n📄 Procesando página {page_count}/{max_pages}: {page_url}")
            
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
                time.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Error en página {page_count}: {e}")
                continue
        
        print(f"\n✅ Prueba completada: {total_articles} artículos migrados")
        return total_articles
        
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    test_pachamama_page_by_page()
