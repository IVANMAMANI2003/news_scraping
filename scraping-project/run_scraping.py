#!/usr/bin/env python3
"""
Script principal para ejecutar el scraping de noticias
"""

import os
import subprocess
import sys
import time
from datetime import datetime


def run_spider(spider_name):
    """Ejecuta un spider específico"""
    try:
        print(f"🕷️  Ejecutando spider: {spider_name}")
        print(f"⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 50)
        
        # Ejecutar el spider
        result = subprocess.run([
            'scrapy', 'crawl', spider_name
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            print(f"✅ Spider {spider_name} ejecutado correctamente")
            print(f"📊 Salida: {result.stdout}")
        else:
            print(f"❌ Error en spider {spider_name}")
            print(f"🔍 Error: {result.stderr}")
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error al ejecutar spider {spider_name}: {e}")
        return False

def run_all_spiders():
    """Ejecuta todos los spiders disponibles"""
    spiders = [
        'losandes',
        'pachamamaradio', 
        'punonoticias',
        'sinfronteras'
    ]
    
    print("🚀 Iniciando scraping de todas las fuentes...")
    print("=" * 60)
    
    successful = 0
    failed = 0
    
    for spider in spiders:
        if run_spider(spider):
            successful += 1
        else:
            failed += 1
        
        # Pausa entre spiders para ser respetuoso
        if spider != spiders[-1]:  # No pausar después del último
            print(f"⏳ Esperando 30 segundos antes del siguiente spider...")
            time.sleep(30)
    
    print("\n" + "=" * 60)
    print(f"📈 Resumen de ejecución:")
    print(f"✅ Exitosos: {successful}")
    print(f"❌ Fallidos: {failed}")
    print(f"⏰ Finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def run_single_spider():
    """Ejecuta un spider específico seleccionado por el usuario"""
    spiders = [
        'losandes',
        'pachamamaradio', 
        'punonoticias',
        'sinfronteras'
    ]
    
    print("🕷️  Spiders disponibles:")
    for i, spider in enumerate(spiders, 1):
        print(f"  {i}. {spider}")
    
    try:
        choice = int(input("\nSelecciona un spider (número): ")) - 1
        if 0 <= choice < len(spiders):
            selected_spider = spiders[choice]
            run_spider(selected_spider)
        else:
            print("❌ Selección inválida")
    except ValueError:
        print("❌ Por favor ingresa un número válido")

def main():
    """Función principal"""
    print("📰 Sistema de Scraping de Noticias")
    print("=" * 40)
    print("1. Ejecutar todos los spiders")
    print("2. Ejecutar un spider específico")
    print("3. Salir")
    
    try:
        choice = input("\nSelecciona una opción (1-3): ").strip()
        
        if choice == '1':
            run_all_spiders()
        elif choice == '2':
            run_single_spider()
        elif choice == '3':
            print("👋 ¡Hasta luego!")
            sys.exit(0)
        else:
            print("❌ Opción inválida")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Ejecución interrumpida por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
