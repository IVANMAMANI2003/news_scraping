#!/usr/bin/env python3
"""
Script para verificar localmente que cada spider esté funcionando correctamente
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from scraper.spiders.pachamamaradio import PachamamaradioSpider
from scraper.spiders.punonoticias import PunonoticiasSpider
from scraper.spiders.sinfronteras import SinfronterasSpider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


def test_spider(spider_class, spider_name):
    """Prueba un spider individualmente"""
    print(f"\n{'='*70}")
    print(f"🔍 Probando spider: {spider_name}")
    print(f"{'='*70}")
    
    try:
        # Configurar Scrapy
        settings = get_project_settings()
        settings.set('LOG_LEVEL', 'INFO')
        settings.set('DOWNLOAD_DELAY', 2)  # Delay más largo para pruebas
        settings.set('CONCURRENT_REQUESTS', 1)
        settings.set('ITEM_PIPELINES', {})  # Deshabilitar pipelines para pruebas rápidas
        settings.set('FEEDS', {})  # Deshabilitar feeds
        
        # Crear proceso de crawler
        process = CrawlerProcess(settings)
        
        # Agregar spider
        process.crawl(spider_class)
        
        # Ejecutar
        process.start()
        
        print(f"✅ Spider {spider_name} completado exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en spider {spider_name}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    print("\n" + "="*70)
    print("🧪 VERIFICACIÓN LOCAL DE SPIDERS")
    print("="*70)
    
    spiders_to_test = [
        (PachamamaradioSpider, "pachamamaradio"),
        (PunonoticiasSpider, "punonoticias"),
        (SinfronterasSpider, "sinfronteras"),
    ]
    
    results = {}
    
    for spider_class, spider_name in spiders_to_test:
        result = test_spider(spider_class, spider_name)
        results[spider_name] = result
    
    # Resumen
    print("\n" + "="*70)
    print("📊 RESUMEN DE PRUEBAS")
    print("="*70)
    
    for spider_name, result in results.items():
        status = "✅ OK" if result else "❌ ERROR"
        print(f"  {status} - {spider_name}")
    
    print("\n" + "="*70)
    print("⚠️  NOTA: Los Andes no es un spider de Scrapy válido")
    print("   Necesita ser convertido a un spider de Scrapy")
    print("="*70 + "\n")
    
    # Retornar código de salida
    all_passed = all(results.values())
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())

