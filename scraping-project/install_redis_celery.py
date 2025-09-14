#!/usr/bin/env python3
"""
Script para instalar y configurar Redis y Celery
"""

import os
import platform
import subprocess
import sys


def install_requirements():
    """Instalar dependencias de Python"""
    print("📦 Instalando dependencias de Python...")
    
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', 'api/requirements.txt'
        ])
        print("✅ Dependencias instaladas correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        return False

def install_redis():
    """Instalar Redis según el sistema operativo"""
    print("🔴 Instalando Redis...")
    
    system = platform.system().lower()
    
    try:
        if system == 'windows':
            print("ℹ️ Para Windows, instala Redis desde:")
            print("   https://github.com/microsoftarchive/redis/releases")
            print("   O usa Docker: docker run -d -p 6379:6379 redis:alpine")
            return True
        elif system == 'linux':
            # Ubuntu/Debian
            subprocess.check_call(['sudo', 'apt-get', 'update'])
            subprocess.check_call(['sudo', 'apt-get', 'install', '-y', 'redis-server'])
            subprocess.check_call(['sudo', 'systemctl', 'start', 'redis-server'])
            subprocess.check_call(['sudo', 'systemctl', 'enable', 'redis-server'])
        elif system == 'darwin':  # macOS
            subprocess.check_call(['brew', 'install', 'redis'])
            subprocess.check_call(['brew', 'services', 'start', 'redis'])
        else:
            print(f"❌ Sistema operativo no soportado: {system}")
            return False
        
        print("✅ Redis instalado correctamente")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando Redis: {e}")
        return False
    except FileNotFoundError:
        print("❌ Comando no encontrado. Instala Redis manualmente.")
        return False

def test_redis_connection():
    """Probar conexión a Redis"""
    print("🔍 Probando conexión a Redis...")
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Conexión a Redis exitosa")
        return True
    except Exception as e:
        print(f"❌ Error conectando a Redis: {e}")
        return False

def test_celery():
    """Probar Celery"""
    print("🔧 Probando Celery...")
    
    try:
        from celery_app import celery_app
        print("✅ Celery configurado correctamente")
        return True
    except Exception as e:
        print(f"❌ Error configurando Celery: {e}")
        return False

def create_directories():
    """Crear directorios necesarios"""
    print("📁 Creando directorios...")
    
    directories = [
        'celery_tasks',
        'celery_workers', 
        'redis_data',
        'logs'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"   ✅ {directory}/")
    
    return True

def create_env_file():
    """Crear archivo .env si no existe"""
    print("⚙️ Configurando variables de entorno...")
    
    env_file = '.env'
    if not os.path.exists(env_file):
        with open(env_file, 'w') as f:
            f.write("""# Configuración de Redis
REDIS_URL=redis://localhost:6379/0

# Configuración de Base de Datos
DATABASE_URL=postgresql://postgres:123456@localhost:5432/noticias

# Configuración de Scraping
SCRAPING_INTERVAL_HOURS=6
DUPLICATE_CHECK_ENABLED=true

# Configuración de Logging
LOG_LEVEL=INFO
""")
        print(f"✅ Archivo {env_file} creado")
    else:
        print(f"ℹ️ Archivo {env_file} ya existe")
    
    return True

def main():
    print("🚀 INSTALADOR DE REDIS Y CELERY")
    print("=" * 50)
    
    success = True
    
    # 1. Crear directorios
    if not create_directories():
        success = False
    
    # 2. Crear archivo .env
    if not create_env_file():
        success = False
    
    # 3. Instalar dependencias de Python
    if not install_requirements():
        success = False
    
    # 4. Instalar Redis
    if not install_redis():
        success = False
    
    # 5. Probar conexión a Redis
    if not test_redis_connection():
        success = False
    
    # 6. Probar Celery
    if not test_celery():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ¡Instalación completada exitosamente!")
        print("\n📋 Próximos pasos:")
        print("1. Iniciar Redis: redis-server")
        print("2. Iniciar workers: python start_redis_celery.py")
        print("3. Disparar scraping: python celery_workers/control_tasks.py trigger-scraping")
    else:
        print("❌ Instalación completada con errores")
        print("Revisa los mensajes anteriores para más detalles")
    
    return success

if __name__ == '__main__':
    main()
