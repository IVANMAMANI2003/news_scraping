#!/usr/bin/env python3
"""
Script simple para probar el scraping sin PostgreSQL
"""

import os
import subprocess
import sys
from datetime import datetime


def test_spider_simple(spider_name):
    """Prueba un spider específico sin base de datos"""
    print(f"🕷️  Probando spider: {spider_name}")
    
    try:
        # Ejecutar spider con límite de items y sin pipeline de PostgreSQL
        result = subprocess.run([
            'scrapy', 'crawl', spider_name, 
            '-s', 'CLOSESPIDER_ITEMCOUNT=1',  # Solo 1 item para prueba
            '-s', 'ITEM_PIPELINES={}',  # Sin pipelines
            '-L', 'INFO'
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            # Verificar si se extrajo algún item
            if "item_scraped_count': 0" in result.stdout:
                print(f"⚠️  Spider {spider_name} ejecutado pero no extrajo items")
                print("   Posibles causas:")
                print("   - Los selectores CSS no coinciden con el sitio")
                print("   - El sitio web ha cambiado su estructura")
                print("   - No hay artículos en la página principal")
                return False
            else:
                print(f"✅ Spider {spider_name} funcionando correctamente")
                print(f"📊 Salida: {result.stdout[-300:]}")  # Últimos 300 caracteres
                return True
        else:
            print(f"❌ Error en spider {spider_name}")
            print(f"🔍 Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout en spider {spider_name}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado en spider {spider_name}: {e}")
        return False

def main():
    """Función principal de prueba"""
    print("🧪 Prueba Simple de Spiders de Noticias")
    print("=" * 50)
    
    spiders = ['losandes', 'pachamamaradio', 'punonoticias', 'sinfronteras']
    
    successful = 0
    failed = 0
    
    for spider in spiders:
        print(f"\n🔍 Probando {spider}...")
        if test_spider_simple(spider):
            successful += 1
        else:
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Resumen de pruebas:")
    print(f"✅ Exitosas: {successful}")
    print(f"❌ Fallidas: {failed}")
    
    if successful > 0:
        print("\n🎉 ¡Al menos un spider funciona!")
        print("✅ Los spiders de Scrapy están configurados correctamente")
        print("\n📝 Próximos pasos:")
        print("1. Ajustar los selectores CSS en los spiders")
        print("2. Configurar PostgreSQL")
        print("3. Ejecutar el scraping completo")
    else:
        print("\n⚠️  Los spiders necesitan ajustes")
        print("Los selectores CSS probablemente no coinciden con los sitios web")

if __name__ == "__main__":
    main()
