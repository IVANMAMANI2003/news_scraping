#!/usr/bin/env python3
"""
Prueba rápida de Pachamama Radio - Solo 5 páginas
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_quick_pachamama():
    print("⚡ PRUEBA RÁPIDA DE PACHAMAMA RADIO")
    print("=" * 50)
    print("🎯 Solo 5 páginas para prueba rápida")
    
    try:
        from spiders.pachamamaradio_local import PachamamaRadioSpider

        # Crear instancia del spider
        spider = PachamamaRadioSpider()
        
        print("🕷️  Ejecutando scraping rápido...")
        
        # Ejecutar solo las primeras 5 páginas
        articles = []
        page_count = 0
        max_pages = 5
        
        for page_url in spider.get_archive_pages():
            if page_count >= max_pages:
                break
                
            print(f"📄 Procesando página {page_count + 1}/{max_pages}: {page_url}")
            
            try:
                page_articles = spider.scrape_page(page_url)
                articles.extend(page_articles)
                print(f"   ✅ {len(page_articles)} artículos encontrados")
                page_count += 1
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue
        
        print(f"\n📊 Total artículos extraídos: {len(articles)}")
        
        if articles:
            print("✅ ¡Scraping exitoso!")
            print("📝 Primeros 3 artículos:")
            for i, article in enumerate(articles[:3], 1):
                print(f"   {i}. {article.get('titulo', 'Sin título')[:50]}...")
        else:
            print("❌ No se extrajeron artículos")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_quick_pachamama()
