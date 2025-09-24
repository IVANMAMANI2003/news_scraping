#!/usr/bin/env python3
"""
Script simplificado para iniciar el sistema en Docker
"""

import os
import subprocess
import sys
import time
from datetime import datetime


def print_banner():
    print("🐳 SISTEMA DOCKER - SCRAPING AUTOMÁTICO")
    print("=" * 60)
    print(f"⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

def wait_for_database():
    """Esperar a que la base de datos esté lista"""
    print("🔄 Esperando que PostgreSQL esté listo...")
    
    for i in range(60):  # Esperar hasta 2 minutos
        try:
            from config.database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            print("✅ PostgreSQL conectado")
            return True
        except Exception as e:
            if i % 10 == 0:  # Mostrar cada 20 segundos
                print(f"   ⏳ Intento {i+1}/60: {e}")
            time.sleep(2)
    
    print("❌ No se pudo conectar a PostgreSQL")
    return False

def run_scraping():
    """Ejecutar scraping completo"""
    print("🕷️  Ejecutando scraping completo...")
    
    try:
        from run_all_spiders_complete import main as run_scraping
        run_scraping()
        print("✅ Scraping completado")
        return True
    except Exception as e:
        print(f"❌ Error en scraping: {e}")
        return False

def start_api():
    """Iniciar API FastAPI"""
    print("🔄 Iniciando API...")
    
    try:
        # Iniciar API en background
        process = subprocess.Popen([
            'uvicorn', 'api.main:app', 
            '--host', '0.0.0.0', '--port', '8000'
        ])
        
        print("✅ API iniciada en http://0.0.0.0:8000")
        return process
    except Exception as e:
        print(f"❌ Error iniciando API: {e}")
        return None

def main():
    """Función principal"""
    print_banner()
    
    # Esperar base de datos
    if not wait_for_database():
        sys.exit(1)
    
    # Ejecutar scraping inicial
    print("\n🚀 Ejecutando scraping inicial...")
    run_scraping()
    
    # Iniciar API
    api_process = start_api()
    
    if not api_process:
        print("❌ Error iniciando API")
        sys.exit(1)
    
    # Mostrar estado
    print("\n📊 SISTEMA INICIADO CORRECTAMENTE")
    print("=" * 60)
    print("🐳 Servicios activos:")
    print("   - PostgreSQL: Base de datos")
    print("   - Redis: Broker de tareas")
    print("   - API: http://0.0.0.0:8000")
    
    print("\n🔧 Comandos útiles:")
    print("   - Ver logs: docker logs news_system_complete")
    print("   - Backup: python backup_restore.py")
    print("   - Detener: docker-compose -f docker-compose-production.yml down")
    
    print("\n✅ El sistema está funcionando")
    print("💡 Puedes cerrar Cursor y el sistema seguirá funcionando")
    
    # Mantener el proceso activo
    try:
        while True:
            time.sleep(60)  # Verificar cada minuto
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo sistema...")
        if api_process:
            api_process.terminate()
        print("✅ Sistema detenido")

if __name__ == "__main__":
    main()
