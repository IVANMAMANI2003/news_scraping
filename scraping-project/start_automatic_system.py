#!/usr/bin/env python3
"""
Script para iniciar el sistema completo de scraping automático
Incluye: Redis, PostgreSQL, Celery Workers y Beat
"""

import os
import subprocess
import sys
import time
from datetime import datetime


def print_banner():
    print("🚀 SISTEMA DE SCRAPING AUTOMÁTICO")
    print("=" * 50)
    print(f"⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

def check_docker():
    """Verificar que Docker esté funcionando"""
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✅ Docker: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker no está instalado o no funciona")
        return False

def start_containers():
    """Iniciar contenedores de Redis y PostgreSQL"""
    print("\n🐳 Iniciando contenedores Docker...")
    
    try:
        # Detener contenedores existentes
        subprocess.run(['docker-compose', '-f', 'docker-compose-full.yml', 'down'], 
                      capture_output=True)
        
        # Iniciar contenedores
        result = subprocess.run(['docker-compose', '-f', 'docker-compose-full.yml', 'up', '-d'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Contenedores iniciados correctamente")
            return True
        else:
            print(f"❌ Error iniciando contenedores: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error con Docker: {e}")
        return False

def wait_for_services():
    """Esperar a que los servicios estén listos"""
    print("\n⏳ Esperando que los servicios estén listos...")
    
    # Esperar Redis
    print("   🔄 Verificando Redis...")
    for i in range(30):
        try:
            result = subprocess.run(['docker', 'exec', 'news_redis', 'redis-cli', 'ping'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and 'PONG' in result.stdout:
                print("   ✅ Redis listo")
                break
        except:
            pass
        time.sleep(2)
    else:
        print("   ❌ Redis no responde")
        return False
    
    # Esperar PostgreSQL
    print("   🔄 Verificando PostgreSQL...")
    for i in range(30):
        try:
            result = subprocess.run(['docker', 'exec', 'news_postgres', 'pg_isready', '-U', 'news_user', '-d', 'news_db'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("   ✅ PostgreSQL listo")
                break
        except:
            pass
        time.sleep(2)
    else:
        print("   ❌ PostgreSQL no responde")
        return False
    
    return True

def start_celery_workers():
    """Iniciar workers de Celery"""
    print("\n👷 Iniciando workers de Celery...")
    
    try:
        # Worker de scraping
        print("   🔄 Iniciando worker de scraping...")
        scraping_worker = subprocess.Popen([
            sys.executable, 'celery_workers/start_worker.py', '--queue', 'scraping'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Worker de migración
        print("   🔄 Iniciando worker de migración...")
        migration_worker = subprocess.Popen([
            sys.executable, 'celery_workers/start_worker.py', '--queue', 'migration'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Scheduler (Beat)
        print("   🔄 Iniciando scheduler (Beat)...")
        beat_scheduler = subprocess.Popen([
            sys.executable, 'celery_workers/start_beat.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("✅ Workers de Celery iniciados")
        return True
        
    except Exception as e:
        print(f"❌ Error iniciando workers: {e}")
        return False

def show_status():
    """Mostrar estado del sistema"""
    print("\n📊 ESTADO DEL SISTEMA")
    print("=" * 50)
    print("🐳 Contenedores Docker:")
    subprocess.run(['docker', 'ps', '--filter', 'name=news_'], check=False)
    
    print("\n👷 Procesos Python:")
    subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], check=False)
    
    print("\n📝 Próximos pasos:")
    print("1. El sistema se ejecutará automáticamente cada 6 horas")
    print("2. Los datos se guardan en PostgreSQL")
    print("3. Para detener: Ctrl+C")
    print("4. Para ver logs: docker logs news_redis o news_postgres")

def main():
    """Función principal"""
    print_banner()
    
    # Verificar Docker
    if not check_docker():
        sys.exit(1)
    
    # Iniciar contenedores
    if not start_containers():
        sys.exit(1)
    
    # Esperar servicios
    if not wait_for_services():
        print("❌ Los servicios no están listos")
        sys.exit(1)
    
    # Iniciar Celery
    if not start_celery_workers():
        print("❌ Error iniciando Celery")
        sys.exit(1)
    
    # Mostrar estado
    show_status()
    
    print("\n🎉 ¡Sistema iniciado correctamente!")
    print("Presiona Ctrl+C para detener")
    
    try:
        # Mantener el script corriendo
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n\n🛑 Deteniendo sistema...")
        subprocess.run(['docker-compose', '-f', 'docker-compose-full.yml', 'down'])
        print("✅ Sistema detenido")

if __name__ == "__main__":
    main()
