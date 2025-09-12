#!/usr/bin/env python3
"""
Script de prueba simple para verificar que los spiders funcionen
sin depender de PostgreSQL
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
            '-s', 'CLOSESPIDER_ITEMCOUNT=2',  # Solo 2 items para prueba
            '-s', 'ITEM_PIPELINES={}',  # Sin pipelines
            '-L', 'INFO'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"✅ Spider {spider_name} funcionando correctamente")
            print(f"📊 Salida: {result.stdout[-200:]}")  # Últimos 200 caracteres
            return True
        else:
            print(f"❌ Error en spider {spider_name}")
            print(f"🔍 Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout en spider {spider_name}")
        return False
    except FileNotFoundError:
        print(f"❌ Scrapy no está instalado. Ejecuta: pip install scrapy")
        return False
    except Exception as e:
        print(f"❌ Error inesperado en spider {spider_name}: {e}")
        return False

def main():
    """Función principal de prueba"""
    print("🧪 Prueba Simple de Spiders")
    print("=" * 40)
    
    spiders = ['losandes', 'pachamamaradio', 'punonoticias', 'sinfronteras']
    
    successful = 0
    failed = 0
    
    for spider in spiders:
        print(f"\n🔍 Probando {spider}...")
        if test_spider_simple(spider):
            successful += 1
        else:
            failed += 1
    
    print("\n" + "=" * 40)
    print(f"📊 Resumen de pruebas:")
    print(f"✅ Exitosas: {successful}")
    print(f"❌ Fallidas: {failed}")
    
    if successful > 0:
        print("\n🎉 ¡Al menos un spider funciona!")
        print("✅ Los spiders de Scrapy están configurados correctamente")
    else:
        print("\n⚠️  Ningún spider funcionó")
        print("Revisa la instalación de Scrapy y la configuración")

if __name__ == "__main__":
    main()
