#!/usr/bin/env python3
"""
Script para iniciar el sistema de producción completo
"""

import subprocess
import sys
import time
from datetime import datetime


def print_banner():
    print("🚀 SISTEMA DE PRODUCCIÓN - SCRAPING AUTOMÁTICO")
    print("=" * 60)
    print(f"⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

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
    """Iniciar contenedores de producción"""
    print("\n🐳 Iniciando sistema de producción...")
    
    try:
        # Detener contenedores existentes
        subprocess.run(['docker-compose', '-f', 'docker-compose-production.yml', 'down'], 
                      capture_output=True)
        
        # Construir e iniciar contenedores
        result = subprocess.run(['docker-compose', '-f', 'docker-compose-production.yml', 'up', '-d', '--build'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Sistema de producción iniciado")
            return True
        else:
            print(f"❌ Error iniciando sistema: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def wait_for_services():
    """Esperar a que los servicios estén listos"""
    print("\n⏳ Esperando que los servicios estén listos...")
    
    # Esperar PostgreSQL
    print("   🔄 Verificando PostgreSQL...")
    for i in range(30):
        try:
            result = subprocess.run(['docker', 'exec', 'news_postgres_prod', 'pg_isready', '-U', 'postgres'], 
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
    
    # Esperar Redis
    print("   🔄 Verificando Redis...")
    for i in range(30):
        try:
            result = subprocess.run(['docker', 'exec', 'news_redis_prod', 'redis-cli', 'ping'], 
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
    
    return True

def show_status():
    """Mostrar estado del sistema"""
    print("\n📊 ESTADO DEL SISTEMA")
    print("=" * 60)
    print("🐳 Contenedores:")
    subprocess.run(['docker', 'ps', '--filter', 'name=news_'], check=False)
    
    print("\n📝 Servicios disponibles:")
    print("   - PostgreSQL: localhost:5432")
    print("   - Redis: localhost:6379")
    print("   - API: http://localhost:8000")
    print("   - Celery Worker: Procesando tareas")
    print("   - Celery Beat: Programando tareas cada 6 horas")
    
    print("\n🔧 Comandos útiles:")
    print("   - Ver logs: docker logs news_celery_worker")
    print("   - Backup: python backup_restore.py")
    print("   - Detener: docker-compose -f docker-compose-production.yml down")

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
    
    # Mostrar estado
    show_status()
    
    print("\n🎉 ¡Sistema de producción iniciado correctamente!")
    print("📊 El sistema se ejecutará automáticamente cada 6 horas")
    print("🔄 Los datos se guardan en PostgreSQL en Docker")
    print("💾 Usa 'python backup_restore.py' para hacer backup")
    
    print("\n⏰ El sistema continuará ejecutándose...")
    print("Presiona Ctrl+C para detener")

if __name__ == "__main__":
    main()
