#!/usr/bin/env python3
"""
Script para iniciar el sistema de scraping SIN Docker
Usa Redis local y PostgreSQL local
"""

import os
import subprocess
import sys
import time
from datetime import datetime


def print_banner():
    print("🚀 SISTEMA DE SCRAPING AUTOMÁTICO (SIN DOCKER)")
    print("=" * 60)
    print(f"⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

def check_services():
    """Verificar servicios necesarios"""
    print("\n🔍 Verificando servicios...")
    
    # Verificar PostgreSQL
    try:
        result = subprocess.run(['psql', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✅ PostgreSQL: {result.stdout.strip()}")
    except:
        print("❌ PostgreSQL no encontrado")
        return False
    
    # Verificar Python
    print(f"✅ Python: {sys.version}")
    
    return True

def start_celery_system():
    """Iniciar sistema Celery"""
    print("\n👷 Iniciando sistema Celery...")
    
    try:
        # Worker de scraping
        print("   🔄 Iniciando worker de scraping...")
        scraping_worker = subprocess.Popen([
            sys.executable, 'celery_workers/start_worker.py', '--queue', 'scraping'
        ])
        
        # Worker de migración
        print("   🔄 Iniciando worker de migración...")
        migration_worker = subprocess.Popen([
            sys.executable, 'celery_workers/start_worker.py', '--queue', 'migration'
        ])
        
        # Scheduler (Beat)
        print("   🔄 Iniciando scheduler (Beat)...")
        beat_scheduler = subprocess.Popen([
            sys.executable, 'celery_workers/start_beat.py'
        ])
        
        print("✅ Sistema Celery iniciado")
        return True
        
    except Exception as e:
        print(f"❌ Error iniciando Celery: {e}")
        return False

def show_instructions():
    """Mostrar instrucciones"""
    print("\n📋 INSTRUCCIONES")
    print("=" * 60)
    print("1. Asegúrate de que PostgreSQL esté ejecutándose")
    print("2. Asegúrate de que Redis esté ejecutándose")
    print("3. El sistema se ejecutará automáticamente cada 6 horas")
    print("4. Los datos se guardan en PostgreSQL")
    print("5. Para detener: Ctrl+C")
    print("\n🔧 Si no tienes Redis instalado:")
    print("   - Descarga desde: https://github.com/microsoftarchive/redis/releases")
    print("   - O usa: docker run -d -p 6379:6379 redis:alpine")

def main():
    """Función principal"""
    print_banner()
    
    # Verificar servicios
    if not check_services():
        print("\n❌ Servicios necesarios no encontrados")
        show_instructions()
        sys.exit(1)
    
    # Mostrar instrucciones
    show_instructions()
    
    # Preguntar si continuar
    response = input("\n¿Continuar con el inicio? (s/n): ").lower()
    if response != 's':
        print("❌ Operación cancelada")
        sys.exit(0)
    
    # Iniciar Celery
    if not start_celery_system():
        print("❌ Error iniciando Celery")
        sys.exit(1)
    
    print("\n🎉 ¡Sistema iniciado correctamente!")
    print("Presiona Ctrl+C para detener")
    
    try:
        # Mantener el script corriendo
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n\n🛑 Deteniendo sistema...")
        print("✅ Sistema detenido")

if __name__ == "__main__":
    main()
